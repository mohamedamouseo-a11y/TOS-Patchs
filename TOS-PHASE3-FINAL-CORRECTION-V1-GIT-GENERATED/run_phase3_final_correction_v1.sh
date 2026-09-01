#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${1:-/var/www/TOS}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_FILE="$(mktemp /tmp/tos-phase3-final-v1.XXXXXX.patch)"
trap 'rm -f "$PATCH_FILE"' EXIT

cd "$REPO_ROOT"

echo "== TOS Phase 3 Final Correction V1 =="
echo "REPO_ROOT=$REPO_ROOT"
echo "HEAD=$(git rev-parse HEAD)"

python3 "$SCRIPT_DIR/generate_phase3_final_correction_v1.py" "$REPO_ROOT" "$PATCH_FILE"

git apply --check "$PATCH_FILE"
git apply "$PATCH_FILE"

# Remove generated PM2 artifacts from Git tracking only. Runtime files remain on disk.
# -f is intentional because runtime files may have changed after the last commit.
git rm -f --cached --ignore-unmatch backend/.pm2/module_conf.json backend/.pm2/touch || true

node --check backend/src/routes/tasks.routes.js
npm --prefix frontend run build

git diff --check

echo
echo "PHASE3_FINAL_CORRECTION_V1_APPLIED=YES"
echo "PM2_RUNTIME_FILES_LEFT_ON_DISK=YES"
echo "PRIMARY_ASSIGNEE_SCORING=YES"
echo "NO_GIT_COMMIT_OR_PUSH_PERFORMED=YES"
echo
echo "git status --short"
git status --short
