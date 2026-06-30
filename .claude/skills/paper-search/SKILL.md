---
name: paper-search
description: "ローカルに保存されたarXiv論文を検索・一覧表示・閲覧する。論文を探したい・一覧を見たい・特定論文の情報を確認したいときに使う。MANDATORY TRIGGERS: 論文を検索, 論文一覧, 論文を探す, arq search, arq list, arq show, paper-search。"
---

# paper-search

ローカルの論文ライブラリを検索・閲覧する。

## 一覧表示

```bash
arq list              # 全論文を一覧表示
arq list --json       # JSON形式
arq list --tsv        # TSV形式（ID\tTitle\tAuthor\tDate\tKeywords）
```

## 検索

```bash
arq search "<keyword>"                    # タイトル・abstract・summaryを横断検索
arq search "<kw1>" "<kw2>"               # AND検索
arq search --field title "<keyword>"      # タイトルのみ
arq search --field summary "<keyword>"    # 要約のみ
arq search --json "<keyword>"             # JSON出力
arq search --id "<keyword>"              # IDのみ出力（パイプ用）
```

## 個別論文の確認

```bash
arq show <query>               # メタ情報＋要約をターミナルで表示
arq show --summary <query>     # 要約のみ
arq show --json <query>        # JSON形式

arq path <query>               # 実体ディレクトリのパスを返す
arq has <id>                   # 取得済みか確認（0: あり、1: なし）
```

`<query>` はID・ID部分一致・タイトル部分一致のいずれでも可。

## ブラウザで閲覧

```bash
arq view               # ライブラリ全体をブラウザで開く
arq view <query>       # 特定論文に直接ジャンプ
```

ブラウザビューアのキーボードショートカット：

| キー | 操作 |
|------|------|
| `j` / `k` | 論文リストを移動 |
| `l` | 英語PDF ↔ 日本語PDF 切り替え |
| `n` | ノートパネル表示/非表示 |
| `f` | フルスクリーン |
| `t` | ダーク/ライトモード切替 |

## 組み合わせ例

```bash
# 検索結果をブラウザで開く
arq view "$(arq search --id 'diffusion model' | head -1)"

# 検索結果の要約をまとめて表示
arq search --id "transformer" | xargs -I{} arq show --summary {}
```
