#!/usr/bin/env bash
# Orchestrate the ar5iv/arXiv-HTML-or-PDF -> Docling Markdown -> LiteLLM
# Japanese translation -> Obsidian citation-linked Markdown pipeline for one
# paper. Replaces the old pdf2zh step.
#
# Usage: translate-paper.sh <paper_dir> [--force]
#
# Stages (fetch-paper-source -> convert_to_markdown -> translate_markdown ->
# link_citations) are each independently idempotent, keyed off their own
# output file, so re-running after a partial failure (e.g. a rate-limited
# translation call) only repeats what didn't finish. After
# TRANSLATE_MAX_FAILURES consecutive failures of the SAME stage, a
# <paper_dir>/.translate/failed marker is written and this script becomes a
# no-op until that marker is removed or --force is passed.
set -euo pipefail

export PATH="$PATH:/Users/ishimarutaisei/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_DIR="$ROOT/.logs"
LOG_FILE="$LOG_DIR/translate.log"
PYBIN="$ROOT/.venv/bin/python"

MAX_FAILURES="${TRANSLATE_MAX_FAILURES:-3}"

dir="${1:-}"
force=0
[[ "${2:-}" == "--force" ]] && force=1

mkdir -p "$LOG_DIR"
log() { printf '[%s] %s\n' "$(date '+%Y-%m-%dT%H:%M:%S%z')" "translate-paper: $*" >> "$LOG_FILE"; }

if [[ -z "$dir" || ! -d "$dir" ]]; then
  echo "usage: $0 <paper_dir> [--force]" >&2
  exit 2
fi

if [[ ! -x "$PYBIN" ]] || ! "$PYBIN" -c "import docling, litellm, bs4" 2>/dev/null; then
  log "ERROR: docling/litellm/beautifulsoup4 not available in $PYBIN. Run scripts/setup.sh"
  exit 1
fi
if [[ -z "${OPENAI_API_KEY:-}" && -z "${GEMINI_API_KEY:-}" ]]; then
  log "ERROR: neither OPENAI_API_KEY nor GEMINI_API_KEY is set (add to $ROOT/.env.local)"
  exit 1
fi

translate_dir="$dir/.translate"
failed_marker="$translate_dir/failed"

if [[ -f "$failed_marker" && "$force" -eq 0 ]]; then
  log "SKIP: $dir marked failed after repeated attempts (rm $failed_marker or pass --force)"
  exit 0
fi
[[ "$force" -eq 1 ]] && rm -f "$failed_marker"

bump_failure() {
  local stage="$1" count_file count
  mkdir -p "$translate_dir"
  count_file="$translate_dir/.failcount-$stage"
  count=$(( $(cat "$count_file" 2>/dev/null || echo 0) + 1 ))
  echo "$count" > "$count_file"
  if [[ "$count" -ge "$MAX_FAILURES" ]]; then
    log "ERROR: $stage failed $count times for $dir, marking failed"
    date -u '+%Y-%m-%dT%H:%M:%SZ' > "$failed_marker"
  fi
}

clear_failure() { rm -f "$translate_dir/.failcount-$1" 2>/dev/null || true; }

run_stage() {
  local name="$1"
  shift
  if "$@"; then
    clear_failure "$name"
    return 0
  fi
  log "WARN: stage '$name' failed for $dir"
  bump_failure "$name"
  return 1
}

run_stage fetch bash "$SCRIPT_DIR/fetch-paper-source.sh" "$dir" || exit 1
run_stage convert "$PYBIN" "$SCRIPT_DIR/convert_to_markdown.py" "$dir" || exit 1
run_stage translate "$PYBIN" "$SCRIPT_DIR/translate_markdown.py" "$dir" || exit 1
run_stage render "$PYBIN" "$SCRIPT_DIR/link_citations.py" "$dir" || exit 1

log "done: $dir"
