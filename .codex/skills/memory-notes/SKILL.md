---
name: memory-notes
description: 会話の要点・意図・判断を Markdown に保存し、検索して要約を返す外部記憶スキル。ユーザーが「記憶して」「覚えておいて」「中断前にまとめて」など保存指示を出すとき、または「○○について思い出して」「前回のメモを探して」など再開指示を出すときに使う。必要に応じて /Users/mgos0p/.codex/memory を GitHub リポジトリ化して commit/push する作業にも使う。
---

# Memory Notes

## Overview
外部記憶として要点を Markdown に保存し、検索結果を要約して再開を助ける。意図と判断を最優先で残す。

## Quick Start
1. 保存は `scripts/save_memory.py` を使う。
2. 検索は `scripts/recall_memory.py` を使う。
3. GitHub 連携は `scripts/publish_github.py` を使う。

## 保存
1. 会話から保存すべき要点を抽出する。
2. Intent と Decisions を最優先で書く。必要に応じて Context と Next を補う。
3. 他に残すべき判断材料があれば、Risks や Constraints などの追加セクションを判断して付ける。
4. 不明点が致命的なら 1 問だけ確認する。不要なら即保存する。
5. `scripts/save_memory.py` で保存する。

保存フォーマットはスクリプトで自動生成される。内容は短く、再開時に使える粒度にまとめる。

保存例:
```bash
python3 scripts/save_memory.py \
  --title "検索機能の設計方針" \
  --intent "ユーザーが意図と判断を素早く再開できる外部記憶を作る" \
  --decisions "1記憶=1ファイル、Intent/Decisionsを最優先" \
  --context "保存先は /Users/mgos0p/.codex/memory" \
  --next "recall のスコアリングを単純化して実装する" \
  --tags "memory,skill"
```

## 再開
1. `scripts/recall_memory.py` で候補を検索する。
2. 上位 1 件を開いて要約する。Intent/Decisions/Next を中心に短く書く。
3. 要約の末尾に参照したファイルパスを添える。
4. 該当なしなら、ユーザーに検索語の再指定を促す。

検索例:
```bash
python3 scripts/recall_memory.py --query "検索機能の設計"
```

## GitHub 連携
1. ユーザーが GitHub への保存を求めたら `scripts/publish_github.py` を使う。
2. `gh auth status` で未認証なら認証を促す。
3. 既存リポジトリに接続するなら `--remote-url` を使う。
4. 失敗した場合は理由と次の手を短く返す。

公開例:
```bash
python3 scripts/publish_github.py --repo memory-notes --visibility private
```

## Notes
- デフォルトの保存先は `/Users/mgos0p/.codex/memory`。変更する場合は各スクリプトの `--dir` を使う。
- 検索スコアは単純なキーワード一致。精度が低い場合は検索語を具体化する。
