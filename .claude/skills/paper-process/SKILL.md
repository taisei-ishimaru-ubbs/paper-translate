---
name: paper-process
description: "取得済みのarXiv論文を手動で処理する（翻訳・要約・図抽出・Obsidianノート生成）。デーモンが止まっていて処理されていないとき、特定論文だけ再処理したいとき、個別ステップを実行したいときに使う。MANDATORY TRIGGERS: 論文を翻訳, 論文を要約, 図を抽出, ノートを生成, 手動処理, 再処理, paper-process。"
---

# paper-process

取得済み論文を手動でパイプライン処理する。

## プロジェクトパス

```
SCRIPTS=~/projects/ubbs/paper-translate/scripts/
PAPERS=~/papers/arxiv.org/<category>/<id>/
```

## 論文ディレクトリの特定

```bash
arq path <query>   # IDまたはタイトル部分一致で実体パスを返す
# 例: arq path 2303.12345
# 例: arq path "attention is all"
```

## 処理ステップ

### 全ステップをまとめて実行（未処理分）

```bash
~/projects/ubbs/paper-translate/scripts/translate-papers-daemon.sh
```

`papers/` を走査し、未処理の論文をすべて順に処理する。

### 個別ステップ

各スクリプトは `<paper_dir>` を引数に取る。`--force` で再処理。

```bash
PAPER_DIR=$(arq path <query>)

# 1. 翻訳 (paper.pdf → paper_ja.pdf)
pdf2zh "$PAPER_DIR/paper.pdf" --output "$PAPER_DIR"

# 2. 日本語要約 (→ summary.md)
~/projects/ubbs/paper-translate/scripts/summarize-paper.sh "$PAPER_DIR"
~/projects/ubbs/paper-translate/scripts/summarize-paper.sh --force "$PAPER_DIR"

# 3. 引用・被引用取得 (→ references.json)
~/projects/ubbs/paper-translate/scripts/fetch-references.sh "$PAPER_DIR"

# 4. 図クロップ＋概要図 (→ figures/, overview.png)
~/projects/ubbs/paper-translate/scripts/extract-figures.sh "$PAPER_DIR"

# 5. Obsidianノート生成 (→ <snake_title>.md)
~/projects/ubbs/paper-translate/scripts/generate-obsidian-note.sh "$PAPER_DIR"

# 6. by-title symlinkの再構築
~/projects/ubbs/paper-translate/scripts/update-by-title.sh
```

## 処理済み確認

```bash
ls $(arq path <id>)
# paper.pdf, paper_ja.pdf, summary.md, references.json, overview.png, figures/ があれば完了
```

## 概要図の手動指定

自動選定が外れた場合は図番号ファイルを置いて再実行：

```bash
echo "2" > "$(arq path <id>)/.overview-figure"
~/projects/ubbs/paper-translate/scripts/extract-figures.sh --force "$(arq path <id>)"
```
