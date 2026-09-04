#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/var/www/TOS}"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_REPO_ROOT="$(cd "$PATCH_DIR/.." && pwd)"
SOURCE_APPEND="$PATCH_DIR/projects-light-visibility-recovery-v16.append.css"

MAIN_TARGET="frontend/src/main.jsx"
PROJECTS_TARGET="frontend/src/pages/ProjectsPage.jsx"
CSS_TARGET="frontend/src/styles/projects-github-reference.css"

EXPECTED_MAIN_HEAD_BLOB="10a76aae2e1c5a20ce84d28e304c565a96aef500"
EXPECTED_PROJECTS_HEAD_BLOB="1720111a2bab77133eac9f7c754ddd89a58fa179"
EXPECTED_V14_CSS_SHA256="223251c2c4ef5f676b6285c1635b1750edf17b36e3d3b0baf8e9017278826bca"
IMPORT_LINE='import "./styles/projects-github-reference.css";'
V14_RUNTIME='--tos-projects-light-final-v14-runtime'
V16_RUNTIME='--tos-projects-light-visibility-v16-runtime'

DIST="$ROOT/frontend/dist"
LIVE_PARENT="/opt/apps/tamiyouz-front"
LIVE="$LIVE_PARENT/build"
STAMP="$(date +%Y%m%d-%H%M%S)"
STAGE="$LIVE_PARENT/build.phase02-light-visibility-v16.new.$$"
BACKUP="$LIVE_PARENT/build.phase02-light-visibility-v16.backup-$STAMP"

fail() {
  echo "PHASE02_PROJECTS_LIGHT_VISIBILITY_RECOVERY_V16=FAIL"
  echo "ERROR=$1" >&2
  exit "${2:-1}"
}

[ -d "$ROOT/.git" ] || fail "TOS repository not found" 2
[ -d "$PATCH_REPO_ROOT/.git" ] || fail "TOS-Patchs repository not found" 3
[ -f "$SOURCE_APPEND" ] || fail "Missing V16 CSS source" 4
[ -f "$ROOT/$MAIN_TARGET" ] || fail "Missing main.jsx" 5
[ -f "$ROOT/$PROJECTS_TARGET" ] || fail "Missing ProjectsPage.jsx" 6
[ -f "$ROOT/$CSS_TARGET" ] || fail "Missing Projects stylesheet" 7
[ -d "$LIVE" ] || fail "Live frontend root missing" 8

SOURCE_REL="${SOURCE_APPEND#$PATCH_REPO_ROOT/}"
[ "$(git -C "$PATCH_REPO_ROOT" hash-object "$SOURCE_APPEND")" = "$(git -C "$PATCH_REPO_ROOT" rev-parse "HEAD:$SOURCE_REL")" ] || fail "V16 patch source differs from TOS-Patchs HEAD" 9

git -C "$ROOT" diff --cached --quiet || fail "Staged changes exist; stop" 10
[ "$(git -C "$ROOT" rev-parse "HEAD:$MAIN_TARGET")" = "$EXPECTED_MAIN_HEAD_BLOB" ] || fail "Committed main.jsx baseline changed" 11
[ "$(git -C "$ROOT" rev-parse "HEAD:$PROJECTS_TARGET")" = "$EXPECTED_PROJECTS_HEAD_BLOB" ] || fail "Committed ProjectsPage.jsx baseline changed" 12
[ "$(grep -Fxc "$IMPORT_LINE" "$ROOT/$MAIN_TARGET" || true)" = "1" ] || fail "Projects CSS import missing or duplicated" 13
[ "$(grep -Fc -- "$V14_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V14 runtime baseline missing" 14

STATUS="$(git -C "$ROOT" status --porcelain=v1 --untracked-files=all)"
PATHS="$(printf '%s\n' "$STATUS" | sed '/^$/d' | cut -c4- | sort -u)"
EXPECTED_PATHS="$(printf '%s\n%s\n%s\n' "$MAIN_TARGET" "$PROJECTS_TARGET" "$CSS_TARGET" | sort)"
[ "$PATHS" = "$EXPECTED_PATHS" ] || {
  echo "--- PRE-EXISTING STATUS ---"
  printf '%s\n' "$STATUS"
  fail "Expected exact reviewed V14 working-tree paths only" 15
}

CURRENT_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"
[ "$CURRENT_SHA" = "$EXPECTED_V14_CSS_SHA256" ] || fail "Projects CSS is not exact reviewed V14 baseline" 16

python3 - "$ROOT/$PROJECTS_TARGET" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text()

# Normalize inspector status from either pre-V14 or V14 state.
if 'id="tos-project-inspector-status-anchor"' not in text:
    v14 = '<Badge tone={STATUS_TONES[selectedProject.status]} className="tos-project-inspector-status">{labels.status[selectedProject.status] || ui.project}</Badge>'
    base = '<Badge tone={STATUS_TONES[selectedProject.status]}>{labels.status[selectedProject.status] || ui.project}</Badge>'
    replacement = '<span id="tos-project-inspector-status-anchor"><Badge tone={STATUS_TONES[selectedProject.status]} className="tos-project-inspector-status">{labels.status[selectedProject.status] || ui.project}</Badge></span>'
    if v14 in text:
        text = text.replace(v14, replacement, 1)
    elif base in text:
        text = text.replace(base, replacement, 1)
    else:
        raise SystemExit('could not locate inspector status badge in current V14 working tree')

# Normalize Project Overview gauge from either pre-V14 or V14 state.
if 'id="tos-project-overview-progress"' not in text:
    open_v14 = '<div className="tos-project-overview-progress grid h-14 w-14 place-items-center rounded-full p-1.5" style={{ background: `conic-gradient(#f59e0b ${selectedProgress}%, #f4f4f5 0)` }}>'
    open_base = '<div className="grid h-14 w-14 place-items-center rounded-full p-1.5" style={{ background: `conic-gradient(#f59e0b ${selectedProgress}%, #f4f4f5 0)` }}>'
    open_new = '<div id="tos-project-overview-progress" className="tos-project-overview-progress grid h-14 w-14 place-items-center rounded-full p-1.5" style={{ "--tos-project-progress": `${selectedProgress}%`, background: `conic-gradient(#f59e0b ${selectedProgress}%, #f4f4f5 0)` }}>'
    if open_v14 in text:
        text = text.replace(open_v14, open_new, 1)
    elif open_base in text:
        text = text.replace(open_base, open_new, 1)
    else:
        raise SystemExit('could not locate Project Overview progress outer markup in current V14 working tree')

if 'id="tos-project-overview-progress-value"' not in text:
    inner_v14 = '<div className="tos-project-overview-progress-value grid h-full w-full place-items-center rounded-full bg-white text-[11px] font-black text-zinc-950 dark:bg-zinc-950 dark:text-white">{selectedProgress}%</div>'
    inner_base = '<div className="grid h-full w-full place-items-center rounded-full bg-white text-[11px] font-black text-zinc-950 dark:bg-zinc-950 dark:text-white">{selectedProgress}%</div>'
    inner_new = '<div id="tos-project-overview-progress-value" className="tos-project-overview-progress-value grid h-full w-full place-items-center rounded-full bg-white text-[11px] font-black text-zinc-950 dark:bg-zinc-950 dark:text-white">{selectedProgress}%</div>'
    if inner_v14 in text:
        text = text.replace(inner_v14, inner_new, 1)
    elif inner_base in text:
        text = text.replace(inner_base, inner_new, 1)
    else:
        raise SystemExit('could not locate Project Overview progress value markup in current V14 working tree')

path.write_text(text)
PY

grep -Fq 'id="tos-project-inspector-status-anchor"' "$ROOT/$PROJECTS_TARGET" || fail "V16 inspector anchor missing" 17
grep -Fq 'id="tos-project-overview-progress"' "$ROOT/$PROJECTS_TARGET" || fail "V16 overview progress anchor missing" 18
grep -Fq 'id="tos-project-overview-progress-value"' "$ROOT/$PROJECTS_TARGET" || fail "V16 overview progress value anchor missing" 19
grep -Fq '"--tos-project-progress": `${selectedProgress}%`' "$ROOT/$PROJECTS_TARGET" || fail "V16 dynamic progress value missing" 20

V16_COUNT="$(grep -Fc -- "$V16_RUNTIME" "$ROOT/$CSS_TARGET" || true)"
[ "$V16_COUNT" = "0" ] || fail "V16 already present unexpectedly" 21
printf '\n' >> "$ROOT/$CSS_TARGET"
cat "$SOURCE_APPEND" >> "$ROOT/$CSS_TARGET"

[ "$(grep -Fc -- "$V16_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V16 runtime sentinel missing in source" 22

git -C "$ROOT" diff --check -- "$MAIN_TARGET" "$PROJECTS_TARGET" "$CSS_TARGET"

cd "$ROOT/frontend"
npm run build
cd "$ROOT"

[ -f "$DIST/index.html" ] || fail "Built dist index missing" 23
grep -RFlq -- "$V16_RUNTIME" "$DIST/assets" || fail "V16 runtime sentinel missing from dist assets" 24
grep -RFlq 'tos-project-inspector-status-anchor' "$DIST/assets" || fail "V16 status anchor missing from dist assets" 25
grep -RFlq 'tos-project-overview-progress-value' "$DIST/assets" || fail "V16 overview anchor missing from dist assets" 26

rm -rf "$STAGE"
mkdir -p "$STAGE"
cp -a "$DIST/." "$STAGE/"
[ -f "$STAGE/index.html" ] || fail "Staged index missing" 27
grep -RFlq -- "$V16_RUNTIME" "$STAGE/assets" || fail "V16 runtime sentinel missing from staged assets" 28

mv "$LIVE" "$BACKUP"
if ! mv "$STAGE" "$LIVE"; then
  mv "$BACKUP" "$LIVE" || true
  fail "Failed to activate V16 live build; rollback attempted" 29
fi

if ! grep -RFlq -- "$V16_RUNTIME" "$LIVE/assets"; then
  rm -rf "$LIVE"
  mv "$BACKUP" "$LIVE" || true
  fail "Live V16 runtime sentinel missing; rolled back" 30
fi

FINAL_STATUS="$(git -C "$ROOT" status --porcelain=v1 --untracked-files=all)"
FINAL_PATHS="$(printf '%s\n' "$FINAL_STATUS" | sed '/^$/d' | cut -c4- | sort -u)"
[ "$FINAL_PATHS" = "$EXPECTED_PATHS" ] || fail "Unexpected TOS files changed" 31

FINAL_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"
echo "PHASE02_PROJECTS_LIGHT_VISIBILITY_RECOVERY_V16=PASS"
echo "SCREEN=Projects"
echo "LIGHT_MODE_ONLY=YES"
echo "INSPECTOR_ACTIVE_BADGE=LOCKED"
echo "OVERVIEW_PROGRESS_GAUGE=LOCKED"
echo "OVERVIEW_PROGRESS_DYNAMIC=YES"
echo "DARK_MODE_CHANGED=NO"
echo "BUILD_RESULT=PASS"
echo "LIVE_DEPLOY=PASS"
echo "CSS_SHA256=$FINAL_SHA"
echo "BUSINESS_LOGIC_CHANGED=NO"
echo "COMMIT_CREATED=NO"
echo "PUSH_PERFORMED=NO"
echo "--- GIT STATUS ---"
printf '%s\n' "$FINAL_STATUS"
