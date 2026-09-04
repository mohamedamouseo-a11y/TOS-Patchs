#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/var/www/TOS}"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_REPO_ROOT="$(cd "$PATCH_DIR/.." && pwd)"
V5_DIR="$PATCH_REPO_ROOT/TOS-UXUI-PHASE-03-TASKS-FLAGSHIP-SIGNATURE-V5"
ORIGINAL="$V5_DIR/apply_phase03_tasks_flagship_signature_v5.sh"
FALLBACK_SOURCE="$PATCH_DIR/tasks-flagship-signature-v5rr.append.css"

MAIN_TARGET="frontend/src/main.jsx"
TASKS_TARGET="frontend/src/components/ProfessionalTaskBoard.jsx"
CSS_TARGET="frontend/src/styles/tasks-projects-premium-reference.css"
EXPECTED_MAIN_WORKTREE_BLOB="9c712d900da43e06f2f0b6f1983cf7dfd6c0641d"
EXPECTED_TASKS_HEAD_BLOB="2a4fe1052b55e7f7f3d5da88c7eb0eb29fdb26d5"
EXPECTED_V4_CSS_SHA256="54c5e1463867b1e97a9362ab4ef8add0f0ea46e90ef3b57d567bb1252b821093"
V4_RUNTIME='--tos-tasks-couture-v4-runtime'
V5_RUNTIME='--tos-tasks-flagship-v5-runtime'
V5RR_RUNTIME='--tos-tasks-flagship-v5rr-runtime'
CARD_ANCHOR='data-tos-task-card-layout-polish="v1"'

DIST="$ROOT/frontend/dist"
LIVE_PARENT="/opt/apps/tamiyouz-front"
LIVE="$LIVE_PARENT/build"
STAMP="$(date +%Y%m%d-%H%M%S)"
STAGE="$LIVE_PARENT/build.phase03-tasks-v5rr.new.$$"
BACKUP="$LIVE_PARENT/build.phase03-tasks-v5rr.backup-$STAMP"
TMP="$PATCH_DIR/.apply_phase03_tasks_flagship_signature_v5rr.inner.$$.sh"
trap 'rm -f "$TMP"' EXIT

fail() {
  echo "PHASE03_TASKS_FLAGSHIP_SIGNATURE_V5RR=FAIL"
  echo "ERROR=$1" >&2
  exit "${2:-1}"
}

[ -d "$ROOT/.git" ] || fail "TOS repository not found" 2
[ -d "$PATCH_REPO_ROOT/.git" ] || fail "TOS-Patchs repository not found" 3
[ -f "$ORIGINAL" ] || fail "Original V5 script missing" 4
[ -f "$FALLBACK_SOURCE" ] || fail "V5RR fallback CSS missing" 5
[ -f "$ROOT/$MAIN_TARGET" ] || fail "main.jsx missing" 6
[ -f "$ROOT/$TASKS_TARGET" ] || fail "ProfessionalTaskBoard.jsx missing" 7
[ -f "$ROOT/$CSS_TARGET" ] || fail "Tasks premium stylesheet missing" 8
[ -d "$LIVE" ] || fail "Live frontend root missing" 9

git -C "$ROOT" diff --cached --quiet || fail "Staged changes exist; stop" 10

# The reviewed working tree after V4 contains the Tasks stylesheet import even if HEAD moved.
MAIN_WORKTREE_BLOB="$(git -C "$ROOT" hash-object "$MAIN_TARGET")"
[ "$MAIN_WORKTREE_BLOB" = "$EXPECTED_MAIN_WORKTREE_BLOB" ] || {
  echo "MAIN_WORKTREE_BLOB=$MAIN_WORKTREE_BLOB"
  fail "main.jsx is not the exact reviewed Tasks import state" 11
}
[ "$(grep -Fxc 'import "./styles/tasks-projects-premium-reference.css";' "$ROOT/$MAIN_TARGET" || true)" = "1" ] || fail "Tasks premium CSS import missing or duplicated" 12

# Keep the ProfessionalTaskBoard committed source pinned. V5RR only relaxes the incorrect legacy class check.
[ "$(git -C "$ROOT" rev-parse "HEAD:$TASKS_TARGET")" = "$EXPECTED_TASKS_HEAD_BLOB" ] || fail "Committed ProfessionalTaskBoard baseline changed" 13

# Stable task-card DOM anchor used by the current board. This replaces the false legacy .tos-modern-task-card guard.
grep -Fq "$CARD_ANCHOR" "$ROOT/$TASKS_TARGET" || fail "Stable task-card layout anchor missing" 14

# Before V5 is applied, require the exact reviewed V4 CSS state.
V5_COUNT="$(grep -Fc -- "$V5_RUNTIME" "$ROOT/$CSS_TARGET" || true)"
if [ "$V5_COUNT" = "0" ]; then
  [ "$(grep -Fc -- "$V4_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V4 runtime baseline missing" 15
  CURRENT_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"
  echo "BASELINE_CSS_SHA256=$CURRENT_SHA"
  [ "$CURRENT_SHA" = "$EXPECTED_V4_CSS_SHA256" ] || fail "Tasks CSS is not exact reviewed V4 baseline" 16
fi

# Verify the V5RR fallback source is exactly what is committed in TOS-Patchs HEAD.
SOURCE_REL="${FALLBACK_SOURCE#$PATCH_REPO_ROOT/}"
[ "$(git -C "$PATCH_REPO_ROOT" hash-object "$FALLBACK_SOURCE")" = "$(git -C "$PATCH_REPO_ROOT" rev-parse "HEAD:$SOURCE_REL")" ] || fail "V5RR fallback source differs from TOS-Patchs HEAD" 17

# Build a temporary V5 runner against the actual current committed main.jsx blob,
# and replace only the obsolete task-card class guard with the stable DOM anchor guard.
CURRENT_HEAD_MAIN_BLOB="$(git -C "$ROOT" rev-parse "HEAD:$MAIN_TARGET")"
python3 - "$ORIGINAL" "$TMP" "$CURRENT_HEAD_MAIN_BLOB" <<'PY'
from pathlib import Path
import re
import sys

source = Path(sys.argv[1])
target = Path(sys.argv[2])
current_main_blob = sys.argv[3]
text = source.read_text()

text, n = re.subn(
    r'EXPECTED_MAIN_HEAD_BLOB="[0-9a-f]{40}"',
    f'EXPECTED_MAIN_HEAD_BLOB="{current_main_blob}"',
    text,
    count=1,
)
if n != 1:
    raise SystemExit(f"main baseline guard replacement count={n}")

old = "grep -Fq 'tos-modern-task-card' \"$ROOT/$TASKS_TARGET\" || fail \"Task card hook missing\" 17"
new = "grep -Fq 'data-tos-task-card-layout-polish=\"v1\"' \"$ROOT/$TASKS_TARGET\" || fail \"Stable task card layout anchor missing\" 17"
if text.count(old) != 1:
    raise SystemExit(f"legacy task-card guard replacement count={text.count(old)}")
text = text.replace(old, new, 1)
target.write_text(text)
PY
chmod +x "$TMP"

echo "V5RR_REBASE_MAIN_HEAD_BLOB=$CURRENT_HEAD_MAIN_BLOB"
bash "$TMP" "$ROOT"

# V5 must now be fully present, including its new semantic hooks.
[ "$(grep -Fc -- "$V5_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V5 runtime sentinel missing after recovery" 18
[ "$(grep -Fc -- 'tos-task-kpi-deck' "$ROOT/$TASKS_TARGET" || true)" = "1" ] || fail "V5 KPI hook missing" 19
[ "$(grep -Fc -- 'tos-task-kanban-shell' "$ROOT/$TASKS_TARGET" || true)" = "1" ] || fail "V5 Kanban shell hook missing" 20
[ "$(grep -Fc -- 'tos-task-kanban-hero' "$ROOT/$TASKS_TARGET" || true)" = "1" ] || fail "V5 Kanban hero hook missing" 21

# Add a semantic fallback for task cards only if not already present.
V5RR_COUNT="$(grep -Fc -- "$V5RR_RUNTIME" "$ROOT/$CSS_TARGET" || true)"
[ "$V5RR_COUNT" -le 1 ] || fail "Duplicate V5RR runtime sentinel" 22
if [ "$V5RR_COUNT" = "0" ]; then
  printf '\n' >> "$ROOT/$CSS_TARGET"
  cat "$FALLBACK_SOURCE" >> "$ROOT/$CSS_TARGET"
  FALLBACK_ACTION="APPLIED_TASK_CARD_SEMANTIC_FALLBACK"
else
  FALLBACK_ACTION="VALIDATED_EXISTING_TASK_CARD_FALLBACK"
fi
[ "$(grep -Fc -- "$V5RR_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V5RR runtime sentinel missing" 23

git -C "$ROOT" diff --check -- "$MAIN_TARGET" "$TASKS_TARGET" "$CSS_TARGET"

cd "$ROOT/frontend"
npm run build
cd "$ROOT"

[ -f "$DIST/index.html" ] || fail "Built dist index missing" 24
grep -RFlq -- "$V5_RUNTIME" "$DIST/assets" || fail "V5 runtime sentinel missing from dist" 25
grep -RFlq -- "$V5RR_RUNTIME" "$DIST/assets" || fail "V5RR runtime sentinel missing from dist" 26
grep -RFlq -- 'tos-task-kanban-shell' "$DIST/assets" || fail "Kanban shell hook missing from dist" 27

rm -rf "$STAGE"
mkdir -p "$STAGE"
cp -a "$DIST/." "$STAGE/"
[ -f "$STAGE/index.html" ] || fail "Staged index missing" 28
grep -RFlq -- "$V5RR_RUNTIME" "$STAGE/assets" || fail "V5RR runtime sentinel missing from staged assets" 29

mv "$LIVE" "$BACKUP"
if ! mv "$STAGE" "$LIVE"; then
  mv "$BACKUP" "$LIVE" || true
  fail "Failed to activate V5RR live build; rollback attempted" 30
fi
if ! grep -RFlq -- "$V5RR_RUNTIME" "$LIVE/assets"; then
  rm -rf "$LIVE"
  mv "$BACKUP" "$LIVE" || true
  fail "Live V5RR runtime sentinel missing; rolled back" 31
fi

FINAL_STATUS="$(git -C "$ROOT" status --porcelain=v1 --untracked-files=all)"
FINAL_PATHS="$(printf '%s\n' "$FINAL_STATUS" | sed '/^$/d' | cut -c4- | sort -u)"
EXPECTED_PATHS="$(printf '%s\n%s\n%s\n' "$MAIN_TARGET" "$TASKS_TARGET" "$CSS_TARGET" | sort)"
[ "$FINAL_PATHS" = "$EXPECTED_PATHS" ] || {
  echo "--- FINAL STATUS ---"
  printf '%s\n' "$FINAL_STATUS"
  fail "Unexpected TOS files changed" 32
}

FINAL_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"
echo "PHASE03_TASKS_FLAGSHIP_SIGNATURE_V5RR=PASS"
echo "SCREEN=Tasks"
echo "STATE=Active_Task_Board"
echo "RECOVERY=LEGACY_TASK_CARD_GUARD_REPLACED_WITH_STABLE_DOM_ANCHOR"
echo "FALLBACK_ACTION=$FALLBACK_ACTION"
echo "V5_FLAGSHIP_STYLES=APPLIED"
echo "TASK_CARD_SIGNATURE_FALLBACK=APPLIED"
echo "BUSINESS_LOGIC_CHANGED=NO"
echo "BUILD_RESULT=PASS"
echo "LIVE_DEPLOY=PASS"
echo "CSS_SHA256=$FINAL_SHA"
echo "NO_COMMIT_OR_PUSH=YES"
echo "--- GIT STATUS ---"
printf '%s\n' "$FINAL_STATUS"
