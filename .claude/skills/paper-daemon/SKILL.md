---
name: paper-daemon
description: "paper-translateのlaunchdデーモンを管理する（起動・停止・状態確認・ログ確認）。デーモンの状態を確認したい、起動・再起動したい、ログを見たいときに使う。MANDATORY TRIGGERS: デーモン, daemon, launchd, translate-papers, 自動翻訳を起動, 自動処理, paper-daemon。"
---

# paper-daemon

watchexec + launchd で動く翻訳・要約デーモンを管理する。

## プロジェクトパス

```
~/projects/ubbs/paper-translate/scripts/install_agent.sh
~/projects/ubbs/paper-translate/.logs/
```

## 基本操作

```bash
INSTALL=~/projects/ubbs/paper-translate/scripts/install_agent.sh

$INSTALL status      # 状態確認
$INSTALL install     # launchdに登録して起動
$INSTALL uninstall   # launchdから削除して停止
```

再起動したい場合：

```bash
$INSTALL uninstall && $INSTALL install
```

## ログ確認

```bash
# リアルタイム監視
tail -f ~/projects/ubbs/paper-translate/.logs/translate-papers.log

# launchd標準出力ログ
tail -f ~/projects/ubbs/paper-translate/.logs/launchd.stdout.log
tail -f ~/projects/ubbs/paper-translate/.logs/launchd.stderr.log
```

## 前提条件の確認

デーモンが正常動作するには以下が必要：

```bash
ollama signin          # minimax-m3:cloud の認証（期限切れ時、要約用）
ollama ps              # Ollamaが起動しているか確認
which watchexec        # watchexec がインストールされているか確認
~/projects/ubbs/paper-translate/.venv/bin/python -c "import docling, litellm, bs4"  # 翻訳依存が入っているか確認
echo "$OPENAI_API_KEY $GEMINI_API_KEY"  # 翻訳には少なくとも一方が必要（.env.local）
```

## トラブルシューティング

- **デーモンが起動しない**: `launchd.stderr.log` でエラーを確認
- **要約が止まる**: `ollama signin` の期限切れを疑う。再サインインして再起動
- **翻訳が止まる**: OpenAI/Gemini のレート制限・クォータ切れを疑う。`.translate/translate.log` を確認。
  チャンクはキャッシュされるため次回実行時に失敗分だけ再試行される。3回連続失敗すると `<paper_dir>/.translate/failed` が
  作られスキップされる（削除するか `translate-paper.sh <dir> --force` で再試行）
- **コミットが止まる**: remote との分岐を確認（`git status`, `git fetch origin`）
- **ログが増えない**: `watchexec` が `~/papers/` を監視しているか `$INSTALL status` で確認
