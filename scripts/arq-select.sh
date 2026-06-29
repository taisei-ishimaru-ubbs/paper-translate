#!/usr/bin/env bash
# Interactive paper selector: arq list --tsv | fzf -> open PDF or browser.

set -euo pipefail

export PATH="$PATH:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

tsv="$(arq list --tsv 2>/dev/null)"
if [[ -z "$tsv" ]]; then
  echo "No papers found. Run: arq get <arxiv_id>"
  exit 0
fi

# TSV columns: ID\tTitle\tAuthorShort\tPublishedShort\tKeywords
# fzf shows cols 2..4; searches all including keywords (col 5)
selected="$(echo "$tsv" | fzf \
  --prompt 'Paper> ' \
  --with-nth=2..4 \
  --preview "$SCRIPT_DIR/arq-preview.sh {1}" \
  --preview-window=right:50%:wrap \
  --height=80%)"

[[ -z "$selected" ]] && exit 0

id="$(echo "$selected" | cut -f1)"
pdf_path="$(arq path "$id" 2>/dev/null)" || true
dir="$(dirname "$pdf_path")"

actions="Summary (browser)\nPDF (English)"
[[ -f "$dir/paper_ja.pdf" ]] && actions="$actions\nPDF (Japanese)"

action="$(printf '%b' "$actions" | fzf --prompt 'Action> ' --height=10)"

case "$action" in
  "Summary (browser)")
    arq view "$id"
    ;;
  "PDF (English)")
    open -a Skim "$dir/paper.pdf"
    ;;
  "PDF (Japanese)")
    open -a Skim "$dir/paper_ja.pdf"
    ;;
esac
