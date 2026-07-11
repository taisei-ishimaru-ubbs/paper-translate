#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_ROOT="$(mktemp -d)"
trap 'rm -rf "$TMP_ROOT"' EXIT

WORK="$TMP_ROOT/work"
mkdir -p "$WORK/scripts" "$WORK/.venv/bin" "$WORK/.logs"
cp "$PROJECT_ROOT/scripts/translate-paper.sh" "$WORK/scripts/"
CALL_LOG="$WORK/calls.log"
export CALL_LOG GEMINI_API_KEY=test-key

cat > "$WORK/scripts/fetch-paper-source.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
dir="$1"
mkdir -p "$dir/.translate"
if [[ -n "${PAPER_FETCH_NO_TEX:-}" ]]; then
  printf '{"source":"arxiv_html"}\n' > "$dir/.translate/state.json"
  echo 'fetch:html' >> "$CALL_LOG"
else
  printf '{"source":"latex"}\n' > "$dir/.translate/state.json"
  echo 'fetch:latex' >> "$CALL_LOG"
fi
EOF

cat > "$WORK/.venv/bin/python" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
[[ "${1:-}" == "-c" ]] && exit 0
script="$(basename "$1")"
dir="$2"
case "$script" in
  convert_tex_to_markdown.py)
    echo 'convert:tex' >> "$CALL_LOG"
    [[ "${FAIL_TEX:-0}" == 1 ]] && exit 1
    touch "$dir/.translate/paper_en.md" "$dir/.translate/bibs.json"
    ;;
  convert_to_markdown.py)
    echo 'convert:html' >> "$CALL_LOG"
    touch "$dir/.translate/paper_en.md" "$dir/.translate/bibs.json"
    ;;
  translate_markdown.py) echo 'translate' >> "$CALL_LOG" ;;
  link_citations.py) echo 'render' >> "$CALL_LOG" ;;
  *) echo "unexpected script: $script" >&2; exit 1 ;;
esac
EOF
chmod +x "$WORK/scripts/"*.sh "$WORK/.venv/bin/python"

mkdir -p "$WORK/paper-latex" "$WORK/paper-fallback"
FAIL_TEX=0 bash "$WORK/scripts/translate-paper.sh" "$WORK/paper-latex"
FAIL_TEX=1 bash "$WORK/scripts/translate-paper.sh" "$WORK/paper-fallback"

expected=$'fetch:latex\nconvert:tex\ntranslate\nrender\nfetch:latex\nconvert:tex\nfetch:html\nconvert:html\ntranslate\nrender'
actual="$(cat "$CALL_LOG")"
[[ "$actual" == "$expected" ]] || {
  echo "unexpected routing:" >&2
  printf '%s\n' "$actual" >&2
  exit 1
}

echo 'translate-paper routing tests passed'
