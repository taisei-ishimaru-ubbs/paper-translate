#!/usr/bin/env bash
# fzf preview: show summary.md or paper metadata for the selected arXiv ID.

set -euo pipefail

export PATH="$PATH:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"

id="$1"
[[ -z "$id" ]] && exit 0

pdf_path="$(arq path "$id" 2>/dev/null)" || true
if [[ -z "$pdf_path" ]]; then
  echo "No local data for $id"
  exit 0
fi

dir="$(dirname "$pdf_path")"
summary="$dir/summary.md"

if [[ -f "$summary" ]]; then
  cat "$summary"
elif [[ -f "$dir/meta.json" ]]; then
  cat "$dir/meta.json"
else
  echo "[$id]"
  echo "dir: $dir"
  ls "$dir" 2>/dev/null || true
fi
