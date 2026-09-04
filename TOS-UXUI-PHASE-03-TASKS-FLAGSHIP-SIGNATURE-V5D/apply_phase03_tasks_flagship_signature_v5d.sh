#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/var/www/TOS}"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_REPO_ROOT="$(cd "$PATCH_DIR/.." && pwd)"
V5_SOURCE="$PATCH_REPO_ROOT/TOS-UXUI-PHASE-03-TASKS-FLAGSHIP-SIGNATURE-V5/tasks-flagship-signature-v5.append.css"
FALLBACK_SOURCE="$PATCH_DIR/tasks-flagship-signature-v5d-fallback.css"

MAIN_TARGET="frontend/src/main.jsx"
TASKS_TARGET="frontend/src/components/ProfessionalTaskBoard.jsx"
CSS_TARGET="frontend/src/styles/tasks-projects-premium-reference.css"

EXPECTED_MAIN_BLOB="9c712d900da43e06f2f0b6f1983cf7dfd6c0641d"
EXPECTED_TASKS_BLOB="2a4fe1052b55e7f7f3d5da88c7eb0eb29fdb26d5"
EXPECTED_CSS_BLOB="565805db1125013812a901ce11838980b5991b7a"
V4_RUNTIME='--tos-tasks-couture-v4-runtime'
V5_RUNTIME='--tos-tasks-flagship-v5-runtime'
V5D_RUNTIME='--tos-tasks-flagship-v5d-runtime'

DIST="$ROOT/frontend/dist"
LIVE_PARENT="/opt/apps/tamiyouz-front"
LIVE="$LIVE_PARENT/build"
STAMP="$(date +%Y%m%d-%H%M%S)"
STAGE="$LIVE_PARENT/build.phase03-tasks-v5d.new.$$"
BACKUP="$LIVE_PARENT/build.phase03-tasks-v5d.backup-$STAMP"

fail() {
  echo "PHASE03_TASKS_FLAGSHIP_SIGNATURE_V5D=FAIL"
  echo "ERROR=$1" >&2
  exit "${2:-1}"
}

[ -d "$ROOT/.git" ] || fail "TOS repository not found" 2
[ -d "$PATCH_REPO_ROOT/.git" ] || fail "TOS-Patchs repository not found" 3
[ -f "$V5_SOURCE" ] || fail "Original V5 CSS source missing" 4
[ -f "$FALLBACK_SOURCE" ] || fail "V5D fallback CSS missing" 5
[ -f "$ROOT/$MAIN_TARGET" ] || fail "main.jsx missing" 6
[ -f "$ROOT/$TASKS_TARGET" ] || fail "ProfessionalTaskBoard.jsx missing" 7
[ -f "$ROOT/$CSS_TARGET" ] || fail "Tasks stylesheet missing" 8
[ -d "$LIVE" ] || fail "Live frontend root missing" 9

git -C "$ROOT" diff --cached --quiet || fail "Staged changes exist; stop" 10
git -C "$ROOT" diff --quiet -- "$MAIN_TARGET" "$TASKS_TARGET" "$CSS_TARGET" || fail "Reviewed tracked files are already modified" 11

[ "$(git -C "$ROOT" hash-object "$MAIN_TARGET")" = "$EXPECTED_MAIN_BLOB" ] || fail "main.jsx content differs from reviewed baseline" 12
[ "$(git -C "$ROOT" hash-object "$TASKS_TARGET")" = "$EXPECTED_TASKS_BLOB" ] || fail "ProfessionalTaskBoard content differs from reviewed baseline" 13
[ "$(git -C "$ROOT" hash-object "$CSS_TARGET")" = "$EXPECTED_CSS_BLOB" ] || fail "Tasks stylesheet content differs from reviewed V4 baseline" 14

[ "$(grep -Fc -- "$V4_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V4 runtime sentinel missing" 15
[ "$(grep -Fc -- "$V5_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "0" ] || fail "V5 already present unexpectedly" 16
[ "$(grep -Fc -- "$V5D_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "0" ] || fail "V5D already present unexpectedly" 17

# Verify patch sources are exactly what TOS-Patchs HEAD contains.
for source in "$V5_SOURCE" "$FALLBACK_SOURCE"; do
  rel="${source#$PATCH_REPO_ROOT/}"
  [ "$(git -C "$PATCH_REPO_ROOT" hash-object "$source")" = "$(git -C "$PATCH_REPO_ROOT" rev-parse "HEAD:$rel")" ] || fail "Patch source differs from TOS-Patchs HEAD: $rel" 18
done

python3 - "$ROOT/$TASKS_TARGET" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text()

replacements = [
    (
        '<div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">',
        '<div className="tos-task-kpi-deck grid gap-3 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">',
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
cat "$V5_SOURCE" >> "$ROOT/$CSS_TARGET"
printf '\n' >> "$ROOT/$CSS_TARGET"
cat "$FALLBACK_SOURCE" >> "$ROOT/$CSS_TARGET"

[ "$(grep -Fc -- "$V5_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V5 runtime sentinel missing after append" 19
[ "$(grep -Fc -- "$V5D_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V5D runtime sentinel missing after append" 20
[ "$(grep -Fc -- 'tos-task-kpi-deck' "$ROOT/$TASKS_TARGET" || true)" = "1" ] || fail "KPI semantic hook missing" 21
[ "$(grep -Fc -- 'tos-task-kanban-shell' "$ROOT/$TASKS_TARGET" || true)" = "1" ] || fail "Kanban shell semantic hook missing" 22
[ "$(grep -Fc -- 'tos-task-kanban-hero' "$ROOT/$TASKS_TARGET" || true)" = "1" ] || fail "Kanban hero semantic hook missing" 23

git -C "$ROOT" diff --check -- "$TASKS_TARGET" "$CSS_TARGET"

cd "$ROOT/frontend"
npm run build
cd "$ROOT"

[ -f "$DIST/index.html" ] || fail "Built dist index missing" 24
grep -RFlq -- "$V5_RUNTIME" "$DIST/assets" || fail "V5 runtime sentinel missing from dist assets" 25
grep -RFlq -- "$V5D_RUNTIME" "$DIST/assets" || fail "V5D runtime sentinel missing from dist assets" 26
grep -RFlq -- 'tos-task-kanban-shell' "$DIST/assets" || fail "Kanban semantic hook missing from dist" 27

rm -rf "$STAGE"
mkdir -p "$STAGE"
cp -a "$DIST/." "$STAGE/"
[ -f "$STAGE/index.html" ] || fail "Staged index missing" 28
grep -RFlq -- "$V5D_RUNTIME" "$STAGE/assets" || fail "V5D runtime sentinel missing from staged assets" 29

mv "$LIVE" "$BACKUP"
if ! mv "$STAGE" "$LIVE"; then
  mv "$BACKUP" "$LIVE" || true
  fail "Failed to activate V5D live build; rollback attempted" 30
fi
if ! grep -RFlq -- "$V5D_RUNTIME" "$LIVE/assets"; then
  rm -rf "$LIVE"
  mv "$BACKUP" "$LIVE" || true
  fail "Live V5D runtime sentinel missing; rolled back" 31
fi

# Only the intended tracked files may differ. Ignore harmless untracked recovery folders.
TRACKED_CHANGED="$(git -C "$ROOT" diff --name-only | sort)"
EXPECTED_CHANGED="$(printf '%s\n%s\n' "$TASKS_TARGET" "$CSS_TARGET" | sort)"
[ "$TRACKED_CHANGED" = "$EXPECTED_CHANGED" ] || {
  echo "--- TRACKED CHANGES ---"
  printf '%s\n' "$TRACKED_CHANGED"
  fail "Unexpected tracked files changed" 32
}

git -C "$ROOT" diff --cached --quiet || fail "Unexpected staged changes after patch" 33

FINAL_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"
echo "PHASE03_TASKS_FLAGSHIP_SIGNATURE_V5D=PASS"
echo "SCREEN=Tasks"
echo "STATE=Active_Task_Board"
echo "RECOVERY=CLEAN_EXACT_V4_TO_V5"
echo "LEGACY_TASK_CARD_GUARDS=NOT_USED"
echo "TASK_CARD_TARGETING=STRUCTURAL_ARTICLE_SELECTOR"
echo "KPI_DECK=FLAGSHIP"
echo "KANBAN_SHELL=FLAGSHIP"
echo "KANBAN_HERO=FLAGSHIP"
echo "BUSINESS_LOGIC_CHANGED=NO"
echo "BUILD_RESULT=PASS"
echo "LIVE_DEPLOY=PASS"
echo "SOURCE_CSS_SHA256=$FINAL_SHA"
echo "NO_COMMIT_OR_PUSH=YES"
echo "--- GIT STATUS ---"
git -C "$ROOT" status --short
