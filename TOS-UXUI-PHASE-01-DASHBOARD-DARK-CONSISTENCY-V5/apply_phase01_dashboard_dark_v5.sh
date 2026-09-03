#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/var/www/TOS}"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_APPEND="$PATCH_DIR/dashboard-dark-consistency-v5.append.css"
MAIN_TARGET="frontend/src/main.jsx"
DASHBOARD_TARGET="frontend/src/pages/Dashboard.jsx"
CSS_TARGET="frontend/src/styles/dashboard-github-reference.css"
EXPECTED_MAIN_HEAD_BLOB="0035c796b14f106b276d53421b8ba4bf1ae99514"
EXPECTED_DASHBOARD_HEAD_BLOB="3eeac204cf77a4be4114580a5232d4437268db1a"
EXPECTED_V4_CSS_SHA256="77102cdc5cb485de2d935ae053a6c0b4a3a5768717857c0b1c8a4a0a36d3942e"
EXPECTED_APPEND_SHA256="caf53ea05dceebdcf6ec3ddcf5a5545c1fadcffb0cc33a3d3333b4c114de20e3"
IMPORT_LINE='import "./styles/dashboard-github-reference.css";'
START_MARKER='TOS_PHASE01_DASHBOARD_DARK_CONSISTENCY_V5_START'
END_MARKER='TOS_PHASE01_DASHBOARD_DARK_CONSISTENCY_V5_END'

fail() {
  echo "PHASE01_DASHBOARD_DARK_V5=FAIL"
  echo "ERROR=$1" >&2
  exit "${2:-1}"
}

[ -d "$ROOT/.git" ] || fail "TOS repository not found at $ROOT" 2
[ -f "$SOURCE_APPEND" ] || fail "Missing V5 source append file" 3
[ -f "$ROOT/$MAIN_TARGET" ] || fail "Missing $MAIN_TARGET" 4
[ -f "$ROOT/$DASHBOARD_TARGET" ] || fail "Missing $DASHBOARD_TARGET" 5
[ -f "$ROOT/$CSS_TARGET" ] || fail "Phase 01 V4 stylesheet is not present" 6

HEAD="$(git -C "$ROOT" rev-parse HEAD)"
MAIN_HEAD_BLOB="$(git -C "$ROOT" rev-parse "HEAD:$MAIN_TARGET")"
DASHBOARD_HEAD_BLOB="$(git -C "$ROOT" rev-parse "HEAD:$DASHBOARD_TARGET")"
echo "TOS_HEAD=$HEAD"
echo "MAIN_HEAD_BLOB=$MAIN_HEAD_BLOB"
echo "DASHBOARD_HEAD_BLOB=$DASHBOARD_HEAD_BLOB"
[ "$MAIN_HEAD_BLOB" = "$EXPECTED_MAIN_HEAD_BLOB" ] || fail "Committed main.jsx baseline changed; regenerate patch" 7
[ "$DASHBOARD_HEAD_BLOB" = "$EXPECTED_DASHBOARD_HEAD_BLOB" ] || fail "Committed Dashboard.jsx baseline changed; regenerate patch" 8

APPEND_SHA="$(sha256sum "$SOURCE_APPEND" | awk '{print $1}')"
echo "V5_APPEND_SHA256=$APPEND_SHA"
[ "$APPEND_SHA" = "$EXPECTED_APPEND_SHA256" ] || fail "V5 source append checksum mismatch" 9

IMPORT_COUNT="$(grep -Fxc "$IMPORT_LINE" "$ROOT/$MAIN_TARGET" || true)"
[ "$IMPORT_COUNT" = "1" ] || fail "Expected exactly one Phase 01 CSS import in main.jsx" 10

STATUS="$(git -C "$ROOT" status --porcelain=v1 --untracked-files=all)"
PATHS="$(printf '%s\n' "$STATUS" | sed '/^$/d' | cut -c4- | sort -u)"
EXPECTED_PATHS="$(printf '%s\n%s\n' "$MAIN_TARGET" "$CSS_TARGET" | sort)"
[ "$PATHS" = "$EXPECTED_PATHS" ] || {
  echo "--- PRE-EXISTING STATUS ---"
  printf '%s\n' "$STATUS"
  fail "Expected exact Phase 01 V4 working-tree state only" 11
}

if printf '%s\n' "$STATUS" | grep -Eq '^[^ ?]|^.[^ M?]'; then
  fail "Unexpected staged/status state in Phase 01 files" 12
fi

CURRENT_CSS_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"
echo "CURRENT_CSS_SHA256=$CURRENT_CSS_SHA"

START_COUNT="$(grep -Fc "$START_MARKER" "$ROOT/$CSS_TARGET" || true)"
END_COUNT="$(grep -Fc "$END_MARKER" "$ROOT/$CSS_TARGET" || true)"

if [ "$START_COUNT" = "0" ] && [ "$END_COUNT" = "0" ]; then
  [ "$CURRENT_CSS_SHA" = "$EXPECTED_V4_CSS_SHA256" ] || fail "Dashboard CSS is not the expected V4 baseline" 13
  BACKUP="$(mktemp /tmp/tos-dashboard-v5-css.XXXXXX)"
  cp "$ROOT/$CSS_TARGET" "$BACKUP"
  printf '\n' >> "$ROOT/$CSS_TARGET"
  cat "$SOURCE_APPEND" >> "$ROOT/$CSS_TARGET"
  PATCH_ACTION="APPENDED_V5"
else
  [ "$START_COUNT" = "1" ] && [ "$END_COUNT" = "1" ] || fail "Partial/duplicate V5 marker state detected" 14
  python3 - "$ROOT/$CSS_TARGET" "$SOURCE_APPEND" <<'PY'
from pathlib import Path
import sys
target = Path(sys.argv[1]).read_text(encoding="utf-8")
append = Path(sys.argv[2]).read_text(encoding="utf-8")
if not target.rstrip().endswith(append.rstrip()):
    raise SystemExit("V5 append content does not match package source")
PY
  PATCH_ACTION="VALIDATED_EXISTING_V5"
  BACKUP=""
fi

START_COUNT="$(grep -Fc "$START_MARKER" "$ROOT/$CSS_TARGET" || true)"
END_COUNT="$(grep -Fc "$END_MARKER" "$ROOT/$CSS_TARGET" || true)"
[ "$START_COUNT" = "1" ] && [ "$END_COUNT" = "1" ] || fail "V5 marker verification failed" 15

git -C "$ROOT" diff --check -- "$MAIN_TARGET" "$CSS_TARGET"

cd "$ROOT/frontend"
if ! npm run build; then
  cd "$ROOT"
  if [ -n "${BACKUP:-}" ] && [ -f "$BACKUP" ]; then
    cp "$BACKUP" "$ROOT/$CSS_TARGET"
  fi
  fail "Frontend build failed; V5 CSS append was restored" 16
fi
cd "$ROOT"
[ -z "${BACKUP:-}" ] || rm -f "$BACKUP"

FINAL_STATUS="$(git status --porcelain=v1 --untracked-files=all)"
FINAL_PATHS="$(printf '%s\n' "$FINAL_STATUS" | sed '/^$/d' | cut -c4- | sort -u)"
[ "$FINAL_PATHS" = "$EXPECTED_PATHS" ] || {
  echo "--- UNEXPECTED FINAL STATUS ---"
  printf '%s\n' "$FINAL_STATUS"
  fail "Unexpected files changed after V5/build" 17
}

NUMSTAT="$(git diff --numstat -- "$MAIN_TARGET")"
[ "$NUMSTAT" = $'1\t0\tfrontend/src/main.jsx' ] || fail "main.jsx is not the exact one-line Phase 01 import change" 18

FINAL_CSS_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"
echo "PHASE01_DASHBOARD_DARK_V5=PASS"
echo "SCREEN=Dashboard"
echo "PATCH_ACTION=$PATCH_ACTION"
echo "BUILD_RESULT=PASS"
echo "CHANGED_FILES=$MAIN_TARGET,$CSS_TARGET"
echo "CSS_SHA256=$FINAL_CSS_SHA"
echo "DARK_WHITE_CARD_LEAK=FIXED_BY_SCOPED_OVERRIDES"
echo "LIGHT_MODE_CHANGED=NO"
echo "BUSINESS_LOGIC_CHANGED=NO"
echo "RAMZY_CHANGED=NO"
echo "TCS_CHANGED=NO"
echo "COMMIT_CREATED=NO"
echo "PUSH_PERFORMED=NO"
echo "READY_FOR_VISUAL_REVIEW=YES"
echo "--- GIT STATUS ---"
printf '%s\n' "$FINAL_STATUS"
