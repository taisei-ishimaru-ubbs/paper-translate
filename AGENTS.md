# リポジトリルール

## 目的

arq で取得した arXiv 論文と手動取得PDFを、LaTeXソース(e-print)→pandoc（無ければ arXiv HTML/PDF→Docling）→ LiteLLM 翻訳で
日本語 Markdown 化し、Ollama で要約するための基盤。
`uchidalab/paper-translate` の fork として、スクリプト・設定・launchd agent・論文ライブラリを管理する。
論文本体と生成画像は `papers/` に置いて git 管理し、PDF/PNG は Git LFS で追跡する。

## ディレクトリ構成

```
scripts/
  translate-papers-daemon.sh   # papers/ を走査し翻訳・要約・引用・図・ノート・by-title を統合実行
  translate-papers-watch.sh    # watchexec ラッパー
  commit-paper-library.sh      # 論文ライブラリだけを安全に自動 commit/push
  translate-paper.sh           # 1論文分の翻訳オーケストレータ（fetch→convert→translate→render、各段冪等）
  fetch-paper-source.sh        # e-print(LaTeX) → arxiv.org/html → ar5iv の順で取得。tarball展開または画像ローカル化
  convert_tex_to_markdown.py   # LaTeXソース → pandoc → $...$数式付き英語MD + bibs.json（主経路、.venv）
  localize_html_images.py      # HTML内<img>をダウンロードしローカル相対パスに書換（.venv）
  convert_to_markdown.py       # HTML/PDF → Docling → 引用マーカー付き英語MD + bibs.json（フォールバック、.venv）
  translate_markdown.py        # 英語MD → LiteLLM(openai→gemini) → 日本語MD（チャンク永続化・再開可、.venv）
  link_citations.py            # 引用マーカーをwikilink/ブロック参照に描画（冪等、.venv）
  import-paper.sh              # 手動PDFをメタデータ付きでpapers/manualへ取り込む
  import-inbox.sh              # inbox内のPDFを一括取り込み
  paper-metadata.sh            # meta.json / metadata.json の共通読取
  semantic-scholar.sh          # Semantic Scholar API・再試行の共通処理
  summarize-paper.sh           # 単一論文の日本語要約を Ollama で生成
  fetch-references.sh          # Semantic Scholar から引用・被引用を取得 → references.json
  extract-figures.sh           # 図クロップ(PyMuPDF)＋概要図選定＋arq thumbnail 登録
  extract_figures.py           # PyMuPDF で Figure N をクロップ・キャプションスコア（.venv で実行）
  generate-obsidian-note.sh    # 各論文 dir に <snake(title)>.md を生成（引用 wikilink・日本語MDリンク付き）
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
    <snake(title)>.md          # Obsidian ノート（生成物・追跡）
    <snake(title)>_ja.md       # 翻訳全文Markdown（生成物・追跡。tags:[paper-translation]でgallery除外）
    assets/figNN.png           # 翻訳MD用に抽出した図版（生成物・追跡、LFS）
    .translate/                # 翻訳パイプラインの中間状態（詳細は下記）
  manual/<title>_<hash>/       # 手動取得論文（metadata.json + 同じ生成物）
  by-title/<snake(title)>/      # 実体への相対 symlink（人間用の別名・snake_case）
inbox/                         # 手動PDF drop folder（git管理外）
gallery.md                     # ルート直下の Dataview ギャラリー（追跡）
.obsidian/snippets/paper-gallery.css  # ギャラリー CSS（追跡）, app.json で by-title を除外
.logs/                         # デーモン・launchd のログ（git管理外）
```

### `<paper_dir>/.translate/`（翻訳パイプラインの中間状態）

```
paper_en.md       # pandoc/Docling変換直後の英語Markdown（{{CITE:N}}/{{BIBSTART:N}}マーカー付き。追跡）
paper_ja_raw.md   # 翻訳済みMarkdown（マーカーは未解決のまま保持。追跡）
bibs.json         # 参考文献リストから抽出した{N: {raw, arxiv_id, doi}}（追跡）
state.json        # 取得元の判定結果 {source: latex|arxiv_html|ar5iv|pdf_only, url, checked_at}（git管理外・再判定不要のキャッシュ）
source-tex/       # 展開したe-print(LaTeXソース)一式（git管理外・再取得すれば復元可能）
source/           # 取得したHTML原文＋ローカル化画像（git管理外・再取得すれば復元可能）
chunks/NNN.json   # 翻訳チャンクごとのキャッシュ（ハッシュ照合で再開・再翻訳を判定、git管理外）
failed            # 同一ステージがTRANSLATE_MAX_FAILURES回失敗した印（git管理外。削除か--forceで再試行）
```

## 翻訳・要約・引用・図

- 本文翻訳は `translate-paper.sh` が統括する4段パイプライン fetch→convert→translate→render（各段は出力ファイルの有無で判定する冪等ステップ。convert は `state.source` で tex/HTML 経路に分岐）:
  1. `fetch-paper-source.sh`: arXiv IDがあれば **`arxiv.org/e-print/<id>`（LaTeXソース）を最優先**で取り、tarball を `.translate/source-tex/`
     へ展開して main tex（`\documentclass`＋`\begin{document}`）と番号付き参考文献（`.bbl` か inline `thebibliography`）が揃えば `latex` を採用する。
     使えなければ `arxiv.org/html/<id>` → `ar5iv.labs.arxiv.org/html/<id>`（`class="ltx_document"` で判定）→ `pdf_only` の順にフォールバックする。
     判定結果は `.translate/state.json` にキャッシュされ、`--force` を付けない限り再判定しない。HTML採用時は画像もローカル化する（`localize_html_images.py`）。
     `PAPER_FETCH_NO_TEX=1` で e-print を飛ばして HTML/PDF 経路を強制でき、次段の tex 変換失敗時のフォールバックに使う。
  2. **変換（`state.source` で分岐）**:
     - `source==latex` → `convert_tex_to_markdown.py`（主経路）: main tex を平坦化し、`\cite` を `.bbl` の `\bibitem` 出現順（unsrt=引用順）で採番して
       `{{CITE:N}}` に置換、figure 環境は `\includegraphics` を PyMuPDF/コピーで `<dir>/assets/figNN.png` 化し画像マーカー＋caption 段落に事前置換
       （caption 内数式を保つため）、`pandoc -f latex -t markdown` で **数式を素の `$...$`/`$$...$$`** に保って変換する。参考文献は `.bbl` から `{{BIBSTART:N}}`
       付きで自前生成。pandoc 失敗・本文が短すぎる等なら exit≠0 で `translate-paper.sh` が HTML/PDF 経路へフォールバックする。
     - それ以外 → `convert_to_markdown.py`（フォールバック）: Docling で HTML/PDF を Markdown 化。HTML経由は `<math alttext>` を LaTeX へ事前置換し、
       番号付き数式の `<table class="ltx_equation">` は丸ごと `$$...$$` 段落へ置換（テーブル化に伴う `|`/`<` のエンティティ破壊を回避）、残存エンティティも
       export 後に復元する。`escape_underscores=False` で出力。図は `PictureItem` から `assets/figNN.png` に保存。引用は `[label](#bib.bibN)` リンク→`{{CITE:N}}`、
       無ければブラケット数字を参考文献と突合して `{{CITE:N}}`。各参考文献に `{{BIBSTART:N}}` を付与し生テキスト・arXiv ID・DOI を `.translate/bibs.json` に保存。
  3. `translate_markdown.py`: 見出し境界でチャンク分割（上限12000字）し、参考文献セクションは翻訳せず英語のまま素通し。
     LiteLLM経由で`TRANSLATE_MODEL`（既定`openai/gpt-5.6-terra`）→`TRANSLATE_FALLBACK_MODEL`（既定`gemini/gemini-3.1-flash-lite`）の
     順にフォールバック。`{{CITE:N}}`/`{{BIBSTART:N}}`マーカー・画像参照・LaTeX・コードフェンスの保持をチャンクごとに検証し、
     壊れていれば1回リトライ、それでも失敗したチャンクは英語原文のまま採用してWARNログを出す。チャンクは`.translate/chunks/`に
     ハッシュ付きでキャッシュされ、中断・再実行時は完了分を再送信しない。**1チャンクでも失敗すると`paper_ja_raw.md`は書き出さず**、
     次回デーモン実行時に失敗分だけ再試行させる。
     OpenAI呼び出し前にOrganization Usage APIのUTC当日実績とrepo-local予約量を確認し、いずれかが
     `OPENAI_DAILY_TOKEN_LIMIT`（既定240万）を超える場合、またはUsage APIを読めない場合はOpenAIを送信せずGeminiへ切り替える。
     状態は既定で`~/.local/state/ubbs/paper-translate-openai-quota.json`に保存する。
  4. `link_citations.py`: `paper_ja_raw.md`のマーカーを、`bibs.json`＋この論文の`references.json`＋ライブラリ全体の識別子→slugマップ
     （`LOCAL_MAP_FILE`）を突き合わせてローカル論文の`[[slug|N]]`に、無ければ同一ファイル内`[[#^ref-N|N]]`ブロック参照に描画し、
     `<dir>/<snake(title)>_ja.md`を生成する。raw を書き換えないため何度でも再描画でき、新規論文追加時にデーモンが全論文を再描画すると
     外部参照がローカルwikilinkへ昇格する（ノート再生成と同じ仕組み）。
  - 同一ステージが`TRANSLATE_MAX_FAILURES`（既定3）回連続で失敗すると`.translate/failed`を置き、それ以降は`--force`を付けるまでスキップする。
  - **既存論文はバックフィルしない**: `paper_ja.pdf`（旧pdf2zh成果物）または`<snake(title)>_ja.md`が既にあればこの4段全体をスキップする。
  - `OPENAI_API_KEY`/`GEMINI_API_KEY`は少なくとも一方が必要。Usage API用の`OPENAI_ADMIN_API_KEY`は
    `api.usage.read`権限だけを持たせる。すべて git 管理外の `.env.local`（`.env.local.example` を参照）に置き、daemon が起動時に読み込む。
  - Docling・LiteLLM・BeautifulSoup4・PyMuPDF は `.venv`（`setup.sh`が導入）で実行する。Doclingは torch を含み初回インストールが重い。
    LaTeX主経路の変換には `pandoc` が別途必要（`brew install pandoc`）。無い場合 tex 変換は失敗し HTML/PDF 経路へフォールバックする。
- 要約は `summarize-paper.sh`（pdftotext → Ollama）→ `summary.md`（arq view が読む名前）。
- 引用は `fetch-references.sh`（Semantic Scholar Graph API）→ `references.json`。429 が出やすいので指数バックオフ必須。
- 図は `extract-figures.sh`（PyMuPDF）が「Figure N」キャプションごとにクロップ → `figures/fig-NN.png`。
  キャプションのキーワードで最高スコアの図を `overview.png` にして `arq thumbnail set` で登録（thumbnail は複製）。
  PyMuPDF は `.venv` に導入（`setup.sh` が自動）。図が無い PDF はページ描画にフォールバック。
- arq 自体の title/abstract LLM 翻訳・summarize は無効（Ollama 非対応のため）。
- 手動PDFは `import-paper.sh` または `inbox/` から取り込む。外部IDが無い場合はPDFからメタデータを推定し、Semantic Scholarの正規化タイトルが完全一致したときだけ引用を紐付ける。
- minimax-m3:cloud は Ollama クラウド実行のため `ollama signin` が必須。
- デーモンは処理完了後、`papers/` と `gallery.md` の変更だけを commit し、現在のブランチを `origin` へ push する。
  remote の先行・分岐や、論文ライブラリ以外を含む未pushコミットを検出した場合は停止する。
- root repository (`uchidalab/paper-translate`) では論文ライブラリのcommitを拒否する。自動commit/pushはfork専用とする。

## 制約

- arq は `papers/arxiv.org/<cat>/<id>/` を直接探す。**この実体ディレクトリをリネームしない**こと。英語名アクセスは `by-title/` の symlink で提供する。
- **meta.json は arq 所有**（keywords/translate/thumbnail で書き換える）。引用データは meta.json に書かず `references.json` に保存する。サムネイルは `arq thumbnail set` 経由で登録する。
- 手動論文は `papers/manual/` に置き、メタデータは `metadata.json` に保存する。手動論文へ `meta.json` を作らない。
- **Obsidian の vault ルートはリポジトリルート**。ノートは各論文 dir に `<snake(title)>.md` で置き、引用は `[[<snake>|<title>]]`（ノート basename）で解決する。ファイル名・by-title は小文字 snake_case に統一。ノート/ギャラリーは保有論文集合に依存するためデーモンが毎回再生成する。

## Git・remote 操作

- 公開 root repository は `uchidalab/paper-translate`。fork checkout では `origin` を自分の fork、`upstream` を root repository とする。
- スクリプト・設定・ドキュメントの変更は root repository の `main` で行い、fork は `upstream/main` をmergeして取り込む。fork固有の論文データをmerge時に削除しない。
- root repository の `papers/` は `.gitkeep` だけを保持し、論文本体・翻訳・生成物をcommitしない。`.lfs-seed` はpublic forkのLFS初期化専用で、論文データを含めない。
- forkではスクリプト・設定・`gallery.md`・`.obsidian` の共有設定に加え、`papers/` の原文・翻訳・要約・引用・図・ノート・symlink をcommit対象とする。
- `papers/**/*.pdf` と `papers/**/*.png` は Git LFS で追跡する。
- `.logs/`、`.venv/`、Obsidian のローカル状態、pdf2zh の `*-dual.pdf` / `*-mono.pdf`（レガシー中間生成物）、
  `.translate/{source,chunks,state.json,failed,.failcount-*,translate.log}`（翻訳パイプラインの再生成可能な中間状態）は commit しない。
- デーモンによる `papers/` と `gallery.md` の自動 commit/push は常時許可する。それ以外の commit/push、root repository への手動 push はユーザーから明示的に指示された場合のみ実行する。
