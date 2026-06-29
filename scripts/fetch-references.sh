#!/usr/bin/env bash
# Fetch a paper's references and citations from the Semantic Scholar Graph API
# and save them to <paper_dir>/references.json.
#
# arq does not capture citation relationships and meta.json is owned by arq, so
# we keep the citation graph in our own references.json instead.
#
# Usage: fetch-references.sh <paper_dir> [--force]
#   <paper_dir> = papers/arxiv.org/<category>/<id>
set -euo pipefail

export PATH="$PATH:/Users/ishimarutaisei/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_DIR="$ROOT/.logs"
LOG_FILE="$LOG_DIR/references.log"

# Semantic Scholar is unauthenticated here and returns 429 readily, so back off.
S2_SLEEP="${S2_SLEEP:-3}"        # seconds to sleep after each successful call
S2_MAX_RETRY="${S2_MAX_RETRY:-4}"
S2_LIMIT="${S2_LIMIT:-1000}"
S2_BASE="https://api.semanticscholar.org/graph/v1/paper"

dir="${1:-}"
force=0
[[ "${2:-}" == "--force" ]] && force=1

mkdir -p "$LOG_DIR"
log() { printf '[%s] %s\n' "$(date '+%Y-%m-%dT%H:%M:%S%z')" "$*" >> "$LOG_FILE"; }

if [[ -z "$dir" || ! -d "$dir" ]]; then
  echo "usage: $0 <paper_dir> [--force]" >&2
  exit 2
fi

for t in curl jq; do
  command -v "$t" >/dev/null 2>&1 || { log "ERROR: $t not found in PATH"; exit 1; }
done

meta="$dir/meta.json"
out="$dir/references.json"

[[ -f "$meta" ]] || { log "SKIP: no meta.json in $dir"; exit 0; }
if [[ -f "$out" && "$force" -eq 0 ]]; then
  log "SKIP: references.json already exists in $dir"
  exit 0
fi

id="$(jq -r '.id // .ID // ""' "$meta")"
[[ -n "$id" ]] || { log "ERROR: no id in $meta"; exit 1; }

# GET a Semantic Scholar endpoint with exponential backoff on 429/5xx.
# Echoes the JSON body on success; returns "[]"-wrapped empty data on 404.
s2_get() {
  local url="$1" attempt=0 body code resp backoff
  while :; do
    resp="$(curl -sS -m 30 -w $'\n%{http_code}' "$url" 2>>"$LOG_FILE" || true)"
    code="${resp##*$'\n'}"
    body="${resp%$'\n'*}"
    case "$code" in
      200) printf '%s' "$body"; sleep "$S2_SLEEP"; return 0 ;;
      404) log "WARN: 404 (not in S2) for $url"; printf '%s' '{"data":[]}'; return 0 ;;
      429|5*)
        attempt=$((attempt + 1))
        if [[ "$attempt" -gt "$S2_MAX_RETRY" ]]; then
          log "ERROR: gave up after $S2_MAX_RETRY retries ($code) for $url"
          return 1
        fi
        backoff=$((5 * 3 ** (attempt - 1)))   # 5, 15, 45, 135 ...
        log "rate-limited ($code), retry $attempt/$S2_MAX_RETRY in ${backoff}s: $url"
        sleep "$backoff"
        ;;
      *) log "ERROR: unexpected HTTP $code for $url"; return 1 ;;
    esac
  done
}

# Map a Semantic Scholar paper list under .data[].<key> to our compact shape:
# [{arxiv_id, title}], stripping any trailing version suffix (v3) from arXiv IDs.
extract() {
  local key="$1"
  jq -c --arg key "$key" '
    [ .data[]? | .[$key] | select(. != null)
      | { arxiv_id: (.externalIds.ArXiv // null | if . == null then null else sub("v[0-9]+$"; "") end),
          title: (.title // "") } ]'
}

log "fetching references/citations for $id"

refs_raw="$(s2_get "$S2_BASE/arXiv:$id/references?fields=externalIds,title&limit=$S2_LIMIT")" || exit 1
cites_raw="$(s2_get "$S2_BASE/arXiv:$id/citations?fields=externalIds,title&limit=$S2_LIMIT")" || exit 1

references="$(printf '%s' "$refs_raw" | extract citedPaper)"
citations="$(printf '%s' "$cites_raw" | extract citingPaper)"

tmp="$out.tmp.$$"
if jq -n \
    --arg id "$id" \
    --argjson references "$references" \
    --argjson citations "$citations" \
    '{ id: $id, references: $references, citations: $citations }' > "$tmp"; then
  mv "$tmp" "$out"
  log "done: $out (references=$(printf '%s' "$references" | jq length), citations=$(printf '%s' "$citations" | jq length))"
else
  rm -f "$tmp"
  log "ERROR: failed to assemble references.json for $id"
  exit 1
fi
