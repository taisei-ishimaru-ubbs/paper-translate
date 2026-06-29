#!/usr/bin/env bash
# watchexec wrapper: watch papers/ for new paper.pdf and invoke translate-papers-daemon.sh.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# NOTE: arq stores papers at papers/arxiv.org/<category>/<id>/paper.pdf (deep).
# The article's "*/paper.pdf" only matches one level deep and never fires here,
# so we use "**/paper.pdf" which matches paper.pdf at any depth. Generated
# paper_ja.pdf / paper-dual.pdf are intentionally ignored to avoid retriggering.
#
# --no-vcs-ignore / --no-project-ignore are REQUIRED: this repo's .gitignore
# excludes "papers/*", and watchexec respects .gitignore by default, which would
# otherwise make it silently ignore every paper.pdf event under papers/.
exec watchexec \
  --watch "$ROOT/papers" \
  --filter "**/paper.pdf" \
  --no-vcs-ignore \
  --no-project-ignore \
  --debounce 30s \
  --on-busy-update queue \
  --no-meta \
  -- "$SCRIPT_DIR/translate-papers-daemon.sh"
