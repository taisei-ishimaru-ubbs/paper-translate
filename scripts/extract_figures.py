#!/usr/bin/env python3
"""Crop figures from a paper PDF with PyMuPDF and score them by caption.

For each "Figure N" caption we locate the graphic region directly above it
(vector drawing clusters + raster image rects, so vector architecture diagrams
work too), render that region at high resolution, and save it as fig-NN.png.
Each figure is scored from its caption text; the highest scorer is the method
overview. Writes figures/figures.json and prints the chosen file to stdout
(or "NONE" when no figure could be detected, so the caller can fall back).

Usage: extract_figures.py <pdf> <out_dir> <zoom>
"""
import json
import os
import re
import sys

import fitz  # PyMuPDF

CAP_RE = re.compile(r"^\s*(figure|fig\.?)\s*([0-9]+)", re.I)

# Caption keyword weights. Figure 1 is almost always the overview/architecture.
KEYWORDS = [
    (re.compile(r"architecture|framework|pipeline|overview|schematic", re.I), 12),
    (re.compile(r"proposed|our method|our approach|our model", re.I), 9),
    (re.compile(r"\bmodel\b", re.I), 6),
    (re.compile(r"\bmethod\b", re.I), 5),
    (re.compile(r"attention|adapter|prompt|encoder|decoder", re.I), 3),
]


def score_caption(caption, fig_no):
    score = 80.0 if fig_no == 1 else (18.0 if fig_no == 2 else 0.0)
    for pattern, weight in KEYWORDS:
        score += len(pattern.findall(caption)) * weight
    return score


def graphic_rects(page):
    """Vector drawing clusters + raster image rectangles on the page."""
    rects = []
    try:
        rects += [fitz.Rect(r) for r in page.cluster_drawings()]
    except Exception:
        for drawing in page.get_drawings():
            rects.append(fitz.Rect(drawing["rect"]))
    for img in page.get_images(full=True):
        try:
            rects += list(page.get_image_rects(img[0]))
        except Exception:
            pass
    return [r for r in rects if r.width > 8 and r.height > 8]


def figure_bbox(page, cap_rect, captions_on_page, rects, blocks):
    """Region above the caption, bounded by the nearest caption above it."""
    col_left, col_right = cap_rect.x0, cap_rect.x1
    # Upper bound: bottom of the nearest caption above, in the same column.
    upper = page.rect.y0
    for other in captions_on_page:
        if other is cap_rect:
            continue
        if other.y1 <= cap_rect.y0 and other.x0 < col_right and other.x1 > col_left:
            upper = max(upper, other.y1)
    above = [
        r for r in rects
        if r.y1 <= cap_rect.y0 + 2 and r.y0 >= upper - 2
        and r.x1 > col_left - 5 and r.x0 < col_right + 5
    ]
    if above:
        box = fitz.Rect(above[0])
        for r in above[1:]:
            box |= r
        # Widen to the caption's column so labels at the edges are not clipped.
        box.x0 = min(box.x0, col_left)
        box.x1 = max(box.x1, col_right)
        # Pull in short text labels hugging the figure (axis / I/O labels that
        # are text, not drawings, so they fall outside the graphic union).
        margin = max(18.0, 0.06 * box.height)
        for block in blocks:
            br = fitz.Rect(block[:4])
            if br == cap_rect:
                continue
            if not (upper <= br.y0 and br.y1 <= cap_rect.y0):
                continue
            if br.x1 <= box.x0 or br.x0 >= box.x1:
                continue
            if br.y0 >= box.y0 - margin and br.y1 <= box.y1 + margin:
                box |= br
    else:
        # No graphics detected: take the gap between the previous text and caption.
        prev_bottom = upper
        for block in blocks:
            br = fitz.Rect(block[:4])
            if br.y1 <= cap_rect.y0 - 2 and br.x0 < col_right and br.x1 > col_left:
                prev_bottom = max(prev_bottom, br.y1)
        box = fitz.Rect(col_left, prev_bottom, col_right, cap_rect.y0)
    pad = 4
    box = fitz.Rect(box.x0 - pad, box.y0 - pad, box.x1 + pad, box.y1 + pad)
    return box & page.rect


def main():
    pdf_path, out_dir, zoom = sys.argv[1], sys.argv[2], float(sys.argv[3])
    os.makedirs(out_dir, exist_ok=True)
    doc = fitz.open(pdf_path)
    matrix = fitz.Matrix(zoom, zoom)

    figures = []
    for pno in range(len(doc)):
        page = doc[pno]
        blocks = [b for b in page.get_text("blocks") if b[6] == 0 and b[4].strip()]
        cap_rects = [fitz.Rect(b[:4]) for b in blocks if CAP_RE.match(b[4].strip())]
        rects = graphic_rects(page)
        for block in blocks:
            text = block[4].strip()
            m = CAP_RE.match(text)
            if not m:
                continue
            fig_no = int(m.group(2))
            cap_rect = fitz.Rect(block[:4])
            caption = " ".join(text.split())
            box = figure_bbox(page, cap_rect, cap_rects, rects, blocks)
            if box.width < 24 or box.height < 24:
                continue
            figures.append({
                "page": pno + 1,
                "figure_no": fig_no,
                "caption": caption[:300],
                "rect": [box.x0, box.y0, box.x1, box.y1],
                "score": score_caption(caption, fig_no),
            })

    if not figures:
        print("NONE")
        return

    # Render each detected figure.
    records = []
    for idx, fig in enumerate(figures):
        page = doc[fig["page"] - 1]
        pix = page.get_pixmap(matrix=matrix, clip=fitz.Rect(fig["rect"]))
        name = f"fig-{idx:02d}.png"
        pix.save(os.path.join(out_dir, name))
        records.append({
            "file": name,
            "figure_no": fig["figure_no"],
            "page": fig["page"],
            "caption": fig["caption"],
            "score": round(fig["score"], 1),
        })

    with open(os.path.join(out_dir, "figures.json"), "w", encoding="utf-8") as handle:
        json.dump(records, handle, ensure_ascii=False, indent=2)

    best = max(
        range(len(records)),
        key=lambda i: (records[i]["score"], -records[i]["page"], -records[i]["figure_no"]),
    )
    print(records[best]["file"])


if __name__ == "__main__":
    main()
