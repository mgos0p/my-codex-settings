#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shlex
import shutil
import subprocess
from pathlib import Path

DEFAULT_DIR = "/Users/mgos0p/.codex/memory"


def run(cmd: list[str], dry_run: bool) -> str:
    if dry_run:
        print("DRY-RUN:", " ".join(shlex.quote(part) for part in cmd))
        return ""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\n{message}")
    return result.stdout.strip()


def command_ok(cmd: list[str]) -> bool:
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0


def ensure_repo(path: Path, branch: str, dry_run: bool) -> None:
    if not (path / ".git").exists():
        run(["git", "-C", str(path), "init"], dry_run)
        run(["git", "-C", str(path), "checkout", "-b", branch], dry_run)
        return

    if dry_run:
        return

    current = run(["git", "-C", str(path), "rev-parse", "--abbrev-ref", "HEAD"], False)
    if current == branch:
        return

    branch_exists = command_ok(
        ["git", "-C", str(path), "show-ref", "--verify", f"refs/heads/{branch}"]
    )
    if branch_exists:
        run(["git", "-C", str(path), "checkout", branch], False)
    else:
        run(["git", "-C", str(path), "checkout", "-b", branch], False)


def stage_and_commit(path: Path, message: str, dry_run: bool) -> None:
    run(["git", "-C", str(path), "add", "-A"], dry_run)
    if dry_run:
        return

    has_staged_changes = subprocess.run(
        ["git", "-C", str(path), "diff", "--cached", "--quiet"],
        capture_output=True,
    ).returncode

    if has_staged_changes != 0:
        run(["git", "-C", str(path), "commit", "-m", message], False)
        return

    has_commits = command_ok(["git", "-C", str(path), "rev-parse", "--verify", "HEAD"])
    if not has_commits:
        run(["git", "-C", str(path), "commit", "--allow-empty", "-m", message], False)


def get_remote(path: Path) -> str:
    result = subprocess.run(
        ["git", "-C", str(path), "remote", "get-url", "origin"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish local notes to GitHub.")
    parser.add_argument("--dir", default=DEFAULT_DIR, help="Notes directory")
    parser.add_argument("--repo", required=True, help="GitHub repo name")
    parser.add_argument("--owner", default="", help="GitHub owner/org (optional)")
    parser.add_argument(
        "--visibility",
        choices=["private", "public"],
        default="private",
        help="Repo visibility",
    )
    parser.add_argument(
        "--commit-message",
        default="Update memory notes",
        help="Commit message",
    )
    parser.add_argument("--branch", default="main", help="Git branch name")
    parser.add_argument(
        "--remote-url",
        default="",
        help="Use existing remote URL instead of gh repo create",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print commands only")
    args = parser.parse_args()

    if not args.dry_run:
        if shutil.which("git") is None:
            raise SystemExit("git is required but not found")
        if shutil.which("gh") is None:
            raise SystemExit("gh is required but not found")

    path = Path(args.dir).expanduser()
    if not path.exists():
        raise SystemExit(f"Directory not found: {path}")

    ensure_repo(path, args.branch, args.dry_run)
    stage_and_commit(path, args.commit_message, args.dry_run)

    remote = get_remote(path) if not args.dry_run else ""
    if args.remote_url and not remote:
        run(["git", "-C", str(path), "remote", "add", "origin", args.remote_url], args.dry_run)
        remote = args.remote_url

    if not remote:
        if not args.dry_run:
            auth_ok = command_ok(["gh", "auth", "status"])
            if not auth_ok:
                raise SystemExit("gh is not authenticated. Run 'gh auth login'.")

        repo_target = f"{args.owner}/{args.repo}" if args.owner else args.repo
        visibility_flag = "--private" if args.visibility == "private" else "--public"
        run(
            [
                "gh",
                "repo",
                "create",
                repo_target,
                visibility_flag,
                "--source",
                str(path),
                "--remote",
                "origin",
                "--push",
                "--confirm",
            ],
            args.dry_run,
        )
    else:
        run(["git", "-C", str(path), "push", "-u", "origin", args.branch], args.dry_run)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
