#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/var/www/TOS}"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_REPO_ROOT="$(cd "$PATCH_DIR/.." && pwd)"
V5_SOURCE="$PATCH_REPO_ROOT/TOS-UXUI-PHASE-03-TASKS-FLAGSHIP-SIGNATURE-V5/tasks-flagship-signature-v5.append.css"

MAIN_TARGET="frontend/src/main.jsx"
TASKS_TARGET="frontend/src/components/ProfessionalTaskBoard.jsx"
CSS_TARGET="frontend/src/styles/tasks-projects-premium-reference.css"

# Exact reviewed V4 worktree content. These are worktree blob hashes, so the
# recovery works whether V4 is committed already or still present as local
# reviewed changes.
EXPECTED_MAIN_WORKTREE_BLOB="9c712d900da43e06f2f0b6f1983cf7dfd6c0641d"
EXPECTED_TASKS_WORKTREE_BLOB="2a4fe1052b55e7f7f3d5da88c7eb0eb29fdb26d5"
EXPECTED_V4_CSS_WORKTREE_BLOB="565805db1125013812a901ce11838980b5991b7a"

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
STAGE="$LIVE_PARENT/build.phase03-tasks-v5c.new.$$"
BACKUP="$LIVE_PARENT/build.phase03-tasks-v5c.backup-$STAMP"

fail() {
  echo "PHASE03_TASKS_FLAGSHIP_SIGNATURE_V5C=FAIL"
  echo "ERROR=$1" >&2
  exit "${2:-1}"
}

[ -d "$ROOT/.git" ] || fail "TOS repository not found at $ROOT" 2
[ -d "$PATCH_REPO_ROOT/.git" ] || fail "TOS-Patchs checkout not found beside this script" 3
[ -f "$V5_SOURCE" ] || fail "V5 flagship CSS source missing" 4
[ -f "$ROOT/$MAIN_TARGET" ] || fail "main.jsx missing" 5
[ -f "$ROOT/$TASKS_TARGET" ] || fail "ProfessionalTaskBoard.jsx missing" 6
[ -f "$ROOT/$CSS_TARGET" ] || fail "Tasks premium stylesheet missing" 7
[ -d "$LIVE" ] || fail "Live frontend root missing" 8

TOS_REMOTE="$(git -C "$ROOT" remote get-url origin 2>/dev/null || true)"
PATCH_REMOTE="$(git -C "$PATCH_REPO_ROOT" remote get-url origin 2>/dev/null || true)"
case "$TOS_REMOTE" in
  *mohamedamouseo-a11y/TOS.git|*mohamedamouseo-a11y/TOS) ;;
  *) fail "Wrong TOS checkout remote: $TOS_REMOTE" 9 ;;
esac
case "$PATCH_REMOTE" in
  *mohamedamouseo-a11y/TOS-Patchs.git|*mohamedamouseo-a11y/TOS-Patchs) ;;
  *) fail "Patch script is not running from a real TOS-Patchs checkout: $PATCH_REMOTE" 10 ;;
esac
[ "$(git -C "$ROOT" rev-parse --show-toplevel)" = "$ROOT" ] || fail "TOS root mismatch" 11
[ "$(git -C "$PATCH_REPO_ROOT" rev-parse --show-toplevel)" = "$PATCH_REPO_ROOT" ] || fail "TOS-Patchs root mismatch" 12

git -C "$ROOT" diff --cached --quiet || fail "Staged TOS changes exist; stop" 13

MAIN_BLOB="$(git -C "$ROOT" hash-object "$MAIN_TARGET")"
TASKS_BLOB="$(git -C "$ROOT" hash-object "$TASKS_TARGET")"
CSS_BLOB="$(git -C "$ROOT" hash-object "$CSS_TARGET")"

echo "TOS_HEAD=$(git -C "$ROOT" rev-parse HEAD)"
echo "MAIN_WORKTREE_BLOB=$MAIN_BLOB"
echo "TASKS_WORKTREE_BLOB=$TASKS_BLOB"
echo "V4_CSS_WORKTREE_BLOB=$CSS_BLOB"

[ "$MAIN_BLOB" = "$EXPECTED_MAIN_WORKTREE_BLOB" ] || fail "main.jsx is not the exact reviewed V4 state" 14
[ "$TASKS_BLOB" = "$EXPECTED_TASKS_WORKTREE_BLOB" ] || fail "ProfessionalTaskBoard is not the exact reviewed V4 state" 15
[ "$CSS_BLOB" = "$EXPECTED_V4_CSS_WORKTREE_BLOB" ] || fail "Tasks stylesheet is not the exact reviewed V4 state" 16
[ "$(grep -Fxc "$IMPORT_LINE" "$ROOT/$MAIN_TARGET" || true)" = "1" ] || fail "Tasks premium CSS import missing or duplicated" 17
[ "$(grep -Fc -- "$V4_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V4 runtime sentinel missing or duplicated" 18
[ "$(grep -Fc -- "$V5_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "0" ] || fail "V5 already appears in this worktree; stop for review" 19

grep -Fq 'tos-modern-task-card' "$ROOT/$TASKS_TARGET" || fail "Reviewed task-card class missing despite exact task-board blob" 20
grep -Fq 'data-tos-task-card-layout-polish="v1"' "$ROOT/$TASKS_TARGET" || fail "Reviewed task-card DOM anchor missing despite exact task-board blob" 21

# Do not reject unrelated untracked recovery folders left by earlier failed
# attempts. Tracked local changes, if any, may only be the already-reviewed
# main/CSS files from the Phase 03 sequence.
TRACKED_DIRTY="$(git -C "$ROOT" diff --name-only | sort -u)"
if [ -n "$TRACKED_DIRTY" ]; then
  while IFS= read -r p; do
    [ -z "$p" ] && continue
    case "$p" in
      "$MAIN_TARGET"|"$CSS_TARGET") ;;
      *) fail "Unexpected tracked local change before V5C: $p" 22 ;;
    esac
  done <<< "$TRACKED_DIRTY"
fi

SOURCE_REL="${V5_SOURCE#$PATCH_REPO_ROOT/}"
[ "$(git -C "$PATCH_REPO_ROOT" hash-object "$V5_SOURCE")" = "$(git -C "$PATCH_REPO_ROOT" rev-parse "HEAD:$SOURCE_REL")" ] || fail "V5 CSS source differs from TOS-Patchs HEAD" 23

python3 - "$ROOT/$TASKS_TARGET" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text()

replacements = [
    (
        'tos-task-kpi-deck',
        '<div id={taskBoardHeaderPanelId}>\n                    <div className="mt-1">\n                      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">',
        '<div id={taskBoardHeaderPanelId}>\n                    <div className="mt-1">\n                      <div className="tos-task-kpi-deck grid gap-3 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">',
        'KPI deck anchor',
    ),
    (
        'tos-task-kanban-shell',
        '<section className="mt-3 rounded-[24px] border border-white/85 bg-white/94 p-3 shadow-[0_12px_34px_rgba(15,23,42,0.05)] ring-1 ring-slate-100/70 backdrop-blur-xl dark:border-white/10 dark:bg-zinc-950/92 dark:shadow-black/30 dark:ring-white/5">',
        '<section className="tos-task-kanban-shell mt-3 rounded-[24px] border border-white/85 bg-white/94 p-3 shadow-[0_12px_34px_rgba(15,23,42,0.05)] ring-1 ring-slate-100/70 backdrop-blur-xl dark:border-white/10 dark:bg-zinc-950/92 dark:shadow-black/30 dark:ring-white/5">',
        'Kanban shell anchor',
    ),
    (
        'tos-task-kanban-hero',
        '<div className="mb-3 flex flex-col gap-2.5 border-b border-slate-100 pb-3 dark:border-white/10 md:flex-row md:items-center md:justify-between">',
        '<div className="tos-task-kanban-hero mb-3 flex flex-col gap-2.5 border-b border-slate-100 pb-3 dark:border-white/10 md:flex-row md:items-center md:justify-between">',
        'Kanban hero anchor',
    ),
]

for hook, old, new, label in replacements:
    existing = text.count(hook)
    if existing == 1:
        continue
    if existing != 0:
        raise SystemExit(f'{label}: hook count before patch={existing}')
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected source anchor exactly once, got {count}')
    text = text.replace(old, new, 1)

path.write_text(text)
PY

printf '\n' >> "$ROOT/$CSS_TARGET"
cat "$V5_SOURCE" >> "$ROOT/$CSS_TARGET"

[ "$(grep -Fc -- "$V5_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V5 runtime sentinel missing after apply" 24
[ "$(grep -Fc -- "$KPI_HOOK" "$ROOT/$TASKS_TARGET" || true)" = "1" ] || fail "KPI semantic hook missing or duplicated" 25
[ "$(grep -Fc -- "$KANBAN_HOOK" "$ROOT/$TASKS_TARGET" || true)" = "1" ] || fail "Kanban shell hook missing or duplicated" 26
[ "$(grep -Fc -- "$HERO_HOOK" "$ROOT/$TASKS_TARGET" || true)" = "1" ] || fail "Kanban hero hook missing or duplicated" 27

git -C "$ROOT" diff --check -- "$MAIN_TARGET" "$TASKS_TARGET" "$CSS_TARGET"

cd "$ROOT/frontend"
npm run build
cd "$ROOT"

[ -f "$DIST/index.html" ] || fail "Built frontend/dist/index.html missing" 28
grep -RFlq -- "$V5_RUNTIME" "$DIST/assets" || fail "V5 runtime sentinel missing from built assets" 29
grep -RFlq -- "$KANBAN_HOOK" "$DIST/assets" || fail "Kanban semantic hook missing from built assets" 30

rm -rf "$STAGE"
mkdir -p "$STAGE"
cp -a "$DIST/." "$STAGE/"
[ -f "$STAGE/index.html" ] || fail "Staged live index missing" 31
grep -RFlq -- "$V5_RUNTIME" "$STAGE/assets" || fail "V5 runtime sentinel missing from staged assets" 32

mv "$LIVE" "$BACKUP"
if ! mv "$STAGE" "$LIVE"; then
  mv "$BACKUP" "$LIVE" || true
  fail "Failed to activate V5C live build; rollback attempted" 33
fi
if ! grep -RFlq -- "$V5_RUNTIME" "$LIVE/assets"; then
  rm -rf "$LIVE"
  mv "$BACKUP" "$LIVE" || true
  fail "Live V5 runtime sentinel missing; rolled back" 34
fi

FINAL_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"
echo "PHASE03_TASKS_FLAGSHIP_SIGNATURE_V5C=PASS"
echo "SCREEN=Tasks"
echo "STATE=Active_Task_Board"
echo "RECOVERY=SEPARATE_PATCH_CHECKOUT_AND_EXACT_V4_WORKTREE_REBASE"
echo "BUILD_RESULT=PASS"
echo "LIVE_DEPLOY=PASS"
echo "CSS_SHA256=$FINAL_SHA"
echo "NO_COMMIT_OR_PUSH=YES"
echo "--- GIT STATUS ---"
git -C "$ROOT" status --short
