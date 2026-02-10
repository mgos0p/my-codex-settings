#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import re
from pathlib import Path
from typing import List, Optional

DEFAULT_DIR = "/Users/mgos0p/.codex/memory"
TIME_FORMAT = "%Y-%m-%d %H:%M"
FILENAME_TIME_FORMAT = "%Y%m%d-%H%M%S"


def slugify(text: str) -> str:
    slug = text.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    return slug


def pick_title(candidates: List[Optional[str]]) -> str:
    for item in candidates:
        if not item:
            continue
        line = item.strip().splitlines()[0].strip()
        if line:
            return line[:120]
    return "Memory Note"


def parse_tags(raw: str) -> List[str]:
    if not raw:
        return []
    return [tag.strip() for tag in raw.split(",") if tag.strip()]


def read_notes(notes: str, notes_file: Optional[str]) -> str:
    parts = []
    if notes:
        parts.append(notes.strip())
    if notes_file:
        path = Path(notes_file)
        if not path.exists():
            raise FileNotFoundError(f"notes file not found: {notes_file}")
        parts.append(path.read_text(encoding="utf-8").strip())
    return "\n\n".join([part for part in parts if part])


def build_content(
    title: str,
    timestamp: str,
    tags: List[str],
    source: str,
    intent: str,
    decisions: str,
    context: str,
    next_steps: str,
    notes: str,
) -> str:
    lines = [f"# {title}", "", f"- Date: {timestamp}"]
    if tags:
        lines.append(f"- Tags: {', '.join(tags)}")
    if source:
        lines.append(f"- Source: {source}")

    sections = [
        ("Intent", intent),
        ("Decisions", decisions),
        ("Context", context),
        ("Next", next_steps),
        ("Notes", notes),
    ]

    for name, value in sections:
        if value:
            lines.extend(["", f"## {name}", "", value.strip()])

    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Save a memory note as Markdown.")
    parser.add_argument("--dir", default=DEFAULT_DIR, help="Output directory")
    parser.add_argument("--title", help="Note title")
    parser.add_argument("--intent", default="", help="Intent section")
    parser.add_argument("--decisions", default="", help="Decisions section")
    parser.add_argument("--context", default="", help="Context section")
    parser.add_argument("--next", dest="next_steps", default="", help="Next section")
    parser.add_argument("--notes", default="", help="Additional notes")
    parser.add_argument("--notes-file", help="Path to additional notes file")
    parser.add_argument("--tags", default="", help="Comma-separated tags")
    parser.add_argument("--source", default="", help="Optional source string")
    parser.add_argument(
        "--timestamp",
        default="",
        help="Override timestamp (YYYY-MM-DD HH:MM)",
    )
    args = parser.parse_args()

    notes = read_notes(args.notes, args.notes_file)
    title = pick_title(
        [args.title, args.intent, args.decisions, args.context, args.next_steps, notes]
    )

    if not any([args.intent, args.decisions, args.context, args.next_steps, notes]):
        raise SystemExit("Nothing to save. Provide at least one section or notes.")

    now = dt.datetime.now()
    timestamp = args.timestamp.strip() if args.timestamp else now.strftime(TIME_FORMAT)
    filename_time = now.strftime(FILENAME_TIME_FORMAT)
    slug = slugify(title) or "memory-note"
    output_dir = Path(args.dir).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{filename_time}--{slug}.md"

    content = build_content(
        title=title,
        timestamp=timestamp,
        tags=parse_tags(args.tags),
        source=args.source.strip(),
        intent=args.intent,
        decisions=args.decisions,
        context=args.context,
        next_steps=args.next_steps,
        notes=notes,
    )

    path.write_text(content, encoding="utf-8")
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
