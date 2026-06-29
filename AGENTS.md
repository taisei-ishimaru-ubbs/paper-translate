# リポジトリルール

## 目的

arq で取得した arXiv 論文を pdf2zh + Ollama で日本語 PDF 化するための基盤。
スクリプト・設定・launchd agent のみを管理する。論文本体は `papers/` に置くが git 管理外。

## ディレクトリ構成

```
scripts/
  translate-papers-daemon.sh   # papers/ を走査して翻訳・要約・by-title更新
  translate-papers-watch.sh    # watchexec ラッパー
  summarize-paper.sh           # 単一論文の日本語要約を Ollama で生成
  update-by-title.sh           # by-title symlink ツリーの再構築
  arq-select.sh                # fzf セレクタ
  arq-preview.sh               # fzf プレビュー（summary.md を表示）
  setup.sh                     # 初回設定
  install_agent.sh             # launchd agent の install/uninstall/status
  com.taisei.translate-papers.plist  # launchd agent 定義
papers/
  arxiv.org/<cat>/<id>/        # arq の実体（構造ハードコード・リネーム禁止）
  by-title/<英語タイトル>/      # 実体への相対 symlink（人間用の別名）
.logs/                         # デーモン・launchd のログ（git 管理外）
```

## 翻訳・要約

- 本文 PDF 翻訳は `pdf2zh` + `OLLAMA_MODEL=minimax-m3:cloud` → `paper_ja.pdf`。
- 要約は `summarize-paper.sh`（pdftotext → Ollama）→ `summary.md`（arq view が読む名前）。
- arq 自体の title/abstract LLM 翻訳・summarize は無効（Ollama 非対応のため）。
- minimax-m3:cloud は Ollama クラウド実行のため `ollama signin` が必須。

## フォルダ構造の制約

- arq は `papers/arxiv.org/<cat>/<id>/` を直接探す（`internal/paper/store.go`）。
  **この実体ディレクトリをリネームしない**こと。英語名アクセスは `by-title/` の symlink で提供する。

## Git 操作

- スクリプト・設定の変更のみ commit する。
- `papers/`、`.logs/` は commit しない。
- commit / push はユーザーから明示的に指示された場合のみ実行する。
