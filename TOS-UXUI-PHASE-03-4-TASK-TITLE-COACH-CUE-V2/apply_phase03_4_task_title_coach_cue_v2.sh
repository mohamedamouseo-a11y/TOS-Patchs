#!/usr/bin/env bash
set -euo pipefail

echo "RUNNING=PHASE03_4_TASK_TITLE_COACH_CUE_V2"

ROOT="${1:-/var/www/TOS}"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_REPO_ROOT="$(cd "$PATCH_DIR/.." && pwd)"
SOURCE_CSS="$PATCH_DIR/task-title-coach-cue-v2.css"

BOARD_TARGET="frontend/src/components/ProfessionalTaskBoard.jsx"
WORKSPACE_TARGET="frontend/src/pages/MyTaskWorkspace.jsx"
CSS_TARGET="frontend/src/styles/tasks-projects-premium-reference.css"
PARTS_TARGET="frontend/src/features/tasks/taskBoardParts.jsx"

V31_RUNTIME='--tos-task-details-declutter-v1-runtime'
V32_RUNTIME='--tos-task-details-minimal-v1-runtime'
V33_RUNTIME='--tos-task-title-disclosure-cue-v1-runtime'
V34_RUNTIME='--tos-task-title-coach-cue-v1-runtime'
V34R_RUNTIME='--tos-task-title-coach-cue-v2-runtime'
AUTOFIT_HOOK='tos-task-title-autofit'
POINTER_HOOK='tos-task-coach-pointer'
COACH_STORAGE='tos.taskDetails.coach.v1'

DIST="$ROOT/frontend/dist"
LIVE_PARENT="/opt/apps/tamiyouz-front"
LIVE="$LIVE_PARENT/build"
STAMP="$(date +%Y%m%d-%H%M%S)"
STAGE="$LIVE_PARENT/build.phase03-4-title-coach-v2.new.$$"
BACKUP="$LIVE_PARENT/build.phase03-4-title-coach-v2.backup-$STAMP"

fail() {
  echo "PHASE03_4_TASK_TITLE_COACH_CUE_V2=FAIL"
  echo "ERROR=$1" >&2
  exit "${2:-1}"
}

[ -d "$ROOT/.git" ] || fail "TOS repository not found" 2
[ -d "$PATCH_REPO_ROOT/.git" ] || fail "TOS-Patchs repository not found" 3
[ -f "$SOURCE_CSS" ] || fail "V2 recovery CSS missing" 4
for path in "$BOARD_TARGET" "$WORKSPACE_TARGET" "$CSS_TARGET" "$PARTS_TARGET"; do
  [ -f "$ROOT/$path" ] || fail "Missing target: $path" 5
done
[ -d "$LIVE" ] || fail "Live frontend root missing" 6

git -C "$ROOT" diff --cached --quiet || fail "Staged changes exist; stop" 7

PRE_CHANGED="$(git -C "$ROOT" diff --name-only | sort)"
while IFS= read -r path; do
  [ -z "$path" ] && continue
  case "$path" in
    "$BOARD_TARGET"|"$WORKSPACE_TARGET"|"$CSS_TARGET"|"$PARTS_TARGET") ;;
    *) fail "Unexpected tracked change before Phase 03.4 V2: $path" 8 ;;
  esac
done <<< "$PRE_CHANGED"

[ "$(grep -Fc -- "$V31_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "Phase 03.1 runtime missing or duplicated" 9
[ "$(grep -Fc -- "$V32_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "Phase 03.2 runtime missing or duplicated" 10
[ "$(grep -Fc -- "$V33_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "Phase 03.3 runtime missing or duplicated" 11
[ "$(grep -Fc -- "$V34_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "Phase 03.4 V1 partial runtime missing or duplicated" 12
[ "$(grep -Fc -- "$AUTOFIT_HOOK" "$ROOT/$BOARD_TARGET" || true)" = "1" ] || fail "Auto-fit title hook missing or duplicated" 13
[ "$(grep -Fc -- "$POINTER_HOOK" "$ROOT/$BOARD_TARGET" || true)" = "2" ] || fail "Coach pointer hooks missing or duplicated" 14
[ "$(grep -Fc -- "$COACH_STORAGE" "$ROOT/$BOARD_TARGET" || true)" -ge "1" ] || fail "Coach persistence logic missing" 15

SOURCE_REL="${SOURCE_CSS#$PATCH_REPO_ROOT/}"
[ "$(git -C "$PATCH_REPO_ROOT" hash-object "$SOURCE_CSS")" = "$(git -C "$PATCH_REPO_ROOT" rev-parse "HEAD:$SOURCE_REL")" ] || fail "V2 CSS differs from TOS-Patchs HEAD" 16

V2_COUNT="$(grep -Fc -- "$V34R_RUNTIME" "$ROOT/$CSS_TARGET" || true)"
HAND_COUNT="$(grep -Fc -- 'HandPointer' "$ROOT/$BOARD_TARGET" || true)"
INLINE_COUNT="$(grep -Fc -- 'tos-coach-hand-vector-v2' "$ROOT/$BOARD_TARGET" || true)"

if [ "$V2_COUNT" = "0" ] && [ "$HAND_COUNT" = "3" ] && [ "$INLINE_COUNT" = "0" ]; then
  python3 - "$ROOT/$BOARD_TARGET" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text()

import_old = '  HandPointer,\n'
if text.count(import_old) != 1:
    raise SystemExit(f'HandPointer import count={text.count(import_old)}')
text = text.replace(import_old, '', 1)

use_old = '<HandPointer size={17} strokeWidth={2.2} />'
if text.count(use_old) != 2:
    raise SystemExit(f'HandPointer JSX use count={text.count(use_old)}')

# Dependency-free vector hand. It inherits currentColor and is deliberately
# local to the coach bubble, so no lucide-react export is required.
use_new = '''<svg className="tos-coach-hand-vector-v2" viewBox="0 0 24 24" width="17" height="17" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
                      <path d="M9 11V5.7a1.45 1.45 0 0 1 2.9 0V10" />
                      <path d="M11.9 10V4.7a1.45 1.45 0 0 1 2.9 0v5.6" />
                      <path d="M14.8 10.3V6.1a1.4 1.4 0 0 1 2.8 0v5.6" />
                      <path d="M17.6 11.7V8.5a1.35 1.35 0 0 1 2.7 0v5.2c0 4.2-2.7 7.3-7 7.3h-1.1c-2.4 0-4.3-1-5.7-3L3.8 14a1.45 1.45 0 0 1 2.3-1.7L9 15.1V11" />
                    </svg>'''
text = text.replace(use_old, use_new)

path.write_text(text)
PY

  printf '\n' >> "$ROOT/$CSS_TARGET"
  cat "$SOURCE_CSS" >> "$ROOT/$CSS_TARGET"
  PATCH_ACTION="RECOVERED_FAILED_V1"
elif [ "$V2_COUNT" = "1" ] && [ "$HAND_COUNT" = "0" ] && [ "$INLINE_COUNT" = "2" ]; then
  PATCH_ACTION="VALIDATED_EXISTING"
else
  echo "V2_COUNT=$V2_COUNT"
  echo "HAND_COUNT=$HAND_COUNT"
  echo "INLINE_COUNT=$INLINE_COUNT"
  fail "Unexpected/partial Phase 03.4 V2 recovery state" 17
fi

[ "$(grep -Fc -- "$V34R_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V2 runtime missing or duplicated" 18
[ "$(grep -Fc -- 'HandPointer' "$ROOT/$BOARD_TARGET" || true)" = "0" ] || fail "Unsupported HandPointer dependency still present" 19
[ "$(grep -Fc -- 'tos-coach-hand-vector-v2' "$ROOT/$BOARD_TARGET" || true)" = "2" ] || fail "Inline coach hand vectors missing or duplicated" 20
[ "$(grep -Fc -- "$AUTOFIT_HOOK" "$ROOT/$BOARD_TARGET" || true)" = "1" ] || fail "Auto-fit title hook changed" 21
[ "$(grep -Fc -- "$POINTER_HOOK" "$ROOT/$BOARD_TARGET" || true)" = "2" ] || fail "Coach pointer hooks changed" 22

git -C "$ROOT" diff --check -- "$BOARD_TARGET" "$WORKSPACE_TARGET" "$CSS_TARGET" "$PARTS_TARGET"

cd "$ROOT/frontend"
npm run build
cd "$ROOT"

[ -f "$DIST/index.html" ] || fail "Built dist index missing" 23
grep -RFlq -- "$V34R_RUNTIME" "$DIST/assets" || fail "V2 runtime missing from dist assets" 24
grep -RFlq -- "$AUTOFIT_HOOK" "$DIST/assets" || fail "Auto-fit title hook missing from dist assets" 25
grep -RFlq -- "$POINTER_HOOK" "$DIST/assets" || fail "Coach pointer hook missing from dist assets" 26
grep -RFlq -- 'tos-coach-hand-vector-v2' "$DIST/assets" || fail "Inline coach hand vector missing from dist assets" 27
if grep -RFlq -- 'HandPointer' "$DIST/assets"; then fail "Unsupported HandPointer leaked into built assets" 28; fi

rm -rf "$STAGE"
mkdir -p "$STAGE"
cp -a "$DIST/." "$STAGE/"
[ -f "$STAGE/index.html" ] || fail "Staged index missing" 29
grep -RFlq -- "$V34R_RUNTIME" "$STAGE/assets" || fail "V2 runtime missing from staged assets" 30

mv "$LIVE" "$BACKUP"
if ! mv "$STAGE" "$LIVE"; then
  mv "$BACKUP" "$LIVE" || true
  fail "Failed to activate Phase 03.4 V2 build; rollback attempted" 31
fi
if ! grep -RFlq -- "$V34R_RUNTIME" "$LIVE/assets"; then
  rm -rf "$LIVE"
  mv "$BACKUP" "$LIVE" || true
  fail "Live V2 runtime missing; rolled back" 32
fi

POST_CHANGED="$(git -C "$ROOT" diff --name-only | sort)"
while IFS= read -r path; do
  [ -z "$path" ] && continue
  case "$path" in
    "$BOARD_TARGET"|"$WORKSPACE_TARGET"|"$CSS_TARGET"|"$PARTS_TARGET") ;;
    *) fail "Unexpected tracked change after Phase 03.4 V2: $path" 33 ;;
  esac
done <<< "$POST_CHANGED"

git -C "$ROOT" diff --cached --quiet || fail "Unexpected staged changes after V2" 34

BOARD_SHA="$(sha256sum "$ROOT/$BOARD_TARGET" | awk '{print $1}')"
WORKSPACE_SHA="$(sha256sum "$ROOT/$WORKSPACE_TARGET" | awk '{print $1}')"
CSS_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"
PARTS_SHA="$(sha256sum "$ROOT/$PARTS_TARGET" | awk '{print $1}')"

echo "PHASE03_4_TASK_TITLE_COACH_CUE_V2=PASS"
echo "SCREEN=Task_Details"
echo "FIX=Unsupported_HandPointer_replaced_with_dependency_free_vector"
echo "PATCH_ACTION=$PATCH_ACTION"
echo "TITLE_AUTOFIT=PRESERVED"
echo "FIRST_TIME_COACH=PRESERVED"
echo "BUSINESS_LOGIC_CHANGED=NO"
echo "BUILD_RESULT=PASS"
echo "LIVE_DEPLOY=PASS"
echo "BOARD_SHA256=$BOARD_SHA"
echo "MY_WORKSPACE_SHA256=$WORKSPACE_SHA"
echo "TASKS_CSS_SHA256=$CSS_SHA"
echo "TASK_BOARD_PARTS_SHA256=$PARTS_SHA"
echo "NO_COMMIT_OR_PUSH=YES"
echo "--- GIT STATUS ---"
git -C "$ROOT" status --short
