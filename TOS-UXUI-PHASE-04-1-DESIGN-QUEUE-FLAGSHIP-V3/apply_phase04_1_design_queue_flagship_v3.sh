#!/usr/bin/env bash
set -euo pipefail

echo "RUNNING=PHASE04_1_DESIGN_QUEUE_FLAGSHIP_V3"

ROOT="${1:-/var/www/TOS}"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_REPO_ROOT="$(cd "$PATCH_DIR/.." && pwd)"
SOURCE_CSS="$PATCH_DIR/design-queue-flagship-v3.css"

DESIGN_TARGET="frontend/src/pages/DesignQueuePage.jsx"
WORKHUB_TARGET="frontend/src/pages/EmployeeWorkHub.jsx"
TEAM_TARGET="frontend/src/pages/TeamPage.jsx"
PERF_TARGET="frontend/src/pages/TeamPerformanceDashboard.jsx"
CSS_TARGET="frontend/src/index.css"

# Exact reviewed Phase 04 V2 live-worktree SHA256 values supplied after PASS.
DESIGN_V2_SHA256="d1a7d362d18506582e61f2a6f552fb88793bebd8174c3b6d60c74a3214a9cb3c"
WORKHUB_V2_SHA256="d86f5553b002b6fd89328c90ab5c369050595cee87695200d89f77a74d292e43"
TEAM_V2_SHA256="d14814aca4482d8c89d7a8a734125703f5b6123f58ccfff7368878ca94b67efe"
PERF_V2_SHA256="36dc277b800dc03129d8fc7feefc7b877906eb6ee9a73712805237326262bcaf"
CSS_V2_SHA256="da943a12e29aabb1a391fc58bf421dbdb5fd667ed2018f9ebb2eb06127ef9e51"

V1_RUNTIME="--tos-phase04-runtime"
V2_RUNTIME="--tos-phase04-v2-runtime"
V3_RUNTIME="--tos-dq-v3-runtime"
DESIGN_HOOK="tos-core-design-queue-premium"

DIST="$ROOT/frontend/dist"
LIVE_PARENT="/opt/apps/tamiyouz-front"
LIVE="$LIVE_PARENT/build"
STAMP="$(date +%Y%m%d-%H%M%S)"
STAGE="$LIVE_PARENT/build.phase04-1-design-queue-v3.new.$$"
BACKUP="$LIVE_PARENT/build.phase04-1-design-queue-v3.backup-$STAMP"

fail() {
  echo "PHASE04_1_DESIGN_QUEUE_FLAGSHIP_V3=FAIL"
  echo "ERROR=$1" >&2
  exit "${2:-1}"
}

sha256() { sha256sum "$ROOT/$1" | awk '{print $1}'; }

[ -d "$ROOT/.git" ] || fail "TOS repository not found" 2
[ -d "$PATCH_REPO_ROOT/.git" ] || fail "TOS-Patchs repository not found" 3
[ -f "$SOURCE_CSS" ] || fail "V3 CSS source missing" 4
for path in "$DESIGN_TARGET" "$WORKHUB_TARGET" "$TEAM_TARGET" "$PERF_TARGET" "$CSS_TARGET"; do
  [ -f "$ROOT/$path" ] || fail "Missing target: $path" 5
done
[ -d "$LIVE" ] || fail "Live frontend root missing" 6

git -C "$ROOT" diff --cached --quiet || fail "Staged changes exist; stop" 7

# Phase 04 V1/V2 intentionally left these five files modified before the user's final Push.
CURRENT_CHANGED="$(git -C "$ROOT" diff --name-only | sort)"
EXPECTED_CHANGED="$(printf '%s\n' "$CSS_TARGET" "$DESIGN_TARGET" "$WORKHUB_TARGET" "$PERF_TARGET" "$TEAM_TARGET" | sort)"
[ "$CURRENT_CHANGED" = "$EXPECTED_CHANGED" ] || fail "Unexpected worktree shape before Design Queue V3" 8

[ "$(sha256 "$DESIGN_TARGET")" = "$DESIGN_V2_SHA256" ] || fail "Design Queue is not the reviewed V2 source" 9
[ "$(sha256 "$WORKHUB_TARGET")" = "$WORKHUB_V2_SHA256" ] || fail "WorkHub changed since reviewed V2" 10
[ "$(sha256 "$TEAM_TARGET")" = "$TEAM_V2_SHA256" ] || fail "Team changed since reviewed V2" 11
[ "$(sha256 "$PERF_TARGET")" = "$PERF_V2_SHA256" ] || fail "Team Performance changed since reviewed V2" 12
[ "$(sha256 "$CSS_TARGET")" = "$CSS_V2_SHA256" ] || fail "index.css is not the reviewed V2 visual base" 13

[ "$(grep -Fc -- "$V1_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "Phase 04 V1 runtime missing/duplicated" 14
[ "$(grep -Fc -- "$V2_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "Phase 04 V2 runtime missing/duplicated" 15
[ "$(grep -Fc -- "$V3_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "0" ] || fail "Design Queue V3 already present" 16
[ "$(grep -Fc -- "$DESIGN_HOOK" "$ROOT/$DESIGN_TARGET" || true)" = "2" ] || fail "Design Queue premium hooks missing" 17

SOURCE_REL="${SOURCE_CSS#$PATCH_REPO_ROOT/}"
[ "$(git -C "$PATCH_REPO_ROOT" hash-object "$SOURCE_CSS")" = "$(git -C "$PATCH_REPO_ROOT" rev-parse "HEAD:$SOURCE_REL")" ] || fail "V3 CSS differs from TOS-Patchs HEAD" 18

printf '\n' >> "$ROOT/$CSS_TARGET"
cat "$SOURCE_CSS" >> "$ROOT/$CSS_TARGET"

[ "$(grep -Fc -- "$V3_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "Design Queue V3 runtime missing or duplicated" 19

git -C "$ROOT" diff --check -- "$DESIGN_TARGET" "$WORKHUB_TARGET" "$TEAM_TARGET" "$PERF_TARGET" "$CSS_TARGET"

cd "$ROOT/frontend"
npm run build
cd "$ROOT"

[ -f "$DIST/index.html" ] || fail "Built dist index missing" 20
grep -RFlq -- "$V3_RUNTIME" "$DIST/assets" || fail "Design Queue V3 runtime missing from dist" 21
grep -RFlq -- "$DESIGN_HOOK" "$DIST/assets" || fail "Design Queue premium hook missing from dist" 22

rm -rf "$STAGE"
mkdir -p "$STAGE"
cp -a "$DIST/." "$STAGE/"
[ -f "$STAGE/index.html" ] || fail "Staged index missing" 23
grep -RFlq -- "$V3_RUNTIME" "$STAGE/assets" || fail "Design Queue V3 runtime missing from staged assets" 24

mv "$LIVE" "$BACKUP"
if ! mv "$STAGE" "$LIVE"; then
  mv "$BACKUP" "$LIVE" || true
  fail "Failed to activate Design Queue V3; rollback attempted" 25
fi
if ! grep -RFlq -- "$V3_RUNTIME" "$LIVE/assets"; then
  rm -rf "$LIVE"
  mv "$BACKUP" "$LIVE" || true
  fail "Live Design Queue V3 runtime missing; rolled back" 26
fi

systemctl is-active --quiet nginx || fail "Nginx is not active after deploy" 27

git -C "$ROOT" diff --cached --quiet || fail "Unexpected staged changes after V3" 28
POST_CHANGED="$(git -C "$ROOT" diff --name-only | sort)"
[ "$POST_CHANGED" = "$EXPECTED_CHANGED" ] || fail "Unexpected tracked files changed after V3" 29

# V3 must be visual-only: the four JSX files remain byte-identical to reviewed V2.
[ "$(sha256 "$DESIGN_TARGET")" = "$DESIGN_V2_SHA256" ] || fail "Design Queue JSX changed unexpectedly" 30
[ "$(sha256 "$WORKHUB_TARGET")" = "$WORKHUB_V2_SHA256" ] || fail "WorkHub JSX changed unexpectedly" 31
[ "$(sha256 "$TEAM_TARGET")" = "$TEAM_V2_SHA256" ] || fail "Team JSX changed unexpectedly" 32
[ "$(sha256 "$PERF_TARGET")" = "$PERF_V2_SHA256" ] || fail "Team Performance JSX changed unexpectedly" 33

echo "PHASE04_1_DESIGN_QUEUE_FLAGSHIP_V3=PASS"
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
