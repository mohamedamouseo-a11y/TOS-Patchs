#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/var/www/TOS}"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_REPO_ROOT="$(cd "$PATCH_DIR/.." && pwd)"
SOURCE_APPEND="$PATCH_DIR/tasks-flagship-signature-v5.append.css"

MAIN_TARGET="frontend/src/main.jsx"
TASKS_TARGET="frontend/src/components/ProfessionalTaskBoard.jsx"
CSS_TARGET="frontend/src/styles/tasks-projects-premium-reference.css"

EXPECTED_MAIN_HEAD_BLOB="725b57d3b7927b802dcedc26cca49c6a7f10ee55"
EXPECTED_TASKS_HEAD_BLOB="2a4fe1052b55e7f7f3d5da88c7eb0eb29fdb26d5"
EXPECTED_V4_CSS_SHA256="54c5e1463867b1e97a9362ab4ef8add0f0ea46e90ef3b57d567bb1252b821093"
IMPORT_LINE='import "./styles/tasks-projects-premium-reference.css";'
V4_RUNTIME='--tos-tasks-couture-v4-runtime'
V5_RUNTIME='--tos-tasks-flagship-v5-runtime'
KPI_HOOK='tos-task-kpi-deck'
KANBAN_HOOK='tos-task-kanban-shell'
HERO_HOOK='tos-task-kanban-hero'

DIST="$ROOT/frontend/dist"
LIVE_PARENT="/opt/apps/tamiyouz-front"
LIVE="$LIVE_PARENT/build"
STAMP="$(date +%Y%m%d-%H%M%S)"
STAGE="$LIVE_PARENT/build.phase03-tasks-v5.new.$$"
BACKUP="$LIVE_PARENT/build.phase03-tasks-v5.backup-$STAMP"

fail() {
  echo "PHASE03_TASKS_FLAGSHIP_SIGNATURE_V5=FAIL"
  echo "ERROR=$1" >&2
  exit "${2:-1}"
}

[ -d "$ROOT/.git" ] || fail "TOS repository not found" 2
[ -d "$PATCH_REPO_ROOT/.git" ] || fail "TOS-Patchs repository not found" 3
[ -f "$SOURCE_APPEND" ] || fail "Missing V5 CSS source" 4
[ -f "$ROOT/$MAIN_TARGET" ] || fail "Missing main.jsx" 5
[ -f "$ROOT/$TASKS_TARGET" ] || fail "Missing ProfessionalTaskBoard.jsx" 6
[ -f "$ROOT/$CSS_TARGET" ] || fail "Missing Tasks premium stylesheet" 7
[ -d "$LIVE" ] || fail "Live frontend root missing" 8

SOURCE_REL="${SOURCE_APPEND#$PATCH_REPO_ROOT/}"
[ "$(git -C "$PATCH_REPO_ROOT" hash-object "$SOURCE_APPEND")" = "$(git -C "$PATCH_REPO_ROOT" rev-parse "HEAD:$SOURCE_REL")" ] || fail "V5 patch source differs from TOS-Patchs HEAD" 9

git -C "$ROOT" diff --cached --quiet || fail "Staged changes exist; stop" 10
[ "$(git -C "$ROOT" rev-parse "HEAD:$MAIN_TARGET")" = "$EXPECTED_MAIN_HEAD_BLOB" ] || fail "Committed main.jsx baseline changed" 11
[ "$(git -C "$ROOT" rev-parse "HEAD:$TASKS_TARGET")" = "$EXPECTED_TASKS_HEAD_BLOB" ] || fail "Committed ProfessionalTaskBoard baseline changed" 12
[ "$(grep -Fxc "$IMPORT_LINE" "$ROOT/$MAIN_TARGET" || true)" = "1" ] || fail "Tasks premium CSS import missing or duplicated" 13
[ "$(grep -Fc -- "$V4_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V4 runtime baseline missing" 14

grep -Fq 'tos-workspace-management-panel' "$ROOT/$TASKS_TARGET" || fail "Workspace management hook missing" 15
grep -Fq 'tos-modern-board-column' "$ROOT/$TASKS_TARGET" || fail "Board column hook missing" 16
grep -Fq 'tos-modern-task-card' "$ROOT/$TASKS_TARGET" || fail "Task card hook missing" 17

STATUS="$(git -C "$ROOT" status --porcelain=v1 --untracked-files=all)"
PATHS="$(printf '%s\n' "$STATUS" | sed '/^$/d' | cut -c4- | sort -u)"
PRE_V5_PATHS="$(printf '%s\n%s\n' "$MAIN_TARGET" "$CSS_TARGET" | sort)"
POST_V5_PATHS="$(printf '%s\n%s\n%s\n' "$MAIN_TARGET" "$TASKS_TARGET" "$CSS_TARGET" | sort)"

V5_COUNT="$(grep -Fc -- "$V5_RUNTIME" "$ROOT/$CSS_TARGET" || true)"
KPI_COUNT="$(grep -Fc -- "$KPI_HOOK" "$ROOT/$TASKS_TARGET" || true)"
KANBAN_COUNT="$(grep -Fc -- "$KANBAN_HOOK" "$ROOT/$TASKS_TARGET" || true)"
HERO_COUNT="$(grep -Fc -- "$HERO_HOOK" "$ROOT/$TASKS_TARGET" || true)"

if [ "$V5_COUNT" = "0" ]; then
  [ "$PATHS" = "$PRE_V5_PATHS" ] || {
    echo "--- PRE-EXISTING STATUS ---"
    printf '%s\n' "$STATUS"
    fail "Expected exact reviewed V4 working-tree paths only" 18
  }
  [ "$KPI_COUNT" = "0" ] || fail "Unexpected pre-existing KPI hook" 19
  [ "$KANBAN_COUNT" = "0" ] || fail "Unexpected pre-existing Kanban hook" 20
  [ "$HERO_COUNT" = "0" ] || fail "Unexpected pre-existing Kanban hero hook" 21

  CURRENT_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"
  echo "BASELINE_CSS_SHA256=$CURRENT_SHA"
  [ "$CURRENT_SHA" = "$EXPECTED_V4_CSS_SHA256" ] || fail "Tasks CSS is not exact reviewed V4 baseline" 22

  python3 - "$ROOT/$TASKS_TARGET" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text()

replacements = [
    (
        '<div id={taskBoardHeaderPanelId}>\n                    <div className="mt-1">\n                      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">',
        '<div id={taskBoardHeaderPanelId}>\n                    <div className="mt-1">\n                      <div className="tos-task-kpi-deck grid gap-3 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">',
        'KPI deck anchor',
    ),
    (
        '<section className="mt-3 rounded-[24px] border border-white/85 bg-white/94 p-3 shadow-[0_12px_34px_rgba(15,23,42,0.05)] ring-1 ring-slate-100/70 backdrop-blur-xl dark:border-white/10 dark:bg-zinc-950/92 dark:shadow-black/30 dark:ring-white/5">',
        '<section className="tos-task-kanban-shell mt-3 rounded-[24px] border border-white/85 bg-white/94 p-3 shadow-[0_12px_34px_rgba(15,23,42,0.05)] ring-1 ring-slate-100/70 backdrop-blur-xl dark:border-white/10 dark:bg-zinc-950/92 dark:shadow-black/30 dark:ring-white/5">',
        'Kanban shell anchor',
    ),
    (
        '<div className="mb-3 flex flex-col gap-2.5 border-b border-slate-100 pb-3 dark:border-white/10 md:flex-row md:items-center md:justify-between">',
        '<div className="tos-task-kanban-hero mb-3 flex flex-col gap-2.5 border-b border-slate-100 pb-3 dark:border-white/10 md:flex-row md:items-center md:justify-between">',
        'Kanban hero anchor',
    ),
]

for old, new, label in replacements:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected exactly once, got {count}')
    text = text.replace(old, new, 1)

path.write_text(text)
PY

  printf '\n' >> "$ROOT/$CSS_TARGET"
  cat "$SOURCE_APPEND" >> "$ROOT/$CSS_TARGET"
  PATCH_ACTION="APPLIED_FLAGSHIP_SIGNATURE_V5"
else
  [ "$V5_COUNT" = "1" ] || fail "Duplicate V5 runtime sentinel" 23
  [ "$PATHS" = "$POST_V5_PATHS" ] || fail "Existing V5 state has unexpected working-tree paths" 24
  PATCH_ACTION="VALIDATED_EXISTING_FLAGSHIP_V5"
fi

[ "$(grep -Fc -- "$V5_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V5 runtime sentinel missing or duplicated" 25
[ "$(grep -Fc -- "$KPI_HOOK" "$ROOT/$TASKS_TARGET" || true)" = "1" ] || fail "KPI semantic hook missing or duplicated" 26
[ "$(grep -Fc -- "$KANBAN_HOOK" "$ROOT/$TASKS_TARGET" || true)" = "1" ] || fail "Kanban shell hook missing or duplicated" 27
[ "$(grep -Fc -- "$HERO_HOOK" "$ROOT/$TASKS_TARGET" || true)" = "1" ] || fail "Kanban hero hook missing or duplicated" 28

git -C "$ROOT" diff --check -- "$MAIN_TARGET" "$TASKS_TARGET" "$CSS_TARGET"

cd "$ROOT/frontend"
npm run build
cd "$ROOT"

[ -f "$DIST/index.html" ] || fail "Built dist index missing" 29
grep -RFlq -- "$V5_RUNTIME" "$DIST/assets" || fail "V5 runtime sentinel missing from dist assets" 30
grep -RFlq -- "$KPI_HOOK" "$DIST/assets" || fail "KPI hook missing from dist assets" 31
grep -RFlq -- "$KANBAN_HOOK" "$DIST/assets" || fail "Kanban hook missing from dist assets" 32

rm -rf "$STAGE"
mkdir -p "$STAGE"
cp -a "$DIST/." "$STAGE/"
[ -f "$STAGE/index.html" ] || fail "Staged index missing" 33
grep -RFlq -- "$V5_RUNTIME" "$STAGE/assets" || fail "V5 runtime sentinel missing from staged assets" 34

mv "$LIVE" "$BACKUP"
if ! mv "$STAGE" "$LIVE"; then
  mv "$BACKUP" "$LIVE" || true
  fail "Failed to activate V5 live build; rollback attempted" 35
fi

if ! grep -RFlq -- "$V5_RUNTIME" "$LIVE/assets"; then
  rm -rf "$LIVE"
  mv "$BACKUP" "$LIVE" || true
  fail "Live V5 runtime sentinel missing; rolled back" 36
fi

FINAL_STATUS="$(git -C "$ROOT" status --porcelain=v1 --untracked-files=all)"
FINAL_PATHS="$(printf '%s\n' "$FINAL_STATUS" | sed '/^$/d' | cut -c4- | sort -u)"
[ "$FINAL_PATHS" = "$POST_V5_PATHS" ] || {
  echo "--- FINAL STATUS ---"
  printf '%s\n' "$FINAL_STATUS"
  fail "Unexpected TOS files changed" 37
}

FINAL_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"
echo "PHASE03_TASKS_FLAGSHIP_SIGNATURE_V5=PASS"
echo "SCREEN=Tasks"
echo "STATE=Active_Task_Board"
echo "REFERENCE=Phase_02_Projects_Premium"
echo "PATCH_ACTION=$PATCH_ACTION"
echo "WORKSPACE_DECK=SIGNATURE_EXECUTIVE"
echo "KPI_DECK=FLOATING_INSTRUMENT_PODS"
echo "KANBAN_SHELL=FLAGSHIP_FRAME"
echo "COLUMNS=SCULPTED_MATERIAL"
echo "TASK_CARDS=SIGNATURE_RAISED"
echo "PRIMARY_ACTIONS=CHAMPAGNE_HARDWARE"
echo "BUSINESS_LOGIC_CHANGED=NO"
echo "BUILD_RESULT=PASS"
echo "LIVE_DEPLOY=PASS"
echo "DIST_RUNTIME_SENTINEL=PASS"
echo "LIVE_RUNTIME_SENTINEL=PASS"
echo "CHANGED_FILES=$MAIN_TARGET,$TASKS_TARGET,$CSS_TARGET"
echo "CSS_SHA256=$FINAL_SHA"
echo "COMMIT_CREATED=NO"
echo "PUSH_PERFORMED=NO"
echo "READY_FOR_VISUAL_REVIEW=YES"
echo "--- GIT STATUS ---"
printf '%s\n' "$FINAL_STATUS"
