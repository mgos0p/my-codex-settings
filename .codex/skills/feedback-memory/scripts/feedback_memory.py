#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
import uuid
from datetime import date, datetime
from pathlib import Path

DEFAULT_SUBDIR = "feedback-memory"
DEFAULT_FILE = "feedback.jsonl"


def resolve_store_path(store_dir: str | None) -> Path:
    if store_dir:
        base = Path(store_dir)
    else:
        codex_home = os.environ.get("CODEX_HOME")
        if codex_home:
            base = Path(codex_home)
        else:
            base = Path.home() / ".codex"
        base = base / DEFAULT_SUBDIR
    return base / DEFAULT_FILE


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


def normalize_tags(values: list[str]) -> list[str]:
    seen = set()
    output = []
    for raw in values:
        for part in raw.split(","):
            tag = part.strip().lower()
            if not tag or tag in seen:
                continue
            seen.add(tag)
            output.append(tag)
    return output


def collect_tags(args: argparse.Namespace) -> list[str]:
    values: list[str] = []
    if args.tags:
        values.append(args.tags)
    if args.tag:
        values.extend(args.tag)
    return normalize_tags(values)


def shorten(text: str, max_len: int = 120) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "…"


BULLET_RE = re.compile(r"^\s*(?:[-*•・]|\d+[.)])\s+")


def read_raw_input(args: argparse.Namespace) -> str:
    if args.raw:
        return args.raw
    if args.file:
        return Path(args.file).read_text(encoding="utf-8")
    if not sys.stdin.isatty():
        return sys.stdin.read()
    return ""


def split_raw_items(raw: str) -> list[str]:
    lines = raw.splitlines()
    if not lines:
        return []
    use_bullets = any(BULLET_RE.match(line) for line in lines)
    items: list[str] = []
    current: list[str] = []

    def flush() -> None:
        nonlocal current
        if not current:
            return
        item = "\n".join(current).strip()
        if item:
            items.append(item)
        current = []

    if use_bullets:
        for line in lines:
            if not line.strip():
                flush()
                continue
            if BULLET_RE.match(line):
                flush()
                current.append(BULLET_RE.sub("", line).strip())
            else:
                current.append(line.strip())
        flush()
        return items

    for line in lines:
        if not line.strip():
            flush()
            continue
        current.append(line.strip())
    flush()
    return items


def extract_title(content: str) -> str:
    stripped = content.strip()
    if not stripped:
        return "untitled"
    first_line = stripped.splitlines()[0]
    return shorten(first_line, 60)


def entry_date(entry: dict) -> date | None:
    raw = entry.get("date")
    if isinstance(raw, str):
        try:
            return date.fromisoformat(raw)
        except ValueError:
            pass
    created_at = entry.get("created_at")
    if isinstance(created_at, str) and len(created_at) >= 10:
        try:
            return date.fromisoformat(created_at[:10])
        except ValueError:
            return None
    return None


def add_entry(args: argparse.Namespace) -> int:
    store_path = resolve_store_path(args.store_dir)
    ensure_parent(store_path)

    now = datetime.now().astimezone()
    tags = collect_tags(args)

    entry = {
        "id": str(uuid.uuid4()),
        "type": args.type,
        "date": (args.date or date.today().isoformat()),
        "created_at": now.isoformat(timespec="seconds"),
        "title": args.title,
        "content": args.content,
        "summary": args.summary,
        "author": args.author,
        "project": args.project,
        "source": args.source,
        "severity": args.severity,
        "tags": tags or None,
    }

    with store_path.open("a", encoding="utf-8") as f:
        json.dump(entry, f, ensure_ascii=False)
        f.write("\n")

    title = entry.get("title") or shorten(entry["content"], 60)
    print(f"OK {entry['id']} {entry['date']} [{entry['type']}] {title}")
    return 0


def bulk_add(args: argparse.Namespace) -> int:
    raw = read_raw_input(args)
    if not raw.strip():
        print("入力が空です")
        return 1

    items = split_raw_items(raw)
    if not items:
        print("入力が空です")
        return 1

    store_path = resolve_store_path(args.store_dir)
    ensure_parent(store_path)

    tags = collect_tags(args)

    with store_path.open("a", encoding="utf-8") as f:
        for item in items:
            now = datetime.now().astimezone()
            entry = {
                "id": str(uuid.uuid4()),
                "type": args.type,
                "date": (args.date or date.today().isoformat()),
                "created_at": now.isoformat(timespec="seconds"),
                "title": extract_title(item),
                "content": item,
                "summary": args.summary,
                "author": args.author,
                "project": args.project,
                "source": args.source,
                "severity": args.severity,
                "tags": tags or None,
            }
            json.dump(entry, f, ensure_ascii=False)
            f.write("\n")
            title = entry.get("title") or shorten(entry["content"], 60)
            print(f"OK {entry['id']} {entry['date']} [{entry['type']}] {title}")

    return 0


def matches_text(entry: dict, query: str) -> bool:
    if not query:
        return True
    q = query.lower()
    fields = [
        entry.get("title"),
        entry.get("content"),
        entry.get("summary"),
        entry.get("author"),
        entry.get("project"),
        entry.get("source"),
    ]
    tags = entry.get("tags") or []
    fields.extend(tags)
    haystack = "\n".join([str(v) for v in fields if v])
    return q in haystack.lower()


def matches_tags(entry: dict, required: list[str]) -> bool:
    if not required:
        return True
    entry_tags = [str(t).lower() for t in (entry.get("tags") or [])]
    return all(tag in entry_tags for tag in required)


def matches_value(entry: dict, key: str, expected: str | None) -> bool:
    if not expected:
        return True
    value = entry.get(key)
    if not value:
        return False
    return expected.lower() in str(value).lower()


def query_entries(args: argparse.Namespace) -> int:
    store_path = resolve_store_path(args.store_dir)
    if not store_path.exists():
        print("該当なし")
        return 0

    required_tags = collect_tags(args)
    date_from = parse_date(args.date_from) if args.date_from else None
    date_to = parse_date(args.date_to) if args.date_to else None

    entries: list[dict] = []
    with store_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            entries.append(entry)

    filtered: list[dict] = []
    for entry in entries:
        if args.type and entry.get("type") != args.type:
            continue
        if not matches_value(entry, "author", args.author):
            continue
        if not matches_value(entry, "project", args.project):
            continue
        if not matches_value(entry, "source", args.source):
            continue
        if args.severity and entry.get("severity") != args.severity:
            continue
        if not matches_tags(entry, required_tags):
            continue
        if not matches_text(entry, args.query or ""):
            continue
        d = entry_date(entry)
        if date_from and (not d or d < date_from):
            continue
        if date_to and (not d or d > date_to):
            continue
        filtered.append(entry)

    filtered.sort(key=lambda e: entry_date(e) or date.min, reverse=True)

    if args.limit is not None:
        filtered = filtered[: args.limit]

    if args.format == "json":
        print(json.dumps(filtered, ensure_ascii=False, indent=2))
        return 0

    if not filtered:
        print("該当なし")
        return 0

    if args.format == "text":
        for entry in filtered:
            title = entry.get("title") or shorten(entry.get("content", ""), 80)
            tags = ",".join(entry.get("tags") or [])
            print(
                f"{entry.get('date','')} [{entry.get('type','')}] {title}"
                f" | author={entry.get('author','')} tags={tags} source={entry.get('source','')}"
            )
        return 0

    if args.format == "summary":
        for entry in filtered:
            summary = (
                entry.get("summary")
                or entry.get("title")
                or shorten(entry.get("content", ""), 80)
            )
            tags = ", ".join(entry.get("tags") or [])
            parts = [
                f"{entry.get('date','')}",
                f"[{entry.get('type','')}]",
                summary,
            ]
            meta = []
            if entry.get("author"):
                meta.append(f"author: {entry['author']}")
            if tags:
                meta.append(f"tags: {tags}")
            if entry.get("source"):
                meta.append(f"source: {entry['source']}")
            if entry.get("project"):
                meta.append(f"project: {entry['project']}")
            meta_text = " / ".join(meta)
            if meta_text:
                parts.append(f"({meta_text})")
            print("- " + " ".join([p for p in parts if p]))
        return 0

    for entry in filtered:
        title = entry.get("title") or shorten(entry.get("content", ""), 80)
        tags = ", ".join(entry.get("tags") or [])
        parts = [
            f"{entry.get('date','')}",
            f"[{entry.get('type','')}]",
            title,
        ]
        meta = []
        if entry.get("author"):
            meta.append(f"author: {entry['author']}")
        if tags:
            meta.append(f"tags: {tags}")
        if entry.get("source"):
            meta.append(f"source: {entry['source']}")
        if entry.get("project"):
            meta.append(f"project: {entry['project']}")
        meta_text = " / ".join(meta)
        if meta_text:
            parts.append(f"({meta_text})")
        print("- " + " ".join([p for p in parts if p]))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Feedback memory utility")
    parser.add_argument("--store-dir", help="保存先ディレクトリを上書き")

    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="指摘を追加")
    add_parser.add_argument("--type", required=True, choices=["pr-review", "design-review", "incident-retro", "other"], help="pr-review/design-review/incident-retro/other")
    add_parser.add_argument("--date", help="YYYY-MM-DD")
    add_parser.add_argument("--title", help="短いタイトル")
    add_parser.add_argument("--content", required=True, help="指摘本文")
    add_parser.add_argument("--summary", help="要約")
    add_parser.add_argument("--author", help="指摘者")
    add_parser.add_argument("--project", help="プロジェクト名")
    add_parser.add_argument("--source", help="参照元")
    add_parser.add_argument("--severity", choices=["low", "medium", "high"], help="重要度")
    add_parser.add_argument("--tags", help="カンマ区切りタグ")
    add_parser.add_argument("--tag", action="append", help="タグ（複数回指定可）")

    bulk_parser = subparsers.add_parser("bulk", help="指摘を一括追加")
    bulk_parser.add_argument("--type", required=True, choices=["pr-review", "design-review", "incident-retro", "other"], help="pr-review/design-review/incident-retro/other")
    bulk_parser.add_argument("--date", help="YYYY-MM-DD")
    bulk_parser.add_argument("--author", help="指摘者")
    bulk_parser.add_argument("--project", help="プロジェクト名")
    bulk_parser.add_argument("--source", help="参照元")
    bulk_parser.add_argument("--severity", choices=["low", "medium", "high"], help="重要度")
    bulk_parser.add_argument("--summary", help="共通サマリー")
    bulk_parser.add_argument("--tags", help="カンマ区切りタグ")
    bulk_parser.add_argument("--tag", action="append", help="タグ（複数回指定可）")
    bulk_parser.add_argument("--raw", help="コピペしたテキスト")
    bulk_parser.add_argument("--file", help="テキストファイル")

    query_parser = subparsers.add_parser("query", help="指摘を検索")
    query_parser.add_argument("--query", help="キーワード")
    query_parser.add_argument("--type", choices=["pr-review", "design-review", "incident-retro", "other"], help="pr-review/design-review/incident-retro/other")
    query_parser.add_argument("--author", help="指摘者")
    query_parser.add_argument("--project", help="プロジェクト名")
    query_parser.add_argument("--source", help="参照元")
    query_parser.add_argument("--severity", choices=["low", "medium", "high"], help="重要度")
    query_parser.add_argument("--tags", help="カンマ区切りタグ")
    query_parser.add_argument("--tag", action="append", help="タグ（複数回指定可）")
    query_parser.add_argument("--from", dest="date_from", help="開始日 YYYY-MM-DD")
    query_parser.add_argument("--to", dest="date_to", help="終了日 YYYY-MM-DD")
    query_parser.add_argument("--limit", type=int, default=50, help="最大件数")
    query_parser.add_argument(
        "--format",
        choices=["md", "text", "summary", "json"],
        default="md",
        help="出力形式",
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "add":
        return add_entry(args)
    if args.command == "bulk":
        return bulk_add(args)
    if args.command == "query":
        return query_entries(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
