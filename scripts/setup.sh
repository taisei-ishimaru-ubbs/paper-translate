#!/usr/bin/env bash
# One-shot setup: configure arq root and disable built-in LLM translation.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
PAPERS_DIR="$ROOT/papers"
LOG_DIR="$ROOT/.logs"

echo "=== arq + pdf2zh setup ==="

mkdir -p "$PAPERS_DIR" "$LOG_DIR"
echo "created: $PAPERS_DIR"
echo "created: $LOG_DIR"

arq config set root "$PAPERS_DIR"
arq config set translate.enabled false
arq config set summarize.enabled false

echo ""
echo "=== current arq config ==="
arq config
echo ""
echo "Setup complete."
echo ""
echo "Next steps:"
echo "  1. ollama signin            # minimax-m3:cloud requires Ollama account"
echo "  2. scripts/install_agent.sh install   # start watchexec daemon via launchd"
echo "  3. arq get <arxiv_id>       # fetch a paper"
