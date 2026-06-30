# Obsidian セットアップ

このリポジトリのルートをそのまま Obsidian の vault として開ける。論文ノート・引用リンク・カードギャラリーが利用できる。

## 初回セットアップ

1. Obsidian で `/Users/ishimarutaisei/projects/ubbs/paper-translate` を vault として開く。
2. コミュニティプラグイン `Dataview` をインストールして有効化。
3. Dataview 設定で `Enable JavaScript Queries` を ON。
4. `Settings > Appearance > CSS snippets` で `paper-gallery` を有効化。
5. ルート直下の `gallery.md` を開く。

## 構成

- `papers/arxiv.org/<cat>/<id>/<snake(title)>.md` または `papers/manual/<title>_<hash>/<snake(title)>.md` — 論文ごとのノート（`scripts/generate-obsidian-note.sh` が生成、論文と同じ場所に保存）。
  - ファイル名は小文字 snake_case のタイトル（例 `attention_is_all_you_need.md`）。
  - frontmatter（id/title/authors/category/published/thumbnail/tags）
  - 概要図サムネイルと `summary.md` の埋め込み
  - `## 参考文献` / `## 被引用`：ローカル保有論文へは `[[<snake>|<title>]]` wikilink、未保有は arXiv・DOI・Semantic Scholar リンク
- `gallery.md`（ルート直下） — `#paper` タグのノートをカード表示する Dataview JS ギャラリー（検索付き）。
- グラフビューで引用 wikilink による論文間の繋がりを俯瞰できる。

## 除外設定

`.obsidian/app.json` の `userIgnoreFilters` で以下を除外済み（二重インデックス回避）:

- `papers/by-title/`（実体への symlink）
- `inbox/`、`.logs/`、`scratchpad/`

## 注意

- ノート本体（`papers/` 配下の `<snake(title)>.md`）は生成物だが、論文ライブラリの一部として git 管理する。
  `scripts/translate-papers-daemon.sh` または `scripts/generate-obsidian-note.sh` で再生成する。
- `.obsidian/plugins/` と `workspace*.json` は git 管理外（環境依存）。`snippets/paper-gallery.css` と
  `app.json` は追跡する。
- ノートのリンクはローカル保有論文の集合に依存するため、論文を追加したらデーモンが全ノートを再生成する。
