#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import List, Tuple

DEFAULT_DIR = "/Users/mgos0p/.codex/memory"
SNIPPET_LEN = 160


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def tokenize(query: str) -> List[str]:
    tokens = [token for token in re.split(r"\s+", query.lower()) if token]
    return tokens or [query.lower()]


def score_content(content: str, query: str, tokens: List[str]) -> int:
    lowered = content.lower()
    score = 0
    if query.lower() in lowered:
        score += 5
    for token in tokens:
        if token:
            score += lowered.count(token)
    return score


def extract_title(lines: List[str]) -> str:
    for line in lines:
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def extract_date(lines: List[str]) -> str:
    for line in lines:
        if line.startswith("- Date: "):
            return line[8:].strip()
    return ""


def collect_notes(dir_path: Path, query: str, limit: int) -> List[Tuple[int, Path, str, str, str]]:
    tokens = tokenize(query)
    results = []
    for path in sorted(dir_path.glob("*.md")):
        try:
            content = path.read_text(encoding="utf-8")
        except Exception:
            continue
        score = score_content(content, query, tokens)
        if score == 0:
            continue
        lines = content.splitlines()
        title = extract_title(lines)
        date = extract_date(lines)
        snippet = normalize(content)[:SNIPPET_LEN]
        results.append((score, path, title, date, snippet))
    results.sort(key=lambda item: (item[0], item[1].stat().st_mtime), reverse=True)
    return results[:limit]


def main() -> int:
    parser = argparse.ArgumentParser(description="Recall memory notes by keyword.")
    parser.add_argument("--dir", default=DEFAULT_DIR, help="Notes directory")
    parser.add_argument("--query", required=True, help="Search query")
    parser.add_argument("--limit", type=int, default=3, help="Max results")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    dir_path = Path(args.dir).expanduser()
    if not dir_path.exists():
        raise SystemExit(f"Directory not found: {dir_path}")

    results = collect_notes(dir_path, args.query, args.limit)

    if args.json:
        payload = [
            {
                "path": str(path),
                "score": score,
                "title": title,
                "date": date,
                "snippet": snippet,
            }
            for score, path, title, date, snippet in results
        ]
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0

    if not results:
        print("No matches")
        return 0

    for index, (score, path, title, date, snippet) in enumerate(results, start=1):
        print(f"[{index}] score={score} {date} {title}")
        print(str(path))
        print(snippet)
        print("-")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
