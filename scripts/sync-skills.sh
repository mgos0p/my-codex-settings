#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
DEFAULT_SRC="${HOME}/.codex/skills"
DEFAULT_DEST="${SCRIPT_DIR}/../.codex/skills"

if [[ $# -gt 2 ]]; then
  echo "Usage: $0 [src] [dest]" >&2
  exit 1
fi

SRC="${1:-$DEFAULT_SRC}"
DEST="${2:-$DEFAULT_DEST}"
OS="$(uname -s)"

case "$OS" in
  Darwin*)
    mkdir -p "$DEST"
    # macOS では rsync で .DS_Store を除外しつつミラー同期する。
    rsync -a --delete --exclude=".DS_Store" "$SRC/" "$DEST/"
    ;;
  MINGW*|MSYS*|CYGWIN*)
    if ! command -v cygpath >/dev/null 2>&1; then
      echo "cygpath is required on Windows." >&2
      exit 1
    fi

    SRC_WIN="$(cygpath -w "$SRC")"
    DEST_WIN="$(cygpath -w "$DEST")"

    powershell.exe -NoProfile -Command '
      $src = $args[0]
      $dest = $args[1]
      New-Item -ItemType Directory -Force -Path $dest | Out-Null
      robocopy $src $dest /MIR /XD .git /XF .DS_Store | Out-Null
      if ($LASTEXITCODE -ge 8) { exit $LASTEXITCODE }
    ' --% "$SRC_WIN" "$DEST_WIN"
    ;;
  *)
    echo "Unsupported OS: $OS" >&2
    exit 1
    ;;
esac