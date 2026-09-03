#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/var/www/TOS}"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_REPO_ROOT="$(cd "$PATCH_DIR/.." && pwd)"
SOURCE_APPEND="$PATCH_DIR/projects-platinum-contrast-v7.append.css"

MAIN_TARGET="frontend/src/main.jsx"
PROJECTS_TARGET="frontend/src/pages/ProjectsPage.jsx"
CSS_TARGET="frontend/src/styles/projects-github-reference.css"

EXPECTED_MAIN_HEAD_BLOB="10a76aae2e1c5a20ce84d28e304c565a96aef500"
EXPECTED_PROJECTS_HEAD_BLOB="1720111a2bab77133eac9f7c754ddd89a58fa179"
EXPECTED_V6_CSS_SHA256="239dbbfbf9bc679a61f47bc005831bd4c329a3496564271025bf4c04f741a327"
IMPORT_LINE='import "./styles/projects-github-reference.css";'
V6_RUNTIME='--tos-projects-ultra-premium-v6-runtime'
V7_RUNTIME='--tos-projects-platinum-v7-runtime'

DIST="$ROOT/frontend/dist"
LIVE_PARENT="/opt/apps/tamiyouz-front"
LIVE="$LIVE_PARENT/build"
STAMP="$(date +%Y%m%d-%H%M%S)"
STAGE="$LIVE_PARENT/build.phase02-platinum-v7.new.$$"
BACKUP="$LIVE_PARENT/build.phase02-platinum-v7.backup-$STAMP"

fail() {
  echo "PHASE02_PROJECTS_PLATINUM_CONTRAST_V7=FAIL"
  echo "ERROR=$1" >&2
  exit "${2:-1}"
}

[ -d "$ROOT/.git" ] || fail "TOS repository not found" 2
[ -d "$PATCH_REPO_ROOT/.git" ] || fail "TOS-Patchs repository not found" 3
[ -f "$SOURCE_APPEND" ] || fail "Missing V7 CSS source" 4
[ -f "$ROOT/$MAIN_TARGET" ] || fail "Missing main.jsx" 5
[ -f "$ROOT/$PROJECTS_TARGET" ] || fail "Missing ProjectsPage.jsx" 6
[ -f "$ROOT/$CSS_TARGET" ] || fail "Missing Projects stylesheet" 7
[ -d "$LIVE" ] || fail "Live frontend root missing" 8

SOURCE_REL="${SOURCE_APPEND#$PATCH_REPO_ROOT/}"
[ "$(git -C "$PATCH_REPO_ROOT" hash-object "$SOURCE_APPEND")" = "$(git -C "$PATCH_REPO_ROOT" rev-parse "HEAD:$SOURCE_REL")" ] || fail "V7 patch source differs from TOS-Patchs HEAD" 9

git -C "$ROOT" diff --cached --quiet || fail "Staged changes exist; stop" 10
[ "$(git -C "$ROOT" rev-parse "HEAD:$MAIN_TARGET")" = "$EXPECTED_MAIN_HEAD_BLOB" ] || fail "Committed main.jsx baseline changed" 11
[ "$(git -C "$ROOT" rev-parse "HEAD:$PROJECTS_TARGET")" = "$EXPECTED_PROJECTS_HEAD_BLOB" ] || fail "Committed ProjectsPage.jsx baseline changed" 12
[ "$(grep -Fxc "$IMPORT_LINE" "$ROOT/$MAIN_TARGET" || true)" = "1" ] || fail "Projects CSS import missing or duplicated" 13
[ "$(grep -Fc -- "$V6_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V6 runtime baseline missing" 14

STATUS="$(git -C "$ROOT" status --porcelain=v1 --untracked-files=all)"
PATHS="$(printf '%s\n' "$STATUS" | sed '/^$/d' | cut -c4- | sort -u)"
PRE_V7_PATHS="$(printf '%s\n%s\n' "$MAIN_TARGET" "$CSS_TARGET" | sort)"
V7_PATHS="$(printf '%s\n%s\n%s\n' "$MAIN_TARGET" "$PROJECTS_TARGET" "$CSS_TARGET" | sort)"
[ "$PATHS" = "$PRE_V7_PATHS" ] || [ "$PATHS" = "$V7_PATHS" ] || {
  echo "--- PRE-EXISTING STATUS ---"
  printf '%s\n' "$STATUS"
  fail "Unexpected working-tree paths before V7" 15
}

V7_COUNT="$(grep -Fc -- "$V7_RUNTIME" "$ROOT/$CSS_TARGET" || true)"
[ "$V7_COUNT" -le 1 ] || fail "Duplicate V7 runtime sentinel" 16

if [ "$V7_COUNT" = "0" ]; then
  CURRENT_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"
  echo "BASELINE_CSS_SHA256=$CURRENT_SHA"
  [ "$CURRENT_SHA" = "$EXPECTED_V6_CSS_SHA256" ] || fail "Projects CSS is not exact reviewed V6 baseline" 17
  printf '\n' >> "$ROOT/$CSS_TARGET"
  cat "$SOURCE_APPEND" >> "$ROOT/$CSS_TARGET"
  CSS_ACTION="APPLIED_PLATINUM_CONTRAST_V7"
else
  CSS_ACTION="VALIDATED_EXISTING_V7"
fi

python3 - "$ROOT/$PROJECTS_TARGET" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text()

replacements = [
    (
        '<section className="overflow-hidden rounded-[22px] border border-zinc-200/70 bg-white shadow-[0_12px_34px_rgba(15,23,42,0.045)] ring-1 ring-white/70 dark:border-zinc-800 dark:bg-zinc-950 dark:ring-white/[0.025]">',
        '<section className="tos-project-list-shell overflow-hidden rounded-[22px] border border-zinc-200/70 bg-white shadow-[0_12px_34px_rgba(15,23,42,0.045)] ring-1 ring-white/70 dark:border-zinc-800 dark:bg-zinc-950 dark:ring-white/[0.025]">',
        'tos-project-list-shell',
    ),
    (
        '"group grid w-full gap-3 border-b border-zinc-100 px-4 py-3 text-start transition-colors last:border-b-0 hover:bg-zinc-50/80 dark:border-zinc-800 dark:hover:bg-white/[0.035] lg:grid-cols-[minmax(220px,1.45fr)_minmax(100px,.8fr)_92px_120px_72px_104px] lg:items-center",',
        '"tos-project-list-row group grid w-full gap-3 border-b border-zinc-100 px-4 py-3 text-start transition-colors last:border-b-0 hover:bg-zinc-50/80 dark:border-zinc-800 dark:hover:bg-white/[0.035] lg:grid-cols-[minmax(220px,1.45fr)_minmax(100px,.8fr)_92px_120px_72px_104px] lg:items-center",',
        'tos-project-list-row group grid',
    ),
    (
        'selected && "bg-gradient-to-r from-amber-50/90 via-white to-white ring-1 ring-inset ring-amber-200/80 shadow-[0_10px_30px_rgba(245,158,11,0.08)] dark:from-amber-500/10 dark:via-zinc-950 dark:to-zinc-950 dark:ring-amber-500/20"',
        'selected && "tos-project-list-row--selected bg-gradient-to-r from-amber-50/90 via-white to-white ring-1 ring-inset ring-amber-200/80 shadow-[0_10px_30px_rgba(245,158,11,0.08)] dark:from-amber-500/10 dark:via-zinc-950 dark:to-zinc-950 dark:ring-amber-500/20"',
        'tos-project-list-row--selected',
    ),
    (
        '<aside className="self-start overflow-hidden rounded-[22px] border border-zinc-200/70 bg-white shadow-[0_12px_34px_rgba(15,23,42,0.055)] ring-1 ring-white/70 dark:border-zinc-800 dark:bg-zinc-950 dark:ring-white/[0.025] 2xl:sticky 2xl:top-4">',
        '<aside className="tos-project-inspector self-start overflow-hidden rounded-[22px] border border-zinc-200/70 bg-white shadow-[0_12px_34px_rgba(15,23,42,0.055)] ring-1 ring-white/70 dark:border-zinc-800 dark:bg-zinc-950 dark:ring-white/[0.025] 2xl:sticky 2xl:top-4">',
        'tos-project-inspector self-start',
    ),
]

for old, new, marker in replacements:
    count = text.count(marker)
    if count == 1:
        continue
    if count != 0:
        raise SystemExit(f'unexpected marker count for {marker}: {count}')
    old_count = text.count(old)
    if old_count != 1:
        raise SystemExit(f'expected exact source target once for {marker}, got {old_count}')
    text = text.replace(old, new, 1)

path.write_text(text)
PY

[ "$(grep -Fc 'tos-project-list-shell' "$ROOT/$PROJECTS_TARGET" || true)" = "1" ] || fail "Project list shell hook missing" 18
[ "$(grep -Fc 'tos-project-list-row group grid' "$ROOT/$PROJECTS_TARGET" || true)" = "1" ] || fail "Project row hook missing" 19
[ "$(grep -Fc 'tos-project-list-row--selected' "$ROOT/$PROJECTS_TARGET" || true)" = "1" ] || fail "Selected row hook missing" 20
[ "$(grep -Fc 'tos-project-inspector self-start' "$ROOT/$PROJECTS_TARGET" || true)" = "1" ] || fail "Inspector hook missing" 21
[ "$(grep -Fc -- "$V7_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V7 runtime sentinel missing in source" 22

git -C "$ROOT" diff --check -- "$MAIN_TARGET" "$PROJECTS_TARGET" "$CSS_TARGET"

cd "$ROOT/frontend"
npm run build
cd "$ROOT"

[ -f "$DIST/index.html" ] || fail "Built dist index missing" 23
grep -RFlq -- "$V7_RUNTIME" "$DIST/assets" || fail "V7 runtime sentinel missing from dist assets" 24
grep -RFlq 'tos-project-list-row--selected' "$DIST/assets" || fail "V7 selected-row hook missing from dist assets" 25

rm -rf "$STAGE"
mkdir -p "$STAGE"
cp -a "$DIST/." "$STAGE/"
[ -f "$STAGE/index.html" ] || fail "Staged index missing" 26
grep -RFlq -- "$V7_RUNTIME" "$STAGE/assets" || fail "V7 runtime sentinel missing from staged assets" 27

mv "$LIVE" "$BACKUP"
if ! mv "$STAGE" "$LIVE"; then
  mv "$BACKUP" "$LIVE" || true
  fail "Failed to activate V7 live build; rollback attempted" 28
fi

if ! grep -RFlq -- "$V7_RUNTIME" "$LIVE/assets"; then
  rm -rf "$LIVE"
  mv "$BACKUP" "$LIVE" || true
  fail "Live V7 runtime sentinel missing; rolled back" 29
fi
if ! grep -RFlq 'tos-project-list-row--selected' "$LIVE/assets"; then
  rm -rf "$LIVE"
  mv "$BACKUP" "$LIVE" || true
  fail "Live V7 selected-row hook missing; rolled back" 30
fi

FINAL_STATUS="$(git -C "$ROOT" status --porcelain=v1 --untracked-files=all)"
FINAL_PATHS="$(printf '%s\n' "$FINAL_STATUS" | sed '/^$/d' | cut -c4- | sort -u)"
[ "$FINAL_PATHS" = "$V7_PATHS" ] || fail "Unexpected TOS files changed" 31

FINAL_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"
echo "PHASE02_PROJECTS_PLATINUM_CONTRAST_V7=PASS"
echo "SCREEN=Projects"
echo "PATCH_ACTION=$CSS_ACTION"
echo "DESIGN_SYSTEM=BLACK_TITANIUM_PLATINUM_CHAMPAGNE"
echo "SELECTED_ROW_FIX=DEDICATED_HOOK"
echo "CONTRAST_AUDIT=PASS_BY_STYLE_RULES"
echo "BUILD_RESULT=PASS"
echo "LIVE_DEPLOY=PASS"
echo "DIST_RUNTIME_SENTINEL=PASS"
echo "LIVE_RUNTIME_SENTINEL=PASS"
echo "CHANGED_FILES=$MAIN_TARGET,$PROJECTS_TARGET,$CSS_TARGET"
echo "CSS_SHA256=$FINAL_SHA"
echo "BUSINESS_LOGIC_CHANGED=NO"
echo "COMMIT_CREATED=NO"
echo "PUSH_PERFORMED=NO"
echo "READY_FOR_VISUAL_REVIEW=YES"
echo "--- GIT STATUS ---"
printf '%s\n' "$FINAL_STATUS"
