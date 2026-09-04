#!/usr/bin/env bash
set -euo pipefail

echo "RUNNING=PHASE04_CORE_DAILY_SCREENS_BATCH_V1"

ROOT="${1:-/var/www/TOS}"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_REPO_ROOT="$(cd "$PATCH_DIR/.." && pwd)"
SOURCE_CSS="$PATCH_DIR/core-daily-screens-premium-v1.css"

DESIGN_TARGET="frontend/src/pages/DesignQueuePage.jsx"
WORKHUB_TARGET="frontend/src/pages/EmployeeWorkHub.jsx"
TEAM_TARGET="frontend/src/pages/TeamPage.jsx"
PERF_TARGET="frontend/src/pages/TeamPerformanceDashboard.jsx"
CSS_TARGET="frontend/src/index.css"

DESIGN_BASE="91a4704e63942334e2fd793cdeff481b0d1ef7a5"
WORKHUB_BASE="8c7b50d880e6c8349a5b624e4c0f0b0deb1638bf"
TEAM_BASE="bff8ae1e93dfbb84b1470b462139a1616afa1aca"
PERF_BASE="af64ba534c0d8597d026cd32e1f4bbd8d73bc0ca"
CSS_BASE="408bf676ce3647a43647b7c53c102d6f175fe91c"

DESIGN_HOOK="tos-core-design-queue-premium"
WORKHUB_HOOK="tos-core-workhub-premium"
TEAM_HOOK="tos-core-team-premium"
PERF_HOOK="tos-core-team-performance-premium"
RUNTIME="--tos-phase04-runtime"

DIST="$ROOT/frontend/dist"
LIVE_PARENT="/opt/apps/tamiyouz-front"
LIVE="$LIVE_PARENT/build"
STAMP="$(date +%Y%m%d-%H%M%S)"
STAGE="$LIVE_PARENT/build.phase04-core-daily-v1.new.$$"
BACKUP="$LIVE_PARENT/build.phase04-core-daily-v1.backup-$STAMP"

fail() {
  echo "PHASE04_CORE_DAILY_SCREENS_BATCH_V1=FAIL"
  echo "ERROR=$1" >&2
  exit "${2:-1}"
}

[ -d "$ROOT/.git" ] || fail "TOS repository not found" 2
[ -d "$PATCH_REPO_ROOT/.git" ] || fail "TOS-Patchs repository not found" 3
[ -f "$SOURCE_CSS" ] || fail "Phase 04 CSS source missing" 4
for path in "$DESIGN_TARGET" "$WORKHUB_TARGET" "$TEAM_TARGET" "$PERF_TARGET" "$CSS_TARGET"; do
  [ -f "$ROOT/$path" ] || fail "Missing target: $path" 5
done
[ -d "$LIVE" ] || fail "Live frontend root missing" 6

git -C "$ROOT" diff --cached --quiet || fail "Staged changes exist; stop" 7
[ -z "$(git -C "$ROOT" status --short)" ] || fail "TOS worktree must be clean after the user's Push before Phase 04" 8

SOURCE_REL="${SOURCE_CSS#$PATCH_REPO_ROOT/}"
[ "$(git -C "$PATCH_REPO_ROOT" hash-object "$SOURCE_CSS")" = "$(git -C "$PATCH_REPO_ROOT" rev-parse "HEAD:$SOURCE_REL")" ] || fail "Phase 04 CSS differs from TOS-Patchs HEAD" 9

RUNTIME_COUNT="$(grep -Fc -- "$RUNTIME" "$ROOT/$CSS_TARGET" || true)"
DESIGN_COUNT="$(grep -Fc -- "$DESIGN_HOOK" "$ROOT/$DESIGN_TARGET" || true)"
WORKHUB_COUNT="$(grep -Fc -- "$WORKHUB_HOOK" "$ROOT/$WORKHUB_TARGET" || true)"
TEAM_COUNT="$(grep -Fc -- "$TEAM_HOOK" "$ROOT/$TEAM_TARGET" || true)"
PERF_COUNT="$(grep -Fc -- "$PERF_HOOK" "$ROOT/$PERF_TARGET" || true)"

if [ "$RUNTIME_COUNT" = "0" ] && [ "$DESIGN_COUNT" = "0" ] && [ "$WORKHUB_COUNT" = "0" ] && [ "$TEAM_COUNT" = "0" ] && [ "$PERF_COUNT" = "0" ]; then
  [ "$(git -C "$ROOT" hash-object "$ROOT/$DESIGN_TARGET")" = "$DESIGN_BASE" ] || fail "Design Queue source is not the pushed Phase 04 base" 10
  [ "$(git -C "$ROOT" hash-object "$ROOT/$WORKHUB_TARGET")" = "$WORKHUB_BASE" ] || fail "Employee Work Hub source is not the pushed Phase 04 base" 11
  [ "$(git -C "$ROOT" hash-object "$ROOT/$TEAM_TARGET")" = "$TEAM_BASE" ] || fail "Team source is not the pushed Phase 04 base" 12
  [ "$(git -C "$ROOT" hash-object "$ROOT/$PERF_TARGET")" = "$PERF_BASE" ] || fail "Team Performance source is not the pushed Phase 04 base" 13
  [ "$(git -C "$ROOT" hash-object "$ROOT/$CSS_TARGET")" = "$CSS_BASE" ] || fail "index.css is not the pushed Phase 04 base" 14

  python3 - "$ROOT/$DESIGN_TARGET" "$ROOT/$WORKHUB_TARGET" "$ROOT/$TEAM_TARGET" "$ROOT/$PERF_TARGET" <<'PY'
from pathlib import Path
import sys

design_path, workhub_path, team_path, perf_path = map(Path, sys.argv[1:])

# Design Queue has one main state and one detail-workspace state using the same shell.
text = design_path.read_text()
old = '<div className="space-y-4 p-4 text-start sm:p-5" dir={isAr ? "rtl" : "ltr"}>'
if text.count(old) != 2:
    raise SystemExit(f'Design Queue root anchor count={text.count(old)}')
text = text.replace(old, '<div className="tos-core-design-queue-premium space-y-4 p-4 text-start sm:p-5" dir={isAr ? "rtl" : "ltr"}>')
design_path.write_text(text)

# Employee Work Hub main page shell.
text = workhub_path.read_text()
old = '<div dir={isAr ? "rtl" : "ltr"} className="tos-page text-start">'
if text.count(old) != 1:
    raise SystemExit(f'Employee Work Hub root anchor count={text.count(old)}')
text = text.replace(old, '<div dir={isAr ? "rtl" : "ltr"} className="tos-page tos-core-workhub-premium text-start">', 1)
workhub_path.write_text(text)

# Team main page only; do not style the separate permissions full-page route as Team Members.
text = team_path.read_text()
marker = 'export function TeamPage({ user, inviteSignal = 0 }) {'
pos = text.find(marker)
if pos < 0:
    raise SystemExit('TeamPage export anchor missing')
head, tail = text[:pos], text[pos:]
old = '<div className="tos-page">'
if old not in tail:
    raise SystemExit('TeamPage root anchor missing')
tail = tail.replace(old, '<div className="tos-page tos-core-team-premium">', 1)
team_path.write_text(head + tail)

# Team Performance already owns a premium namespace; add the shared Phase 04 namespace beside it.
text = perf_path.read_text()
old = '<div className="tos-page tos-team-performance-premium space-y-4">'
if text.count(old) != 1:
    raise SystemExit(f'Team Performance root anchor count={text.count(old)}')
text = text.replace(old, '<div className="tos-page tos-team-performance-premium tos-core-team-performance-premium space-y-4">', 1)
perf_path.write_text(text)
PY

  printf '\n' >> "$ROOT/$CSS_TARGET"
  cat "$SOURCE_CSS" >> "$ROOT/$CSS_TARGET"
  PATCH_ACTION="APPLIED"
else
  fail "Partial or pre-existing Phase 04 state detected; stop instead of stacking styles" 15
fi

[ "$(grep -Fc -- "$RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "Phase 04 runtime missing or duplicated" 16
[ "$(grep -Fc -- "$DESIGN_HOOK" "$ROOT/$DESIGN_TARGET" || true)" = "2" ] || fail "Design Queue premium hooks missing or duplicated" 17
[ "$(grep -Fc -- "$WORKHUB_HOOK" "$ROOT/$WORKHUB_TARGET" || true)" = "1" ] || fail "Employee Work Hub premium hook missing or duplicated" 18
[ "$(grep -Fc -- "$TEAM_HOOK" "$ROOT/$TEAM_TARGET" || true)" = "1" ] || fail "Team premium hook missing or duplicated" 19
[ "$(grep -Fc -- "$PERF_HOOK" "$ROOT/$PERF_TARGET" || true)" = "1" ] || fail "Team Performance premium hook missing or duplicated" 20

git -C "$ROOT" diff --check -- "$DESIGN_TARGET" "$WORKHUB_TARGET" "$TEAM_TARGET" "$PERF_TARGET" "$CSS_TARGET"

cd "$ROOT/frontend"
npm run build
cd "$ROOT"

[ -f "$DIST/index.html" ] || fail "Built dist index missing" 21
grep -RFlq -- "$RUNTIME" "$DIST/assets" || fail "Phase 04 CSS runtime missing from dist" 22
for hook in "$DESIGN_HOOK" "$WORKHUB_HOOK" "$TEAM_HOOK" "$PERF_HOOK"; do
  grep -RFlq -- "$hook" "$DIST/assets" || fail "Premium hook missing from dist: $hook" 23
done

rm -rf "$STAGE"
mkdir -p "$STAGE"
cp -a "$DIST/." "$STAGE/"
[ -f "$STAGE/index.html" ] || fail "Staged index missing" 24
grep -RFlq -- "$RUNTIME" "$STAGE/assets" || fail "Phase 04 runtime missing from staged assets" 25

mv "$LIVE" "$BACKUP"
if ! mv "$STAGE" "$LIVE"; then
  mv "$BACKUP" "$LIVE" || true
  fail "Failed to activate Phase 04 build; rollback attempted" 26
fi
if ! grep -RFlq -- "$RUNTIME" "$LIVE/assets"; then
  rm -rf "$LIVE"
  mv "$BACKUP" "$LIVE" || true
  fail "Live Phase 04 runtime missing; rolled back" 27
fi

systemctl is-active --quiet nginx || fail "Nginx is not active after deploy" 28

git -C "$ROOT" diff --cached --quiet || fail "Unexpected staged changes after Phase 04" 29
POST_CHANGED="$(git -C "$ROOT" diff --name-only | sort)"
EXPECTED_CHANGED="$(printf '%s\n' "$CSS_TARGET" "$DESIGN_TARGET" "$WORKHUB_TARGET" "$PERF_TARGET" "$TEAM_TARGET" | sort)"
[ "$POST_CHANGED" = "$EXPECTED_CHANGED" ] || fail "Unexpected tracked files changed after Phase 04" 30

sha() { sha256sum "$ROOT/$1" | awk '{print $1}'; }

echo "PHASE04_CORE_DAILY_SCREENS_BATCH_V1=PASS"
echo "SCREENS=Design_Queue,Employee_Work_Hub,Team_Members,Team_Performance"
echo "PATCH_ACTION=$PATCH_ACTION"
echo "LIGHT_DARK=SUPPORTED"
echo "BUSINESS_LOGIC_CHANGED=NO"
echo "BUILD_RESULT=PASS"
echo "LIVE_DEPLOY=PASS"
echo "DESIGN_QUEUE_SHA256=$(sha "$DESIGN_TARGET")"
echo "WORKHUB_SHA256=$(sha "$WORKHUB_TARGET")"
echo "TEAM_SHA256=$(sha "$TEAM_TARGET")"
echo "TEAM_PERFORMANCE_SHA256=$(sha "$PERF_TARGET")"
echo "INDEX_CSS_SHA256=$(sha "$CSS_TARGET")"
echo "NO_COMMIT_OR_PUSH=YES"
echo "--- GIT STATUS ---"
git -C "$ROOT" status --short
