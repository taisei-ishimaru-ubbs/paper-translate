#!/usr/bin/env bash
# Decide whether an arXiv paper has a usable HTML rendering (arxiv.org/html
# first, then ar5iv.labs.arxiv.org) and, if so, fetch it and localize its
# images so convert_to_markdown.py never has to touch the network.
#
# Usage: fetch-paper-source.sh <paper_dir> [--force]
#
# Writes:
#   <paper_dir>/.translate/state.json         {source, url, checked_at}
#   <paper_dir>/.translate/source/source.html (only when source != pdf_only)
#   <paper_dir>/.translate/source/assets/*    (localized images)
#
# "pdf_only" is a cached decision: once written, subsequent runs skip the
# network probe entirely unless --force is passed.
set -euo pipefail

export PATH="$PATH:/Users/ishimarutaisei/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_DIR="$ROOT/.logs"
LOG_FILE="$LOG_DIR/translate.log"

FETCH_MAX_RETRY="${FETCH_MAX_RETRY:-4}"
FETCH_TIMEOUT="${FETCH_TIMEOUT:-60}"

dir="${1:-}"
force=0
[[ "${2:-}" == "--force" ]] && force=1

mkdir -p "$LOG_DIR"
log() { printf '[%s] %s\n' "$(date '+%Y-%m-%dT%H:%M:%S%z')" "fetch-paper-source: $*" >> "$LOG_FILE"; }

if [[ -z "$dir" || ! -d "$dir" ]]; then
  echo "usage: $0 <paper_dir> [--force]" >&2
  exit 2
fi
for tool in curl jq; do
  command -v "$tool" >/dev/null 2>&1 || { log "ERROR: $tool not found"; exit 1; }
done

PYBIN="$ROOT/.venv/bin/python"
[[ -x "$PYBIN" ]] && "$PYBIN" -c "import bs4" 2>/dev/null || {
  log "ERROR: beautifulsoup4 not available in $PYBIN. Run: uv pip install --python $PYBIN beautifulsoup4"
  exit 1
}

translate_dir="$dir/.translate"
state_file="$translate_dir/state.json"
source_dir="$translate_dir/source"

if [[ -f "$state_file" && "$force" -eq 0 ]]; then
  log "SKIP: state.json already exists in $dir ($(jq -r '.source' "$state_file" 2>/dev/null))"
  exit 0
fi

metadata="$(bash "$SCRIPT_DIR/paper-metadata.sh" "$dir" 2>/dev/null || true)"
[[ -n "$metadata" ]] || { log "SKIP: no supported metadata in $dir"; exit 0; }
arxiv_id="$(jq -r '.identifiers.arxiv // ""' <<<"$metadata")"

write_state() {
  local source="$1" url="$2" tmp
  mkdir -p "$translate_dir"
  tmp="$state_file.tmp.$$"
  jq -n --arg source "$source" --arg url "$url" --arg checked_at "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \
    '{source: $source, url: (if $url == "" then null else $url end), checked_at: $checked_at}' > "$tmp"
  mv "$tmp" "$state_file"
}

if [[ -z "$arxiv_id" ]]; then
  write_state "pdf_only" ""
  log "SKIP: no arXiv id for $dir, marked pdf_only"
  exit 0
fi

# Fetch a candidate URL with 429/5xx exponential backoff. Prints two lines on
# success: the HTTP code, then the effective (post-redirect) URL. Body goes to
# the given file. Returns 1 on exhausted retries or non-2xx status.
fetch_candidate() {
  local url="$1" out_file="$2" attempt=0 code final_url backoff
  while :; do
    if ! final_url="$(curl -sL -m "$FETCH_TIMEOUT" -o "$out_file" \
        -w '%{http_code} %{url_effective}' "$url" 2>>"$LOG_FILE")"; then
      code="000"
    else
      code="${final_url%% *}"
      final_url="${final_url#* }"
    fi
    case "$code" in
      2*) printf '%s\n%s\n' "$code" "$final_url"; return 0 ;;
      404) printf '%s\n%s\n' "$code" "$final_url"; return 0 ;;
      429|5*|000)
        attempt=$((attempt + 1))
        if [[ "$attempt" -gt "$FETCH_MAX_RETRY" ]]; then
          log "WARN: giving up on $url after $FETCH_MAX_RETRY retries (last code $code)"
          return 1
        fi
        backoff=$((5 * 3 ** (attempt - 1)))
        log "retrying $url in ${backoff}s (code $code)"
        sleep "$backoff"
        ;;
      *) log "WARN: unexpected HTTP $code for $url"; return 1 ;;
    esac
  done
}

is_ltx_document() { grep -q 'class="ltx_document' "$1" 2>/dev/null; }

source_name=""
source_url=""
raw_html="$translate_dir/.fetch-tmp.$$.html"
mkdir -p "$translate_dir"
trap 'rm -f "$raw_html"' EXIT

for candidate in \
  "arxiv_html https://arxiv.org/html/$arxiv_id" \
  "ar5iv https://ar5iv.labs.arxiv.org/html/$arxiv_id"
do
  name="${candidate%% *}"
  url="${candidate#* }"
  result="$(fetch_candidate "$url" "$raw_html" || true)"
  [[ -z "$result" ]] && continue
  code="$(sed -n '1p' <<<"$result")"
  effective_url="$(sed -n '2p' <<<"$result")"
  [[ "$code" == 2* ]] || continue
  is_ltx_document "$raw_html" || continue
  if [[ "$name" == "ar5iv" ]]; then
    # A conversion-less paper 302s away from ar5iv.labs.arxiv.org entirely.
    [[ "$effective_url" == *"ar5iv"* ]] || continue
  fi
  source_name="$name"
  source_url="$effective_url"
  break
done

if [[ -z "$source_name" ]]; then
  write_state "pdf_only" ""
  log "no HTML rendering found for $arxiv_id, marked pdf_only"
  exit 0
fi

rm -rf "$source_dir"
mkdir -p "$source_dir"
localize_summary="$("$PYBIN" "$SCRIPT_DIR/localize_html_images.py" "$source_url" "$raw_html" "$source_dir" 2>>"$LOG_FILE")" \
  || { log "ERROR: localize_html_images.py failed for $dir"; exit 1; }
log "fetched $source_name for $arxiv_id ($source_url); $localize_summary"

write_state "$source_name" "$source_url"
