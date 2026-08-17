#!/usr/bin/env bash
# Connects Claude to Vertex AI for Veo video generation:
#   ADC login (if needed) -> project (reuse/create) -> link billing -> enable Vertex -> save project id.
# Requires gcloud installed and an active billing account (the $300 trial + a card).
#
# Usage: ./connect-vertex.sh [PROJECT_ID]
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
command -v gcloud >/dev/null 2>&1 || { echo "❌ Install gcloud: https://cloud.google.com/sdk/docs/install"; exit 1; }

# 1) Application Default Credentials
if ! gcloud auth application-default print-access-token >/dev/null 2>&1; then
  echo "▶ Opening Google sign-in (Application Default Credentials)..."
  gcloud auth application-default login
fi

# 2) project
PROJECT_ID="${1:-$(cat "$HERE/.veo-project" 2>/dev/null || true)}"
if [ -z "$PROJECT_ID" ]; then
  echo "▶ Finding an open billing account..."
  BILLING="$(gcloud billing accounts list --filter='open=true' --format='value(name)' 2>/dev/null | head -1)"
  [ -n "$BILLING" ] || { echo "❌ No open billing account. Claim the \$300 trial + add a card, then re-run."; exit 1; }
  SUFFIX="$(date +%s)"; PROJECT_ID="claude-veo-${SUFFIX: -6}"
  echo "▶ Creating project $PROJECT_ID ..."
  gcloud projects create "$PROJECT_ID" --name="Claude Veo" 2>/dev/null || true
  gcloud billing projects link "$PROJECT_ID" --billing-account="$BILLING"
fi
echo "$PROJECT_ID" > "$HERE/.veo-project"

# 3) enable Vertex + set ADC quota project
echo "▶ Enabling Vertex AI (aiplatform.googleapis.com)..."
gcloud services enable aiplatform.googleapis.com --project="$PROJECT_ID"
gcloud auth application-default set-quota-project "$PROJECT_ID"

# 4) make the project id available to the skill + future shells
SKILL_DIR="$HOME/.claude/skills/veo-video"; mkdir -p "$SKILL_DIR"; echo "$PROJECT_ID" > "$SKILL_DIR/.project"
ZRC="$HOME/.zshrc"
grep -q 'claude-veo / vertex' "$ZRC" 2>/dev/null || \
  printf '\n# >>> claude-veo / vertex >>>\nexport GOOGLE_CLOUD_PROJECT="%s"\n# <<< claude-veo / vertex <<<\n' "$PROJECT_ID" >> "$ZRC"

echo "✅ Connected. Project: $PROJECT_ID  (Vertex AI enabled, ADC ready)"
echo "   Now run ./install.sh, then in Claude Code say: \"generate a video of ...\""
