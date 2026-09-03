#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/var/www/TOS}"
MAIN_TARGET="frontend/src/main.jsx"
DASHBOARD_TARGET="frontend/src/pages/Dashboard.jsx"
TWS_TARGET="frontend/src/pages/tws/TwsRecentFilesWidget.jsx"
CSS_TARGET="frontend/src/styles/dashboard-github-reference.css"

EXPECTED_MAIN_HEAD_BLOB="0035c796b14f106b276d53421b8ba4bf1ae99514"
EXPECTED_DASHBOARD_HEAD_BLOB="3eeac204cf77a4be4114580a5232d4437268db1a"
EXPECTED_TWS_HEAD_BLOB="ae39b3864ca7cf67432945ff9102af0610e06fc8"
EXPECTED_V8_CSS_SHA256="2b00d2629167a9f0844fb87d396d00be72733cb0ff915d6ecfb6c1a4d9b5da1e"
IMPORT_LINE='import "./styles/dashboard-github-reference.css";'

fail() {
  echo "PHASE01_DASHBOARD_DARK_V9=FAIL"
  echo "ERROR=$1" >&2
  exit "${2:-1}"
}

[ -d "$ROOT/.git" ] || fail "TOS repository not found at $ROOT" 2
[ -f "$ROOT/$MAIN_TARGET" ] || fail "Missing $MAIN_TARGET" 3
[ -f "$ROOT/$DASHBOARD_TARGET" ] || fail "Missing $DASHBOARD_TARGET" 4
[ -f "$ROOT/$TWS_TARGET" ] || fail "Missing $TWS_TARGET" 5
[ -f "$ROOT/$CSS_TARGET" ] || fail "Missing Phase 01 stylesheet" 6

git -C "$ROOT" diff --cached --quiet || fail "Staged changes exist; stop without reset/stash" 7

[ "$(git -C "$ROOT" rev-parse "HEAD:$MAIN_TARGET")" = "$EXPECTED_MAIN_HEAD_BLOB" ] || fail "Committed main.jsx baseline changed" 8
[ "$(git -C "$ROOT" rev-parse "HEAD:$DASHBOARD_TARGET")" = "$EXPECTED_DASHBOARD_HEAD_BLOB" ] || fail "Committed Dashboard.jsx baseline changed" 9
[ "$(git -C "$ROOT" rev-parse "HEAD:$TWS_TARGET")" = "$EXPECTED_TWS_HEAD_BLOB" ] || fail "Committed TWS widget baseline changed" 10
[ "$(grep -Fxc "$IMPORT_LINE" "$ROOT/$MAIN_TARGET" || true)" = "1" ] || fail "Expected one Dashboard CSS import" 11

STATUS="$(git -C "$ROOT" status --porcelain=v1 --untracked-files=all)"
PATHS="$(printf '%s\n' "$STATUS" | sed '/^$/d' | cut -c4- | sort -u)"
V8_PATHS="$(printf '%s\n%s\n%s\n' "$MAIN_TARGET" "$DASHBOARD_TARGET" "$CSS_TARGET" | sort)"
V9_PATHS="$(printf '%s\n%s\n%s\n%s\n' "$MAIN_TARGET" "$DASHBOARD_TARGET" "$TWS_TARGET" "$CSS_TARGET" | sort)"

if [ "$PATHS" = "$V8_PATHS" ]; then
  CURRENT_CSS_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"
  echo "CURRENT_CSS_SHA256=$CURRENT_CSS_SHA"
  [ "$CURRENT_CSS_SHA" = "$EXPECTED_V8_CSS_SHA256" ] || fail "Dashboard CSS is not exact V8 baseline" 12

  [ "$(grep -Fc 'tos-dashboard-dark-card' "$ROOT/$DASHBOARD_TARGET" || true)" = "5" ] || fail "Expected five V8 Dashboard card classes" 13
  [ "$(grep -Fc 'className="tos-dashboard-tws"' "$ROOT/$DASHBOARD_TARGET" || true)" = "1" ] || fail "Expected V8 TWS wrapper" 14

  python3 - "$ROOT/$DASHBOARD_TARGET" "$ROOT/$TWS_TARGET" <<'PY'
from pathlib import Path
import sys

dash_path = Path(sys.argv[1])
tws_path = Path(sys.argv[2])

dash = dash_path.read_text(encoding="utf-8")
open_tag = '<Card className="tos-dashboard-dark-card rounded-[22px] border-zinc-200/70 bg-white/95 p-5 shadow-sm dark:border-white/10 dark:bg-white/[0.035]">'
new_open = '<section className="tos-dashboard-dark-card rounded-[22px] border border-zinc-200/70 bg-white/95 p-5 shadow-sm dark:border-white/10 dark:bg-white/[0.035]">'
if dash.count(open_tag) != 5:
    raise SystemExit(f"DASHBOARD_CARD_OPEN_COUNT={dash.count(open_tag)}")
if dash.count('</Card>') != 5:
    raise SystemExit(f"DASHBOARD_CARD_CLOSE_COUNT={dash.count('</Card>')}")
dash = dash.replace(open_tag, new_open)
dash = dash.replace('</Card>', '</section>')
old_tws = '<div className="tos-dashboard-tws"><TwsRecentFilesWidget /></div>'
new_tws = '<div className="tos-dashboard-tws"><TwsRecentFilesWidget dashboardSurface /></div>'
if dash.count(old_tws) != 1:
    raise SystemExit(f"DASHBOARD_TWS_CALL_COUNT={dash.count(old_tws)}")
dash = dash.replace(old_tws, new_tws, 1)
dash_path.write_text(dash, encoding="utf-8", newline="\n")

tws = tws_path.read_text(encoding="utf-8")
old_sig = 'export function TwsRecentFilesWidget({ onOpenDocument }) {'
new_sig = 'export function TwsRecentFilesWidget({ onOpenDocument, dashboardSurface = false }) {'
if tws.count(old_sig) != 1:
    raise SystemExit(f"TWS_SIGNATURE_COUNT={tws.count(old_sig)}")
tws = tws.replace(old_sig, new_sig, 1)
old_guard = '  if (!loading && items.length === 0) return null;\n\n  return (\n    <Card className="p-5">'
new_guard = '  if (!loading && items.length === 0) return null;\n\n  const Surface = dashboardSurface ? "div" : Card;\n\n  return (\n    <Surface className={dashboardSurface ? "tos-dashboard-dark-card rounded-[22px] border border-zinc-200/70 bg-white p-5 shadow-sm dark:border-white/10 dark:bg-[#1d2b36] dark:text-white" : "p-5"}>'
if tws.count(old_guard) != 1:
    raise SystemExit(f"TWS_CARD_OPEN_COUNT={tws.count(old_guard)}")
tws = tws.replace(old_guard, new_guard, 1)
if tws.count('</Card>') != 1:
    raise SystemExit(f"TWS_CARD_CLOSE_COUNT={tws.count('</Card>')}")
tws = tws.replace('</Card>', '</Surface>', 1)
tws_path.write_text(tws, encoding="utf-8", newline="\n")
PY

  PATCH_ACTION="BYPASSED_SHARED_CARD_PRIMITIVE"
elif [ "$PATHS" = "$V9_PATHS" ]; then
  PATCH_ACTION="VALIDATED_EXISTING_V9"
else
  echo "--- PRE-EXISTING STATUS ---"
  printf '%s\n' "$STATUS"
  fail "Unexpected working-tree state; do not reset/stash" 15
fi

[ "$(grep -Fc '<section className="tos-dashboard-dark-card' "$ROOT/$DASHBOARD_TARGET" || true)" = "5" ] || fail "Five native Dashboard surfaces not present" 16
[ "$(grep -Fc '<TwsRecentFilesWidget dashboardSurface />' "$ROOT/$DASHBOARD_TARGET" || true)" = "1" ] || fail "Dashboard TWS opt-in missing" 17
[ "$(grep -Fc 'dashboardSurface = false' "$ROOT/$TWS_TARGET" || true)" = "1" ] || fail "TWS dashboardSurface prop missing" 18
[ "$(grep -Fc 'const Surface = dashboardSurface ? "div" : Card;' "$ROOT/$TWS_TARGET" || true)" = "1" ] || fail "TWS surface bypass missing" 19

# V9 does not alter the Phase 01 stylesheet; V8 CSS remains the trusted scoped dark layer.
FINAL_CSS_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"
[ "$FINAL_CSS_SHA" = "$EXPECTED_V8_CSS_SHA256" ] || fail "Phase 01 CSS changed unexpectedly during V9" 20

git -C "$ROOT" diff --check -- "$MAIN_TARGET" "$DASHBOARD_TARGET" "$TWS_TARGET" "$CSS_TARGET"

cd "$ROOT/frontend"
npm run build
cd "$ROOT"

FINAL_STATUS="$(git status --porcelain=v1 --untracked-files=all)"
FINAL_PATHS="$(printf '%s\n' "$FINAL_STATUS" | sed '/^$/d' | cut -c4- | sort -u)"
[ "$FINAL_PATHS" = "$V9_PATHS" ] || {
  echo "--- UNEXPECTED FINAL STATUS ---"
  printf '%s\n' "$FINAL_STATUS"
  fail "Unexpected files changed after V9/build" 21
}

echo "PHASE01_DASHBOARD_DARK_V9=PASS"
echo "SCREEN=Dashboard"
echo "PATCH_ACTION=$PATCH_ACTION"
echo "BUILD_RESULT=PASS"
echo "CHANGED_FILES=$MAIN_TARGET,$DASHBOARD_TARGET,$TWS_TARGET,$CSS_TARGET"
echo "CSS_SHA256=$FINAL_CSS_SHA"
echo "SHARED_CARD_PRIMITIVE_BYPASSED=YES"
echo "LIGHT_MODE_CHANGED=NO"
echo "BUSINESS_LOGIC_CHANGED=NO"
echo "RAMZY_CHANGED=NO"
echo "TCS_CHANGED=NO"
echo "COMMIT_CREATED=NO"
echo "PUSH_PERFORMED=NO"
echo "READY_FOR_VISUAL_REVIEW=YES"
echo "--- GIT STATUS ---"
printf '%s\n' "$FINAL_STATUS"
