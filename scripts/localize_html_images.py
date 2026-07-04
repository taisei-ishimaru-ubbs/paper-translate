#!/usr/bin/env python3
"""Download every <img> referenced by a fetched arXiv/ar5iv HTML page next to
it and rewrite src attributes to the local relative path, so Docling never
needs network access during conversion.

Usage: localize_html_images.py <source_url> <input_html> <output_dir>

Writes <output_dir>/source.html and <output_dir>/assets/imgNNN.<ext>.
Prints a one-line summary to stdout. Images that fail to download have their
src attribute removed rather than aborting the whole fetch.
"""
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup

TIMEOUT = 30
MAX_ATTEMPTS = 2


def guess_ext(url: str, content_type: str) -> str:
    path_ext = Path(urlparse(url).path).suffix.lower()
    if path_ext in (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"):
        return path_ext
    mapping = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/gif": ".gif",
        "image/svg+xml": ".svg",
        "image/webp": ".webp",
    }
    return mapping.get(content_type.split(";")[0].strip(), ".png")


def download(url: str) -> tuple[bytes, str] | None:
    for attempt in range(MAX_ATTEMPTS):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "paper-translate/1.0"})
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                return resp.read(), resp.headers.get("Content-Type", "")
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            if attempt + 1 >= MAX_ATTEMPTS:
                return None
    return None


def main() -> int:
    if len(sys.argv) != 4:
        print(__doc__, file=sys.stderr)
        return 2
    source_url, input_html, output_dir = sys.argv[1:4]
    out = Path(output_dir)
    assets_dir = out / "assets"

    html = Path(input_html).read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(html, "html.parser")

    total = 0
    downloaded = 0
    for i, img in enumerate(soup.find_all("img")):
        src = img.get("src", "")
        if not src or src.startswith("data:"):
            continue
        total += 1
        abs_url = urljoin(source_url, src)
        result = download(abs_url)
        if result is None:
            print(f"WARN: failed to fetch image {abs_url}", file=sys.stderr)
            del img["src"]
            continue
        data, content_type = result
        ext = guess_ext(abs_url, content_type)
        assets_dir.mkdir(parents=True, exist_ok=True)
        filename = f"img{i:04d}{ext}"
        (assets_dir / filename).write_bytes(data)
        img["src"] = f"assets/{filename}"
        downloaded += 1

    out.mkdir(parents=True, exist_ok=True)
    (out / "source.html").write_text(str(soup), encoding="utf-8")
    print(f"images: total={total} downloaded={downloaded} failed={total - downloaded}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
