#!/usr/bin/env bash
# Installs the veo-video skill into ~/.claude/skills/ so Claude Code can use it globally.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DEST="$HOME/.claude/skills/veo-video"
mkdir -p "$DEST"
cp "$HERE/skills/veo-video/SKILL.md" "$DEST/SKILL.md"
cp "$HERE/skills/veo-video/generate_veo.py" "$DEST/generate_veo.py"
chmod +x "$DEST/generate_veo.py"
# carry over the project id if connect-vertex.sh already saved one
[ -f "$HERE/.veo-project" ] && cp "$HERE/.veo-project" "$DEST/.project"
echo "✅ Installed veo-video skill → $DEST"
echo "   In Claude Code, just say:  \"generate a video of <your idea>\""
