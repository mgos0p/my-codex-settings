#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from dataclasses import dataclass
from typing import Iterable, Sequence


@dataclass(frozen=True)
class Step:
    command: Sequence[str]
    prompt: str | None = None


def run_command(command: Sequence[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=check, text=True, capture_output=False)


def run_command_capture(command: Sequence[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=True, text=True, capture_output=True)


def command_to_str(command: Sequence[str]) -> str:
    return " ".join(shlex.quote(part) for part in command)


def confirm(message: str) -> bool:
    answer = input(f"{message} [y/N]: ").strip().lower()
    return answer in {"y", "yes"}


def validate_git_state(allow_dirty: bool) -> None:
    try:
        run_command_capture(["git", "rev-parse", "--is-inside-work-tree"])
    except subprocess.CalledProcessError as error:
        raise RuntimeError("Git リポジトリ内で実行してください。") from error

    status = run_command_capture(["git", "status", "--porcelain"]).stdout.strip()
    if status and not allow_dirty:
        raise RuntimeError(
            "作業ツリーに未コミット変更があります。安全のため中断しました。"
            " --allow-dirty を付けると継続できます。"
        )


def branch_exists(branch_name: str) -> bool:
    exists = subprocess.run(
        ["git", "show-ref", "--verify", "--quiet", f"refs/heads/{branch_name}"],
        check=False,
    )
    return exists.returncode == 0


def ensure_branch_exists(branch_name: str) -> None:
    if not branch_exists(branch_name):
        raise RuntimeError(f"ブランチ {branch_name} が存在しません。")


def ensure_branch_not_exists(branch_name: str) -> None:
    if branch_exists(branch_name):
        raise RuntimeError(
            f"ブランチ {branch_name} は既に存在します。"
            " 重複作成を避けるため中断しました。"
        )


def build_steps(flow: str, base_a: str, branch_b: str, branch_c: str) -> list[Step]:
    create_steps = [
        Step(("git", "switch", base_a)),
        Step(("git", "switch", "-c", branch_b)),
        Step(("git", "switch", "-c", branch_c)),
    ]

    retarget_steps = [
        Step(("git", "switch", base_a)),
        Step(("git", "merge", "--no-ff", branch_b), prompt="B を A にマージします。続行しますか?"),
        Step(("git", "switch", branch_c)),
        Step(
            ("git", "rebase", "--onto", base_a, branch_b, branch_c),
            prompt="C の履歴を書き換えてベースを A に切り替えます。続行しますか?",
        ),
    ]

    if flow == "create-only":
        return create_steps
    if flow == "retarget-only":
        return retarget_steps
    return [*create_steps, *retarget_steps]


def validate_branch_rules(flow: str, base_a: str, branch_b: str, branch_c: str) -> None:
    ensure_branch_exists(base_a)

    if flow in {"full", "create-only"}:
        ensure_branch_not_exists(branch_b)
        ensure_branch_not_exists(branch_c)

    if flow == "retarget-only":
        ensure_branch_exists(branch_b)
        ensure_branch_exists(branch_c)


def print_plan(steps: Iterable[Step]) -> None:
    print("以下を順に実行します:\n")
    for step in steps:
        print(f"{command_to_str(step.command)}")


def execute_steps(steps: Iterable[Step], *, yes: bool) -> None:
    for step in steps:
        if step.prompt and not yes and not confirm(step.prompt):
            raise RuntimeError("ユーザー操作で中断しました。")
        print(f"$ {command_to_str(step.command)}")
        run_command(step.command)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "A をベースに B、B をベースに C を作成し、"
            "B の A へのマージ後に C のベースを A に切り替える。"
        )
    )
    parser.add_argument("--base-a", required=True, help="ベースとなるブランチA")
    parser.add_argument("--branch-b", required=True, help="A から作るブランチB")
    parser.add_argument("--branch-c", required=True, help="B から作るブランチC")
    parser.add_argument(
        "--flow",
        choices=("full", "create-only", "retarget-only"),
        default="full",
        help="full: 一連の処理 / create-only: B,C 作成のみ / retarget-only: BのA取込み+Cベース切替",
    )
    parser.add_argument(
        "--mode",
        choices=("run", "plan"),
        default="run",
        help="run: 実行 / plan: コピペ用コマンド出力のみ",
    )
    parser.add_argument("--yes", action="store_true", help="確認プロンプトをスキップして実行する")
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="未コミット変更があっても中断しない",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if len({args.base_a, args.branch_b, args.branch_c}) != 3:
        print("--base-a / --branch-b / --branch-c はすべて異なる名前にしてください。", file=sys.stderr)
        return 2

    try:
        validate_git_state(args.allow_dirty)
        validate_branch_rules(args.flow, args.base_a, args.branch_b, args.branch_c)

        steps = build_steps(args.flow, args.base_a, args.branch_b, args.branch_c)
        print_plan(steps)

        if args.mode == "plan":
            return 0

        if not args.yes and not confirm("この手順を実行しますか?"):
            print("中断しました。")
            return 130

        execute_steps(steps, yes=args.yes)
        print("完了しました。")
        return 0
    except (RuntimeError, subprocess.CalledProcessError) as error:
        print(f"エラー: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
