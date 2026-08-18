#!/usr/bin/env bash
# Launches the Veo Studio web UI (a local Higgsfield-style interface) and opens the browser.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
PORT="${PORT:-8787}"

# make the project id available if it isn't already exported
if [ -z "${GOOGLE_CLOUD_PROJECT:-}" ] && [ -f "$HOME/.claude/skills/veo-video/.project" ]; then
  export GOOGLE_CLOUD_PROJECT="$(cat "$HOME/.claude/skills/veo-video/.project")"
fi

echo "Starting Veo Studio on http://localhost:$PORT  (Ctrl+C to stop)"
( sleep 1; open "http://localhost:$PORT" 2>/dev/null || xdg-open "http://localhost:$PORT" 2>/dev/null || true ) &
PORT="$PORT" exec python3 "$HERE/server.py"
