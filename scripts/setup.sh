#!/usr/bin/env bash
# One-shot setup: configure arq root and disable built-in LLM translation.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PAPERS_DIR="$ROOT/papers"
LOG_DIR="$ROOT/.logs"

echo "=== arq + Markdown translation setup ==="

mkdir -p "$PAPERS_DIR" "$ROOT/inbox" "$LOG_DIR"
echo "created: $PAPERS_DIR and $ROOT/inbox"
echo "created: $LOG_DIR"

if ! command -v git-lfs >/dev/null 2>&1; then
  echo "ERROR: git-lfs is required (brew install git-lfs)" >&2
  exit 1
fi
git -C "$ROOT" lfs install --local
echo "Git LFS: configured for this repository"

# PyMuPDF (figure cropping), Docling (HTML/PDF -> Markdown), LiteLLM
# (openai -> gemini translation fallback) and BeautifulSoup4 (HTML
# pre-processing) live in a project venv to avoid PEP 668 issues.
# NOTE: docling pulls in torch and is a multi-GB install; it can take a
# while the first time.
if [[ ! -x "$ROOT/.venv/bin/python" ]]; then
  uv venv "$ROOT/.venv"
fi
if ! "$ROOT/.venv/bin/python" -c "import fitz, docling, litellm, tenacity, bs4" 2>/dev/null; then
  echo "installing pymupdf/docling/litellm/tenacity/beautifulsoup4 into $ROOT/.venv (this can take a while) ..."
  uv pip install --python "$ROOT/.venv/bin/python" pymupdf docling litellm tenacity beautifulsoup4
fi
echo "PyMuPDF: $("$ROOT/.venv/bin/python" -c 'import fitz; print(fitz.pymupdf_version)')"
echo "Docling: $("$ROOT/.venv/bin/python" -c 'import docling; print(docling.__version__)' 2>/dev/null || echo installed)"

if ! command -v pandoc >/dev/null 2>&1; then
  echo "WARN: pandoc is unavailable; LaTeX papers will fall back to HTML/PDF conversion" >&2
fi

if [[ "${PREFETCH_DOCLING_MODELS:-0}" == "1" ]]; then
  echo "prefetching Docling PDF pipeline models ..."
  "$ROOT/.venv/bin/docling-tools" models download
fi

arq config set root "$PAPERS_DIR"
arq config set translate.enabled false
arq config set summarize.enabled false

echo ""
echo "=== current arq config ==="
arq config
echo ""
echo "Setup complete."
echo ""
echo "Next steps:"
echo "  1. ollama signin            # minimax-m3:cloud requires Ollama account"
echo "  2. scripts/install_agent.sh install   # start watchexec daemon via launchd"
echo "  3. arq get <arxiv_id>       # fetch a paper"
echo "     or: cp paper.pdf $ROOT/inbox/  # import a manually obtained PDF"
