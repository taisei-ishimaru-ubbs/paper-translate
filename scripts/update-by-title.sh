#!/usr/bin/env bash
# (Re)build papers/by-title/<English title> symlinks pointing to arq's <id> dirs.
# arq stores papers at papers/arxiv.org/<category>/<id>/. Renaming those breaks arq,
# so we expose a human-friendly alias tree of relative symlinks instead.
set -euo pipefail

export PATH="$PATH:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PAPERS_DIR="$ROOT/papers"
ARXIV_DIR="$PAPERS_DIR/arxiv.org"
BYTITLE_DIR="$PAPERS_DIR/by-title"
LOG_DIR="$ROOT/.logs"
LOG_FILE="$LOG_DIR/by-title.log"

mkdir -p "$LOG_DIR"
log() { printf '[%s] %s\n' "$(date '+%Y-%m-%dT%H:%M:%S%z')" "$*" >> "$LOG_FILE"; }

command -v jq >/dev/null 2>&1 || { log "ERROR: jq not found"; exit 1; }
[[ -d "$ARXIV_DIR" ]] || { log "no arxiv.org dir yet"; exit 0; }

# Replace path-breaking / control chars; keep spaces and capitalization.
sanitize_title() {
  printf '%s' "$1" \
    | tr '/\n\r\t' '____' \
    | sed -E 's/[[:cntrl:]]//g; s/^[[:space:].]+//; s/[[:space:].]+$//'
}

# Rebuild from scratch so stale links are removed.
rm -rf "$BYTITLE_DIR"
mkdir -p "$BYTITLE_DIR"

count=0
while IFS= read -r -d '' meta; do
  dir="$(dirname "$meta")"            # papers/arxiv.org/<cat>/<id>
  id="$(basename "$dir")"
  title="$(jq -r '.title // ""' "$meta" 2>/dev/null)"
  [[ -z "$title" ]] && title="$id"
  name="$(sanitize_title "$title")"
  [[ -z "$name" ]] && name="$id"

  link="$BYTITLE_DIR/$name"
  if [[ -e "$link" || -L "$link" ]]; then
    name="$name ($id)"
    link="$BYTITLE_DIR/$name"
  fi

  # Relative target from by-title/ -> arxiv.org/<cat>/<id>
  rel="../arxiv.org/${dir#$ARXIV_DIR/}"
  ln -s "$rel" "$link"
  count=$((count + 1))
done < <(find "$ARXIV_DIR" -mindepth 3 -maxdepth 3 -name meta.json -print0 2>/dev/null)

log "rebuilt by-title: $count link(s)"
