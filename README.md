# paper-translate

arXiv 論文を arq で取得し、pdf2zh + Ollama (minimax-m3:cloud) で日本語 PDF 化・要約する基盤リポジトリ。

## ワークフロー

1. `arq get <arxiv_id>` — 論文を `papers/` に取得
2. watchexec デーモンが `paper.pdf` の追加を検知し、自動で以下を実行
   - `pdf2zh` による本文翻訳 → `paper_ja.pdf`
   - Ollama による日本語要約 → `summary.md`
   - 英語タイトルの別名 symlink → `papers/by-title/<英語タイトル>/`
3. `scripts/arq-select.sh`（または Ctrl-A）で論文を選択して閲覧

## ディレクトリ構成

```
papers/
├── arxiv.org/<category>/<id>/   # arq の実体（変更不可）
│   ├── paper.pdf                # 原文
│   ├── paper_ja.pdf             # 日本語訳
│   ├── summary.md               # 日本語要約
│   └── meta.json
└── by-title/<英語タイトル>/      # 上記実体への symlink（人間用の別名）
```

## セットアップ

```bash
# 初回のみ
scripts/setup.sh
scripts/install_agent.sh install

# Ollama 認証（minimax-m3:cloud に必要）
ollama signin
```

## コマンド

```bash
# 論文取得
arq get 2501.12345

# インタラクティブ選択（fzf）
scripts/arq-select.sh

# デーモン操作
scripts/install_agent.sh install
scripts/install_agent.sh status
scripts/install_agent.sh uninstall

# 手動で翻訳+要約+by-title更新（未処理分をまとめて）
scripts/translate-papers-daemon.sh

# 単一論文の要約のみ生成（--force で再生成）
scripts/summarize-paper.sh papers/arxiv.org/cs.CL/1706.03762

# by-title symlink の再構築
scripts/update-by-title.sh
```

## 環境変数

| 変数 | デフォルト | 説明 |
|---|---|---|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama エンドポイント |
| `OLLAMA_MODEL` | `minimax-m3:cloud` | 翻訳・要約モデル |
| `SUMMARY_MAX_CHARS` | `50000` | 要約に渡す本文の最大文字数 |

`scripts/com.taisei.translate-papers.plist` の `EnvironmentVariables` で上書き可能。

## 要件

- `arq` (brew)
- `pdf2zh` (uv tool)
- `watchexec` (brew)
- `ollama`（`ollama signin` 済み）
- `fzf` (brew)
- Skim（PDF ビューア）
