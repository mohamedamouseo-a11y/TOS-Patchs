#!/usr/bin/env bash
set -euo pipefail

echo "RUNNING=PHASE04_1_DESIGN_QUEUE_FLAGSHIP_V4"

ROOT="${1:-/var/www/TOS}"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_REPO_ROOT="$(cd "$PATCH_DIR/.." && pwd)"
SOURCE_CSS="$PATCH_DIR/design-queue-flagship-v4.css"

DESIGN_TARGET="frontend/src/pages/DesignQueuePage.jsx"
WORKHUB_TARGET="frontend/src/pages/EmployeeWorkHub.jsx"
TEAM_TARGET="frontend/src/pages/TeamPage.jsx"
PERF_TARGET="frontend/src/pages/TeamPerformanceDashboard.jsx"
CSS_TARGET="frontend/src/index.css"

# Exact verified V3 live-worktree state.
DESIGN_V3_SHA256="d1a7d362d18506582e61f2a6f552fb88793bebd8174c3b6d60c74a3214a9cb3c"
CSS_V3_SHA256="51054e06b02cf01ec8989b2ca7774d021a8c5c7944bc597122e479cf78250107"

V1_RUNTIME="--tos-phase04-runtime"
V2_RUNTIME="--tos-phase04-v2-runtime"
V3_RUNTIME="--tos-dq-v3-runtime"
V4_RUNTIME="--tos-dq-v4-runtime"
DESIGN_HOOK="tos-core-design-queue-premium"

DIST="$ROOT/frontend/dist"
LIVE_PARENT="/opt/apps/tamiyouz-front"
LIVE="$LIVE_PARENT/build"
STAMP="$(date +%Y%m%d-%H%M%S)"
STAGE="$LIVE_PARENT/build.phase04-1-design-queue-v4.new.$$"
BACKUP="$LIVE_PARENT/build.phase04-1-design-queue-v4.backup-$STAMP"

fail(){ echo "PHASE04_1_DESIGN_QUEUE_FLAGSHIP_V4=FAIL"; echo "ERROR=$1" >&2; exit "${2:-1}"; }
sha256(){ sha256sum "$ROOT/$1" | awk '{print $1}'; }

[ -d "$ROOT/.git" ] || fail "TOS repository not found" 2
[ -d "$PATCH_REPO_ROOT/.git" ] || fail "TOS-Patchs repository not found" 3
[ -f "$SOURCE_CSS" ] || fail "V4 CSS source missing" 4
[ -d "$LIVE" ] || fail "Live frontend root missing" 5

for path in "$DESIGN_TARGET" "$WORKHUB_TARGET" "$TEAM_TARGET" "$PERF_TARGET" "$CSS_TARGET"; do
  [ -f "$ROOT/$path" ] || fail "Missing target: $path" 6
done

git -C "$ROOT" diff --cached --quiet || fail "Staged changes exist; stop" 7

CURRENT_CHANGED="$(git -C "$ROOT" diff --name-only | sort)"
EXPECTED_CHANGED="$(printf '%s\n' "$CSS_TARGET" "$DESIGN_TARGET" "$WORKHUB_TARGET" "$PERF_TARGET" "$TEAM_TARGET" | sort)"
[ "$CURRENT_CHANGED" = "$EXPECTED_CHANGED" ] || fail "Unexpected worktree shape before V4" 8

[ "$(sha256 "$DESIGN_TARGET")" = "$DESIGN_V3_SHA256" ] || fail "Design Queue JSX differs from verified V3 state" 9
[ "$(sha256 "$CSS_TARGET")" = "$CSS_V3_SHA256" ] || fail "index.css differs from verified V3 state" 10

[ "$(grep -Fc -- "$V1_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "Phase04 V1 runtime missing/duplicated" 11
[ "$(grep -Fc -- "$V2_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "Phase04 V2 runtime missing/duplicated" 12
[ "$(grep -Fc -- "$V3_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "Design Queue V3 runtime missing/duplicated" 13
[ "$(grep -Fc -- "$V4_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "0" ] || fail "Design Queue V4 already present" 14
[ "$(grep -Fc -- "$DESIGN_HOOK" "$ROOT/$DESIGN_TARGET" || true)" = "2" ] || fail "Design Queue premium hooks missing" 15

SOURCE_REL="${SOURCE_CSS#$PATCH_REPO_ROOT/}"
[ "$(git -C "$PATCH_REPO_ROOT" hash-object "$SOURCE_CSS")" = "$(git -C "$PATCH_REPO_ROOT" rev-parse "HEAD:$SOURCE_REL")" ] || fail "V4 CSS differs from TOS-Patchs HEAD" 16

printf '\n' >> "$ROOT/$CSS_TARGET"
cat "$SOURCE_CSS" >> "$ROOT/$CSS_TARGET"

[ "$(grep -Fc -- "$V4_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "Design Queue V4 runtime missing/duplicated" 17

git -C "$ROOT" diff --check -- "$CSS_TARGET" "$DESIGN_TARGET" "$WORKHUB_TARGET" "$TEAM_TARGET" "$PERF_TARGET"

cd "$ROOT/frontend"
npm run build
cd "$ROOT"

[ -f "$DIST/index.html" ] || fail "Built dist index missing" 18
grep -RFlq -- "$V4_RUNTIME" "$DIST/assets" || fail "V4 runtime missing from dist" 19
grep -RFlq -- "$DESIGN_HOOK" "$DIST/assets" || fail "Design Queue hook missing from dist" 20

rm -rf "$STAGE"
mkdir -p "$STAGE"
cp -a "$DIST/." "$STAGE/"
[ -f "$STAGE/index.html" ] || fail "Staged index missing" 21
grep -RFlq -- "$V4_RUNTIME" "$STAGE/assets" || fail "V4 runtime missing from staged assets" 22

mv "$LIVE" "$BACKUP"
if ! mv "$STAGE" "$LIVE"; then
  mv "$BACKUP" "$LIVE" || true
  fail "Failed to activate V4; rollback attempted" 23
fi
if ! grep -RFlq -- "$V4_RUNTIME" "$LIVE/assets"; then
  rm -rf "$LIVE"
  mv "$BACKUP" "$LIVE" || true
  fail "Live V4 runtime missing; rolled back" 24
fi

systemctl is-active --quiet nginx || fail "Nginx inactive after deploy" 25

git -C "$ROOT" diff --cached --quiet || fail "Unexpected staged changes after V4" 26
POST_CHANGED="$(git -C "$ROOT" diff --name-only | sort)"
[ "$POST_CHANGED" = "$EXPECTED_CHANGED" ] || fail "Unexpected tracked files changed after V4" 27

# Visual-only: Design Queue JSX remains byte-identical.
[ "$(sha256 "$DESIGN_TARGET")" = "$DESIGN_V3_SHA256" ] || fail "Design Queue JSX changed unexpectedly" 28

echo "PHASE04_1_DESIGN_QUEUE_FLAGSHIP_V4=PASS"
echo "SCREEN=Design_Queue_ONLY"
echo "BUSINESS_LOGIC_CHANGED=NO"
echo "BUILD_RESULT=PASS"
echo "LIVE_DEPLOY=PASS"
echo "DESIGN_QUEUE_SHA256=$(sha256 "$DESIGN_TARGET")"
echo "INDEX_CSS_SHA256=$(sha256 "$CSS_TARGET")"
echo "OTHER_PHASE04_SCREENS_TOUCHED=NO"
echo "NO_COMMIT_OR_PUSH=YES"
echo "--- GIT STATUS ---"
git -C "$ROOT" status --short
