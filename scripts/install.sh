#!/usr/bin/env bash
# learnmuse installer. Copies the skill pack into a Muse custom skills
# folder so any Muse user can invoke the skills by name.
#
# Usage:
#   ./scripts/install.sh [--verify-only] [DEST]
#   ./scripts/install.sh --help
#
# DEST defaults to ~/workspace/custom-skills when that folder exists
# (the Muse workspace layout), otherwise to ~/.muse/skills. Pass an
# explicit folder to install anywhere else. Existing learnmuse skills
# in DEST are replaced. Nothing else in DEST is touched.
#
# --verify-only installs only the verifier, for users who already
# have a learning loop and want just that piece: skills/learnmuse-verify
# plus tools/ledger.py, nothing else. The ledger copy lands at
# DEST/learnmuse-verify/tools/ledger.py, identical to the repo copy,
# so the installed verifier is self contained. When run from a clone,
# tools/ledger.py in the repo works the same way.
# Without --verify-only, the full pack installs all 9 skills.
set -euo pipefail

usage() {
  echo "Usage: $0 [--verify-only] [DEST]"
  echo "  --verify-only  install only learnmuse-verify plus tools/ledger.py"
  echo "  --help, -h     show this help"
  echo "  DEST           install folder, default ~/workspace/custom-skills"
  echo "                 or ~/.muse/skills when the workspace folder is absent"
}

SRC="$(cd "$(dirname "$0")/.." && pwd)/skills"
TOOLS_SRC="$(cd "$(dirname "$0")/.." && pwd)/tools/ledger.py"
VERIFY_ONLY=0
DEST=""

while [ $# -gt 0 ]; do
  case "$1" in
    --verify-only)
      VERIFY_ONLY=1
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    --*)
      echo "unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
    *)
      if [ -n "$DEST" ]; then
        echo "too many arguments: $1" >&2
        usage >&2
        exit 2
      fi
      DEST="$1"
      shift
      ;;
  esac
done

if [ -z "$DEST" ]; then
  if [ -d "$HOME/workspace/custom-skills" ]; then
    DEST="$HOME/workspace/custom-skills"
  else
    DEST="$HOME/.muse/skills"
  fi
fi

mkdir -p "$DEST"

if [ "$VERIFY_ONLY" -eq 1 ]; then
  rm -rf "$DEST/learnmuse-verify"
  cp -r "$SRC/learnmuse-verify" "$DEST/learnmuse-verify"
  mkdir -p "$DEST/learnmuse-verify/tools"
  cp "$TOOLS_SRC" "$DEST/learnmuse-verify/tools/ledger.py"
  echo "installed learnmuse-verify"
  echo "installed tools/ledger.py to learnmuse-verify/tools/ledger.py"
  echo "verifier-only install complete in $DEST"
  echo "Invoke learnmuse-verify to check a proposed skill or memory entry."
  exit 0
fi

for skill in "$SRC"/*/; do
  name="$(basename "$skill")"
  rm -rf "$DEST/$name"
  cp -r "$skill" "$DEST/$name"
  echo "installed $name"
done
echo "learnmuse skills installed to $DEST"
echo "Invoke learnmuse-orchestrator to start a learning review."
