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

queue=()
while IFS= read -r -d '' pdf; do
  dir="$(dirname "$pdf")"
  if [[ ! -f "$dir/paper_ja.pdf" ]]; then
    queue+=("$pdf")
  fi
done < <(find "$PAPERS_DIR" -name "paper.pdf" -type f -print0 2>/dev/null)

if [[ ${#queue[@]} -eq 0 ]]; then
  log "nothing to translate"
  log "=== done ==="
  exit 0
fi

log "${#queue[@]} paper(s) to translate"

for pdf in "${queue[@]}"; do
  dir="$(dirname "$pdf")"
  log "translating: $pdf"
  OLLAMA_HOST="$OLLAMA_HOST" OLLAMA_MODEL="$OLLAMA_MODEL" \
    pdf2zh "$pdf" -li en -lo ja -s ollama -t 1 -o "$dir"
  if [[ -f "$dir/paper-mono.pdf" ]]; then
    mv "$dir/paper-mono.pdf" "$dir/paper_ja.pdf"
    log "done: $dir/paper_ja.pdf"
  else
    log "WARN: paper-mono.pdf not found after translation for $pdf"
  fi
done

log "=== done ==="
