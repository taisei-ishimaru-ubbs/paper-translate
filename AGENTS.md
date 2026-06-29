# リポジトリルール

## 目的

arq で取得した arXiv 論文を pdf2zh + Ollama で日本語 PDF 化するための基盤。
スクリプト・設定・launchd agent のみを管理する。論文本体は `papers/` に置くが git 管理外。

## ディレクトリ構成

```
scripts/
  translate-papers-daemon.sh   # papers/ を走査して未翻訳 PDF を翻訳
  translate-papers-watch.sh    # watchexec ラッパー
  arq-select.sh                # fzf セレクタ
  arq-preview.sh               # fzf プレビュー
  setup.sh                     # 初回設定
  install_agent.sh             # launchd agent の install/uninstall/status
  com.taisei.translate-papers.plist  # launchd agent 定義
papers/                        # arq が論文を保存（git 管理外、.gitkeep のみ追跡）
.logs/                         # デーモン・launchd のログ（git 管理外）
```

## 翻訳

- 本文 PDF 翻訳は `pdf2zh` + `OLLAMA_MODEL=minimax-m3:cloud`。
- arq 自体の title/abstract LLM 翻訳は無効（`translate.enabled = false`）。
- minimax-m3:cloud は Ollama クラウド実行のため `ollama signin` が必須。

## Git 操作

- スクリプト・設定の変更のみ commit する。
- `papers/`、`.logs/` は commit しない。
- commit / push はユーザーから明示的に指示された場合のみ実行する。
