#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/var/www/TOS}"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_APPEND="$PATCH_DIR/dashboard-dark-consistency-v6.append.css"
MAIN_TARGET="frontend/src/main.jsx"
DASHBOARD_TARGET="frontend/src/pages/Dashboard.jsx"
CSS_TARGET="frontend/src/styles/dashboard-github-reference.css"
EXPECTED_MAIN_HEAD_BLOB="0035c796b14f106b276d53421b8ba4bf1ae99514"
EXPECTED_DASHBOARD_HEAD_BLOB="3eeac204cf77a4be4114580a5232d4437268db1a"
EXPECTED_V5_CSS_SHA256="d9cb775980baaf27d32c28badfac4256d4d5b547c3dff2b5c8873b0248127d8d"
EXPECTED_APPEND_SHA256="c4329a89eb828fd9dfce88d2dcbc29671a2c8b84c00721129fa6909870067e8f"
IMPORT_LINE='import "./styles/dashboard-github-reference.css";'
ROOT_BEFORE='<div className="mx-auto w-full max-w-[1560px] space-y-4 p-4 sm:p-5 lg:space-y-5 lg:p-6">'
ROOT_AFTER='<div className="tos-dashboard-page mx-auto w-full max-w-[1560px] space-y-4 p-4 sm:p-5 lg:space-y-5 lg:p-6">'
START_MARKER='TOS_PHASE01_DASHBOARD_DARK_CONSISTENCY_V6_START'
END_MARKER='TOS_PHASE01_DASHBOARD_DARK_CONSISTENCY_V6_END'

fail() {
  echo "PHASE01_DASHBOARD_DARK_V6=FAIL"
  echo "ERROR=$1" >&2
  exit "${2:-1}"
}

[ -d "$ROOT/.git" ] || fail "TOS repository not found at $ROOT" 2
[ -f "$SOURCE_APPEND" ] || fail "Missing V6 source append" 3
[ -f "$ROOT/$MAIN_TARGET" ] || fail "Missing $MAIN_TARGET" 4
[ -f "$ROOT/$DASHBOARD_TARGET" ] || fail "Missing $DASHBOARD_TARGET" 5
[ -f "$ROOT/$CSS_TARGET" ] || fail "Missing Phase 01 stylesheet" 6

HEAD="$(git -C "$ROOT" rev-parse HEAD)"
MAIN_HEAD_BLOB="$(git -C "$ROOT" rev-parse "HEAD:$MAIN_TARGET")"
DASHBOARD_HEAD_BLOB="$(git -C "$ROOT" rev-parse "HEAD:$DASHBOARD_TARGET")"
echo "TOS_HEAD=$HEAD"
echo "MAIN_HEAD_BLOB=$MAIN_HEAD_BLOB"
echo "DASHBOARD_HEAD_BLOB=$DASHBOARD_HEAD_BLOB"
[ "$MAIN_HEAD_BLOB" = "$EXPECTED_MAIN_HEAD_BLOB" ] || fail "Committed main.jsx baseline changed; regenerate" 7
[ "$DASHBOARD_HEAD_BLOB" = "$EXPECTED_DASHBOARD_HEAD_BLOB" ] || fail "Committed Dashboard.jsx baseline changed; regenerate" 8

APPEND_SHA="$(sha256sum "$SOURCE_APPEND" | awk '{print $1}')"
echo "V6_APPEND_SHA256=$APPEND_SHA"
[ "$APPEND_SHA" = "$EXPECTED_APPEND_SHA256" ] || fail "V6 append checksum mismatch" 9

[ "$(grep -Fxc "$IMPORT_LINE" "$ROOT/$MAIN_TARGET" || true)" = "1" ] || fail "Expected exactly one Dashboard CSS import" 10

STATUS="$(git -C "$ROOT" status --porcelain=v1 --untracked-files=all)"
PATHS="$(printf '%s\n' "$STATUS" | sed '/^$/d' | cut -c4- | sort -u)"
V5_PATHS="$(printf '%s\n%s\n' "$MAIN_TARGET" "$CSS_TARGET" | sort)"
V6_PATHS="$(printf '%s\n%s\n%s\n' "$MAIN_TARGET" "$DASHBOARD_TARGET" "$CSS_TARGET" | sort)"

if [ "$PATHS" = "$V5_PATHS" ]; then
  CURRENT_CSS_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"
  echo "CURRENT_CSS_SHA256=$CURRENT_CSS_SHA"
  [ "$CURRENT_CSS_SHA" = "$EXPECTED_V5_CSS_SHA256" ] || fail "Dashboard CSS is not exact V5 baseline" 11

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

  printf '\n' >> "$ROOT/$CSS_TARGET"
  cat "$SOURCE_APPEND" >> "$ROOT/$CSS_TARGET"
  PATCH_ACTION="APPLIED_V6"
elif [ "$PATHS" = "$V6_PATHS" ]; then
  PATCH_ACTION="VALIDATED_EXISTING_V6"
else
  echo "--- PRE-EXISTING STATUS ---"
  printf '%s\n' "$STATUS"
  fail "Unexpected working-tree state; do not reset/stash" 12
fi

if printf '%s\n' "$(git -C "$ROOT" status --porcelain=v1 --untracked-files=all)" | grep -Eq '^[^ ?]|^.[^ M?]'; then
  fail "Unexpected staged/status state" 13
fi

[ "$(grep -Fxc "$ROOT_AFTER" "$ROOT/$DASHBOARD_TARGET" || true)" = "1" ] || fail "Dedicated Dashboard root class missing" 14
[ "$(grep -Fc "$START_MARKER" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V6 start marker missing/duplicate" 15
[ "$(grep -Fc "$END_MARKER" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V6 end marker missing/duplicate" 16

git -C "$ROOT" diff --check -- "$MAIN_TARGET" "$DASHBOARD_TARGET" "$CSS_TARGET"

cd "$ROOT/frontend"
npm run build
cd "$ROOT"

FINAL_STATUS="$(git status --porcelain=v1 --untracked-files=all)"
FINAL_PATHS="$(printf '%s\n' "$FINAL_STATUS" | sed '/^$/d' | cut -c4- | sort -u)"
[ "$FINAL_PATHS" = "$V6_PATHS" ] || {
  echo "--- UNEXPECTED FINAL STATUS ---"
  printf '%s\n' "$FINAL_STATUS"
  fail "Unexpected files changed after V6/build" 17
}

[ "$(git diff --numstat -- "$MAIN_TARGET")" = $'1\t0\tfrontend/src/main.jsx' ] || fail "main.jsx diff changed unexpectedly" 18
[ "$(git diff --numstat -- "$DASHBOARD_TARGET")" = $'1\t1\tfrontend/src/pages/Dashboard.jsx' ] || fail "Dashboard.jsx diff is not exact root-class change" 19

FINAL_CSS_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"
echo "PHASE01_DASHBOARD_DARK_V6=PASS"
echo "SCREEN=Dashboard"
echo "PATCH_ACTION=$PATCH_ACTION"
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
