#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/var/www/TOS}"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_REPO_ROOT="$(cd "$PATCH_DIR/.." && pwd)"
SOURCE_CSS="$PATCH_REPO_ROOT/TOS-UXUI-PHASE-01-DASHBOARD-GITHUB-REFERENCE-V1/dashboard-github-reference.css"
MAIN_TARGET="frontend/src/main.jsx"
DASHBOARD_TARGET="frontend/src/pages/Dashboard.jsx"
APP_TARGET="frontend/src/App.jsx"
CSS_TARGET="frontend/src/styles/dashboard-github-reference.css"
EXPECTED_MAIN_HEAD_BLOB="0035c796b14f106b276d53421b8ba4bf1ae99514"
EXPECTED_DASHBOARD_HEAD_BLOB="3eeac204cf77a4be4114580a5232d4437268db1a"
EXPECTED_SOURCE_CSS_SHA256="77102cdc5cb485de2d935ae053a6c0b4a3a5768717857c0b1c8a4a0a36d3942e"
IMPORT_LINE='import "./styles/dashboard-github-reference.css";'

fail() {
  echo "PHASE01_DASHBOARD_V4=FAIL"
  echo "ERROR=$1" >&2
  exit "${2:-1}"
}

[ -d "$ROOT/.git" ] || fail "TOS repository not found at $ROOT" 2
[ -d "$PATCH_REPO_ROOT/.git" ] || fail "TOS-Patchs repository not found" 3
[ -f "$ROOT/$MAIN_TARGET" ] || fail "Missing $MAIN_TARGET" 4
[ -f "$ROOT/$DASHBOARD_TARGET" ] || fail "Missing $DASHBOARD_TARGET" 5
[ -f "$ROOT/$APP_TARGET" ] || fail "Missing $APP_TARGET" 6
[ -f "$SOURCE_CSS" ] || fail "Missing source stylesheet" 7

HEAD="$(git -C "$ROOT" rev-parse HEAD)"
echo "TOS_HEAD=$HEAD"

# V4 intentionally does not pin the whole repository HEAD. Unrelated TOS work may advance
# between phases. Instead, guard the exact files/DOM contract this Dashboard patch depends on.
MAIN_HEAD_BLOB="$(git -C "$ROOT" rev-parse "HEAD:$MAIN_TARGET")"
DASHBOARD_HEAD_BLOB="$(git -C "$ROOT" rev-parse "HEAD:$DASHBOARD_TARGET")"
echo "MAIN_HEAD_BLOB=$MAIN_HEAD_BLOB"
echo "DASHBOARD_HEAD_BLOB=$DASHBOARD_HEAD_BLOB"
[ "$MAIN_HEAD_BLOB" = "$EXPECTED_MAIN_HEAD_BLOB" ] || fail "$MAIN_TARGET committed baseline changed; regenerate patch" 8
[ "$DASHBOARD_HEAD_BLOB" = "$EXPECTED_DASHBOARD_HEAD_BLOB" ] || fail "$DASHBOARD_TARGET changed; regenerate patch" 9

grep -Fq 'tos-premium-page-viewport' "$ROOT/$APP_TARGET" || fail "Dashboard viewport contract missing in App.jsx" 10
grep -Fq 'max-w-[1560px]' "$ROOT/$DASHBOARD_TARGET" || fail "Dashboard root signature changed" 11
grep -Fq 'lg:space-y-5' "$ROOT/$DASHBOARD_TARGET" || fail "Dashboard root spacing signature changed" 12

SOURCE_SHA="$(sha256sum "$SOURCE_CSS" | awk '{print $1}')"
echo "SOURCE_CSS_SHA256=$SOURCE_SHA"
[ "$SOURCE_SHA" = "$EXPECTED_SOURCE_CSS_SHA256" ] || fail "Source stylesheet checksum mismatch" 13

STATUS="$(git -C "$ROOT" status --porcelain=v1 --untracked-files=all)"
PATHS="$(printf '%s\n' "$STATUS" | sed '/^$/d' | cut -c4- | sort -u)"
EXPECTED_PATHS="$(printf '%s\n%s\n' "$MAIN_TARGET" "$CSS_TARGET" | sort)"

if [ -z "$STATUS" ]; then
  PATCH_STATE="CLEAN_BASELINE"
  PATCH_ACTION="APPLIED_NOW"

  if grep -Fq "$IMPORT_LINE" "$ROOT/$MAIN_TARGET"; then
    fail "Dashboard premium import exists in a clean tree unexpectedly" 14
  fi
  [ ! -e "$ROOT/$CSS_TARGET" ] || fail "$CSS_TARGET already exists in a clean tree unexpectedly" 15

  python3 - "$ROOT/$MAIN_TARGET" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
s = p.read_text(encoding="utf-8")
anchor = 'import "./index.css";\n'
line = 'import "./styles/dashboard-github-reference.css";\n'
if s.count(anchor) != 1:
    raise SystemExit(f"IMPORT_ANCHOR_COUNT={s.count(anchor)}")
p.write_text(s.replace(anchor, anchor + line, 1), encoding="utf-8", newline="\n")
PY

  mkdir -p "$ROOT/$(dirname "$CSS_TARGET")"
  cp "$SOURCE_CSS" "$ROOT/$CSS_TARGET"
else
  [ "$PATHS" = "$EXPECTED_PATHS" ] || {
    echo "--- PRE-EXISTING STATUS ---"
    printf '%s\n' "$STATUS"
    fail "Working tree contains unrelated or partial changes; do not reset/stash" 16
  }
  if printf '%s\n' "$STATUS" | grep -Eq '^[^ ?]|^.[^ M?]'; then
    fail "Unexpected staged/status state in intended files" 17
  fi
  PATCH_STATE="EXACT_EXISTING_PHASE01_STATE"
  PATCH_ACTION="VALIDATED_EXISTING"
fi

IMPORT_COUNT="$(grep -Fxc "$IMPORT_LINE" "$ROOT/$MAIN_TARGET" || true)"
[ "$IMPORT_COUNT" = "1" ] || fail "Expected exactly one Dashboard CSS import, found $IMPORT_COUNT" 18
[ -f "$ROOT/$CSS_TARGET" ] || fail "Dashboard stylesheet not present after apply/validation" 19
TARGET_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"
[ "$TARGET_SHA" = "$EXPECTED_SOURCE_CSS_SHA256" ] || fail "Applied stylesheet checksum mismatch" 20

git -C "$ROOT" diff --check -- "$MAIN_TARGET" "$CSS_TARGET"

POST_STATUS="$(git -C "$ROOT" status --porcelain=v1 --untracked-files=all)"
POST_PATHS="$(printf '%s\n' "$POST_STATUS" | sed '/^$/d' | cut -c4- | sort -u)"
[ "$POST_PATHS" = "$EXPECTED_PATHS" ] || {
  echo "--- UNEXPECTED STATUS BEFORE BUILD ---"
  printf '%s\n' "$POST_STATUS"
  fail "Unexpected changed files before build" 21
}

cd "$ROOT/frontend"
npm run build
cd "$ROOT"

FINAL_STATUS="$(git status --porcelain=v1 --untracked-files=all)"
FINAL_PATHS="$(printf '%s\n' "$FINAL_STATUS" | sed '/^$/d' | cut -c4- | sort -u)"
[ "$FINAL_PATHS" = "$EXPECTED_PATHS" ] || {
  echo "--- UNEXPECTED STATUS AFTER BUILD ---"
  printf '%s\n' "$FINAL_STATUS"
  fail "Build introduced unexpected tracked/untracked changes" 22
}

# Ensure main.jsx changed only by the one intended import.
NUMSTAT="$(git diff --numstat -- "$MAIN_TARGET")"
[ "$NUMSTAT" = $'1\t0\tfrontend/src/main.jsx' ] || fail "main.jsx diff is not exactly one added import line" 23

echo "PHASE01_DASHBOARD_V4=PASS"
echo "SCREEN=Dashboard"
echo "PATCH_STATE=$PATCH_STATE"
echo "PATCH_ACTION=$PATCH_ACTION"
echo "BUILD_RESULT=PASS"
echo "CHANGED_FILES=$MAIN_TARGET,$CSS_TARGET"
echo "CSS_SHA256=$TARGET_SHA"
echo "BUSINESS_LOGIC_CHANGED=NO"
echo "RAMZY_CHANGED=NO"
echo "TCS_CHANGED=NO"
echo "COMMIT_CREATED=NO"
echo "PUSH_PERFORMED=NO"
echo "READY_FOR_VISUAL_REVIEW=YES"
echo "--- GIT STATUS ---"
printf '%s\n' "$FINAL_STATUS"
echo "--- MAIN DIFF ---"
git diff -- "$MAIN_TARGET"
