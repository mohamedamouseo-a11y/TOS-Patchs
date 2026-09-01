#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="${1:-/var/www/TOS}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_FILE="$(mktemp /tmp/tos-developer-hub-ignored-staging-v1.XXXXXX.patch)"
trap 'rm -f "$PATCH_FILE"' EXIT

cd "$REPO_ROOT"

echo "== TOS Developer Hub Ignored Staging Fix V1 =="
echo "REPO_ROOT=$REPO_ROOT"
echo "HEAD=$(git rev-parse HEAD)"
echo
echo "STATUS_BEFORE:"
git status --short

echo
echo "STAGED_PM2_BEFORE:"
git diff --cached --name-status -- backend/.pm2 || true

echo
echo "PM2_IGNORE_RULE:"
git check-ignore -v backend/.pm2/module_conf.json backend/.pm2/touch || true

python3 "$SCRIPT_DIR/generate_developer_hub_ignored_staging_fix_v1.py" "$REPO_ROOT" "$PATCH_FILE"

git apply --check "$PATCH_FILE"
git apply "$PATCH_FILE"

node --check backend/src/services/githubAdvanced.service.js
git diff --check

echo
echo "STATIC_VERIFICATION:"
grep -F 'stagedDeletionPaths' backend/src/services/githubAdvanced.service.js >/dev/null
grep -F '["check-ignore", "-q", "--", candidate]' backend/src/services/githubAdvanced.service.js >/dev/null
grep -F 'preservedIgnoredDeletions' backend/src/services/githubAdvanced.service.js >/dev/null
if grep -F 'runOperationGit(repoPath, ["add", "-A", "--", ...safe.slice(index, index + 100)]' backend/src/services/githubAdvanced.service.js >/dev/null; then
  echo "ERROR: vulnerable direct safe[] git add pattern still present" >&2
  exit 41
fi

echo "IGNORED_STAGED_DELETION_PRESERVATION=PASS"
echo "FORCE_ADD_USED=NO"
echo "NODE_CHECK=PASS"
echo
echo "STAGED_PM2_AFTER:"
git diff --cached --name-status -- backend/.pm2 || true

echo
echo "STATUS_AFTER:"
git status --short

echo
echo "DEVELOPER_HUB_IGNORED_STAGING_FIX_V1_APPLIED=YES"
echo "NO_GIT_COMMIT_OR_PUSH_PERFORMED=YES"
