#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/var/www/TOS}"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_REPO_ROOT="$(cd "$PATCH_DIR/.." && pwd)"
SOURCE_CSS="$PATCH_DIR/tasks-projects-premium-reference-v1.css"

MAIN_TARGET="frontend/src/main.jsx"
TASKS_TARGET="frontend/src/components/ProfessionalTaskBoard.jsx"
CSS_TARGET="frontend/src/styles/tasks-projects-premium-reference.css"

EXPECTED_MAIN_HEAD_BLOB="725b57d3b7927b802dcedc26cca49c6a7f10ee55"
EXPECTED_TASKS_HEAD_BLOB="2a4fe1052b55e7f7f3d5da88c7eb0eb29fdb26d5"
IMPORT_AFTER='import "./styles/projects-github-reference.css";'
IMPORT_LINE='import "./styles/tasks-projects-premium-reference.css";'
RUNTIME='--tos-tasks-projects-reference-v1-runtime'

DIST="$ROOT/frontend/dist"
LIVE_PARENT="/opt/apps/tamiyouz-front"
LIVE="$LIVE_PARENT/build"
STAMP="$(date +%Y%m%d-%H%M%S)"
STAGE="$LIVE_PARENT/build.phase03-tasks-v1.new.$$"
BACKUP="$LIVE_PARENT/build.phase03-tasks-v1.backup-$STAMP"

fail() {
  echo "PHASE03_TASKS_PROJECTS_PREMIUM_REFERENCE_V1=FAIL"
  echo "ERROR=$1" >&2
  exit "${2:-1}"
}

[ -d "$ROOT/.git" ] || fail "TOS repository not found" 2
[ -d "$PATCH_REPO_ROOT/.git" ] || fail "TOS-Patchs repository not found" 3
[ -f "$SOURCE_CSS" ] || fail "Missing V1 CSS source" 4
[ -f "$ROOT/$MAIN_TARGET" ] || fail "Missing main.jsx" 5
[ -f "$ROOT/$TASKS_TARGET" ] || fail "Missing ProfessionalTaskBoard.jsx" 6
[ -d "$LIVE" ] || fail "Live frontend root missing" 7

SOURCE_REL="${SOURCE_CSS#$PATCH_REPO_ROOT/}"
[ "$(git -C "$PATCH_REPO_ROOT" hash-object "$SOURCE_CSS")" = "$(git -C "$PATCH_REPO_ROOT" rev-parse "HEAD:$SOURCE_REL")" ] || fail "Patch CSS differs from TOS-Patchs HEAD" 8

git -C "$ROOT" diff --cached --quiet || fail "Staged changes exist; stop" 9
[ "$(git -C "$ROOT" rev-parse "HEAD:$MAIN_TARGET")" = "$EXPECTED_MAIN_HEAD_BLOB" ] || fail "Committed main.jsx baseline changed" 10
[ "$(git -C "$ROOT" rev-parse "HEAD:$TASKS_TARGET")" = "$EXPECTED_TASKS_HEAD_BLOB" ] || fail "Committed ProfessionalTaskBoard baseline changed" 11

grep -Fq 'tos-tasks-entry-v6' "$ROOT/$TASKS_TARGET" || fail "Tasks gateway root missing" 12
grep -Fq 'tos-tasks-system-theme-v15' "$ROOT/$TASKS_TARGET" || fail "Active task-board root missing" 13

IMPORT_COUNT="$(grep -Fxc "$IMPORT_LINE" "$ROOT/$MAIN_TARGET" || true)"
RUNTIME_COUNT=0
[ -f "$ROOT/$CSS_TARGET" ] && RUNTIME_COUNT="$(grep -Fc -- "$RUNTIME" "$ROOT/$CSS_TARGET" || true)"

if [ "$IMPORT_COUNT" = "0" ] && [ "$RUNTIME_COUNT" = "0" ]; then
  STATUS="$(git -C "$ROOT" status --porcelain=v1 --untracked-files=all)"
  [ -z "$STATUS" ] || {
    echo "--- PRE-EXISTING STATUS ---"
    printf '%s\n' "$STATUS"
    fail "Expected clean TOS working tree before Phase 03 V1" 14
  }

  python3 - "$ROOT/$MAIN_TARGET" "$IMPORT_AFTER" "$IMPORT_LINE" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
after = sys.argv[2]
line = sys.argv[3]
text = path.read_text()
if line in text:
    raise SystemExit(0)
if text.count(after) != 1:
    raise SystemExit(f"expected import anchor once, got {text.count(after)}")
text = text.replace(after, after + "\n" + line, 1)
path.write_text(text)
PY

  mkdir -p "$(dirname "$ROOT/$CSS_TARGET")"
  cp "$SOURCE_CSS" "$ROOT/$CSS_TARGET"
  PATCH_ACTION="APPLIED"
elif [ "$IMPORT_COUNT" = "1" ] && [ "$RUNTIME_COUNT" = "1" ]; then
  PATCH_ACTION="VALIDATED_EXISTING"
else
  fail "Partial Phase 03 V1 state detected" 15
fi

[ "$(grep -Fxc "$IMPORT_LINE" "$ROOT/$MAIN_TARGET" || true)" = "1" ] || fail "Tasks CSS import missing or duplicated" 16
[ -f "$ROOT/$CSS_TARGET" ] || fail "Tasks CSS target missing" 17
[ "$(grep -Fc -- "$RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "Runtime sentinel missing or duplicated" 18

git -C "$ROOT" diff --check -- "$MAIN_TARGET" "$CSS_TARGET"

cd "$ROOT/frontend"
npm run build
cd "$ROOT"

[ -f "$DIST/index.html" ] || fail "Built dist index missing" 19
grep -RFlq -- "$RUNTIME" "$DIST/assets" || fail "Runtime sentinel missing from dist assets" 20

rm -rf "$STAGE"
mkdir -p "$STAGE"
cp -a "$DIST/." "$STAGE/"
[ -f "$STAGE/index.html" ] || fail "Staged index missing" 21
grep -RFlq -- "$RUNTIME" "$STAGE/assets" || fail "Runtime sentinel missing from staged assets" 22

mv "$LIVE" "$BACKUP"
if ! mv "$STAGE" "$LIVE"; then
  mv "$BACKUP" "$LIVE" || true
  fail "Failed to activate live build; rollback attempted" 23
fi

if ! grep -RFlq -- "$RUNTIME" "$LIVE/assets"; then
  rm -rf "$LIVE"
  mv "$BACKUP" "$LIVE" || true
  fail "Live runtime sentinel missing; rolled back" 24
fi

FINAL_STATUS="$(git -C "$ROOT" status --porcelain=v1 --untracked-files=all)"
FINAL_PATHS="$(printf '%s\n' "$FINAL_STATUS" | sed '/^$/d' | cut -c4- | sort -u)"
EXPECTED_PATHS="$(printf '%s\n%s\n' "$MAIN_TARGET" "$CSS_TARGET" | sort)"
[ "$FINAL_PATHS" = "$EXPECTED_PATHS" ] || {
  echo "--- FINAL STATUS ---"
  printf '%s\n' "$FINAL_STATUS"
  fail "Unexpected TOS files changed" 25
}

FINAL_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"
echo "PHASE03_TASKS_PROJECTS_PREMIUM_REFERENCE_V1=PASS"
echo "SCREEN=Tasks"
echo "REFERENCE=Phase_02_Projects_Premium"
echo "PATCH_ACTION=$PATCH_ACTION"
echo "GATEWAY_STYLED=YES"
echo "ACTIVE_BOARD_STYLED=YES"
echo "LIGHT_MODE=PREMIUM_PORCELAIN_CHAMPAGNE"
echo "DARK_MODE=OBSIDIAN_TITANIUM_CHAMPAGNE"
echo "BUILD_RESULT=PASS"
echo "LIVE_DEPLOY=PASS"
echo "DIST_RUNTIME_SENTINEL=PASS"
echo "LIVE_RUNTIME_SENTINEL=PASS"
echo "CHANGED_FILES=$MAIN_TARGET,$CSS_TARGET"
echo "CSS_SHA256=$FINAL_SHA"
echo "BUSINESS_LOGIC_CHANGED=NO"
echo "COMMIT_CREATED=NO"
echo "PUSH_PERFORMED=NO"
echo "READY_FOR_VISUAL_REVIEW=YES"
echo "--- GIT STATUS ---"
printf '%s\n' "$FINAL_STATUS"
