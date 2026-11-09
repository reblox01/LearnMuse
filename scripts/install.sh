#!/usr/bin/env bash
# learnmuse installer. Copies the skill pack into a Muse custom skills
# folder so any Muse user can invoke the skills by name.
#
# Usage:
#   ./scripts/install.sh [DEST]
#
# DEST defaults to ~/workspace/custom-skills when that folder exists
# (the Muse workspace layout), otherwise to ~/.muse/skills. Pass an
# explicit folder to install anywhere else. Existing learnmuse skills
# in DEST are replaced. Nothing else in DEST is touched.
set -euo pipefail

SRC="$(cd "$(dirname "$0")/.." && pwd)/skills"
if [ $# -ge 1 ]; then
  DEST="$1"
elif [ -d "$HOME/workspace/custom-skills" ]; then
  DEST="$HOME/workspace/custom-skills"
else
  DEST="$HOME/.muse/skills"
fi

mkdir -p "$DEST"
for skill in "$SRC"/learnmuse-*/; do
  name="$(basename "$skill")"
  rm -rf "$DEST/$name"
  cp -r "$skill" "$DEST/$name"
  echo "installed $name"
done
echo "learnmuse skills installed to $DEST"
echo "Invoke learnmuse-orchestrator to start a learning review."
