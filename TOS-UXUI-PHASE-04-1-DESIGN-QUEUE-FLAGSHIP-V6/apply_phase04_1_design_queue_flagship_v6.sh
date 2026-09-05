#!/usr/bin/env bash
set -euo pipefail

echo "RUNNING=PHASE04_1_DESIGN_QUEUE_FLAGSHIP_V6"

ROOT="${1:-/var/www/TOS}"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_REPO_ROOT="$(cd "$PATCH_DIR/.." && pwd)"
SOURCE_CSS="$PATCH_DIR/design-queue-flagship-v6.css"

DESIGN_TARGET="frontend/src/pages/DesignQueuePage.jsx"
WORKHUB_TARGET="frontend/src/pages/EmployeeWorkHub.jsx"
TEAM_TARGET="frontend/src/pages/TeamPage.jsx"
PERF_TARGET="frontend/src/pages/TeamPerformanceDashboard.jsx"
CSS_TARGET="frontend/src/index.css"

# Exact verified post-V5 server state.
DESIGN_V5_SHA256="d1a7d362d18506582e61f2a6f552fb88793bebd8174c3b6d60c74a3214a9cb3c"
CSS_V5_SHA256="9e0d0d1c8e762731ea0fb5c8408c5a8e96ac02cb671482bee1c031d76b06fc53"
WORKHUB_SHA256="d86f5553b002b6fd89328c90ab5c369050595cee87695200d89f77a74d292e43"
TEAM_SHA256="d14814aca4482d8c89d7a8a734125703f5b6123f58ccfff7368878ca94b67efe"
PERF_SHA256="36dc277b800dc03129d8fc7feefc7b877906eb6ee9a73712805237326262bcaf"

RUNTIMES=("--tos-phase04-runtime" "--tos-phase04-v2-runtime" "--tos-dq-v3-runtime" "--tos-dq-v4-runtime" "--tos-dq-v5-runtime")
V6_RUNTIME="--tos-dq-v6-runtime"
DESIGN_HOOK="tos-core-design-queue-premium"

DIST="$ROOT/frontend/dist"
LIVE_PARENT="/opt/apps/tamiyouz-front"
LIVE="$LIVE_PARENT/build"
STAMP="$(date +%Y%m%d-%H%M%S)"
STAGE="$LIVE_PARENT/build.phase04-1-design-queue-v6.new.$$"
BACKUP="$LIVE_PARENT/build.phase04-1-design-queue-v6.backup-$STAMP"

fail(){ echo "PHASE04_1_DESIGN_QUEUE_FLAGSHIP_V6=FAIL"; echo "ERROR=$1" >&2; exit "${2:-1}"; }
sha256(){ sha256sum "$ROOT/$1" | awk '{print $1}'; }

[ -d "$ROOT/.git" ] || fail "TOS repository not found" 2
[ -d "$PATCH_REPO_ROOT/.git" ] || fail "TOS-Patchs repository not found" 3
[ -f "$SOURCE_CSS" ] || fail "V6 CSS source missing" 4
[ -d "$LIVE" ] || fail "Live frontend root missing" 5

for path in "$DESIGN_TARGET" "$WORKHUB_TARGET" "$TEAM_TARGET" "$PERF_TARGET" "$CSS_TARGET"; do
  [ -f "$ROOT/$path" ] || fail "Missing target: $path" 6
done

git -C "$ROOT" diff --cached --quiet || fail "Staged changes exist; stop" 7

CURRENT_CHANGED="$(git -C "$ROOT" diff --name-only | sort)"
EXPECTED_CHANGED="$(printf '%s\n' "$CSS_TARGET" "$DESIGN_TARGET" "$WORKHUB_TARGET" "$PERF_TARGET" "$TEAM_TARGET" | sort)"
[ "$CURRENT_CHANGED" = "$EXPECTED_CHANGED" ] || fail "Unexpected worktree shape before V6" 8

[ "$(sha256 "$DESIGN_TARGET")" = "$DESIGN_V5_SHA256" ] || fail "Design Queue JSX differs from verified V5 state" 9
[ "$(sha256 "$CSS_TARGET")" = "$CSS_V5_SHA256" ] || fail "index.css differs from verified V5 state" 10
[ "$(sha256 "$WORKHUB_TARGET")" = "$WORKHUB_SHA256" ] || fail "THRS changed unexpectedly" 11
[ "$(sha256 "$TEAM_TARGET")" = "$TEAM_SHA256" ] || fail "Team changed unexpectedly" 12
[ "$(sha256 "$PERF_TARGET")" = "$PERF_SHA256" ] || fail "Team Performance changed unexpectedly" 13

for runtime in "${RUNTIMES[@]}"; do
  [ "$(grep -Fc -- "$runtime" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "Required prior runtime missing/duplicated: $runtime" 14
done
[ "$(grep -Fc -- "$V6_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "0" ] || fail "Design Queue V6 already present" 15
[ "$(grep -Fc -- "$DESIGN_HOOK" "$ROOT/$DESIGN_TARGET" || true)" = "2" ] || fail "Design Queue premium hooks missing" 16

SOURCE_REL="${SOURCE_CSS#$PATCH_REPO_ROOT/}"
[ "$(git -C "$PATCH_REPO_ROOT" hash-object "$SOURCE_CSS")" = "$(git -C "$PATCH_REPO_ROOT" rev-parse "HEAD:$SOURCE_REL")" ] || fail "V6 CSS differs from TOS-Patchs HEAD" 17

printf '\n' >> "$ROOT/$CSS_TARGET"
cat "$SOURCE_CSS" >> "$ROOT/$CSS_TARGET"

[ "$(grep -Fc -- "$V6_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V6 runtime missing/duplicated" 18

git -C "$ROOT" diff --check -- "$CSS_TARGET" "$DESIGN_TARGET" "$WORKHUB_TARGET" "$TEAM_TARGET" "$PERF_TARGET"

cd "$ROOT/frontend"
npm run build
cd "$ROOT"

[ -f "$DIST/index.html" ] || fail "Built dist index missing" 19
grep -RFlq -- "$V6_RUNTIME" "$DIST/assets" || fail "V6 runtime missing from dist" 20
grep -RFlq -- "$DESIGN_HOOK" "$DIST/assets" || fail "Design Queue hook missing from dist" 21

rm -rf "$STAGE"
mkdir -p "$STAGE"
cp -a "$DIST/." "$STAGE/"
[ -f "$STAGE/index.html" ] || fail "Staged index missing" 22
grep -RFlq -- "$V6_RUNTIME" "$STAGE/assets" || fail "V6 runtime missing from staged assets" 23

mv "$LIVE" "$BACKUP"
if ! mv "$STAGE" "$LIVE"; then
  mv "$BACKUP" "$LIVE" || true
  fail "Failed to activate V6; rollback attempted" 24
fi
if ! grep -RFlq -- "$V6_RUNTIME" "$LIVE/assets"; then
  rm -rf "$LIVE"
  mv "$BACKUP" "$LIVE" || true
  fail "Live V6 runtime missing; rolled back" 25
fi
systemctl is-active --quiet nginx || fail "Nginx inactive after deploy" 26

git -C "$ROOT" diff --cached --quiet || fail "Unexpected staged changes after V6" 27
POST_CHANGED="$(git -C "$ROOT" diff --name-only | sort)"
[ "$POST_CHANGED" = "$EXPECTED_CHANGED" ] || fail "Unexpected tracked files changed after V6" 28

[ "$(sha256 "$DESIGN_TARGET")" = "$DESIGN_V5_SHA256" ] || fail "Design Queue JSX changed unexpectedly" 29
[ "$(sha256 "$WORKHUB_TARGET")" = "$WORKHUB_SHA256" ] || fail "THRS changed unexpectedly after V6" 30
[ "$(sha256 "$TEAM_TARGET")" = "$TEAM_SHA256" ] || fail "Team changed unexpectedly after V6" 31
[ "$(sha256 "$PERF_TARGET")" = "$PERF_SHA256" ] || fail "Team Performance changed unexpectedly after V6" 32

POST_CSS_SHA256="$(sha256 "$CSS_TARGET")"

echo "PHASE04_1_DESIGN_QUEUE_FLAGSHIP_V6=PASS"
echo "SCREEN=Design_Queue_ONLY"
echo "BUSINESS_LOGIC_CHANGED=NO"
echo "BUILD_RESULT=PASS"
echo "LIVE_DEPLOY=PASS"
echo "DESIGN_QUEUE_SHA256=$(sha256 "$DESIGN_TARGET")"
echo "INDEX_CSS_SHA256=$POST_CSS_SHA256"
echo "OTHER_PHASE04_SCREENS_TOUCHED=NO"
echo "NO_COMMIT_OR_PUSH=YES"
echo "--- GIT STATUS ---"
git -C "$ROOT" status --short
