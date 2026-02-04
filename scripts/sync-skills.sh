#!/bin/zsh
set -euo pipefail

SRC="/Users/mgos0p/.codex/skills"
DEST="/Users/mgos0p/my-codex-settings/.codex/skills"

mkdir -p "$DEST"
# ローカル同期のみ。コミットや push はしない。
rsync -a --delete --exclude=".DS_Store" "$SRC/" "$DEST/"
