# 指摘データ形式

保存ファイルは JSON Lines 形式の `feedback.jsonl`。
1行=1件の指摘。

## フィールド

| key | type | required | 説明 |
| --- | --- | --- | --- |
| id | string | yes | 一意ID（UUID） |
| type | string | yes | pr-review / design-review / incident-retro / other |
| date | string | yes | 対象日付（YYYY-MM-DD） |
| created_at | string | yes | 追加日時（ISO 8601, timezone付き） |
| title | string | no | 短いタイトル |
| content | string | yes | 指摘の本文 |
| summary | string | no | 要約 |
| author | string | no | 指摘者 |
| project | string | no | プロジェクト/リポジトリ名 |
| source | string | no | 参照元（PR番号、チケットID、URLなど） |
| severity | string | no | low / medium / high |
| tags | string[] | no | タグ（小文字推奨） |

## 例

```json
{"id":"1b4f2e36-7f2a-4f5f-8e45-2b5b5c5b5c5b","type":"pr-review","date":"2026-02-04","created_at":"2026-02-04T10:23:45-08:00","title":"useEffect 依存配列","content":"useEffect の依存配列が空で、props 変更が反映されない。依存配列に props.userId を追加する。","summary":"useEffect 依存配列に userId を追加","author":"Aki","project":"frontend-web","source":"PR #128","severity":"medium","tags":["react","useeffect","hooks"]}
```

## タグ指針

- 2〜5個を目安に付与する。
- 技術名や対象領域を優先する。
- 複数語はハイフンでつなぐ（例: `error-handling`）。
