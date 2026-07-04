#!/usr/bin/env python3
"""Render {{CITE:N}} / {{BIBSTART:N}} markers left by translate_markdown.py
into Obsidian links: a wikilink to the cited paper's own note when we hold it
locally, otherwise a same-file block reference to its bibliography entry.

Usage: link_citations.py <paper_dir>

Reads:
  <paper_dir>/.translate/paper_ja_raw.md   (if absent: no-op, leaves any
                                             existing <slug>_ja.md untouched)
  <paper_dir>/.translate/bibs.json         (from convert_to_markdown.py)
  <paper_dir>/references.json              (this paper's own Semantic
                                             Scholar references, if fetched)
  $LOCAL_MAP_FILE                          TSV of identifier -> slug for all
                                            papers in the library (same file
                                            generate-obsidian-note.sh uses)

Writes:
  <paper_dir>/<slug>_ja.md

This never mutates paper_ja_raw.md, so it can be re-run cheaply every daemon
pass (e.g. after a new paper is added, upgrading a bare-text reference in an
older translation into a real wikilink).
"""
import json
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

CITE_RE = re.compile(r"\{\{CITE:(\d+)\}\}")
BIBSTART_RE = re.compile(r"\{\{BIBSTART:(\d+)\}\}")
MIN_TITLE_MATCH_LEN = 20


def snake(s: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", s.lower())
    return s.strip("_")


def load_local_map() -> dict:
    path = os.environ.get("LOCAL_MAP_FILE")
    note_of = {}
    if path and Path(path).is_file():
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if "\t" not in line:
                continue
            key, value = line.split("\t", 1)
            if key:
                note_of[key] = value
    return note_of


def load_metadata(script_dir: Path, paper_dir: Path) -> dict:
    result = subprocess.run(
        ["bash", str(script_dir / "paper-metadata.sh"), str(paper_dir)],
        capture_output=True, text=True,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return {}
    return json.loads(result.stdout)


def normalize_title(s: str) -> str:
    s = unicodedata.normalize("NFKC", s).casefold()
    return re.sub(r"[^\w]+", "", s, flags=re.UNICODE)


def resolve_slug(paper_id: str, title: str, note_of: dict) -> str:
    slug = note_of.get(paper_id) or (snake(title) if title else "")
    return slug or snake(paper_id)


def find_local_slug(bib: dict, references: list, note_of: dict):
    arxiv_id = bib.get("arxiv_id", "")
    doi = bib.get("doi", "").lower()

    if arxiv_id and (slug := note_of.get(f"arxiv:{arxiv_id}")):
        return slug
    if doi and (slug := note_of.get(f"doi:{doi}")):
        return slug

    raw_norm = normalize_title(bib.get("raw", ""))
    for ref in references:
        ref_arxiv = ref.get("arxiv_id", "")
        ref_doi = (ref.get("doi") or "").lower()
        ref_title = ref.get("title") or ""
        matched = (
            (arxiv_id and ref_arxiv == arxiv_id)
            or (doi and ref_doi == doi)
            or (
                ref_title
                and len(normalize_title(ref_title)) >= MIN_TITLE_MATCH_LEN
                and normalize_title(ref_title) in raw_norm
            )
        )
        if not matched:
            continue
        for field, prefix in (("paper_id", "s2"), ("arxiv_id", "arxiv"), ("doi", "doi")):
            val = ref.get(field)
            if not val:
                continue
            key = f"{prefix}:{val.lower() if prefix == 'doi' else val}"
            if slug := note_of.get(key):
                return slug
    return None


def process_bibstarts(text: str) -> str:
    matches = list(BIBSTART_RE.finditer(text))
    if not matches:
        return text
    pieces = []
    last_end = 0
    for i, m in enumerate(matches):
        pieces.append(text[last_end : m.start()])
        entry_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        entry_text = text[m.end() : entry_end]
        stripped = entry_text.rstrip()
        trailing_ws = entry_text[len(stripped):]
        pieces.append(f"{stripped} ^ref-{m.group(1)}{trailing_ws}")
        last_end = entry_end
    return "".join(pieces)


def process_cites(text: str, bibs: dict, references: list, note_of: dict) -> str:
    def repl(m):
        n = m.group(1)
        bib = bibs.get(n, {})
        slug = find_local_slug(bib, references, note_of)
        if slug:
            return f"[[{slug}|{n}]]"
        return f"[[#^ref-{n}|{n}]]"

    return CITE_RE.sub(repl, text)


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    paper_dir = Path(sys.argv[1])
    if not paper_dir.is_dir():
        print(f"usage: {sys.argv[0]} <paper_dir>", file=sys.stderr)
        return 2

    raw_path = paper_dir / ".translate" / "paper_ja_raw.md"
    if not raw_path.exists():
        return 0

    script_dir = Path(__file__).resolve().parent
    metadata = load_metadata(script_dir, paper_dir)
    if not metadata:
        print(f"SKIP: no supported metadata in {paper_dir}", file=sys.stderr)
        return 0
    paper_id = metadata.get("id", "")
    title = metadata.get("title", "")

    bibs_path = paper_dir / ".translate" / "bibs.json"
    bibs = json.loads(bibs_path.read_text(encoding="utf-8")).get("bibs", {}) if bibs_path.exists() else {}

    refs_path = paper_dir / "references.json"
    references = json.loads(refs_path.read_text(encoding="utf-8")).get("references", []) if refs_path.exists() else []

    note_of = load_local_map()
    slug = resolve_slug(paper_id, title, note_of)

    raw_text = raw_path.read_text(encoding="utf-8")
    rendered = process_bibstarts(raw_text)
    rendered = process_cites(rendered, bibs, references, note_of)

    frontmatter = (
        "---\n"
        f'title: "{title}（日本語訳）"\n'
        "tags: [paper-translation]\n"
        "---\n\n"
        f"[[{slug}|← 論文ノート]]\n\n"
    )
    final_text = frontmatter + rendered

    out_path = paper_dir / f"{slug}_ja.md"
    tmp_path = out_path.with_suffix(".md.tmp")
    tmp_path.write_text(final_text, encoding="utf-8")
    tmp_path.replace(out_path)
    print(f"link_citations: -> {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
