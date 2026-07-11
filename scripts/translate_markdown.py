#!/usr/bin/env python3
"""Translate a paper's English Markdown (from convert_to_markdown.py) into
Japanese via LiteLLM, falling back openai -> gemini so a single provider
outage or rate limit doesn't stall the pipeline.

Usage: translate_markdown.py <paper_dir> [--force]

Reads:
  <paper_dir>/.translate/paper_en.md

Writes:
  <paper_dir>/.translate/paper_ja_raw.md   Translated Markdown. {{CITE:N}} /
                                            {{BIBSTART:N}} markers, image
                                            refs, LaTeX, code fences and URLs
                                            are preserved verbatim; the
                                            References section is left
                                            untranslated.
  <paper_dir>/.translate/chunks/NNN.json   Per-chunk cache keyed by a hash of
                                            the source chunk text, so an
                                            interrupted run resumes without
                                            re-billing already-translated
                                            chunks, and edits to paper_en.md
                                            only re-translate the chunks that
                                            actually changed.

Env vars (see .env.local.example):
  OPENAI_API_KEY, GEMINI_API_KEY   at least one must be set
  TRANSLATE_MODEL                  default: openai/gpt-5.6-terra
  TRANSLATE_FALLBACK_MODEL         default: gemini/gemini-3.1-flash-lite
  TRANSLATE_SLEEP                  seconds between chunk calls, default 5
"""
import hashlib
import json
import logging
import os
import re
import sys
import time
from pathlib import Path

try:
    from .openai_daily_quota import (
        DailyQuotaGuard,
        estimate_request_tokens,
        is_openai_model,
        response_total_tokens,
    )
except ImportError:  # Direct script execution.
    from openai_daily_quota import (
        DailyQuotaGuard,
        estimate_request_tokens,
        is_openai_model,
        response_total_tokens,
    )

sys.path.insert(0, str(Path(__file__).resolve().parent))
from convert_to_markdown import REFERENCES_HEADING  # noqa: E402

CHUNK_CHAR_LIMIT = 12000
FENCE_RE = re.compile(r"^```")
CITE_RE = re.compile(r"\{\{CITE:\d+\}\}")
BIBSTART_RE = re.compile(r"\{\{BIBSTART:\d+\}\}")
IMAGE_RE = re.compile(r"!\[\]\(assets/[^)]+\)")

SYSTEM_PROMPT = """You are translating an academic paper's Markdown from English to Japanese (である調, academic style).

Rules you must follow exactly:
- Preserve every `{{CITE:N}}` and `{{BIBSTART:N}}` marker character-for-character, in the same position relative to the surrounding sentence.
- Preserve every image reference like `![](assets/fig01.png)` character-for-character.
- Preserve LaTeX math delimited by `$...$` or `$$...$$` exactly; do not translate or alter anything inside the delimiters.
- Preserve fenced code blocks (```...```) exactly, including their contents.
- Preserve URLs and Markdown link syntax exactly.
- Preserve table structure exactly: keep every pipe (`|`) and separator row of Markdown tables, and keep all `<table>`/`<tr>`/`<td>`/`<th>` HTML tags and their attributes unchanged. Translate only the visible cell text, never the tags, alignment rows, or math inside cells.
- Keep heading levels (#, ##, ...) unchanged.
- Keep proper nouns, model/method names, and dataset names in English.
- Translate all other prose into natural, precise academic Japanese.
- Output ONLY the translated Markdown. No commentary, no code fences wrapping the whole output.
"""


def split_blocks(text: str) -> list[str]:
    blocks = []
    buf: list[str] = []
    in_fence = False

    def flush():
        if buf:
            blocks.append("\n".join(buf))
            buf.clear()

    for line in text.split("\n"):
        if not in_fence and line.strip() == "":
            flush()
            continue
        buf.append(line)
        if FENCE_RE.match(line.strip()):
            in_fence = not in_fence
    flush()
    return blocks


def pack_chunks(blocks: list[str], limit: int = CHUNK_CHAR_LIMIT) -> list[str]:
    chunks = []
    cur: list[str] = []
    cur_len = 0
    for block in blocks:
        block_len = len(block) + 2
        if cur and cur_len + block_len > limit:
            chunks.append("\n\n".join(cur))
            cur = []
            cur_len = 0
        cur.append(block)
        cur_len += block_len
    if cur:
        chunks.append("\n\n".join(cur))
    return chunks


def split_translatable(md: str) -> tuple[str, str]:
    """Return (translatable_body, untranslated_tail). The tail starts at the
    References heading (kept in English/original language on purpose)."""
    m = REFERENCES_HEADING.search(md)
    if not m:
        return md, ""
    return md[: m.start()], md[m.start() :]


def validate_preserved(source: str, translated: str) -> bool:
    # Order-insensitive: Japanese clause reordering legitimately swaps adjacent
    # citations, and link_citations.py resolves each {{CITE:N}} by N alone.
    if sorted(CITE_RE.findall(source)) != sorted(CITE_RE.findall(translated)):
        return False
    if BIBSTART_RE.findall(source) != BIBSTART_RE.findall(translated):
        return False
    if sorted(IMAGE_RE.findall(source)) != sorted(IMAGE_RE.findall(translated)):
        return False
    if source.count("```") != translated.count("```"):
        return False
    return True


# Provider error messages echo the API key back (partially masked); keep both
# the literal env values and anything key-shaped out of every log line.
_MASKED_KEY_RE = re.compile(r"[A-Za-z0-9_\-]{4,}\*{3,}[A-Za-z0-9_\-]{2,}")


def redact_secrets(text: str) -> str:
    for var in ("OPENAI_API_KEY", "GEMINI_API_KEY"):
        val = os.environ.get(var)
        if val:
            text = text.replace(val, f"<{var}>")
    return _MASKED_KEY_RE.sub("<redacted-key>", text)


def call_llm(chunk: str, primary: str, fallback: str, log, retry_hint: str = "") -> str:
    import litellm

    # LiteLLM's own logger prints errors (API key echoes included) straight to
    # stderr, which the daemon redirects into .logs/translate.log; silence it
    # and rely on our redacted log() lines instead.
    litellm.suppress_debug_info = True
    for name in ("LiteLLM", "LiteLLM Router", "LiteLLM Proxy", "httpx"):
        logging.getLogger(name).setLevel(logging.CRITICAL)

    user_content = chunk if not retry_hint else f"{retry_hint}\n\n---\n\n{chunk}"
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]

    def complete(model: str):
        guard = DailyQuotaGuard("paper-translate", model) if is_openai_model(model) else None
        reservation = None
        settled = False
        try:
            if guard is not None:
                estimated = estimate_request_tokens(litellm, model, messages, max_tokens=16000)
                reservation = guard.reserve(estimated)
            response = litellm.completion(
                model=model,
                messages=messages,
                num_retries=2,
                # Japanese text plus reasoning-model "thinking" tokens can easily
                # exceed a chunk's source length; leave generous headroom so the
                # visible answer is never truncated for token-budget reasons.
                max_tokens=16000,
            )
            if reservation is not None:
                guard.settle(reservation, response_total_tokens(response, reservation.estimated_tokens))
                settled = True
            return response
        finally:
            if reservation is not None and not settled:
                guard.release(reservation)

    try:
        response = complete(primary)
    except Exception as exc:
        log(f"WARN: primary model {primary} unavailable ({exc}); using {fallback}")
        response = complete(fallback)
    return response.choices[0].message.content or ""


def translate_chunk(chunk: str, primary: str, fallback: str, log) -> tuple[str, bool]:
    """Returns (text, success). success=False means the English original is
    being used as a placeholder and should NOT be cached, so the next run
    retries the real translation instead of freezing the fallback forever."""
    try:
        translated = call_llm(chunk, primary, fallback, log)
    except Exception as e:
        log(f"WARN: translation call failed, keeping English: {e}")
        return chunk, False

    if validate_preserved(chunk, translated):
        return translated, True

    log("WARN: preservation check failed, retrying once")
    try:
        retried = call_llm(
            chunk,
            primary,
            fallback,
            log,
            retry_hint=(
                "Your previous translation altered one of the protected markers/links/math/code."
                " Redo the translation, preserving {{CITE:N}}, {{BIBSTART:N}}, image references,"
                " LaTeX, and code fences EXACTLY as they appear in the source."
            ),
        )
    except Exception as e:
        log(f"WARN: retry call failed, keeping English: {e}")
        return chunk, False

    if validate_preserved(chunk, retried):
        return retried, True
    log("WARN: preservation check failed again, keeping English for this chunk")
    return chunk, False


def chunk_cache_path(chunks_dir: Path, index: int) -> Path:
    return chunks_dir / f"{index:03d}.json"


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    paper_dir = Path(sys.argv[1])
    force = "--force" in sys.argv[2:]
    if not paper_dir.is_dir():
        print(f"usage: {sys.argv[0]} <paper_dir> [--force]", file=sys.stderr)
        return 2

    translate_dir = paper_dir / ".translate"
    src = translate_dir / "paper_en.md"
    out = translate_dir / "paper_ja_raw.md"
    chunks_dir = translate_dir / "chunks"

    if not src.exists():
        print(f"SKIP: no {src}", file=sys.stderr)
        return 0
    if out.exists() and not force:
        print(f"SKIP: {out} already exists")
        return 0

    if not os.environ.get("OPENAI_API_KEY") and not os.environ.get("GEMINI_API_KEY"):
        print("ERROR: neither OPENAI_API_KEY nor GEMINI_API_KEY is set", file=sys.stderr)
        return 1

    primary = os.environ.get("TRANSLATE_MODEL", "openai/gpt-5.6-terra")
    fallback = os.environ.get("TRANSLATE_FALLBACK_MODEL", "gemini/gemini-3.1-flash-lite")
    sleep_s = float(os.environ.get("TRANSLATE_SLEEP", "5"))

    log_file = translate_dir / "translate.log"
    translate_dir.mkdir(parents=True, exist_ok=True)

    def log(msg: str):
        line = f"[{time.strftime('%Y-%m-%dT%H:%M:%S%z')}] {redact_secrets(msg)}"
        print(line, file=sys.stderr)
        with log_file.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

    md = src.read_text(encoding="utf-8")
    body, tail = split_translatable(md)
    blocks = split_blocks(body)
    chunks = pack_chunks(blocks)

    chunks_dir.mkdir(parents=True, exist_ok=True)
    translated_chunks = []
    all_succeeded = True
    for i, chunk in enumerate(chunks):
        source_hash = hashlib.sha256(chunk.encode("utf-8")).hexdigest()
        cache_path = chunk_cache_path(chunks_dir, i)
        if cache_path.exists():
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            if cached.get("source_hash") == source_hash:
                translated_chunks.append(cached["translated"])
                log(f"chunk {i+1}/{len(chunks)}: cached")
                continue

        log(f"chunk {i+1}/{len(chunks)}: translating ({len(chunk)} chars)")
        translated, success = translate_chunk(chunk, primary, fallback, log)
        translated_chunks.append(translated)
        if success:
            cache_path.write_text(
                json.dumps({"source_hash": source_hash, "translated": translated}, ensure_ascii=False),
                encoding="utf-8",
            )
        else:
            all_succeeded = False
        if i + 1 < len(chunks):
            time.sleep(sleep_s)

    if not all_succeeded:
        log("WARN: one or more chunks fell back to English; not writing "
            f"{out.name} so the next run retries only the failed chunks")
        print(f"translate: incomplete, {out.name} not written (see {log_file})", file=sys.stderr)
        return 1

    final_md = "\n\n".join(translated_chunks) + ("\n\n" + tail if tail else "")
    tmp = out.with_suffix(".md.tmp")
    tmp.write_text(final_md, encoding="utf-8")
    tmp.replace(out)
    log(f"done: {out} ({len(chunks)} chunks)")
    print(f"translate: {len(chunks)} chunks -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
