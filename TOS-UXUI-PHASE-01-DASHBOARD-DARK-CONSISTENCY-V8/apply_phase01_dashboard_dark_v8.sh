#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/var/www/TOS}"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_APPEND="$PATCH_DIR/dashboard-dark-consistency-v8.append.css"
MAIN_TARGET="frontend/src/main.jsx"
DASHBOARD_TARGET="frontend/src/pages/Dashboard.jsx"
CSS_TARGET="frontend/src/styles/dashboard-github-reference.css"
EXPECTED_MAIN_HEAD_BLOB="0035c796b14f106b276d53421b8ba4bf1ae99514"
EXPECTED_DASHBOARD_HEAD_BLOB="3eeac204cf77a4be4114580a5232d4437268db1a"
EXPECTED_V7_CSS_SHA256="051d7b1858272f37e56f802fc26cc5c348d49bf23560476d2e7b158b19f63189"
IMPORT_LINE='import "./styles/dashboard-github-reference.css";'
ROOT_CLASS='tos-dashboard-page mx-auto w-full max-w-[1560px] space-y-4 p-4 sm:p-5 lg:space-y-5 lg:p-6'
CARD_BEFORE='className="rounded-[22px] border-zinc-200/70 bg-white/95 p-5 shadow-sm dark:border-white/10 dark:bg-white/[0.035]"'
CARD_AFTER='className="tos-dashboard-dark-card rounded-[22px] border-zinc-200/70 bg-white/95 p-5 shadow-sm dark:border-white/10 dark:bg-white/[0.035]"'
TWS_BEFORE='<div><TwsRecentFilesWidget /></div>'
TWS_AFTER='<div className="tos-dashboard-tws"><TwsRecentFilesWidget /></div>'
V8_START='TOS_PHASE01_DASHBOARD_DARK_CONSISTENCY_V8_START'
V8_END='TOS_PHASE01_DASHBOARD_DARK_CONSISTENCY_V8_END'

fail() {
  echo "PHASE01_DASHBOARD_DARK_V8=FAIL"
  echo "ERROR=$1" >&2
  exit "${2:-1}"
}

[ -d "$ROOT/.git" ] || fail "TOS repository not found at $ROOT" 2
[ -f "$SOURCE_APPEND" ] || fail "Missing V8 CSS source" 3
[ -f "$ROOT/$MAIN_TARGET" ] || fail "Missing $MAIN_TARGET" 4
[ -f "$ROOT/$DASHBOARD_TARGET" ] || fail "Missing $DASHBOARD_TARGET" 5
[ -f "$ROOT/$CSS_TARGET" ] || fail "Missing Phase 01 stylesheet" 6

git -C "$ROOT" diff --cached --quiet || fail "Staged changes exist" 7

MAIN_HEAD_BLOB="$(git -C "$ROOT" rev-parse "HEAD:$MAIN_TARGET")"
DASHBOARD_HEAD_BLOB="$(git -C "$ROOT" rev-parse "HEAD:$DASHBOARD_TARGET")"
[ "$MAIN_HEAD_BLOB" = "$EXPECTED_MAIN_HEAD_BLOB" ] || fail "Committed main.jsx baseline changed" 8
[ "$DASHBOARD_HEAD_BLOB" = "$EXPECTED_DASHBOARD_HEAD_BLOB" ] || fail "Committed Dashboard.jsx baseline changed" 9
[ "$(grep -Fxc "$IMPORT_LINE" "$ROOT/$MAIN_TARGET" || true)" = "1" ] || fail "Expected one Dashboard CSS import" 10
grep -Fq "$ROOT_CLASS" "$ROOT/$DASHBOARD_TARGET" || fail "V7 Dashboard root class missing" 11

STATUS="$(git -C "$ROOT" status --porcelain=v1 --untracked-files=all)"
PATHS="$(printf '%s\n' "$STATUS" | sed '/^$/d' | cut -c4- | sort -u)"
EXPECTED_PATHS="$(printf '%s\n%s\n%s\n' "$MAIN_TARGET" "$DASHBOARD_TARGET" "$CSS_TARGET" | sort)"
[ "$PATHS" = "$EXPECTED_PATHS" ] || {
  echo "--- PRE-EXISTING STATUS ---"
  printf '%s\n' "$STATUS"
  fail "Expected exact Phase 01 V7 working-tree state only" 12
}

V8_START_COUNT="$(grep -Fc "$V8_START" "$ROOT/$CSS_TARGET" || true)"
V8_END_COUNT="$(grep -Fc "$V8_END" "$ROOT/$CSS_TARGET" || true)"
[ "$V8_START_COUNT" = "$V8_END_COUNT" ] || fail "Partial V8 marker state" 13
[ "$V8_START_COUNT" -le 1 ] || fail "Duplicate V8 marker state" 14

if [ "$V8_START_COUNT" = "0" ]; then
  CURRENT_CSS_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"
  echo "CURRENT_CSS_SHA256=$CURRENT_CSS_SHA"
  [ "$CURRENT_CSS_SHA" = "$EXPECTED_V7_CSS_SHA256" ] || fail "Dashboard CSS is not exact V7 baseline" 15

  python3 - "$ROOT/$DASHBOARD_TARGET" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
s = p.read_text(encoding='utf-8')
old = 'className="rounded-[22px] border-zinc-200/70 bg-white/95 p-5 shadow-sm dark:border-white/10 dark:bg-white/[0.035]"'
new = 'className="tos-dashboard-dark-card rounded-[22px] border-zinc-200/70 bg-white/95 p-5 shadow-sm dark:border-white/10 dark:bg-white/[0.035]"'
count = s.count(old)
if count != 5:
    raise SystemExit(f"DASHBOARD_CARD_MATCH_COUNT={count}")
s = s.replace(old, new)
old_tws = '<div><TwsRecentFilesWidget /></div>'
new_tws = '<div className="tos-dashboard-tws"><TwsRecentFilesWidget /></div>'
if s.count(old_tws) != 1:
    raise SystemExit(f"TWS_WRAPPER_MATCH_COUNT={s.count(old_tws)}")
s = s.replace(old_tws, new_tws, 1)
p.write_text(s, encoding='utf-8', newline='\n')
PY

  printf '\n' >> "$ROOT/$CSS_TARGET"
  cat "$SOURCE_APPEND" >> "$ROOT/$CSS_TARGET"
  PATCH_ACTION="APPLIED_V8"
else
  PATCH_ACTION="VALIDATED_EXISTING_V8"
fi

[ "$(grep -Fc 'tos-dashboard-dark-card' "$ROOT/$DASHBOARD_TARGET" || true)" = "5" ] || fail "Expected five dedicated Dashboard card classes" 16
[ "$(grep -Fc 'className="tos-dashboard-tws"' "$ROOT/$DASHBOARD_TARGET" || true)" = "1" ] || fail "TWS Dashboard wrapper class missing" 17
[ "$(grep -Fc "$V8_START" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V8 CSS marker missing" 18

git -C "$ROOT" diff --check -- "$MAIN_TARGET" "$DASHBOARD_TARGET" "$CSS_TARGET"

cd "$ROOT/frontend"
npm run build
cd "$ROOT"

FINAL_STATUS="$(git status --porcelain=v1 --untracked-files=all)"
FINAL_PATHS="$(printf '%s\n' "$FINAL_STATUS" | sed '/^$/d' | cut -c4- | sort -u)"
[ "$FINAL_PATHS" = "$EXPECTED_PATHS" ] || {
  echo "--- UNEXPECTED FINAL STATUS ---"
  printf '%s\n' "$FINAL_STATUS"
  fail "Unexpected files changed after V8/build" 19
}

FINAL_CSS_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"
echo "PHASE01_DASHBOARD_DARK_V8=PASS"
echo "SCREEN=Dashboard"
echo "PATCH_ACTION=$PATCH_ACTION"
echo "BUILD_RESULT=PASS"
echo "CHANGED_FILES=$MAIN_TARGET,$DASHBOARD_TARGET,$CSS_TARGET"
echo "CSS_SHA256=$FINAL_CSS_SHA"
echo "DARK_CARD_SCOPE=DEDICATED_CLASSES_WITH_HIGH_SPECIFICITY"
echo "BUSINESS_LOGIC_CHANGED=NO"
echo "RAMZY_CHANGED=NO"
echo "TCS_CHANGED=NO"
echo "COMMIT_CREATED=NO"
echo "PUSH_PERFORMED=NO"
echo "READY_FOR_VISUAL_REVIEW=YES"
echo "--- GIT STATUS ---"
printf '%s\n' "$FINAL_STATUS"
