#!/usr/bin/env python3
r"""Convert a paper's LaTeX source (arXiv e-print) into English Markdown via
pandoc, keeping math as real $...$ / $$...$$ so Obsidian renders it. This is
the primary conversion path; convert_to_markdown.py (HTML/PDF via Docling) is
the fallback for papers whose TeX source is unusable.

Usage: convert_tex_to_markdown.py <paper_dir> [--force]

Reads:
  <paper_dir>/.translate/state.json            (source must be "latex")
  <paper_dir>/.translate/source-tex/           (extracted e-print tarball)

Writes (same contract as convert_to_markdown.py, so translate_markdown.py and
link_citations.py work unchanged):
  <paper_dir>/.translate/paper_en.md   English Markdown with {{CITE:N}} /
                                        {{BIBSTART:N}} markers.
  <paper_dir>/.translate/bibs.json     {"style": "tex-bibitem", "bibs": {...}}
  <paper_dir>/assets/figNN.png         Figures rendered from the tarball.

Exits non-zero (without writing paper_en.md) when the TeX cannot be converted
reliably, so translate-paper.sh can fall back to the HTML/PDF path.
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from convert_to_markdown import extract_bib_fields  # noqa: E402

# A figure placeholder that survives pandoc's LaTeX reader untouched (no TeX
# special chars) and is turned into a real image link afterwards.
FIG_PLACEHOLDER = "ZZFIGUREZZ{:03d}ZZ"
FIG_PLACEHOLDER_RE = re.compile(r"ZZFIGUREZZ(\d{3})ZZ")
INCLUDEGRAPHICS_RE = re.compile(r"\\includegraphics\s*(?:\[[^\]]*\])?\s*\{")
CAPTION_RE = re.compile(r"\\caption\s*(?:\[[^\]]*\])?\s*\{")
RASTER_EXTS = (".png", ".jpg", ".jpeg", ".gif", ".webp")
MIN_BODY_CHARS = 1500


def log(msg: str):
    print(f"convert-tex: {msg}", file=sys.stderr)


# ---------------------------------------------------------------------------
# TeX text utilities
# ---------------------------------------------------------------------------
def match_brace(text: str, open_pos: int) -> int:
    """Given index of an opening '{', return index just past the matching '}'.
    Respects backslash-escaped braces. Returns -1 if unbalanced."""
    depth = 0
    i = open_pos
    n = len(text)
    while i < n:
        c = text[i]
        if c == "\\":
            i += 2
            continue
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    return -1


def strip_comments(tex: str) -> str:
    r"""Drop TeX line comments (unescaped %), preserving \%."""
    out = []
    for line in tex.splitlines():
        i = 0
        cut = None
        while i < len(line):
            if line[i] == "\\":
                i += 2
                continue
            if line[i] == "%":
                cut = i
                break
            i += 1
        out.append(line if cut is None else line[:cut])
    return "\n".join(out)


def flatten_inputs(main_path: Path, seen=None) -> str:
    r"""Recursively inline \input{f} / \include{f} relative to the main file's
    directory, then strip comments."""
    if seen is None:
        seen = set()
    tex = main_path.read_text(encoding="utf-8", errors="replace")
    tex = strip_comments(tex)
    base = main_path.parent

    def repl(m):
        name = m.group(1).strip()
        for cand in (name, name + ".tex"):
            p = base / cand
            if p.is_file() and p.resolve() not in seen:
                seen.add(p.resolve())
                return flatten_inputs(p, seen)
        return ""

    tex = re.sub(r"\\(?:input|include)\s*\{([^}]*)\}", repl, tex)
    return tex


def unwrap_sizing_boxes(tex: str) -> str:
    r"""Strip \resizebox{..}{..}{BODY}, \scalebox{..}{BODY} and
    \adjustbox{..}{BODY} down to BODY. pandoc's LaTeX reader can't parse these
    sizing wrappers and silently drops the tabular they wrap, so tables vanish
    unless we remove the wrapper first."""
    specs = [("\\resizebox", 2), ("\\scalebox", 1), ("\\adjustbox", 1)]
    for cmd, n_args in specs:
        out = []
        pos = 0
        while True:
            idx = tex.find(cmd, pos)
            if idx < 0:
                out.append(tex[pos:])
                break
            out.append(tex[pos:idx])
            i = idx + len(cmd)
            # Skip the leading argument(s): a bracket group or brace groups.
            ok = True
            for _ in range(n_args):
                while i < len(tex) and tex[i] in " \t\n":
                    i += 1
                if i < len(tex) and tex[i] == "[":
                    j = tex.find("]", i)
                    i = j + 1 if j >= 0 else len(tex)
                elif i < len(tex) and tex[i] == "{":
                    j = match_brace(tex, i)
                    if j < 0:
                        ok = False
                        break
                    i = j
                else:
                    ok = False
                    break
            while ok and i < len(tex) and tex[i] in " \t\n":
                i += 1
            if not ok or i >= len(tex) or tex[i] != "{":
                # Not the shape we expected; leave the command untouched.
                out.append(cmd)
                pos = idx + len(cmd)
                continue
            close = match_brace(tex, i)
            if close < 0:
                out.append(cmd)
                pos = idx + len(cmd)
                continue
            out.append(tex[i + 1 : close - 1])  # BODY, wrapper stripped
            pos = close
        tex = "".join(out)
    return tex


# ---------------------------------------------------------------------------
# Bibliography
# ---------------------------------------------------------------------------
def find_bib_text(tex_dir: Path, tex: str):
    r"""Return the thebibliography block text: prefer a .bbl file, else the
    inline \begin{thebibliography} in the flattened source."""
    bbls = sorted(tex_dir.rglob("*.bbl"))
    if bbls:
        return bbls[0].read_text(encoding="utf-8", errors="replace")
    m = re.search(r"\\begin\{thebibliography\}.*?\\end\{thebibliography\}", tex, re.DOTALL)
    return m.group(0) if m else None


def _tex_to_plain(raw: str) -> str:
    r"""Lightweight cleanup of a bib entry's raw TeX into readable plain text
    (bibliography is not translated, only displayed / matched by identifier)."""
    raw = re.sub(r"\\newblock", " ", raw)
    raw = re.sub(r"\\(?:em|it|bf|rm|sc|tt)\b", "", raw)
    raw = re.sub(r"\\(?:emph|textbf|textit|textsc|texttt|text)\s*\{([^{}]*)\}", r"\1", raw)
    raw = re.sub(r"\\url\s*\{([^}]*)\}", r"\1", raw)
    raw = re.sub(r"\\href\s*\{([^}]*)\}\s*\{([^{}]*)\}", r"\2 (\1)", raw)
    raw = raw.replace("~", " ").replace("--", "-")
    raw = re.sub(r"[{}]", "", raw)
    raw = re.sub(r"\\[a-zA-Z]+\b", "", raw)
    raw = re.sub(r"\s+", " ", raw)
    return raw.strip()


def parse_bibitems(bib_text: str):
    r"""Split a thebibliography block on \bibitem, returning
    (key2num, bibs_dict). unsrt style => \bibitem order is the citation number
    order, so N is just the 1-based position."""
    bib_text = strip_comments(bib_text)
    item_re = re.compile(r"\\bibitem\s*(?:\[[^\]]*\])?\s*\{([^}]*)\}")
    matches = list(item_re.finditer(bib_text))
    key2num = {}
    bibs = {}
    for i, m in enumerate(matches):
        key = m.group(1).strip()
        n = i + 1
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(bib_text)
        raw = bib_text[start:end]
        raw = re.sub(r"\\end\{thebibliography\}", "", raw)
        raw = _tex_to_plain(raw)
        key2num[key] = n
        bibs[str(n)] = extract_bib_fields(raw)
    return key2num, bibs


# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------
def render_image(src: Path, dest: Path) -> bool:
    """Copy a raster image, or rasterize a PDF/EPS to PNG via PyMuPDF."""
    ext = src.suffix.lower()
    if ext in RASTER_EXTS:
        shutil.copyfile(src, dest)
        return True
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(src)
        page = doc[0]
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        pix.save(dest)
        doc.close()
        return True
    except Exception as e:
        log(f"WARN: could not render {src.name}: {e}")
        return False


def resolve_graphic(tex_dir: Path, ref: str):
    r"""Resolve an \includegraphics path (often extension-less) inside the
    extracted tarball."""
    ref = ref.strip().strip('"')
    cand = tex_dir / ref
    if cand.is_file():
        return cand
    for ext in (".pdf", ".png", ".jpg", ".jpeg", ".eps", ".PDF", ".PNG"):
        if (tex_dir / (ref + ext)).is_file():
            return tex_dir / (ref + ext)
    hits = list(tex_dir.rglob(Path(ref).name + ".*")) + list(tex_dir.rglob(Path(ref).name))
    return hits[0] if hits else None


def extract_caption(env_body: str) -> str:
    r"""Pull the text of the first \caption{...} in a figure environment."""
    m = CAPTION_RE.search(env_body)
    if not m:
        return ""
    open_pos = m.end() - 1
    close = match_brace(env_body, open_pos)
    if close < 0:
        return ""
    return env_body[open_pos + 1 : close - 1].strip()


def convert_figures(tex: str, tex_dir: Path, assets_dir: Path):
    r"""Replace each figure/figure* environment with figure placeholders plus a
    caption paragraph (kept as TeX so pandoc renders its math as $...$).
    Returns (new_tex, n_figures_rendered, n_skipped)."""
    if assets_dir.exists():
        for old in assets_dir.glob("fig*.png"):
            old.unlink()
    assets_dir.mkdir(parents=True, exist_ok=True)

    counter = {"n": 0}
    skipped = {"n": 0}
    env_re = re.compile(r"\\begin\{(figure\*?)\}")

    def render_one(ref: str):
        """Render a single \\includegraphics target to assets/figNN.png,
        returning its placeholder or None if it can't be resolved/rendered."""
        src = resolve_graphic(tex_dir, ref)
        if src is None:
            log(f"WARN: unresolved graphic {ref}")
            return None
        counter["n"] += 1
        name = f"fig{counter['n']:02d}.png"
        if render_image(src, assets_dir / name):
            return FIG_PLACEHOLDER.format(counter["n"])
        counter["n"] -= 1
        return None

    def replace_includegraphics(text: str) -> str:
        """Replace every \\includegraphics[...]{path} token in `text` with a
        rendered placeholder (used for images outside figure environments)."""
        out = []
        pos = 0
        for gm in INCLUDEGRAPHICS_RE.finditer(text):
            open_pos = gm.end() - 1
            close = match_brace(text, open_pos)
            if close < 0:
                continue
            ph = render_one(text[open_pos + 1 : close - 1])
            out.append(text[pos : gm.start()])
            out.append(f"\n\n{ph}\n\n" if ph else "")
            pos = close
        out.append(text[pos:])
        return "".join(out)

    def render_env(body: str) -> str:
        if re.search(r"\\begin\{(tikzpicture|pgfpicture)\}|\\tikz\b", body):
            skipped["n"] += 1
            return "\n\n"
        placeholders = []
        for gm in INCLUDEGRAPHICS_RE.finditer(body):
            open_pos = gm.end() - 1
            close = match_brace(body, open_pos)
            if close < 0:
                continue
            ph = render_one(body[open_pos + 1 : close - 1])
            if ph:
                placeholders.append(ph)
        if not placeholders:
            skipped["n"] += 1
            return "\n\n"
        caption = extract_caption(body)
        parts = "\n\n".join(placeholders)
        return f"\n\n{parts}\n\n{caption}\n\n"

    # Pass 1: consume figure/figure* environments (placeholder + caption text).
    out = []
    pos = 0
    while True:
        m = env_re.search(tex, pos)
        if not m:
            out.append(tex[pos:])
            break
        envname = m.group(1)
        end_tok = f"\\end{{{envname}}}"
        end_idx = tex.find(end_tok, m.end())
        if end_idx < 0:
            out.append(tex[pos:])
            break
        out.append(tex[pos : m.start()])
        body = tex[m.end() : end_idx]
        out.append(render_env(body))
        pos = end_idx + len(end_tok)
    tex = "".join(out)

    # Pass 2: any \includegraphics left outside figure envs (wrapfigure, table,
    # bare images) — render them too so no figures are silently dropped.
    tex = replace_includegraphics(tex)
    return tex, counter["n"], skipped["n"]


# ---------------------------------------------------------------------------
# pandoc + post-processing
# ---------------------------------------------------------------------------
def run_pandoc(tex: str) -> str:
    # Force pipe_tables: Obsidian only renders GFM pipe tables, not pandoc's
    # default space-aligned "simple"/"multiline" tables. Keep the `markdown`
    # flavour (not gfm) so math stays as $...$ rather than gfm's `$...$`.
    to_fmt = ("markdown-implicit_figures-raw_attribute"
              "-simple_tables-multiline_tables-grid_tables+pipe_tables")
    # --mathjax keeps LaTeX source (\(..\)/\[..\]) inside the raw-HTML tables
    # pandoc emits for multirow/multicolumn tables, instead of rendering it to
    # <em>/<sub> spans; cleanup_markdown turns those back into $...$.
    proc = subprocess.run(
        ["pandoc", "-f", "latex", "-t", to_fmt, "--wrap=none", "--mathjax"],
        input=tex, capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"pandoc failed: {proc.stderr.strip()[:400]}")
    return proc.stdout


def replace_citations(md: str, key2num: dict) -> str:
    r"""Turn pandoc citations into {{CITE:N}}: the `[@k]` / `[@k1; @k2]` form in
    prose, and the `<span class="citation" data-cites="k1 k2">` form pandoc
    emits inside raw-HTML tables."""
    def keys_to_markers(keys):
        nums = [key2num.get(k) for k in keys]
        if not keys or any(n is None for n in nums):
            return None
        return "".join(f"{{{{CITE:{n}}}}}" for n in nums)

    def repl_bracket(m):
        keys = [k.strip().lstrip("@").strip() for k in m.group(1).split(";")]
        return keys_to_markers(keys) or m.group(0)

    def repl_span(m):
        keys = m.group(1).split()
        return keys_to_markers(keys) or ""

    md = re.sub(r'<span class="citation" data-cites="([^"]+)"[^>]*>.*?</span>',
                repl_span, md, flags=re.DOTALL)
    md = re.sub(r"\[(@[^\]]+)\]", repl_bracket, md)
    return md


def cleanup_markdown(md: str) -> str:
    def unwrap_eq(m):
        inner = m.group(1)
        inner = re.sub(r"\\begin\{equation\*?\}", "", inner)
        inner = re.sub(r"\\end\{equation\*?\}", "", inner)
        inner = re.sub(r"\\label\{[^}]*\}", "", inner)
        return "$$" + inner.strip() + "$$"

    # Math inside pandoc's raw-HTML tables arrives as MathJax spans; turn the
    # LaTeX source back into $...$ / $$...$$ so Obsidian renders it.
    md = re.sub(r'<span class="math display">\s*\\\[(.*?)\\\]\s*</span>',
                lambda m: f"$${m.group(1).strip()}$$", md, flags=re.DOTALL)
    md = re.sub(r'<span class="math inline">\s*\\\((.*?)\\\)\s*</span>',
                lambda m: f"${m.group(1).strip()}$", md, flags=re.DOTALL)

    md = re.sub(r"\$\$(.*?)\$\$", unwrap_eq, md, flags=re.DOTALL)
    md = re.sub(r"\[([^\]]*)\]\(#[^)]*\)\{[^}]*\}", r"\1", md)
    md = re.sub(r"\{reference-type=[^}]*\}", "", md)
    md = re.sub(r"(?m)^:::+.*$", "", md)
    md = re.sub(r"\{#[^}]*\}", "", md)
    # Pandoc emits a table caption as a `: Caption.` line; make it a bold
    # paragraph so it reads as a caption in Obsidian instead of a stray colon.
    md = re.sub(r"(?m)^\s*:\s+(\S.*)$", r"**\1**", md)
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip() + "\n"


def build_bibliography(bibs: dict) -> str:
    lines = ["\n\n## References\n"]
    for n in sorted(bibs, key=int):
        lines.append(f"{{{{BIBSTART:{n}}}}}[{n}] {bibs[n]['raw']}\n")
    return "\n".join(lines)


def find_main_tex(tex_dir: Path):
    r"""Pick the .tex containing \documentclass and \begin{document}."""
    candidates = []
    for p in sorted(tex_dir.rglob("*.tex")):
        try:
            head = p.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        if "\\documentclass" in head and "\\begin{document}" in head:
            candidates.append((p.stat().st_size, p))
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][1]


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
    out_md = translate_dir / "paper_en.md"
    out_bibs = translate_dir / "bibs.json"
    tex_dir = translate_dir / "source-tex"

    if out_md.exists() and not force:
        print(f"SKIP: {out_md} already exists")
        return 0
    if not tex_dir.is_dir():
        log("no source-tex/ directory")
        return 1
    if shutil.which("pandoc") is None:
        log("ERROR: pandoc not found (brew install pandoc)")
        return 1

    main_tex = find_main_tex(tex_dir)
    if main_tex is None:
        log("no main .tex (with documentclass + begin document) found")
        return 1

    tex = flatten_inputs(main_tex)
    tex = unwrap_sizing_boxes(tex)

    bib_text = find_bib_text(tex_dir, tex)
    if not bib_text:
        log("no bibliography (.bbl or thebibliography) found; falling back")
        return 1
    key2num, bibs = parse_bibitems(bib_text)
    if not bibs:
        log("could not parse any bibitem; falling back")
        return 1

    # Drop the bibliography from the body: we regenerate it with markers, and
    # strip \bibliography{}/\bibliographystyle{} so pandoc leaves \cite as [@k].
    tex = re.sub(r"\\begin\{thebibliography\}.*?\\end\{thebibliography\}", "", tex, flags=re.DOTALL)
    tex = re.sub(r"\\bibliography\{[^}]*\}", "", tex)
    tex = re.sub(r"\\bibliographystyle\{[^}]*\}", "", tex)

    tex, n_fig, n_skip = convert_figures(tex, tex_dir, paper_dir / "assets")

    try:
        md = run_pandoc(tex)
    except RuntimeError as e:
        log(str(e))
        return 1

    md = replace_citations(md, key2num)
    md = cleanup_markdown(md)
    md = FIG_PLACEHOLDER_RE.sub(lambda m: f"![](assets/fig{int(m.group(1)):02d}.png)", md)

    if len(md) < MIN_BODY_CHARS:
        log(f"body too short ({len(md)} chars); falling back")
        return 1

    n_cite = md.count("{{CITE:")
    final_md = md + build_bibliography(bibs)

    translate_dir.mkdir(parents=True, exist_ok=True)
    out_md.write_text(final_md, encoding="utf-8")
    out_bibs.write_text(
        json.dumps({"style": "tex-bibitem", "bibs": bibs}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"convert-tex: bibs={len(bibs)} cites={n_cite} figures={n_fig} "
          f"skipped={n_skip} -> {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
