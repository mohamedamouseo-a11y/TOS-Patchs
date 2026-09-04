#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/var/www/TOS}"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_REPO_ROOT="$(cd "$PATCH_DIR/.." && pwd)"
SOURCE_APPEND="$PATCH_DIR/projects-light-final-v14.append.css"

MAIN_TARGET="frontend/src/main.jsx"
PROJECTS_TARGET="frontend/src/pages/ProjectsPage.jsx"
CSS_TARGET="frontend/src/styles/projects-github-reference.css"

EXPECTED_MAIN_HEAD_BLOB="10a76aae2e1c5a20ce84d28e304c565a96aef500"
EXPECTED_PROJECTS_HEAD_BLOB="1720111a2bab77133eac9f7c754ddd89a58fa179"
EXPECTED_V13_CSS_SHA256="628a447514f123e21fe0748c3846f26f67dac6e8a19073d8c19017aa1ea5244d"
IMPORT_LINE='import "./styles/projects-github-reference.css";'
V13_RUNTIME='--tos-projects-light-micro-v13-runtime'
V14_RUNTIME='--tos-projects-light-final-v14-runtime'

DIST="$ROOT/frontend/dist"
LIVE_PARENT="/opt/apps/tamiyouz-front"
LIVE="$LIVE_PARENT/build"
STAMP="$(date +%Y%m%d-%H%M%S)"
STAGE="$LIVE_PARENT/build.phase02-light-final-v14.new.$$"
BACKUP="$LIVE_PARENT/build.phase02-light-final-v14.backup-$STAMP"

fail() {
  echo "PHASE02_PROJECTS_LIGHT_FINAL_V14=FAIL"
  echo "ERROR=$1" >&2
  exit "${2:-1}"
}

[ -d "$ROOT/.git" ] || fail "TOS repository not found" 2
[ -d "$PATCH_REPO_ROOT/.git" ] || fail "TOS-Patchs repository not found" 3
[ -f "$SOURCE_APPEND" ] || fail "Missing V14 CSS source" 4
[ -f "$ROOT/$MAIN_TARGET" ] || fail "Missing main.jsx" 5
[ -f "$ROOT/$PROJECTS_TARGET" ] || fail "Missing ProjectsPage.jsx" 6
[ -f "$ROOT/$CSS_TARGET" ] || fail "Missing Projects stylesheet" 7
[ -d "$LIVE" ] || fail "Live frontend root missing" 8

SOURCE_REL="${SOURCE_APPEND#$PATCH_REPO_ROOT/}"
[ "$(git -C "$PATCH_REPO_ROOT" hash-object "$SOURCE_APPEND")" = "$(git -C "$PATCH_REPO_ROOT" rev-parse "HEAD:$SOURCE_REL")" ] || fail "V14 patch source differs from TOS-Patchs HEAD" 9

git -C "$ROOT" diff --cached --quiet || fail "Staged changes exist; stop" 10
[ "$(git -C "$ROOT" rev-parse "HEAD:$MAIN_TARGET")" = "$EXPECTED_MAIN_HEAD_BLOB" ] || fail "Committed main.jsx baseline changed" 11
[ "$(git -C "$ROOT" rev-parse "HEAD:$PROJECTS_TARGET")" = "$EXPECTED_PROJECTS_HEAD_BLOB" ] || fail "Committed ProjectsPage.jsx baseline changed" 12
[ "$(grep -Fxc "$IMPORT_LINE" "$ROOT/$MAIN_TARGET" || true)" = "1" ] || fail "Projects CSS import missing or duplicated" 13
[ "$(grep -Fc -- "$V13_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V13 runtime baseline missing" 14

STATUS="$(git -C "$ROOT" status --porcelain=v1 --untracked-files=all)"
PATHS="$(printf '%s\n' "$STATUS" | sed '/^$/d' | cut -c4- | sort -u)"
EXPECTED_PATHS="$(printf '%s\n%s\n%s\n' "$MAIN_TARGET" "$PROJECTS_TARGET" "$CSS_TARGET" | sort)"
[ "$PATHS" = "$EXPECTED_PATHS" ] || {
  echo "--- PRE-EXISTING STATUS ---"
  printf '%s\n' "$STATUS"
  fail "Expected exact reviewed V13 working-tree paths only" 15
}

python3 - "$ROOT/$PROJECTS_TARGET" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text()

old_badge = '<Badge tone={STATUS_TONES[selectedProject.status]}>{labels.status[selectedProject.status] || ui.project}</Badge>'
new_badge = '<Badge tone={STATUS_TONES[selectedProject.status]} className="tos-project-inspector-status">{labels.status[selectedProject.status] || ui.project}</Badge>'
if 'tos-project-inspector-status' not in text:
    count = text.count(old_badge)
    if count != 1:
        raise SystemExit(f'expected inspector status badge once, got {count}')
    text = text.replace(old_badge, new_badge, 1)

old_progress = '<div className="grid h-14 w-14 place-items-center rounded-full p-1.5" style={{ background: `conic-gradient(#f59e0b ${selectedProgress}%, #f4f4f5 0)` }}><div className="grid h-full w-full place-items-center rounded-full bg-white text-[11px] font-black text-zinc-950 dark:bg-zinc-950 dark:text-white">{selectedProgress}%</div></div>'
new_progress = '<div className="tos-project-overview-progress grid h-14 w-14 place-items-center rounded-full p-1.5" style={{ background: `conic-gradient(#f59e0b ${selectedProgress}%, #f4f4f5 0)` }}><div className="tos-project-overview-progress-value grid h-full w-full place-items-center rounded-full bg-white text-[11px] font-black text-zinc-950 dark:bg-zinc-950 dark:text-white">{selectedProgress}%</div></div>'
if 'tos-project-overview-progress' not in text:
    count = text.count(old_progress)
    if count != 1:
        raise SystemExit(f'expected project overview progress once, got {count}')
    text = text.replace(old_progress, new_progress, 1)

path.write_text(text)
PY

grep -Fq 'tos-project-inspector-status' "$ROOT/$PROJECTS_TARGET" || fail "Inspector status hook missing" 16
grep -Fq 'tos-project-overview-progress grid' "$ROOT/$PROJECTS_TARGET" || fail "Overview progress hook missing" 17
grep -Fq 'tos-project-overview-progress-value grid' "$ROOT/$PROJECTS_TARGET" || fail "Overview progress value hook missing" 18

V14_COUNT="$(grep -Fc -- "$V14_RUNTIME" "$ROOT/$CSS_TARGET" || true)"
[ "$V14_COUNT" -le 1 ] || fail "Duplicate V14 runtime sentinel" 19

if [ "$V14_COUNT" = "0" ]; then
  CURRENT_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"
  echo "BASELINE_CSS_SHA256=$CURRENT_SHA"
  [ "$CURRENT_SHA" = "$EXPECTED_V13_CSS_SHA256" ] || fail "Projects CSS is not exact reviewed V13 baseline" 20
  printf '\n' >> "$ROOT/$CSS_TARGET"
  cat "$SOURCE_APPEND" >> "$ROOT/$CSS_TARGET"
  PATCH_ACTION="APPLIED_LIGHT_FINAL_V14"
else
  PATCH_ACTION="VALIDATED_EXISTING_LIGHT_FINAL_V14"
fi

[ "$(grep -Fc -- "$V14_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V14 runtime sentinel missing in source" 21

git -C "$ROOT" diff --check -- "$MAIN_TARGET" "$PROJECTS_TARGET" "$CSS_TARGET"

cd "$ROOT/frontend"
npm run build
cd "$ROOT"

[ -f "$DIST/index.html" ] || fail "Built dist index missing" 22
grep -RFlq -- "$V14_RUNTIME" "$DIST/assets" || fail "V14 runtime sentinel missing from dist assets" 23
grep -RFlq 'tos-project-inspector-status' "$DIST/assets" || fail "Inspector status hook missing from dist assets" 24
grep -RFlq 'tos-project-overview-progress' "$DIST/assets" || fail "Overview progress hook missing from dist assets" 25

rm -rf "$STAGE"
mkdir -p "$STAGE"
cp -a "$DIST/." "$STAGE/"
[ -f "$STAGE/index.html" ] || fail "Staged index missing" 26
grep -RFlq -- "$V14_RUNTIME" "$STAGE/assets" || fail "V14 runtime sentinel missing from staged assets" 27

mv "$LIVE" "$BACKUP"
if ! mv "$STAGE" "$LIVE"; then
  mv "$BACKUP" "$LIVE" || true
  fail "Failed to activate V14 live build; rollback attempted" 28
fi

if ! grep -RFlq -- "$V14_RUNTIME" "$LIVE/assets"; then
  rm -rf "$LIVE"
  mv "$BACKUP" "$LIVE" || true
  fail "Live V14 runtime sentinel missing; rolled back" 29
fi

FINAL_STATUS="$(git -C "$ROOT" status --porcelain=v1 --untracked-files=all)"
FINAL_PATHS="$(printf '%s\n' "$FINAL_STATUS" | sed '/^$/d' | cut -c4- | sort -u)"
[ "$FINAL_PATHS" = "$EXPECTED_PATHS" ] || fail "Unexpected TOS files changed" 30

FINAL_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"
echo "PHASE02_PROJECTS_LIGHT_FINAL_V14=PASS"
echo "SCREEN=Projects"
echo "PATCH_ACTION=$PATCH_ACTION"
echo "LIGHT_MODE_ONLY=YES"
echo "INSPECTOR_ACTIVE_BADGE=FIXED"
echo "OVERVIEW_PROGRESS_GAUGE=FIXED"
echo "DARK_MODE_CHANGED=NO"
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
