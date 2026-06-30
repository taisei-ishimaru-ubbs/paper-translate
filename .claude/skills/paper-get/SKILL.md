---
name: paper-get
description: "arXiv論文をarqで取得し、翻訳・要約パイプラインを確認する。論文を取得したい・追加したい・arq get を実行したいときに使う。MANDATORY TRIGGERS: 論文を取得, arq get, arXiv IDを渡す, 論文を追加, 論文をダウンロード。"
---

# paper-get

arXiv論文を取得して翻訳パイプラインに乗せる。

## プロジェクトパス

```
~/projects/ubbs/paper-translate/
```

## 手順

### 1. 論文を取得する

```bash
arq get <arxiv_id>
# 例: arq get 2303.12345
# 例: arq get https://arxiv.org/abs/2303.12345
# 複数同時: arq get 2303.12345 2401.67890
```

取得後、`~/papers/arxiv.org/<category>/<id>/` に `paper.pdf` と `meta.json` が置かれる。

### 2. デーモンの状態を確認する

```bash
~/projects/ubbs/paper-translate/scripts/install_agent.sh status
```

デーモンが動いていれば `paper.pdf` の追加を自動検知して翻訳・要約・図・ノートを処理する。
デーモンが停止していれば、手動処理が必要（→ `/paper-process` スキルを使う）。

### 3. ログで進捗を確認する（任意）

```bash
tail -f ~/projects/ubbs/paper-translate/.logs/translate-papers.log
```

## よくあるケース

- **複数IDをまとめて取得**: `arq get id1 id2 id3`
- **再取得（上書き）**: `arq get --force <id>`
- **取得済みか確認**: `arq has <id>`
- **デーモンが動いていない場合**: `/paper-daemon` スキルで起動するか `/paper-process` で手動処理
