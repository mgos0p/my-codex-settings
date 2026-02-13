#!/usr/bin/env python3
"""Create or switch multiple git workspaces from a repo URL or path."""

from __future__ import annotations

import argparse
import os
import shlex
import shutil
import subprocess
import sys
from typing import Dict, Iterable, Set

DEFAULT_BASE = "~/repos"
WORKSPACES = ("dev", "review", "hotfix", "spare")


def run(cmd: Iterable[str], cwd: str | None = None, check: bool = True) -> subprocess.CompletedProcess:
    print("$ " + " ".join(shlex.quote(c) for c in cmd))
    result = subprocess.run(
        list(cmd),
        cwd=cwd,
        text=True,
        capture_output=True,
    )
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    if check and result.returncode != 0:
        raise subprocess.CalledProcessError(
            result.returncode,
            cmd,
            output=result.stdout,
            stderr=result.stderr,
        )
    return result


def normalize_base(base: str) -> str:
    return os.path.abspath(os.path.expanduser(base))


def repo_name_from_url(repo: str) -> str:
    trimmed = repo.rstrip("/")
    if trimmed.endswith(".git"):
        trimmed = trimmed[:-4]
    if ":" in trimmed and not trimmed.startswith(("http://", "https://", "ssh://", "git://")):
        trimmed = trimmed.split(":")[-1]
    name = os.path.basename(trimmed)
    return name or "repo"


def is_duplicate_branch_error(text: str) -> bool:
    lowered = text.lower()
    return "already checked out" in lowered


def default_branch(git_root: str) -> str:
    result = run(
        [
            "git",
            "-C",
            git_root,
            "symbolic-ref",
            "-q",
            "--short",
            "refs/remotes/origin/HEAD",
        ],
        check=False,
    )
    if result.returncode == 0:
        ref = result.stdout.strip()
        if ref.startswith("origin/"):
            return ref.split("/", 1)[1]

    result = run(
        ["git", "-C", git_root, "rev-parse", "--abbrev-ref", "HEAD"],
        check=False,
    )
    if result.returncode == 0:
        branch = result.stdout.strip()
        if branch and branch != "HEAD":
            return branch

    result = run(["git", "-C", git_root, "branch", "-r"], check=False)
    remotes = result.stdout
    if "origin/main" in remotes:
        return "main"
    if "origin/master" in remotes:
        return "master"
    return "main"


def ensure_git_root(repo: str, git_root: str, fetch: bool) -> None:
    if not os.path.exists(git_root):
        os.makedirs(os.path.dirname(git_root), exist_ok=True)
        run(["git", "clone", "--bare", repo, git_root])
    else:
        result = run(["git", "-C", git_root, "rev-parse", "--git-dir"], check=False)
        if result.returncode != 0:
            print(f"[ERROR] {git_root} is not a git repository.", file=sys.stderr)
            sys.exit(1)

    if fetch:
        run(["git", "-C", git_root, "fetch", "--all", "--prune"])

    result = run(["git", "-C", git_root, "rev-parse", "--is-bare-repository"], check=False)
    if result.returncode == 0 and result.stdout.strip() == "false":
        run(["git", "-C", git_root, "checkout", "--detach"], check=False)


def checked_out_branches(git_root: str) -> Set[str]:
    result = run(["git", "-C", git_root, "worktree", "list", "--porcelain"], check=False)
    branches: Set[str] = set()
    for line in result.stdout.splitlines():
        if line.startswith("branch "):
            ref = line.split(" ", 1)[1].strip()
            if ref.startswith("refs/heads/"):
                branches.add(ref.split("refs/heads/", 1)[1])
    return branches


def ref_exists(repo_path: str, ref: str) -> bool:
    result = run(["git", "-C", repo_path, "show-ref", "--verify", "--quiet", ref], check=False)
    return result.returncode == 0


def resolve_start_point(repo_path: str, start_point: str | None) -> str:
    if start_point:
        return start_point

    default = default_branch(repo_path)
    remote_ref = f"refs/remotes/origin/{default}"
    if ref_exists(repo_path, remote_ref):
        return f"origin/{default}"
    return default


def git_root_from_repo_root(repo_root: str) -> str | None:
    git_root = os.path.join(repo_root, ".git-worktree")
    if not os.path.isdir(git_root):
        return None
    result = run(["git", "-C", git_root, "rev-parse", "--git-dir"], check=False)
    if result.returncode == 0:
        return git_root
    return None


def is_safe_child(parent: str, child: str) -> bool:
    parent_abs = os.path.abspath(parent)
    child_abs = os.path.abspath(child)
    return os.path.commonpath([parent_abs, child_abs]) == parent_abs


def checkout_branch(
    workspace_path: str,
    branch: str,
    on_duplicate: str,
    fetch: bool,
    allow_create: bool,
    start_point: str | None,
) -> None:
    if fetch:
        run(["git", "-C", workspace_path, "fetch", "--all", "--prune"])

    result = run(["git", "-C", workspace_path, "checkout", branch], check=False)
    if result.returncode == 0:
        return

    combined = (result.stdout or "") + (result.stderr or "")
    if on_duplicate == "detach" and is_duplicate_branch_error(combined):
        run(["git", "-C", workspace_path, "checkout", "--detach", branch])
        return

    if "pathspec" in combined or "unknown revision" in combined:
        if not branch.startswith("origin/") and not branch.startswith("refs/"):
            remote_ref = f"refs/remotes/origin/{branch}"
            if ref_exists(workspace_path, remote_ref):
                result = run(
                    ["git", "-C", workspace_path, "checkout", "-b", branch, f"origin/{branch}"],
                    check=False,
                )
                if result.returncode == 0:
                    return

            if allow_create:
                base = resolve_start_point(workspace_path, start_point)
                result = run(
                    ["git", "-C", workspace_path, "checkout", "-b", branch, base],
                    check=False,
                )
                if result.returncode == 0:
                    return

    print(f"[ERROR] Failed to checkout {branch} in {workspace_path}", file=sys.stderr)
    sys.exit(result.returncode)


def add_worktree(
    git_root: str,
    workspace_path: str,
    branch: str,
    on_duplicate: str,
) -> None:
    result = run(
        ["git", "-C", git_root, "worktree", "add", workspace_path, branch],
        check=False,
    )
    if result.returncode == 0:
        return

    combined = (result.stdout or "") + (result.stderr or "")
    if on_duplicate == "detach" and is_duplicate_branch_error(combined):
        run(
            [
                "git",
                "-C",
                git_root,
                "worktree",
                "add",
                "--detach",
                workspace_path,
                branch,
            ]
        )
        return

    print(f"[ERROR] Failed to add worktree {workspace_path}", file=sys.stderr)
    sys.exit(result.returncode)


def create_worktrees(
    repo: str,
    repo_root: str,
    branches: Dict[str, str],
    fetch: bool,
    on_duplicate: str,
) -> None:
    git_root = os.path.join(repo_root, ".git-worktree")
    ensure_git_root(repo, git_root, fetch)
    default = default_branch(git_root)
    in_use = checked_out_branches(git_root)

    for workspace in WORKSPACES:
        workspace_path = os.path.join(repo_root, workspace)
        if os.path.exists(workspace_path):
            print(f"[SKIP] {workspace_path} already exists")
            continue
        branch = branches.get(workspace) or default

        if branch in in_use and on_duplicate == "detach":
            run(["git", "-C", git_root, "worktree", "add", "--detach", workspace_path, branch])
        else:
            add_worktree(git_root, workspace_path, branch, on_duplicate)
            in_use.add(branch)


def create_clones(
    repo: str,
    repo_root: str,
    branches: Dict[str, str],
    fetch: bool,
) -> None:
    default_branch_name = None
    for workspace in WORKSPACES:
        workspace_path = os.path.join(repo_root, workspace)
        if os.path.exists(workspace_path):
            print(f"[SKIP] {workspace_path} already exists")
            continue

        run(["git", "clone", repo, workspace_path])
        if default_branch_name is None:
            result = run(
                ["git", "-C", workspace_path, "rev-parse", "--abbrev-ref", "HEAD"],
                check=False,
            )
            default_branch_name = result.stdout.strip() or "main"

        branch = branches.get(workspace)
        if branch and branch != default_branch_name:
            checkout_branch(workspace_path, branch, "error", fetch, False, None)


def parse_branches(args: argparse.Namespace) -> Dict[str, str]:
    branches = {}
    for workspace in WORKSPACES:
        value = getattr(args, workspace)
        if value:
            branches[workspace] = value
    return branches


def setup_command(args: argparse.Namespace) -> None:
    base = normalize_base(args.base)
    os.makedirs(base, exist_ok=True)

    repo_name = repo_name_from_url(args.repo)
    repo_root = os.path.join(base, repo_name)
    os.makedirs(repo_root, exist_ok=True)

    branches = parse_branches(args)
    if args.mode == "worktree":
        create_worktrees(args.repo, repo_root, branches, args.fetch, args.on_duplicate)
    else:
        create_clones(args.repo, repo_root, branches, args.fetch)


def switch_command(args: argparse.Namespace) -> None:
    base = normalize_base(args.base)
    repo_name = repo_name_from_url(args.repo)
    repo_root = os.path.join(base, repo_name)
    workspace_path = os.path.join(repo_root, args.workspace)

    if not os.path.isdir(workspace_path):
        print(f"[ERROR] Workspace not found: {workspace_path}", file=sys.stderr)
        sys.exit(1)

    checkout_branch(
        workspace_path,
        args.branch,
        args.on_duplicate,
        args.fetch,
        args.create,
        args.start_point,
    )


def remove_workspace(repo_root: str, workspace: str, force: bool) -> None:
    workspace_path = os.path.join(repo_root, workspace)
    if not is_safe_child(repo_root, workspace_path):
        print(f"[ERROR] Unsafe workspace path: {workspace_path}", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(workspace_path):
        print(f"[SKIP] {workspace_path} not found")
        return

    git_root = git_root_from_repo_root(repo_root)
    if git_root:
        cmd = ["git", "-C", git_root, "worktree", "remove"]
        if force:
            cmd.append("--force")
        cmd.append(workspace_path)
        result = run(cmd, check=False)
        if result.returncode != 0:
            print(f"[ERROR] Failed to remove worktree {workspace_path}", file=sys.stderr)
            sys.exit(result.returncode)
        return

    if force:
        shutil.rmtree(workspace_path, ignore_errors=True)
    else:
        shutil.rmtree(workspace_path)


def remove_command(args: argparse.Namespace) -> None:
    if args.all and args.workspace:
        print("[ERROR] Use either <workspace> or --all", file=sys.stderr)
        sys.exit(1)
    if not args.all and not args.workspace:
        print("[ERROR] Workspace is required unless --all is specified", file=sys.stderr)
        sys.exit(1)

    base = normalize_base(args.base)
    repo_name = repo_name_from_url(args.repo)
    repo_root = os.path.join(base, repo_name)

    if not os.path.isdir(repo_root):
        print(f"[ERROR] Repo root not found: {repo_root}", file=sys.stderr)
        sys.exit(1)

    targets = WORKSPACES if args.all else (args.workspace,)
    for workspace in targets:
        remove_workspace(repo_root, workspace, args.force)


def paths_command(args: argparse.Namespace) -> None:
    base = normalize_base(args.base)
    repo_name = repo_name_from_url(args.repo)
    repo_root = os.path.join(base, repo_name)
    for workspace in WORKSPACES:
        print(os.path.join(repo_root, workspace))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create or switch multiple git workspaces.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    setup = subparsers.add_parser("setup", help="Create dev/review/hotfix/spare workspaces")
    setup.add_argument("repo", help="Git URL or local path")
    setup.add_argument("--base", default=DEFAULT_BASE, help="Base directory")
    setup.add_argument("--mode", choices=["worktree", "clone"], default="worktree")
    setup.add_argument("--on-duplicate", choices=["detach", "error"], default="detach")
    setup.add_argument("--fetch", dest="fetch", action="store_true", default=True)
    setup.add_argument("--no-fetch", dest="fetch", action="store_false")
    for workspace in WORKSPACES:
        setup.add_argument(f"--{workspace}", help=f"Branch for {workspace}")

    switch = subparsers.add_parser("switch", help="Switch branch in a workspace")
    switch.add_argument("repo", help="Git URL or local path")
    switch.add_argument("workspace", choices=WORKSPACES)
    switch.add_argument("branch")
    switch.add_argument("--base", default=DEFAULT_BASE, help="Base directory")
    switch.add_argument("--on-duplicate", choices=["detach", "error"], default="detach")
    switch.add_argument("--create", action="store_true", help="Create branch if missing")
    switch.add_argument("--start-point", help="Start point for --create (e.g., origin/main)")
    switch.add_argument("--fetch", dest="fetch", action="store_true", default=True)
    switch.add_argument("--no-fetch", dest="fetch", action="store_false")

    paths = subparsers.add_parser("paths", help="Print workspace paths")
    paths.add_argument("repo", help="Git URL or local path")
    paths.add_argument("--base", default=DEFAULT_BASE, help="Base directory")

    remove = subparsers.add_parser("remove", help="Remove worktree/clone workspace")
    remove.add_argument("repo", help="Git URL or local path")
    remove.add_argument("workspace", nargs="?", choices=WORKSPACES)
    remove.add_argument("--all", action="store_true", help="Remove all workspaces")
    remove.add_argument("--force", action="store_true", help="Force remove even if dirty")
    remove.add_argument("--base", default=DEFAULT_BASE, help="Base directory")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "setup":
        setup_command(args)
        return
    if args.command == "switch":
        switch_command(args)
        return
    if args.command == "paths":
        paths_command(args)
        return
    if args.command == "remove":
        remove_command(args)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
