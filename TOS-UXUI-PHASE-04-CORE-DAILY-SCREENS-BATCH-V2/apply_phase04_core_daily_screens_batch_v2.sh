#!/usr/bin/env bash
set -euo pipefail

echo "RUNNING=PHASE04_CORE_DAILY_SCREENS_BATCH_V2"

ROOT="${1:-/var/www/TOS}"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_REPO_ROOT="$(cd "$PATCH_DIR/.." && pwd)"
SOURCE_CSS="$PATCH_DIR/core-daily-screens-premium-v2.css"

DESIGN_TARGET="frontend/src/pages/DesignQueuePage.jsx"
WORKHUB_TARGET="frontend/src/pages/EmployeeWorkHub.jsx"
TEAM_TARGET="frontend/src/pages/TeamPage.jsx"
PERF_TARGET="frontend/src/pages/TeamPerformanceDashboard.jsx"
CSS_TARGET="frontend/src/index.css"

DESIGN_V1_SHA256="d1a7d362d18506582e61f2a6f552fb88793bebd8174c3b6d60c74a3214a9cb3c"
WORKHUB_V1_SHA256="d86f5553b002b6fd89328c90ab5c369050595cee87695200d89f77a74d292e43"
TEAM_V1_SHA256="d14814aca4482d8c89d7a8a734125703f5b6123f58ccfff7368878ca94b67efe"
PERF_V1_SHA256="36dc277b800dc03129d8fc7feefc7b877906eb6ee9a73712805237326262bcaf"
CSS_V1_SHA256="e387b81862022da2f57328533a5b7ea82d83719d75740b83ec1180b51254f068"

DESIGN_HOOK="tos-core-design-queue-premium"
WORKHUB_HOOK="tos-core-workhub-premium"
TEAM_HOOK="tos-core-team-premium"
PERF_HOOK="tos-core-team-performance-premium"
V1_RUNTIME="--tos-phase04-runtime"
V2_RUNTIME="--tos-phase04-v2-runtime"

DIST="$ROOT/frontend/dist"
LIVE_PARENT="/opt/apps/tamiyouz-front"
LIVE="$LIVE_PARENT/build"
STAMP="$(date +%Y%m%d-%H%M%S)"
STAGE="$LIVE_PARENT/build.phase04-core-daily-v2.new.$$"
BACKUP="$LIVE_PARENT/build.phase04-core-daily-v2.backup-$STAMP"

fail() {
  echo "PHASE04_CORE_DAILY_SCREENS_BATCH_V2=FAIL"
  echo "ERROR=$1" >&2
  exit "${2:-1}"
}

sha() { sha256sum "$ROOT/$1" | awk '{print $1}'; }

[ -d "$ROOT/.git" ] || fail "TOS repository not found" 2
[ -d "$PATCH_REPO_ROOT/.git" ] || fail "TOS-Patchs repository not found" 3
[ -f "$SOURCE_CSS" ] || fail "Phase 04 V2 CSS source missing" 4
for path in "$DESIGN_TARGET" "$WORKHUB_TARGET" "$TEAM_TARGET" "$PERF_TARGET" "$CSS_TARGET"; do
  [ -f "$ROOT/$path" ] || fail "Missing target: $path" 5
done
[ -d "$LIVE" ] || fail "Live frontend root missing" 6

git -C "$ROOT" diff --cached --quiet || fail "Staged changes exist; stop" 7

PRE_CHANGED="$(git -C "$ROOT" diff --name-only | sort)"
EXPECTED_CHANGED="$(printf '%s\n' "$CSS_TARGET" "$DESIGN_TARGET" "$WORKHUB_TARGET" "$PERF_TARGET" "$TEAM_TARGET" | sort)"
[ "$PRE_CHANGED" = "$EXPECTED_CHANGED" ] || fail "Phase 04 V1 modified-file set is not intact; do not reset/stash" 8

[ "$(grep -Fc -- "$V1_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "Phase 04 V1 runtime missing or duplicated" 9
[ "$(grep -Fc -- "$DESIGN_HOOK" "$ROOT/$DESIGN_TARGET" || true)" = "2" ] || fail "Design Queue V1 hooks missing or duplicated" 10
[ "$(grep -Fc -- "$WORKHUB_HOOK" "$ROOT/$WORKHUB_TARGET" || true)" = "1" ] || fail "Employee Work Hub V1 hook missing or duplicated" 11
[ "$(grep -Fc -- "$TEAM_HOOK" "$ROOT/$TEAM_TARGET" || true)" = "1" ] || fail "Team V1 hook missing or duplicated" 12
[ "$(grep -Fc -- "$PERF_HOOK" "$ROOT/$PERF_TARGET" || true)" = "1" ] || fail "Team Performance V1 hook missing or duplicated" 13

SOURCE_REL="${SOURCE_CSS#$PATCH_REPO_ROOT/}"
[ "$(git -C "$PATCH_REPO_ROOT" hash-object "$SOURCE_CSS")" = "$(git -C "$PATCH_REPO_ROOT" rev-parse "HEAD:$SOURCE_REL")" ] || fail "Phase 04 V2 CSS differs from TOS-Patchs HEAD" 14

V2_COUNT="$(grep -Fc -- "$V2_RUNTIME" "$ROOT/$CSS_TARGET" || true)"
if [ "$V2_COUNT" = "0" ]; then
  [ "$(sha "$DESIGN_TARGET")" = "$DESIGN_V1_SHA256" ] || fail "Design Queue no longer matches reviewed V1 state" 15
  [ "$(sha "$WORKHUB_TARGET")" = "$WORKHUB_V1_SHA256" ] || fail "Employee Work Hub no longer matches reviewed V1 state" 16
  [ "$(sha "$TEAM_TARGET")" = "$TEAM_V1_SHA256" ] || fail "Team no longer matches reviewed V1 state" 17
  [ "$(sha "$PERF_TARGET")" = "$PERF_V1_SHA256" ] || fail "Team Performance no longer matches reviewed V1 state" 18
  [ "$(sha "$CSS_TARGET")" = "$CSS_V1_SHA256" ] || fail "index.css no longer matches reviewed V1 state" 19

  printf '\n' >> "$ROOT/$CSS_TARGET"
  cat "$SOURCE_CSS" >> "$ROOT/$CSS_TARGET"
  PATCH_ACTION="APPLIED"
elif [ "$V2_COUNT" = "1" ]; then
  PATCH_ACTION="VALIDATED_EXISTING"
else
  fail "Phase 04 V2 runtime duplicated" 20
fi

[ "$(grep -Fc -- "$V2_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "Phase 04 V2 runtime missing after apply" 21

git -C "$ROOT" diff --check -- "$DESIGN_TARGET" "$WORKHUB_TARGET" "$TEAM_TARGET" "$PERF_TARGET" "$CSS_TARGET"

cd "$ROOT/frontend"
npm run build
cd "$ROOT"

[ -f "$DIST/index.html" ] || fail "Built dist index missing" 22
grep -RFlq -- "$V1_RUNTIME" "$DIST/assets" || fail "Phase 04 V1 runtime missing from dist" 23
grep -RFlq -- "$V2_RUNTIME" "$DIST/assets" || fail "Phase 04 V2 runtime missing from dist" 24
for hook in "$DESIGN_HOOK" "$WORKHUB_HOOK" "$TEAM_HOOK" "$PERF_HOOK"; do
  grep -RFlq -- "$hook" "$DIST/assets" || fail "Premium hook missing from dist: $hook" 25
done

rm -rf "$STAGE"
mkdir -p "$STAGE"
cp -a "$DIST/." "$STAGE/"
[ -f "$STAGE/index.html" ] || fail "Staged index missing" 26
grep -RFlq -- "$V2_RUNTIME" "$STAGE/assets" || fail "Phase 04 V2 runtime missing from staged assets" 27

mv "$LIVE" "$BACKUP"
if ! mv "$STAGE" "$LIVE"; then
  mv "$BACKUP" "$LIVE" || true
  fail "Failed to activate Phase 04 V2 build; rollback attempted" 28
fi
if ! grep -RFlq -- "$V2_RUNTIME" "$LIVE/assets"; then
  rm -rf "$LIVE"
  mv "$BACKUP" "$LIVE" || true
  fail "Live Phase 04 V2 runtime missing; rolled back" 29
fi

systemctl is-active --quiet nginx || fail "Nginx is not active after deploy" 30

git -C "$ROOT" diff --cached --quiet || fail "Unexpected staged changes after Phase 04 V2" 31
POST_CHANGED="$(git -C "$ROOT" diff --name-only | sort)"
[ "$POST_CHANGED" = "$EXPECTED_CHANGED" ] || fail "Unexpected tracked files changed after Phase 04 V2" 32

echo "PHASE04_CORE_DAILY_SCREENS_BATCH_V2=PASS"
echo "PATCH_ACTION=$PATCH_ACTION"
echo "DESIGN_QUEUE_DARK_FIX=YES"
echo "TEAM_MEMBERS_DARK_TABLE_FIX=YES"
echo "WORKHUB_DARK_HEADING_CONTRAST_FIX=YES"
echo "TEAM_PERFORMANCE_CHANGED=NO"
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
