#!/usr/bin/env bash
set -euo pipefail

echo "RUNNING=PHASE04_1_DESIGN_QUEUE_FLAGSHIP_V5_RECOVERY"

ROOT="${1:-/var/www/TOS}"
DESIGN_TARGET="frontend/src/pages/DesignQueuePage.jsx"
WORKHUB_TARGET="frontend/src/pages/EmployeeWorkHub.jsx"
TEAM_TARGET="frontend/src/pages/TeamPage.jsx"
PERF_TARGET="frontend/src/pages/TeamPerformanceDashboard.jsx"
CSS_TARGET="frontend/src/index.css"

DESIGN_SHA="d1a7d362d18506582e61f2a6f552fb88793bebd8174c3b6d60c74a3214a9cb3c"
WORKHUB_SHA="d86f5553b002b6fd89328c90ab5c369050595cee87695200d89f77a74d292e43"
TEAM_SHA="d14814aca4482d8c89d7a8a734125703f5b6123f58ccfff7368878ca94b67efe"
PERF_SHA="36dc277b800dc03129d8fc7feefc7b877906eb6ee9a73712805237326262bcaf"
CSS_SHA="9e0d0d1c8e762731ea0fb5c8408c5a8e96ac02cb671482bee1c031d76b06fc53"

RUNTIMES=("--tos-phase04-runtime" "--tos-phase04-v2-runtime" "--tos-dq-v3-runtime" "--tos-dq-v4-runtime" "--tos-dq-v5-runtime")
DESIGN_HOOK="tos-core-design-queue-premium"

DIST="$ROOT/frontend/dist"
LIVE_PARENT="/opt/apps/tamiyouz-front"
LIVE="$LIVE_PARENT/build"
STAMP="$(date +%Y%m%d-%H%M%S)"
STAGE="$LIVE_PARENT/build.phase04-1-design-queue-v5-recovery.new.$$"
BACKUP="$LIVE_PARENT/build.phase04-1-design-queue-v5-recovery.backup-$STAMP"

fail(){ echo "PHASE04_1_DESIGN_QUEUE_FLAGSHIP_V5_RECOVERY=FAIL"; echo "ERROR=$1" >&2; exit "${2:-1}"; }
sha256(){ sha256sum "$ROOT/$1" | awk '{print $1}'; }

[ -d "$ROOT/.git" ] || fail "TOS repository not found" 2
for path in "$DESIGN_TARGET" "$WORKHUB_TARGET" "$TEAM_TARGET" "$PERF_TARGET" "$CSS_TARGET"; do
  [ -f "$ROOT/$path" ] || fail "Missing target: $path" 3
done
[ -d "$LIVE" ] || fail "Live frontend root missing" 4

git -C "$ROOT" diff --cached --quiet || fail "Staged changes exist; stop" 5

CURRENT_CHANGED="$(git -C "$ROOT" diff --name-only | sort)"
EXPECTED_CHANGED="$(printf '%s\n' "$CSS_TARGET" "$DESIGN_TARGET" "$WORKHUB_TARGET" "$PERF_TARGET" "$TEAM_TARGET" | sort)"
[ "$CURRENT_CHANGED" = "$EXPECTED_CHANGED" ] || fail "Unexpected worktree shape" 6

[ "$(sha256 "$DESIGN_TARGET")" = "$DESIGN_SHA" ] || fail "Design Queue hash mismatch" 7
[ "$(sha256 "$WORKHUB_TARGET")" = "$WORKHUB_SHA" ] || fail "THRS hash mismatch" 8
[ "$(sha256 "$TEAM_TARGET")" = "$TEAM_SHA" ] || fail "Team hash mismatch" 9
[ "$(sha256 "$PERF_TARGET")" = "$PERF_SHA" ] || fail "Team Performance hash mismatch" 10
[ "$(sha256 "$CSS_TARGET")" = "$CSS_SHA" ] || fail "index.css is not the verified post-V5 state" 11

for runtime in "${RUNTIMES[@]}"; do
  [ "$(grep -Fc -- "$runtime" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "Runtime missing/duplicated: $runtime" 12
done
[ "$(grep -Fc -- "$DESIGN_HOOK" "$ROOT/$DESIGN_TARGET" || true)" = "2" ] || fail "Design Queue premium hooks missing" 13

git -C "$ROOT" diff --check -- "$CSS_TARGET" "$DESIGN_TARGET" "$WORKHUB_TARGET" "$TEAM_TARGET" "$PERF_TARGET"

cd "$ROOT/frontend"
npm run build
cd "$ROOT"

[ -f "$DIST/index.html" ] || fail "Built dist index missing" 14
grep -RFlq -- "--tos-dq-v5-runtime" "$DIST/assets" || fail "V5 runtime missing from dist" 15
grep -RFlq -- "$DESIGN_HOOK" "$DIST/assets" || fail "Design Queue hook missing from dist" 16

rm -rf "$STAGE"
mkdir -p "$STAGE"
cp -a "$DIST/." "$STAGE/"
[ -f "$STAGE/index.html" ] || fail "Staged index missing" 17
grep -RFlq -- "--tos-dq-v5-runtime" "$STAGE/assets" || fail "V5 runtime missing from staged assets" 18

mv "$LIVE" "$BACKUP"
if ! mv "$STAGE" "$LIVE"; then
  mv "$BACKUP" "$LIVE" || true
  fail "Failed to activate V5 recovery; rollback attempted" 19
fi
if ! grep -RFlq -- "--tos-dq-v5-runtime" "$LIVE/assets"; then
  rm -rf "$LIVE"
  mv "$BACKUP" "$LIVE" || true
  fail "Live V5 runtime missing; rolled back" 20
fi
systemctl is-active --quiet nginx || fail "Nginx inactive after deploy" 21

git -C "$ROOT" diff --cached --quiet || fail "Unexpected staged changes" 22
POST_CHANGED="$(git -C "$ROOT" diff --name-only | sort)"
[ "$POST_CHANGED" = "$EXPECTED_CHANGED" ] || fail "Unexpected tracked files changed" 23

[ "$(sha256 "$DESIGN_TARGET")" = "$DESIGN_SHA" ] || fail "Design Queue changed during recovery" 24
[ "$(sha256 "$CSS_TARGET")" = "$CSS_SHA" ] || fail "index.css changed during recovery" 25

echo "PHASE04_1_DESIGN_QUEUE_FLAGSHIP_V5_RECOVERY=PASS"
echo "V5_SOURCE_ALREADY_PRESENT=YES"
echo "SOURCE_FILES_CHANGED_BY_RECOVERY=NO"
echo "BUILD_RESULT=PASS"
echo "LIVE_DEPLOY=PASS"
echo "DESIGN_QUEUE_SHA256=$(sha256 "$DESIGN_TARGET")"
echo "INDEX_CSS_SHA256=$(sha256 "$CSS_TARGET")"
echo "NO_COMMIT_OR_PUSH=YES"
echo "--- GIT STATUS ---"
git -C "$ROOT" status --short
