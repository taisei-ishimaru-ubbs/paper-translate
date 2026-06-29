# paper-translate

arXiv 論文を arq で取得し、pdf2zh + Ollama で日本語 PDF 化・要約・引用取得・図抽出・Obsidian ノート生成まで自動化する基盤。[`uchidalab/paper-translate`](https://github.com/uchidalab/paper-translate) を root repository とし、各利用者はその fork を使用する。

## セットアップ

```bash
scripts/setup.sh              # 依存インストール・.venv 構築
scripts/install_agent.sh install  # launchd デーモン登録
ollama signin                 # minimax-m3:cloud に必要
```

Obsidian で使う場合はリポジトリルートを vault として開き、`OBSIDIAN.md` の手順に従って Dataview プラグインと `paper-gallery` CSS snippet を有効化する。

## 使い方

```bash
arq get 2501.12345            # 論文を papers/ に取得（デーモンが自動処理）
scripts/arq-select.sh         # fzf で論文を選んで閲覧
```

デーモンは `paper.pdf` の追加を検知すると、翻訳・要約・引用・図・Obsidian ノートを順に生成し、`papers/` と `gallery.md` の変更を commit して `origin` へ push する。

個別スクリプトで手動実行することもできる：

```bash
scripts/translate-papers-daemon.sh                           # 未処理分をまとめて実行
scripts/summarize-paper.sh    papers/arxiv.org/cs.CL/1706.03762
scripts/fetch-references.sh   papers/arxiv.org/cs.CL/1706.03762
scripts/extract-figures.sh    papers/arxiv.org/cs.CL/1706.03762
scripts/generate-obsidian-note.sh papers/arxiv.org/cs.CL/1706.03762
```

## ディレクトリ構成

```
papers/
├── arxiv.org/<category>/<id>/   # arq の実体（パス変更不可）
│   ├── paper.pdf / paper_ja.pdf # 原文・日本語訳
│   ├── summary.md               # 日本語要約
│   ├── references.json          # 引用・被引用（Semantic Scholar）
│   ├── figures/                 # 図クロップ
│   ├── overview.png             # 概要図（arq thumbnail にも登録）
│   └── <snake_case_title>.md    # Obsidian ノート
└── by-title/<snake_case_title>/ # 実体への symlink

gallery.md                       # Dataview ギャラリー
```

概要図の自動選定が外れた場合は `<dir>/.overview-figure` に図番号を書いて `extract-figures.sh --force` で上書きできる。

## Git 運用

- fork では `origin` を自分の fork、`upstream` を root repository に向ける
- `papers/**/*.pdf` と `papers/**/*.png` は Git LFS で管理
- root repository の `papers/` は空（`.gitkeep` のみ）。論文は各 fork だけで管理する
- デーモンの自動 push は `papers/` と `gallery.md` だけが対象。コード変更は含まれない

## 環境変数

| 変数 | デフォルト | 説明 |
|---|---|---|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama エンドポイント |
| `OLLAMA_MODEL` | `minimax-m3:cloud` | 翻訳・要約モデル |
| `PAPER_LIBRARY_AUTO_PUSH` | `1` | `0` で自動 commit/push を無効化 |
| `PAPER_LIBRARY_GIT_REMOTE` | `origin` | push 先 remote |
| `PAPER_LIBRARY_GIT_BRANCH` | 現在のブランチ | push 先ブランチ（detached HEAD 時は指定必須） |

その他のチューニング変数（`S2_*` / `FIGURE_*` / `SUMMARY_MAX_CHARS` など）は `scripts/com.taisei.translate-papers.plist` の `EnvironmentVariables` で設定できる。

## 要件

```
arq, pdf2zh (uv tool), watchexec, ollama, fzf, poppler, uv, git-lfs, jq  # brew / uv
python3, sips  # macOS 標準
Obsidian + Dataview プラグイン
```
