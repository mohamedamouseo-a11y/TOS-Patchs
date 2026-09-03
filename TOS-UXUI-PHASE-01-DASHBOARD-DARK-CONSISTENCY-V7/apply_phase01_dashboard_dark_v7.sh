#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/var/www/TOS}"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_REPO_ROOT="$(cd "$PATCH_DIR/.." && pwd)"
SOURCE_APPEND="$PATCH_DIR/dashboard-dark-consistency-v7.append.css"
V6_APPEND="$PATCH_REPO_ROOT/TOS-UXUI-PHASE-01-DASHBOARD-DARK-CONSISTENCY-V6/dashboard-dark-consistency-v6.append.css"
MAIN_TARGET="frontend/src/main.jsx"
DASHBOARD_TARGET="frontend/src/pages/Dashboard.jsx"
CSS_TARGET="frontend/src/styles/dashboard-github-reference.css"
EXPECTED_MAIN_HEAD_BLOB="0035c796b14f106b276d53421b8ba4bf1ae99514"
EXPECTED_DASHBOARD_HEAD_BLOB="3eeac204cf77a4be4114580a5232d4437268db1a"
EXPECTED_V5_CSS_SHA256="d9cb775980baaf27d32c28badfac4256d4d5b547c3dff2b5c8873b0248127d8d"
IMPORT_LINE='import "./styles/dashboard-github-reference.css";'
ROOT_BEFORE='<div className="mx-auto w-full max-w-[1560px] space-y-4 p-4 sm:p-5 lg:space-y-5 lg:p-6">'
ROOT_CLASS='tos-dashboard-page mx-auto w-full max-w-[1560px] space-y-4 p-4 sm:p-5 lg:space-y-5 lg:p-6'
V6_START='TOS_PHASE01_DASHBOARD_DARK_CONSISTENCY_V6_START'
V6_END='TOS_PHASE01_DASHBOARD_DARK_CONSISTENCY_V6_END'
V7_START='TOS_PHASE01_DASHBOARD_DARK_CONSISTENCY_V7_START'
V7_END='TOS_PHASE01_DASHBOARD_DARK_CONSISTENCY_V7_END'

fail() {
  echo "PHASE01_DASHBOARD_DARK_V7=FAIL"
  echo "ERROR=$1" >&2
  exit "${2:-1}"
}

[ -d "$ROOT/.git" ] || fail "TOS repository not found at $ROOT" 2
[ -d "$PATCH_REPO_ROOT/.git" ] || fail "TOS-Patchs repository not found" 3
[ -f "$SOURCE_APPEND" ] || fail "Missing V7 source append" 4
[ -f "$V6_APPEND" ] || fail "Missing V6 source append used for recovery validation" 5
[ -f "$ROOT/$MAIN_TARGET" ] || fail "Missing $MAIN_TARGET" 6
[ -f "$ROOT/$DASHBOARD_TARGET" ] || fail "Missing $DASHBOARD_TARGET" 7
[ -f "$ROOT/$CSS_TARGET" ] || fail "Missing Phase 01 stylesheet" 8

# Validate the patch sources against the pulled TOS-Patchs HEAD.
for source in "$SOURCE_APPEND" "$V6_APPEND"; do
  rel="${source#$PATCH_REPO_ROOT/}"
  work_blob="$(git -C "$PATCH_REPO_ROOT" hash-object "$source")"
  head_blob="$(git -C "$PATCH_REPO_ROOT" rev-parse "HEAD:$rel")"
  [ "$work_blob" = "$head_blob" ] || fail "Patch source differs from TOS-Patchs HEAD: $rel" 9
done

HEAD="$(git -C "$ROOT" rev-parse HEAD)"
MAIN_HEAD_BLOB="$(git -C "$ROOT" rev-parse "HEAD:$MAIN_TARGET")"
DASHBOARD_HEAD_BLOB="$(git -C "$ROOT" rev-parse "HEAD:$DASHBOARD_TARGET")"
echo "TOS_HEAD=$HEAD"
echo "MAIN_HEAD_BLOB=$MAIN_HEAD_BLOB"
echo "DASHBOARD_HEAD_BLOB=$DASHBOARD_HEAD_BLOB"
[ "$MAIN_HEAD_BLOB" = "$EXPECTED_MAIN_HEAD_BLOB" ] || fail "Committed main.jsx baseline changed; regenerate" 10
[ "$DASHBOARD_HEAD_BLOB" = "$EXPECTED_DASHBOARD_HEAD_BLOB" ] || fail "Committed Dashboard.jsx baseline changed; regenerate" 11
[ "$(grep -Fxc "$IMPORT_LINE" "$ROOT/$MAIN_TARGET" || true)" = "1" ] || fail "Expected exactly one Dashboard CSS import" 12

git -C "$ROOT" diff --cached --quiet || fail "Staged changes exist; stop without reset/stash" 13

STATUS="$(git -C "$ROOT" status --porcelain=v1 --untracked-files=all)"
PATHS="$(printf '%s\n' "$STATUS" | sed '/^$/d' | cut -c4- | sort -u)"
V5_PATHS="$(printf '%s\n%s\n' "$MAIN_TARGET" "$CSS_TARGET" | sort)"
V6_PATHS="$(printf '%s\n%s\n%s\n' "$MAIN_TARGET" "$DASHBOARD_TARGET" "$CSS_TARGET" | sort)"
[ "$PATHS" = "$V5_PATHS" ] || [ "$PATHS" = "$V6_PATHS" ] || {
  echo "--- PRE-EXISTING STATUS ---"
  printf '%s\n' "$STATUS"
  fail "Unexpected working-tree state; do not reset/stash" 14
}

# Add the dedicated Dashboard root class if it is not already present.
if grep -Fq "$ROOT_CLASS" "$ROOT/$DASHBOARD_TARGET"; then
  ROOT_ACTION="VALIDATED_EXISTING_ROOT_CLASS"
else
  python3 - "$ROOT/$DASHBOARD_TARGET" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
s = p.read_text(encoding="utf-8")
before = '<div className="mx-auto w-full max-w-[1560px] space-y-4 p-4 sm:p-5 lg:space-y-5 lg:p-6">'
after = '<div className="tos-dashboard-page mx-auto w-full max-w-[1560px] space-y-4 p-4 sm:p-5 lg:space-y-5 lg:p-6">'
if s.count(before) != 1:
    raise SystemExit(f"DASHBOARD_ROOT_MATCH_COUNT={s.count(before)}")
p.write_text(s.replace(before, after, 1), encoding="utf-8", newline="\n")
PY
  ROOT_ACTION="ADDED_ROOT_CLASS"
fi

grep -Fq "$ROOT_CLASS" "$ROOT/$DASHBOARD_TARGET" || fail "Dedicated Dashboard root class verification failed" 15

V6_START_COUNT="$(grep -Fc "$V6_START" "$ROOT/$CSS_TARGET" || true)"
V6_END_COUNT="$(grep -Fc "$V6_END" "$ROOT/$CSS_TARGET" || true)"
V7_START_COUNT="$(grep -Fc "$V7_START" "$ROOT/$CSS_TARGET" || true)"
V7_END_COUNT="$(grep -Fc "$V7_END" "$ROOT/$CSS_TARGET" || true)"

[ "$V6_START_COUNT" = "$V6_END_COUNT" ] || fail "Partial V6 CSS marker state" 16
[ "$V7_START_COUNT" = "$V7_END_COUNT" ] || fail "Partial V7 CSS marker state" 17
[ "$V6_START_COUNT" -le 1 ] && [ "$V7_START_COUNT" -le 1 ] || fail "Duplicate V6/V7 CSS markers" 18

if [ "$V7_START_COUNT" = "1" ]; then
  python3 - "$ROOT/$CSS_TARGET" "$SOURCE_APPEND" <<'PY'
from pathlib import Path
import sys
target = Path(sys.argv[1]).read_text(encoding="utf-8").rstrip()
append = Path(sys.argv[2]).read_text(encoding="utf-8").rstrip()
if not target.endswith(append):
    raise SystemExit("V7 append content does not match package source")
PY
  CSS_ACTION="VALIDATED_EXISTING_V7"
elif [ "$V6_START_COUNT" = "1" ]; then
  python3 - "$ROOT/$CSS_TARGET" "$V6_APPEND" <<'PY'
from pathlib import Path
import sys
target = Path(sys.argv[1]).read_text(encoding="utf-8").rstrip()
append = Path(sys.argv[2]).read_text(encoding="utf-8").rstrip()
if not target.endswith(append):
    raise SystemExit("Existing V6 append content does not match package source")
PY
  CSS_ACTION="VALIDATED_EXISTING_V6"
else
  CURRENT_CSS_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"
  echo "CURRENT_CSS_SHA256=$CURRENT_CSS_SHA"
  [ "$CURRENT_CSS_SHA" = "$EXPECTED_V5_CSS_SHA256" ] || fail "Dashboard CSS is not exact V5 baseline" 19
  printf '\n' >> "$ROOT/$CSS_TARGET"
  cat "$SOURCE_APPEND" >> "$ROOT/$CSS_TARGET"
  CSS_ACTION="APPENDED_V7"
fi

# CSS must now contain one trusted dedicated-scope correction, V6 or V7.
if [ "$(grep -Fc "$V7_START" "$ROOT/$CSS_TARGET" || true)" = "1" ]; then
  grep -Fq '.dark .tos-dashboard-page .tos-premium-card' "$ROOT/$CSS_TARGET" || fail "V7 scoped Card selector missing" 20
elif [ "$(grep -Fc "$V6_START" "$ROOT/$CSS_TARGET" || true)" = "1" ]; then
  grep -Fq '.dark .tos-dashboard-page .tos-premium-card' "$ROOT/$CSS_TARGET" || fail "V6 scoped Card selector missing" 21
else
  fail "No dedicated Dashboard dark correction found" 22
fi

git -C "$ROOT" diff --check -- "$MAIN_TARGET" "$DASHBOARD_TARGET"

FINAL_PATHS_BEFORE_BUILD="$(git -C "$ROOT" status --porcelain=v1 --untracked-files=all | sed '/^$/d' | cut -c4- | sort -u)"
[ "$FINAL_PATHS_BEFORE_BUILD" = "$V6_PATHS" ] || fail "Unexpected files after V7 apply/recovery" 23

cd "$ROOT/frontend"
npm run build
cd "$ROOT"

FINAL_STATUS="$(git status --porcelain=v1 --untracked-files=all)"
FINAL_PATHS="$(printf '%s\n' "$FINAL_STATUS" | sed '/^$/d' | cut -c4- | sort -u)"
[ "$FINAL_PATHS" = "$V6_PATHS" ] || {
  echo "--- UNEXPECTED FINAL STATUS ---"
  printf '%s\n' "$FINAL_STATUS"
  fail "Build introduced unexpected files" 24
}

[ "$(git diff --numstat -- "$MAIN_TARGET")" = $'1\t0\tfrontend/src/main.jsx' ] || fail "main.jsx diff changed unexpectedly" 25
[ "$(git diff --numstat -- "$DASHBOARD_TARGET")" = $'1\t1\tfrontend/src/pages/Dashboard.jsx' ] || fail "Dashboard.jsx diff is not exact root-class change" 26

FINAL_CSS_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"
echo "PHASE01_DASHBOARD_DARK_V7=PASS"
echo "SCREEN=Dashboard"
echo "ROOT_ACTION=$ROOT_ACTION"
echo "CSS_ACTION=$CSS_ACTION"
echo "BUILD_RESULT=PASS"
echo "CHANGED_FILES=$MAIN_TARGET,$DASHBOARD_TARGET,$CSS_TARGET"
echo "CSS_SHA256=$FINAL_CSS_SHA"
echo "DARK_SCOPE=DEDICATED_TOS_DASHBOARD_PAGE_CLASS"
echo "LIGHT_MODE_CHANGED=NO"
echo "BUSINESS_LOGIC_CHANGED=NO"
echo "RAMZY_CHANGED=NO"
echo "TCS_CHANGED=NO"
echo "COMMIT_CREATED=NO"
echo "PUSH_PERFORMED=NO"
echo "READY_FOR_VISUAL_REVIEW=YES"
echo "--- GIT STATUS ---"
printf '%s\n' "$FINAL_STATUS"
