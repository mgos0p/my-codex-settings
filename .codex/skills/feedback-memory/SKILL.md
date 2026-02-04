---
name: feedback-memory
description: PRレビュー指摘、設計レビュー、運用インシデントの振り返りを保存・検索・再利用するためのスキル。指摘の保存、過去指摘のキーワード/タグ/日付/指摘者検索、指摘一覧の出力が必要なときに使う。
---

# 指摘メモリ

## 目的
指摘を一貫した形式で保存し、再検索・再利用しやすくする。

## 既定の保存場所
- $CODEX_HOME/feedback-memory/feedback.jsonl
- $CODEX_HOME が未設定の場合は ~/.codex/feedback-memory/feedback.jsonl

## 追加
1. 依頼内容から必須情報を埋める。足りない場合は質問する。
2. `scripts/feedback_memory.py add` を使って保存する。
3. 保存後に要約と付与したタグを返す。

必須: type, content
推奨: date, author, tags, source, project, title

## 一括追加
1. 雑にコピペした指摘は `scripts/feedback_memory.py bulk` を使う。
2. 箇条書きは自動分割する（-/*/•/1.) など）。
3. `--raw` または `--file` を使う。stdin でも可。

## 検索
1. `scripts/feedback_memory.py query` を使う。
2. キーワード・タグ・日付範囲・指摘者・種類で絞り込む。
3. 結果が多い場合は `--limit` を使う。
4. 要約だけ返す場合は `--format summary` を使う（summary→title→content の短縮順に出力）。

## 形式
詳細スキーマと例は `references/format.md` を参照する。

## 注意
- 個人情報や機密をそのまま保存しない。必要なら伏字にする。
- タグは小文字・短い名詞で揃える。
