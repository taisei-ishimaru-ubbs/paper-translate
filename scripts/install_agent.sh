#!/usr/bin/env bash
# Install / uninstall the launchd agent that watches papers/ and runs pdf2zh translation.

set -euo pipefail

LABEL="com.taisei.translate-papers"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_PLIST="${SCRIPT_DIR}/${LABEL}.plist"
AGENTS_DIR="${HOME}/Library/LaunchAgents"
LINK_PLIST="${AGENTS_DIR}/${LABEL}.plist"
DOMAIN="gui/$(id -u)"
TARGET="${DOMAIN}/${LABEL}"

cmd="${1:-install}"

case "$cmd" in
  install)
    if [[ ! -f "$PROJECT_PLIST" ]]; then
      echo "ERROR: plist not found at $PROJECT_PLIST" >&2
      exit 1
    fi
    mkdir -p "$AGENTS_DIR"
    ln -sf "$PROJECT_PLIST" "$LINK_PLIST"
    echo "symlinked: $LINK_PLIST -> $PROJECT_PLIST"
    launchctl bootout "$TARGET" 2>/dev/null || true
    launchctl bootstrap "$DOMAIN" "$LINK_PLIST"
    launchctl enable "$TARGET"
    echo "installed: $TARGET"
    ;;
  uninstall)
    launchctl bootout "$TARGET" 2>/dev/null || true
    rm -f "$LINK_PLIST"
    echo "uninstalled: $TARGET"
    ;;
  status)
    launchctl print "$TARGET" 2>/dev/null || echo "not loaded: $TARGET"
    ;;
  *)
    echo "usage: $0 {install|uninstall|status}" >&2
    exit 2
    ;;
esac
