#!/usr/bin/env python3
"""Convert a paper's HTML (ar5iv/arxiv.org) or PDF into English Markdown via
Docling, saving images to <paper_dir>/assets/ and tagging citation markers so
link_citations.py can later turn them into Obsidian links/block references.

Usage: convert_to_markdown.py <paper_dir> [--force]

Reads:
  <paper_dir>/.translate/state.json          (source: arxiv_html|ar5iv|pdf_only)
  <paper_dir>/.translate/source/source.html  (HTML path only, images already localized)
  <paper_dir>/paper.pdf                      (PDF path only)

Writes:
  <paper_dir>/.translate/paper_en.md   English Markdown with {{CITE:N}} /
                                        {{BIBSTART:N}} markers where a
                                        numbered bibliography could be parsed.
  <paper_dir>/.translate/bibs.json     {"style": ..., "bibs": {"N": {"raw",
                                        "arxiv_id", "doi"}}} extracted from the
                                        bibliography, for link_citations.py to
                                        match against this paper's own
                                        references.json.
  <paper_dir>/assets/figNN.png         Figures extracted from the document.

Citation matching to the local library happens later, in link_citations.py,
because this paper's references.json may not exist yet when this step runs.
"""
import json
import re
import sys
from pathlib import Path

MATH_DISPLAY_ANCESTOR = re.compile(r"ltx_equation")
REFERENCES_HEADING = re.compile(
    r"^(#{1,6})\s*(references?|bibliography)\s*$", re.IGNORECASE | re.MULTILINE
)
ENTRY_PATTERNS = [
    re.compile(r"(?m)^- \[(\d{1,3})\]\s?"),
    re.compile(r"(?m)^\[(\d{1,3})\]\s?"),
    re.compile(r"(?m)^(\d{1,3})\.\s+"),
]
HTML_CITE_LINK = re.compile(r"\[([^\[\]]{0,80})\]\([^)]*#bib\.bib(\d+)\)")
BRACKET_CITE = re.compile(r"\[(\d{1,3}(?:\s*[,–-]\s*\d{1,3})*)\]")
ARXIV_ID_RE = re.compile(r"(?:arxiv[:\s]+|abs/)(\d{4}\.\d{4,5})", re.IGNORECASE)
DOI_RE = re.compile(r"10\.\d{4,9}/[^\s,)\]]+")
IMAGE_PLACEHOLDER = "<!-- image -->"


def preprocess_math(soup):
    for math in soup.find_all("math"):
        alttext = math.get("alttext", "")
        if not alttext:
            math.decompose()
            continue
        display = math.find_parent(class_=MATH_DISPLAY_ANCESTOR) is not None
        wrapped = f"$${alttext}$$" if display else f"${alttext}$"
        math.replace_with(wrapped)


def strip_noise(soup):
    for tag_name in ("nav", "header", "footer"):
        for tag in soup.find_all(tag_name):
            tag.decompose()
    # Site-root-relative and empty anchors (e.g. "/", "/html/<other-id>" from
    # ar5iv's version/related-paper nav) crash Docling's local-fetch path
    # resolver, which only understands paths relative to source_uri.
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href == "#" or href.startswith("/"):
            a.unwrap()


def convert_html(paper_dir: Path, translate_dir: Path):
    from bs4 import BeautifulSoup
    from docling.datamodel.backend_options import HTMLBackendOptions
    from docling.datamodel.base_models import InputFormat
    from docling.document_converter import DocumentConverter, HTMLFormatOption

    source_html = translate_dir / "source" / "source.html"
    soup = BeautifulSoup(source_html.read_text(encoding="utf-8", errors="replace"), "html.parser")
    preprocess_math(soup)
    strip_noise(soup)

    preprocessed_path = translate_dir / "source" / "_preprocessed.html"
    preprocessed_path.write_text(str(soup), encoding="utf-8")

    opts = HTMLBackendOptions(fetch_images=True, enable_local_fetch=True, source_uri=preprocessed_path)
    conv = DocumentConverter(format_options={InputFormat.HTML: HTMLFormatOption(backend_options=opts)})
    result = conv.convert(str(preprocessed_path))
    doc = result.document
    md = doc.export_to_markdown(escape_underscores=False)
    return md, doc


def convert_pdf(paper_dir: Path):
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption

    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_ocr = False
    pipeline_options.generate_picture_images = True
    conv = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)})
    result = conv.convert(str(paper_dir / "paper.pdf"))
    doc = result.document
    md = doc.export_to_markdown(escape_underscores=False)
    return md, doc


def replace_image_placeholders(md_text: str, doc, assets_dir: Path) -> str:
    pictures = list(doc.pictures)
    if not pictures:
        return md_text

    if assets_dir.exists():
        for old in assets_dir.glob("fig*.png"):
            old.unlink()
    assets_dir.mkdir(parents=True, exist_ok=True)

    counter = 0

    def repl(_match):
        nonlocal counter
        if counter >= len(pictures):
            return IMAGE_PLACEHOLDER
        pic = pictures[counter]
        counter += 1
        try:
            image = pic.get_image(doc)
        except Exception:
            return IMAGE_PLACEHOLDER
        if image is None:
            return IMAGE_PLACEHOLDER
        filename = f"fig{counter:02d}.png"
        image.save(assets_dir / filename)
        return f"![](assets/{filename})"

    return re.sub(re.escape(IMAGE_PLACEHOLDER), repl, md_text)


def find_references_split(md: str):
    m = REFERENCES_HEADING.search(md)
    if not m:
        return md, None, None
    return md[: m.start()], m.group(0), md[m.end() :]


def find_bib_matches(refs_body: str):
    best = None
    for pattern in ENTRY_PATTERNS:
        matches = list(pattern.finditer(refs_body))
        if len(matches) < 3:
            continue
        nums = [int(mm.group(1)) for mm in matches]
        increasing = sum(1 for a, b in zip(nums, nums[1:]) if b > a)
        if increasing < len(nums) - 1 - max(1, len(nums) // 10):
            continue
        if best is None or len(matches) > len(best[1]):
            best = (pattern, matches)
    return best


def extract_bib_fields(raw_text: str) -> dict:
    arxiv_m = ARXIV_ID_RE.search(raw_text)
    doi_m = DOI_RE.search(raw_text)
    arxiv_id = re.sub(r"v\d+$", "", arxiv_m.group(1)) if arxiv_m else ""
    doi = doi_m.group(0).rstrip(".").lower() if doi_m else ""
    return {"raw": raw_text.strip(), "arxiv_id": arxiv_id, "doi": doi}


def inject_bibstart_markers(refs_body: str, matches) -> str:
    pieces = []
    last = 0
    for m in matches:
        pieces.append(refs_body[last : m.start()])
        pieces.append(f"{{{{BIBSTART:{m.group(1)}}}}}")
        last = m.start()
    pieces.append(refs_body[last:])
    return "".join(pieces)


def replace_html_citation_links(body: str):
    found = HTML_CITE_LINK.search(body) is not None
    marked = HTML_CITE_LINK.sub(lambda m: f"{{{{CITE:{m.group(2)}}}}}", body)
    return marked, found


def expand_bracket(spec: str):
    nums = []
    for part in spec.split(","):
        part = part.strip()
        if "-" in part or "–" in part:
            a, b = re.split(r"[-–]", part)
            nums.extend(range(int(a), int(b) + 1))
        else:
            nums.append(int(part))
    return nums


def replace_bracket_citations(body: str, valid_nums: set):
    def repl(m):
        try:
            nums = expand_bracket(m.group(1))
        except ValueError:
            return m.group(0)
        if not nums or not all(n in valid_nums for n in nums):
            return m.group(0)
        return "".join(f"{{{{CITE:{n}}}}}" for n in nums)

    return BRACKET_CITE.sub(repl, body)


def annotate_citations(md: str):
    """Split off the bibliography, tag {{BIBSTART:N}}/{{CITE:N}} markers, and
    extract raw bib text. Returns (annotated_md, style, bibs_dict). Falls back
    to the untouched markdown with style="none" if no numbered bibliography
    can be reliably parsed."""
    body, heading, refs_body = find_references_split(md)
    if refs_body is None:
        return md, "none", {}

    found = find_bib_matches(refs_body)
    if found is None:
        return md, "none", {}
    pattern, matches = found

    marked_refs_body = inject_bibstart_markers(refs_body, matches)
    bibs = {}
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(refs_body)
        bibs[m.group(1)] = extract_bib_fields(refs_body[start:end])

    marked_body, found_html_links = replace_html_citation_links(body)
    if found_html_links:
        style = "html-anchor"
    else:
        valid_nums = {int(n) for n in bibs}
        candidate = replace_bracket_citations(body, valid_nums)
        style = "bracket-heuristic" if candidate != body else "none"
        marked_body = candidate

    return marked_body + heading + marked_refs_body, style, bibs


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
    if out_md.exists() and not force:
        print(f"SKIP: {out_md} already exists")
        return 0

    state_file = translate_dir / "state.json"
    state = json.loads(state_file.read_text()) if state_file.exists() else {"source": "pdf_only"}
    source = state.get("source", "pdf_only")

    if source != "pdf_only":
        md, doc = convert_html(paper_dir, translate_dir)
    else:
        if not (paper_dir / "paper.pdf").exists():
            print(f"SKIP: no paper.pdf in {paper_dir}", file=sys.stderr)
            return 0
        md, doc = convert_pdf(paper_dir)

    md = replace_image_placeholders(md, doc, paper_dir / "assets")
    md = restore_math_entities(md)
    final_md, style, bibs = annotate_citations(md)

    translate_dir.mkdir(parents=True, exist_ok=True)
    out_md.write_text(final_md, encoding="utf-8")
    out_bibs.write_text(
        json.dumps({"style": style, "bibs": bibs}, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"convert: source={source} style={style} bibs={len(bibs)} -> {out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
