---
name: git-multi-workspace
description: Manage multiple git workspaces (dev/review/hotfix/spare) from a repo URL or local path using git worktree by default or full clones. Use when setting up dev/review/hotfix/spare directories, switching branches per workspace, or working with non-GitHub git servers via https/ssh/local URLs.
---

# Git Multi Workspace

## Quick Start
- `python3 scripts/git_multi_workspace.py setup <repo-url-or-path>` を実行する。
- 既定の作成先は `~/repos/<repo-name>/` で、`dev/review/hotfix/spare` を作成する。
- `--mode clone` を指定すると各ディレクトリをフル clone する。
- `--dev` `--review` `--hotfix` `--spare` で各ディレクトリのブランチを指定する。
- `python3 scripts/git_multi_workspace.py switch <repo> <workspace> <branch>` でブランチを切り替える。
- ブランチが存在しない場合は `--create` を使い、必要なら `--start-point origin/main` を指定する。
- 使わなくなった環境は `python3 scripts/git_multi_workspace.py remove <repo> <workspace>` で削除する。

## Behavior
- 既定のベースは `~/repos`。必要なら `--base` を指定する。
- worktree の管理用リポジトリは `<base>/<repo-name>/.git-worktree` に置く。
- 既に他の worktree で使われているブランチは `--on-duplicate detach` でデタッチにする。

## Commands
- `setup`: URL/パスから4つのディレクトリを作成する。
- `switch`: 指定したディレクトリのブランチを切り替える。`--create` で未存在ブランチを作成できる。
- `paths`: 生成されるパスを表示する。
- `remove`: worktree なら detach+削除、clone ならディレクトリ削除。`--all` で全削除。

## Usage Examples
- `python3 scripts/git_multi_workspace.py setup git@host:org/repo.git --dev feature/hoge`
- `python3 scripts/git_multi_workspace.py setup https://host/org/repo.git --mode clone`
- `python3 scripts/git_multi_workspace.py switch git@host:org/repo.git dev feature/hoge`
- `python3 scripts/git_multi_workspace.py switch git@host:org/repo.git dev feature/new-ui --create --start-point origin/main`
- `python3 scripts/git_multi_workspace.py remove git@host:org/repo.git dev`
- `python3 scripts/git_multi_workspace.py remove git@host:org/repo.git --all --force`
