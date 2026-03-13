---
name: git-branch-base-switch
description: Git の分岐フローを安全に自動化する。A をベースに B を作成し、B をベースに C を作成し、B を A にマージした後で C のベースを B から A に切り替える。ブランチ作成チェーン、マージ後の rebase --onto、確認付き実行、またはコピペ用コマンド生成を求められたときに使う。
---

# Git Branch Base Switch

## Overview

A→B→C の分岐と、B を A に取り込んだ後の C のベース切替を一貫して扱う。
`plan` はコマンド出力のみ、`run` は確認付きで実行する。

## Workflow

1. 入力を確定する。
- `base-a`: 取り込み先ブランチ（例: `main`）
- `branch-b`: A から作るブランチ
- `branch-c`: B から作るブランチ
- `flow`: 実行範囲

2. まず `plan` で実行コマンドを確認する。

```bash
python3 scripts/branch_base_switch.py \
  --base-a main \
  --branch-b feature/b \
  --branch-c feature/c \
  --flow full \
  --mode plan
```

3. 問題なければ `run` で実行する。

```bash
python3 scripts/branch_base_switch.py \
  --base-a main \
  --branch-b feature/b \
  --branch-c feature/c \
  --flow full \
  --mode run
```

## Flow Options

- `--flow full`: B/C 作成からマージ・ベース切替まで一括実行する。
- `--flow create-only`: A→B→C の作成だけ実行する。
- `--flow retarget-only`: B を A にマージし、C のベースを A に切り替える。

## Execution Rules

- 実行前に Git リポジトリ内か確認する。
- 作業ツリーに未コミット変更がある場合は中断する（`--allow-dirty` で解除可能）。
- `base-a` が存在しない場合は中断する。
- `flow=full` / `flow=create-only` では `branch-b` と `branch-c` が既存なら中断する。
- `flow=retarget-only` では `branch-b` と `branch-c` が未作成なら中断する。
- `run` では全体実行前に確認し、さらに以下の直前で確認する。
- `git merge --no-ff <branch-b>`
- `git rebase --onto <base-a> <branch-b> <branch-c>`

## Output Commands

### `flow=full`

```bash
git switch <base-a>
git switch -c <branch-b>
git switch -c <branch-c>
git switch <base-a>
git merge --no-ff <branch-b>
git switch <branch-c>
git rebase --onto <base-a> <branch-b> <branch-c>
```

### `flow=create-only`

```bash
git switch <base-a>
git switch -c <branch-b>
git switch -c <branch-c>
```

### `flow=retarget-only`

```bash
git switch <base-a>
git merge --no-ff <branch-b>
git switch <branch-c>
git rebase --onto <base-a> <branch-b> <branch-c>
```

## Troubleshooting

- `rebase` で競合したら、競合解消後に `git rebase --continue` を実行する。
- 取り消す場合は `git rebase --abort` を実行する。
