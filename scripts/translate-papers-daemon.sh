#!/usr/bin/env bash
# Scan papers/ for untranslated PDFs and translate them via pdf2zh + Ollama.
set -euo pipefail

export PATH="$PATH:/Users/ishimarutaisei/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PAPERS_DIR="$ROOT/papers"
LOG_DIR="$ROOT/.logs"
LOG_FILE="$LOG_DIR/translate.log"
LOCK_FILE="/tmp/translate_papers.lock"

OLLAMA_HOST="${OLLAMA_HOST:-http://localhost:11434}"
OLLAMA_MODEL="${OLLAMA_MODEL:-minimax-m3:cloud}"

mkdir -p "$LOG_DIR"
exec >> "$LOG_FILE" 2>&1

log() {
  printf '[%s] %s\n' "$(date '+%Y-%m-%dT%H:%M:%S%z')" "$*" >&2
}

if ! mkdir "$LOCK_FILE" 2>/dev/null; then
  log "SKIP: another run holds $LOCK_FILE"
  exit 0
fi
trap 'rmdir "$LOCK_FILE" 2>/dev/null || true' EXIT

log "=== translate-papers-daemon start ==="

if ! command -v pdf2zh >/dev/null 2>&1; then
  log "ERROR: pdf2zh not found in PATH ($PATH)"
  exit 1
fi

# Collect all papers; each may need translation, a summary, or both.
papers=()
while IFS= read -r -d '' pdf; do
  papers+=("$pdf")
done < <(find "$PAPERS_DIR" -path "$PAPERS_DIR/by-title" -prune -o -name "paper.pdf" -type f -print0 2>/dev/null)

if [[ ${#papers[@]} -eq 0 ]]; then
  log "no papers found"
  log "=== done ==="
  exit 0
fi

did_work=0
for pdf in "${papers[@]}"; do
  dir="$(dirname "$pdf")"

  # 1. Translate body PDF if not already done.
  if [[ ! -f "$dir/paper_ja.pdf" ]]; then
    did_work=1
    log "translating: $pdf"
    OLLAMA_HOST="$OLLAMA_HOST" OLLAMA_MODEL="$OLLAMA_MODEL" \
      pdf2zh "$pdf" -li en -lo ja -s ollama -t 1 -o "$dir"
    if [[ -f "$dir/paper-mono.pdf" ]]; then
      mv "$dir/paper-mono.pdf" "$dir/paper_ja.pdf"
      log "translated: $dir/paper_ja.pdf"
    else
      log "WARN: paper-mono.pdf not found after translation for $pdf"
    fi
  fi

  # 2. Generate a Japanese summary if not already done (independent of translation).
  if [[ ! -f "$dir/summary.md" ]]; then
    did_work=1
    log "summarizing: $dir"
    OLLAMA_HOST="$OLLAMA_HOST" OLLAMA_MODEL="$OLLAMA_MODEL" \
      bash "$SCRIPT_DIR/summarize-paper.sh" "$dir" || log "WARN: summary failed for $dir"
  fi

  # 3. Fetch the citation graph from Semantic Scholar (independent of the above).
  if [[ ! -f "$dir/references.json" ]]; then
    did_work=1
    log "fetching references: $dir"
    bash "$SCRIPT_DIR/fetch-references.sh" "$dir" || log "WARN: references failed for $dir"
  fi

  # 4. Extract figures and pick a method-overview thumbnail.
  if [[ ! -f "$dir/overview.png" ]]; then
    did_work=1
    log "extracting figures: $dir"
    bash "$SCRIPT_DIR/extract-figures.sh" "$dir" || log "WARN: figures failed for $dir"
  fi
done

# 5. Rebuild Obsidian notes (stored next to each paper as <snake(title)>.md).
#    Wikilinks resolve by note basename, so build one shared id->slug map first,
#    disambiguating any slug shared by two papers, then regenerate every note.
snake() {
  printf '%s' "$1" | tr '[:upper:]' '[:lower:]' \
    | sed -E 's/[^[:alnum:]]+/_/g; s/^_+//; s/_+$//'
}
local_map="$(mktemp)"
declare -A SEEN_SLUG
for pdf in "${papers[@]}"; do
  dir="$(dirname "$pdf")"
  [[ -f "$dir/meta.json" ]] || continue
  mid="$(jq -r '.id // .ID // ""' "$dir/meta.json")"
  [[ -n "$mid" ]] || continue
  mslug="$(snake "$(jq -r '.title // .Title // ""' "$dir/meta.json")")"
  [[ -n "$mslug" ]] || mslug="$(snake "$mid")"
  [[ -n "${SEEN_SLUG[$mslug]:-}" ]] && mslug="${mslug}_${mid//./_}"
  SEEN_SLUG["$mslug"]=1
  printf '%s\t%s\n' "$mid" "$mslug" >> "$local_map"
done
for pdf in "${papers[@]}"; do
  dir="$(dirname "$pdf")"
  LOCAL_MAP_FILE="$local_map" \
    bash "$SCRIPT_DIR/generate-obsidian-note.sh" "$dir" --force || log "WARN: note failed for $dir"
done
rm -f "$local_map"

# 6. Refresh the human-friendly by-title symlink tree.
bash "$SCRIPT_DIR/update-by-title.sh" || log "WARN: update-by-title failed"

# 7. Commit and push the complete paper library after processing. Only papers/
#    and gallery.md are eligible; the helper refuses unsafe branch states.
if [[ "${PAPER_LIBRARY_AUTO_PUSH:-1}" == "1" ]]; then
  bash "$SCRIPT_DIR/commit-paper-library.sh" || {
    log "ERROR: paper-library commit/push failed"
    exit 1
  }
else
  log "paper-library commit/push disabled (PAPER_LIBRARY_AUTO_PUSH=$PAPER_LIBRARY_AUTO_PUSH)"
fi

[[ "$did_work" -eq 0 ]] && log "nothing new to process"
log "=== done ==="
