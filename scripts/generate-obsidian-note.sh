#!/usr/bin/env bash
# Generate an Obsidian note for one paper, stored alongside the paper at
# <paper_dir>/<snake(title)>.md (e.g. attention_is_all_you_need.md).
#
# The repository root is the Obsidian vault, so embeds use vault-root-relative
# paths (papers/arxiv.org/<cat>/<id>/...). References/citations from
# references.json link to locally-held papers as [[<snake>|<title>]] wikilinks
# (resolved by note basename) and to others as plain arXiv links.
#
# Usage: generate-obsidian-note.sh <paper_dir> [--force]
#   LOCAL_MAP_FILE: optional "<id>\t<snake_basename>" map of locally-held papers
#                   (the daemon builds this once and reuses it for all notes).
set -euo pipefail

export PATH="$PATH:/Users/ishimarutaisei/.local/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_DIR="$ROOT/.logs"
LOG_FILE="$LOG_DIR/obsidian.log"

dir="${1:-}"
force=0
[[ "${2:-}" == "--force" ]] && force=1

mkdir -p "$LOG_DIR"
log() { printf '[%s] %s\n' "$(date '+%Y-%m-%dT%H:%M:%S%z')" "$*" >> "$LOG_FILE"; }

# Title -> snake_case slug: lowercase, non-alnum runs -> "_", trim edges.
snake() {
  printf '%s' "$1" | tr '[:upper:]' '[:lower:]' \
    | sed -E 's/[^[:alnum:]]+/_/g; s/^_+//; s/_+$//'
}

if [[ -z "$dir" || ! -d "$dir" ]]; then
  echo "usage: $0 <paper_dir> [--force]" >&2
  exit 2
fi
command -v jq >/dev/null 2>&1 || { log "ERROR: jq not found"; exit 1; }

meta="$dir/meta.json"
[[ -f "$meta" ]] || { log "SKIP: no meta.json in $dir"; exit 0; }

abs_dir="$(cd "$dir" && pwd)"
rel="${abs_dir#$ROOT/}"                 # vault-root-relative paper dir
id="$(jq -r '.id // .ID // ""' "$meta")"
[[ -n "$id" ]] || { log "ERROR: no id in $meta"; exit 1; }

title="$(jq -r '.title // .Title // ""' "$meta")"
category="$(jq -r '.category // .Category // ""' "$meta")"
published="$(jq -r '.published // .Published // ""' "$meta")"

# id -> snake note basename for wikilink resolution. Prefer the shared map the
# daemon builds (handles cross-paper slug collisions); else derive locally.
declare -A NOTE_OF
if [[ -n "${LOCAL_MAP_FILE:-}" && -f "$LOCAL_MAP_FILE" ]]; then
  while IFS=$'\t' read -r mid mslug; do
    [[ -n "$mid" ]] && NOTE_OF["$mid"]="$mslug"
  done < "$LOCAL_MAP_FILE"
else
  while IFS= read -r lid; do
    [[ -z "$lid" ]] && continue
    ldir="$(dirname "$(arq path "$lid" 2>/dev/null || true)")"
    [[ -f "$ldir/meta.json" ]] || continue
    NOTE_OF["$lid"]="$(snake "$(jq -r '.title // .Title // ""' "$ldir/meta.json")")"
  done < <(arq list --id 2>/dev/null || true)
fi

# This paper's own note basename (prefer the shared map for collision handling).
slug="${NOTE_OF[$id]:-$(snake "$title")}"
[[ -n "$slug" ]] || slug="$(snake "$id")"
out="$dir/$slug.md"

# Render one reference/citation list. Reads TSV (arxiv_id\ttitle) on stdin.
render_links() {
  local arxiv t safe note
  while IFS=$'\t' read -r arxiv t; do
    [[ -z "$arxiv" && -z "$t" ]] && continue
    safe="${t//[\[\]|]/ }"            # keep wikilink/markdown syntax intact
    if [[ -n "$arxiv" && "$arxiv" != "null" ]]; then
      note="${NOTE_OF[$arxiv]:-}"
      if [[ -n "$note" ]]; then
        printf -- '- [[%s|%s]]\n' "$note" "$safe"
      else
        printf -- '- %s ([arXiv:%s](https://arxiv.org/abs/%s))\n' "$safe" "$arxiv" "$arxiv"
      fi
    else
      printf -- '- %s\n' "$safe"
    fi
  done
}

refs_tsv=""
cites_tsv=""
if [[ -f "$dir/references.json" ]]; then
  refs_tsv="$(jq -r '.references[]? | [(.arxiv_id // ""), (.title // "")] | @tsv' "$dir/references.json")"
  cites_tsv="$(jq -r '.citations[]? | select((.arxiv_id // "") != "") | [(.arxiv_id // ""), (.title // "")] | @tsv' "$dir/references.json")"
fi

if [[ -f "$out" && "$force" -eq 0 ]]; then
  log "SKIP: note already exists for $id"
  exit 0
fi

tmp="$out.tmp.$$"
{
  echo "---"
  echo "id: $id"
  # jq -r produces a YAML-safe scalar; wrap title in quotes and escape quotes.
  printf 'title: "%s"\n' "${title//\"/\\\"}"
  printf 'aliases: ["%s"]\n' "${title//\"/\\\"}"
  jq -r '"authors:\n" + ((.authors // []) | map("  - " + .) | join("\n"))' "$meta"
  echo "category: $category"
  echo "published: $published"
  [[ -f "$dir/overview.png" ]] && echo "thumbnail: $rel/overview.png"
  echo "tags: [paper]"
  echo "---"
  echo
  echo "# $title"
  echo
  if [[ -f "$dir/overview.png" ]]; then
    echo "![[$rel/overview.png]]"
    echo
  fi
  echo "**分野**: $category ・ **公開**: $published"
  echo
  links=()
  [[ -f "$dir/paper.pdf" ]] && links+=("[原文PDF]($rel/paper.pdf)")
  [[ -f "$dir/paper_ja.pdf" ]] && links+=("[日本語PDF]($rel/paper_ja.pdf)")
  if [[ ${#links[@]} -gt 0 ]]; then
    line="${links[0]}"
    for l in "${links[@]:1}"; do line+=" · $l"; done
    echo "$line"
    echo
  fi
  if [[ -f "$dir/summary.md" ]]; then
    echo "## 要約"
    echo
    echo "![[$rel/summary.md]]"
    echo
  fi
  echo "## 参考文献 (references)"
  echo
  if [[ -n "$refs_tsv" ]]; then
    printf '%s\n' "$refs_tsv" | render_links
  else
    echo "_（取得なし）_"
  fi
  echo
  echo "## 被引用 (citations)"
  echo
  if [[ -n "$cites_tsv" ]]; then
    printf '%s\n' "$cites_tsv" | render_links
  else
    echo "_（取得なし）_"
  fi
} > "$tmp"

mv "$tmp" "$out"
log "wrote note: $out"
