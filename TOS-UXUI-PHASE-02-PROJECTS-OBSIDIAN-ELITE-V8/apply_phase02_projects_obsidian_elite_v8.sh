#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/var/www/TOS}"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_REPO_ROOT="$(cd "$PATCH_DIR/.." && pwd)"
SOURCE_APPEND="$PATCH_DIR/projects-obsidian-elite-v8.append.css"

MAIN_TARGET="frontend/src/main.jsx"
PROJECTS_TARGET="frontend/src/pages/ProjectsPage.jsx"
CSS_TARGET="frontend/src/styles/projects-github-reference.css"

EXPECTED_MAIN_HEAD_BLOB="10a76aae2e1c5a20ce84d28e304c565a96aef500"
EXPECTED_PROJECTS_HEAD_BLOB="1720111a2bab77133eac9f7c754ddd89a58fa179"
EXPECTED_V7_CSS_SHA256="fc367d543e912c37d97c56ecc0325e3614ecce06a794b6fc37f56314233ed536"
IMPORT_LINE='import "./styles/projects-github-reference.css";'
V7_RUNTIME='--tos-projects-platinum-v7-runtime'
V8_RUNTIME='--tos-projects-obsidian-elite-v8-runtime'

DIST="$ROOT/frontend/dist"
LIVE_PARENT="/opt/apps/tamiyouz-front"
LIVE="$LIVE_PARENT/build"
STAMP="$(date +%Y%m%d-%H%M%S)"
STAGE="$LIVE_PARENT/build.phase02-obsidian-v8.new.$$"
BACKUP="$LIVE_PARENT/build.phase02-obsidian-v8.backup-$STAMP"

fail() {
  echo "PHASE02_PROJECTS_OBSIDIAN_ELITE_V8=FAIL"
  echo "ERROR=$1" >&2
  exit "${2:-1}"
}

[ -d "$ROOT/.git" ] || fail "TOS repository not found" 2
[ -d "$PATCH_REPO_ROOT/.git" ] || fail "TOS-Patchs repository not found" 3
[ -f "$SOURCE_APPEND" ] || fail "Missing V8 CSS source" 4
[ -f "$ROOT/$MAIN_TARGET" ] || fail "Missing main.jsx" 5
[ -f "$ROOT/$PROJECTS_TARGET" ] || fail "Missing ProjectsPage.jsx" 6
[ -f "$ROOT/$CSS_TARGET" ] || fail "Missing Projects stylesheet" 7
[ -d "$LIVE" ] || fail "Live frontend root missing" 8

SOURCE_REL="${SOURCE_APPEND#$PATCH_REPO_ROOT/}"
[ "$(git -C "$PATCH_REPO_ROOT" hash-object "$SOURCE_APPEND")" = "$(git -C "$PATCH_REPO_ROOT" rev-parse "HEAD:$SOURCE_REL")" ] || fail "V8 patch source differs from TOS-Patchs HEAD" 9

git -C "$ROOT" diff --cached --quiet || fail "Staged changes exist; stop" 10
[ "$(git -C "$ROOT" rev-parse "HEAD:$MAIN_TARGET")" = "$EXPECTED_MAIN_HEAD_BLOB" ] || fail "Committed main.jsx baseline changed" 11
[ "$(git -C "$ROOT" rev-parse "HEAD:$PROJECTS_TARGET")" = "$EXPECTED_PROJECTS_HEAD_BLOB" ] || fail "Committed ProjectsPage.jsx baseline changed" 12
[ "$(grep -Fxc "$IMPORT_LINE" "$ROOT/$MAIN_TARGET" || true)" = "1" ] || fail "Projects CSS import missing or duplicated" 13
[ "$(grep -Fc -- "$V7_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V7 runtime baseline missing" 14
[ "$(grep -Fc 'tos-project-list-row--selected' "$ROOT/$PROJECTS_TARGET" || true)" = "1" ] || fail "V7 selected-row hook missing" 15
[ "$(grep -Fc 'tos-project-inspector self-start' "$ROOT/$PROJECTS_TARGET" || true)" = "1" ] || fail "V7 inspector hook missing" 16

STATUS="$(git -C "$ROOT" status --porcelain=v1 --untracked-files=all)"
PATHS="$(printf '%s\n' "$STATUS" | sed '/^$/d' | cut -c4- | sort -u)"
EXPECTED_PATHS="$(printf '%s\n%s\n%s\n' "$MAIN_TARGET" "$PROJECTS_TARGET" "$CSS_TARGET" | sort)"
[ "$PATHS" = "$EXPECTED_PATHS" ] || {
  echo "--- PRE-EXISTING STATUS ---"
  printf '%s\n' "$STATUS"
  fail "Expected exact reviewed V7 working-tree paths only" 17
}

V8_COUNT="$(grep -Fc -- "$V8_RUNTIME" "$ROOT/$CSS_TARGET" || true)"
[ "$V8_COUNT" -le 1 ] || fail "Duplicate V8 runtime sentinel" 18

if [ "$V8_COUNT" = "0" ]; then
  CURRENT_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"
  echo "BASELINE_CSS_SHA256=$CURRENT_SHA"
  [ "$CURRENT_SHA" = "$EXPECTED_V7_CSS_SHA256" ] || fail "Projects CSS is not exact reviewed V7 baseline" 19
  printf '\n' >> "$ROOT/$CSS_TARGET"
  cat "$SOURCE_APPEND" >> "$ROOT/$CSS_TARGET"
  CSS_ACTION="APPLIED_OBSIDIAN_ELITE_V8"
else
  CSS_ACTION="VALIDATED_EXISTING_V8"
fi

python3 - "$ROOT/$PROJECTS_TARGET" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text()

replacements = [
    (
        'className={cn("grid gap-3 sm:grid-cols-2 xl:grid-cols-4", isAr ? "direction-rtl" : "direction-ltr")}',
        'className={cn("tos-projects-kpi-strip grid gap-3 sm:grid-cols-2 xl:grid-cols-4", isAr ? "direction-rtl" : "direction-ltr")}',
        'tos-projects-kpi-strip grid gap-3',
    ),
    (
        '<Card className="rounded-[24px] border-zinc-200/70 bg-white/92 p-3 shadow-[0_12px_34px_rgba(15,23,42,0.045)] ring-1 ring-white/70 backdrop-blur-xl dark:border-zinc-800 dark:bg-zinc-900/92 dark:ring-white/[0.025] md:p-3.5">',
        '<Card className="tos-projects-command-center rounded-[24px] border-zinc-200/70 bg-white/92 p-3 shadow-[0_12px_34px_rgba(15,23,42,0.045)] ring-1 ring-white/70 backdrop-blur-xl dark:border-zinc-800 dark:bg-zinc-900/92 dark:ring-white/[0.025] md:p-3.5">',
        'tos-projects-command-center rounded-[24px]',
    ),
    (
        'className="h-10 rounded-[13px] border-zinc-200/80 bg-zinc-50/70 px-3.5 text-[13px] shadow-[inset_0_1px_0_rgba(255,255,255,0.8)] transition focus:border-amber-300 focus:bg-white dark:border-zinc-800 dark:bg-zinc-950"',
        'className="tos-projects-search h-10 rounded-[13px] border-zinc-200/80 bg-zinc-50/70 px-3.5 text-[13px] shadow-[inset_0_1px_0_rgba(255,255,255,0.8)] transition focus:border-amber-300 focus:bg-white dark:border-zinc-800 dark:bg-zinc-950"',
        'tos-projects-search h-10',
    ),
    (
        'className="h-11 justify-center rounded-[14px] border border-zinc-200/80 bg-white px-4 text-zinc-700 shadow-sm hover:border-zinc-300 hover:bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-950 dark:text-zinc-200"',
        'className="tos-projects-filter-toggle h-11 justify-center rounded-[14px] border border-zinc-200/80 bg-white px-4 text-zinc-700 shadow-sm hover:border-zinc-300 hover:bg-zinc-50 dark:border-zinc-800 dark:bg-zinc-950 dark:text-zinc-200"',
        'tos-projects-filter-toggle h-11',
    ),
    (
        'className="h-11 rounded-[14px] border-zinc-200/80 bg-white px-4 shadow-sm dark:border-zinc-800 dark:bg-zinc-950"',
        'className="tos-projects-sort h-11 rounded-[14px] border-zinc-200/80 bg-white px-4 shadow-sm dark:border-zinc-800 dark:bg-zinc-950"',
        'tos-projects-sort h-11',
    ),
    (
        'onClick={() => setShowArchived((value) => !value)}\n            className={cn(',
        'onClick={() => setShowArchived((value) => !value)}\n            data-active={showArchived ? "true" : "false"}\n            className={cn(',
        'data-active={showArchived ? "true" : "false"}',
    ),
    (
        '"flex h-10 min-w-[150px] items-center justify-between rounded-[13px] border px-3.5 shadow-sm transition",',
        '"tos-projects-archive-toggle flex h-10 min-w-[150px] items-center justify-between rounded-[13px] border px-3.5 shadow-sm transition",',
        'tos-projects-archive-toggle flex h-10',
    ),
    (
        '<span className={cn("relative h-7 w-12 rounded-full transition", showArchived ? "bg-white/25 dark:bg-zinc-900/20" : "bg-zinc-200 dark:bg-zinc-800")}>',
        '<span className={cn("tos-projects-archive-switch relative h-7 w-12 rounded-full transition", showArchived ? "bg-white/25 dark:bg-zinc-900/20" : "bg-zinc-200 dark:bg-zinc-800")}>',
        'tos-projects-archive-switch relative',
    ),
    (
        '<span className={cn("absolute top-1 h-5 w-5 rounded-full bg-white shadow-sm transition-all", showArchived ? (isAr ? "right-1" : "left-1") : (isAr ? "right-6" : "left-6"), !showArchived && "bg-zinc-600 dark:bg-zinc-200")} />',
        '<span className={cn("tos-projects-archive-knob absolute top-1 h-5 w-5 rounded-full bg-white shadow-sm transition-all", showArchived ? (isAr ? "right-1" : "left-1") : (isAr ? "right-6" : "left-6"), !showArchived && "bg-zinc-600 dark:bg-zinc-200")} />',
        'tos-projects-archive-knob absolute',
    ),
    (
        'className="h-11 rounded-[14px] border border-amber-300/80 bg-gradient-to-r from-amber-300 to-orange-300 px-5 !text-zinc-950 text-zinc-950 shadow-[0_8px_18px_rgba(245,158,11,0.18)] hover:from-amber-200 hover:to-orange-200 dark:border-amber-300 dark:from-amber-300 dark:to-orange-300 dark:!text-zinc-950 dark:text-zinc-950 [&_*]:!text-zinc-950 [&_svg]:!stroke-zinc-950 [&_svg_*]:!stroke-zinc-950 dark:[&_*]:!text-zinc-950 dark:[&_svg]:!stroke-zinc-950 dark:[&_svg_*]:!stroke-zinc-950"',
        'className="tos-projects-primary-cta h-11 rounded-[14px] border border-amber-300/80 bg-gradient-to-r from-amber-300 to-orange-300 px-5 !text-zinc-950 text-zinc-950 shadow-[0_8px_18px_rgba(245,158,11,0.18)] hover:from-amber-200 hover:to-orange-200 dark:border-amber-300 dark:from-amber-300 dark:to-orange-300 dark:!text-zinc-950 dark:text-zinc-950 [&_*]:!text-zinc-950 [&_svg]:!stroke-zinc-950 [&_svg_*]:!stroke-zinc-950 dark:[&_*]:!text-zinc-950 dark:[&_svg]:!stroke-zinc-950 dark:[&_svg_*]:!stroke-zinc-950"',
        'tos-projects-primary-cta h-11',
    ),
    (
        'className="h-11 rounded-[14px] bg-white px-4 ring-1 ring-zinc-200/80 shadow-sm hover:bg-zinc-50 dark:bg-zinc-950 dark:ring-zinc-800"',
        'className="tos-projects-export-action h-11 rounded-[14px] bg-white px-4 ring-1 ring-zinc-200/80 shadow-sm hover:bg-zinc-50 dark:bg-zinc-950 dark:ring-zinc-800"',
        'tos-projects-export-action h-11',
    ),
    (
        '<div className="mt-3 overflow-hidden rounded-[18px] border border-zinc-200/70 bg-zinc-50/65 shadow-[inset_0_1px_0_rgba(255,255,255,0.8)] dark:border-zinc-800 dark:bg-white/[0.025]">',
        '<div className="tos-projects-filters-shell mt-3 overflow-hidden rounded-[18px] border border-zinc-200/70 bg-zinc-50/65 shadow-[inset_0_1px_0_rgba(255,255,255,0.8)] dark:border-zinc-800 dark:bg-white/[0.025]">',
        'tos-projects-filters-shell mt-3',
    ),
    (
        'selected && "tos-project-list-row--selected bg-gradient-to-r from-amber-50/90 via-white to-white ring-1 ring-inset ring-amber-200/80 shadow-[0_10px_30px_rgba(245,158,11,0.08)] dark:from-amber-500/10 dark:via-zinc-950 dark:to-zinc-950 dark:ring-amber-500/20"',
        'selected && "tos-project-list-row--selected"',
        'selected && "tos-project-list-row--selected"',
    ),
]

for old, new, marker in replacements:
    if marker in text:
        continue
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'expected exact source target once for {marker}, got {count}')
    text = text.replace(old, new, 1)

path.write_text(text)
PY

for marker in \
  'tos-projects-kpi-strip grid gap-3' \
  'tos-projects-command-center rounded-[24px]' \
  'tos-projects-search h-10' \
  'tos-projects-filter-toggle h-11' \
  'tos-projects-sort h-11' \
  'tos-projects-archive-toggle flex h-10' \
  'tos-projects-archive-switch relative' \
  'tos-projects-archive-knob absolute' \
  'tos-projects-primary-cta h-11' \
  'tos-projects-export-action h-11' \
  'tos-projects-filters-shell mt-3' \
  'selected && "tos-project-list-row--selected"'
do
  grep -Fq "$marker" "$ROOT/$PROJECTS_TARGET" || fail "V8 hook missing: $marker" 20
done

[ "$(grep -Fc -- "$V8_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V8 runtime sentinel missing in source" 21

git -C "$ROOT" diff --check -- "$MAIN_TARGET" "$PROJECTS_TARGET" "$CSS_TARGET"

cd "$ROOT/frontend"
npm run build
cd "$ROOT"

[ -f "$DIST/index.html" ] || fail "Built dist index missing" 22
grep -RFlq -- "$V8_RUNTIME" "$DIST/assets" || fail "V8 runtime sentinel missing from dist assets" 23
grep -RFlq 'tos-projects-archive-toggle' "$DIST/assets" || fail "Archive premium hook missing from dist assets" 24
grep -RFlq 'tos-project-list-row--selected' "$DIST/assets" || fail "Selected-row hook missing from dist assets" 25

rm -rf "$STAGE"
mkdir -p "$STAGE"
cp -a "$DIST/." "$STAGE/"
[ -f "$STAGE/index.html" ] || fail "Staged index missing" 26
grep -RFlq -- "$V8_RUNTIME" "$STAGE/assets" || fail "V8 runtime sentinel missing from staged assets" 27

mv "$LIVE" "$BACKUP"
if ! mv "$STAGE" "$LIVE"; then
  mv "$BACKUP" "$LIVE" || true
  fail "Failed to activate V8 live build; rollback attempted" 28
fi

if ! grep -RFlq -- "$V8_RUNTIME" "$LIVE/assets"; then
  rm -rf "$LIVE"
  mv "$BACKUP" "$LIVE" || true
  fail "Live V8 runtime sentinel missing; rolled back" 29
fi
if ! grep -RFlq 'tos-projects-archive-toggle' "$LIVE/assets"; then
  rm -rf "$LIVE"
  mv "$BACKUP" "$LIVE" || true
  fail "Live Archive hook missing; rolled back" 30
fi

FINAL_STATUS="$(git -C "$ROOT" status --porcelain=v1 --untracked-files=all)"
FINAL_PATHS="$(printf '%s\n' "$FINAL_STATUS" | sed '/^$/d' | cut -c4- | sort -u)"
[ "$FINAL_PATHS" = "$EXPECTED_PATHS" ] || fail "Unexpected TOS files changed" 31

FINAL_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"
echo "PHASE02_PROJECTS_OBSIDIAN_ELITE_V8=PASS"
echo "SCREEN=Projects"
echo "PATCH_ACTION=$CSS_ACTION"
echo "DESIGN_SYSTEM=OBSIDIAN_TITANIUM_PLATINUM_CHAMPAGNE"
echo "LIGHT_CONTRAST_AUDIT=APPLIED"
echo "ARCHIVE_CONTROL=PREMIUM_VAULT_SWITCH"
echo "SELECTED_ROW=SEMANTIC_CLASS_ONLY"
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
