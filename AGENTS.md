# リポジトリルール

## 目的

arq で取得した arXiv 論文を pdf2zh + Ollama で日本語 PDF 化するための基盤。
スクリプト・設定・launchd agent のみを管理する。論文本体は `papers/` に置くが git 管理外。

## ディレクトリ構成

```
scripts/
  translate-papers-daemon.sh   # papers/ を走査し翻訳・要約・引用・図・ノート・by-title を統合実行
  translate-papers-watch.sh    # watchexec ラッパー
  summarize-paper.sh           # 単一論文の日本語要約を Ollama で生成
  fetch-references.sh          # Semantic Scholar から引用・被引用を取得 → references.json
  extract-figures.sh           # 図クロップ(PyMuPDF)＋概要図選定＋arq thumbnail 登録
  extract_figures.py           # PyMuPDF で Figure N をクロップ・キャプションスコア（.venv で実行）
  generate-obsidian-note.sh    # 各論文 dir に <snake(title)>.md を生成（引用 wikilink 付き）
  update-by-title.sh           # by-title symlink ツリーの再構築（snake_case 名）
  arq-select.sh                # fzf セレクタ
  arq-preview.sh               # fzf プレビュー（summary.md を表示）
  setup.sh                     # 初回設定
  install_agent.sh             # launchd agent の install/uninstall/status
  com.taisei.translate-papers.plist  # launchd agent 定義
papers/
  arxiv.org/<cat>/<id>/        # arq の実体（構造ハードコード・リネーム禁止）
    references.json            # 引用・被引用（自前ファイル。meta.json には書かない）
    figures/fig-NN.png figures.json  # Figure N ごとのクロップ＋メタ
    overview.png thumbnail.png # 選定した概要図＋arq サムネイル（overview の複製）
    <snake(title)>.md          # Obsidian ノート（生成物・git 管理外）
  by-title/<snake(title)>/      # 実体への相対 symlink（人間用の別名・snake_case）
gallery.md                     # ルート直下の Dataview ギャラリー（追跡）
.obsidian/snippets/paper-gallery.css  # ギャラリー CSS（追跡）, app.json で by-title を除外
.logs/                         # デーモン・launchd のログ（git 管理外）
```

## 翻訳・要約・引用・図

- 本文 PDF 翻訳は `pdf2zh` + `OLLAMA_MODEL=minimax-m3:cloud` → `paper_ja.pdf`。
- 要約は `summarize-paper.sh`（pdftotext → Ollama）→ `summary.md`（arq view が読む名前）。
- 引用は `fetch-references.sh`（Semantic Scholar Graph API）→ `references.json`。429 が出やすいので指数バックオフ必須。
- 図は `extract-figures.sh`（PyMuPDF）が「Figure N」キャプションごとにクロップ → `figures/fig-NN.png`。
  キャプションのキーワードで最高スコアの図を `overview.png` にして `arq thumbnail set` で登録（thumbnail は複製）。
  PyMuPDF は `.venv` に導入（`setup.sh` が自動）。図が無い PDF はページ描画にフォールバック。
- arq 自体の title/abstract LLM 翻訳・summarize は無効（Ollama 非対応のため）。
- minimax-m3:cloud は Ollama クラウド実行のため `ollama signin` が必須。

## 制約

- arq は `papers/arxiv.org/<cat>/<id>/` を直接探す。**この実体ディレクトリをリネームしない**こと。英語名アクセスは `by-title/` の symlink で提供する。
- **meta.json は arq 所有**（keywords/translate/thumbnail で書き換える）。引用データは meta.json に書かず `references.json` に保存する。サムネイルは `arq thumbnail set` 経由で登録する。
- **Obsidian の vault ルートはリポジトリルート**。ノートは各論文 dir に `<snake(title)>.md` で置き、引用は `[[<snake>|<title>]]`（ノート basename）で解決する。ファイル名・by-title は小文字 snake_case に統一。ノート/ギャラリーは保有論文集合に依存するためデーモンが毎回再生成する。

## Git 操作

- スクリプト・設定・`gallery.md`・`.obsidian/snippets`・`.obsidian/*.json`（plugins/ と workspace 除く）のみ commit する。
- `papers/`（ノート・生成図・サムネイル含む）、`.logs/` は commit しない。
- commit / push はユーザーから明示的に指示された場合のみ実行する。
