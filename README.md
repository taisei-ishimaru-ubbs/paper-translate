# paper-translate

arXiv 論文を arq で取得し、pdf2zh + Ollama (minimax-m3:cloud) で日本語 PDF 化する基盤リポジトリ。

## ワークフロー

1. `arq get <arxiv_id>` — 論文を `papers/` に取得
2. watchexec デーモンが `paper.pdf` の追加を検知し、自動で `pdf2zh` を実行
3. `paper_ja.pdf` が生成される
4. `scripts/arq-select.sh`（または Ctrl-A）で論文を選択して閲覧

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

# 手動翻訳
scripts/translate-papers-daemon.sh
```

## 環境変数

| 変数 | デフォルト | 説明 |
|---|---|---|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama エンドポイント |
| `OLLAMA_MODEL` | `minimax-m3:cloud` | 翻訳モデル |

`scripts/com.taisei.translate-papers.plist` の `EnvironmentVariables` で上書き可能。

## 要件

- `arq` (brew)
- `pdf2zh` (uv tool)
- `watchexec` (brew)
- `ollama`（`ollama signin` 済み）
- `fzf` (brew)
- Skim（PDF ビューア）
