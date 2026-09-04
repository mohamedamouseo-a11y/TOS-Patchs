#!/usr/bin/env bash
set -euo pipefail

echo "RUNNING=PHASE03_1_TASK_DETAILS_DECLUTTER_V1"

ROOT="${1:-/var/www/TOS}"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_REPO_ROOT="$(cd "$PATCH_DIR/.." && pwd)"
SOURCE_CSS="$PATCH_DIR/task-details-declutter-v1.css"

BOARD_TARGET="frontend/src/components/ProfessionalTaskBoard.jsx"
WORKSPACE_TARGET="frontend/src/pages/MyTaskWorkspace.jsx"
CSS_TARGET="frontend/src/styles/tasks-projects-premium-reference.css"
PARTS_TARGET="frontend/src/features/tasks/taskBoardParts.jsx"
EXPECTED_PARTS_HEAD_BLOB="9cd3df2a0a4263df4dc5ff61445d34616d3a79e5"

ROOT_HOOK='tos-task-details-modal'
WORKSPACE_HOOK='tos-my-workspace'
SAVE_HOOK='tos-save-description-button'
DATE_HOOK='tos-task-date-input'
DECLUTTER_LAYOUT_HOOK='tos-task-details-layout'
DECLUTTER_PROGRESS_HOOK='tos-task-progress-compact'
DECLUTTER_SIDE_HOOK='tos-task-side-rail'
DECLUTTER_TOOLBAR_HOOK='tos-task-editor-toolbar'
V5G_RUNTIME='--tos-my-workspace-dark-select-v5g-runtime'
V5I_RUNTIME='--tos-task-details-dark-contrast-v5i-runtime'
V5K_RUNTIME='--tos-task-details-dark-visibility-v5k-runtime'
V5L_RUNTIME='--tos-task-details-dark-visibility-v5l-runtime'
DECLUTTER_RUNTIME='--tos-task-details-declutter-v1-runtime'

DIST="$ROOT/frontend/dist"
LIVE_PARENT="/opt/apps/tamiyouz-front"
LIVE="$LIVE_PARENT/build"
STAMP="$(date +%Y%m%d-%H%M%S)"
STAGE="$LIVE_PARENT/build.phase03-1-declutter-v1.new.$$"
BACKUP="$LIVE_PARENT/build.phase03-1-declutter-v1.backup-$STAMP"

fail() {
  echo "PHASE03_1_TASK_DETAILS_DECLUTTER_V1=FAIL"
  echo "ERROR=$1" >&2
  exit "${2:-1}"
}

[ -d "$ROOT/.git" ] || fail "TOS repository not found" 2
[ -d "$PATCH_REPO_ROOT/.git" ] || fail "TOS-Patchs repository not found" 3
[ -f "$SOURCE_CSS" ] || fail "Declutter CSS source missing" 4
for path in "$BOARD_TARGET" "$WORKSPACE_TARGET" "$CSS_TARGET" "$PARTS_TARGET"; do
  [ -f "$ROOT/$path" ] || fail "Missing target: $path" 5
done
[ -d "$LIVE" ] || fail "Live frontend root missing" 6

git -C "$ROOT" diff --cached --quiet || fail "Staged changes exist; stop" 7

# Accept either the current pre-push V5L worktree or the same state already committed by TOS Push.
PRE_CHANGED="$(git -C "$ROOT" diff --name-only | sort)"
while IFS= read -r path; do
  [ -z "$path" ] && continue
  case "$path" in
    "$BOARD_TARGET"|"$WORKSPACE_TARGET"|"$CSS_TARGET") ;;
    *) fail "Unexpected tracked change before Phase 03.1: $path" 8 ;;
  esac
done <<< "$PRE_CHANGED"

[ "$(grep -Fc -- "$ROOT_HOOK" "$ROOT/$BOARD_TARGET" || true)" = "1" ] || fail "Task Details root hook missing or duplicated" 9
[ "$(grep -Fc -- "$WORKSPACE_HOOK" "$ROOT/$WORKSPACE_TARGET" || true)" = "1" ] || fail "My Workspace hook missing or duplicated" 10
[ "$(grep -Fc -- "$SAVE_HOOK" "$ROOT/$BOARD_TARGET" || true)" = "1" ] || fail "V5L save hook missing or duplicated" 11
[ "$(grep -Fc -- "$DATE_HOOK" "$ROOT/$BOARD_TARGET" || true)" = "2" ] || fail "V5L date hooks missing or duplicated" 12
[ "$(grep -Fc -- "$V5G_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V5G runtime missing or duplicated" 13
[ "$(grep -Fc -- "$V5I_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V5I runtime missing or duplicated" 14
[ "$(grep -Fc -- "$V5K_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V5K runtime missing or duplicated" 15
[ "$(grep -Fc -- "$V5L_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "V5L runtime missing or duplicated" 16

SOURCE_REL="${SOURCE_CSS#$PATCH_REPO_ROOT/}"
[ "$(git -C "$PATCH_REPO_ROOT" hash-object "$SOURCE_CSS")" = "$(git -C "$PATCH_REPO_ROOT" rev-parse "HEAD:$SOURCE_REL")" ] || fail "Declutter CSS source differs from TOS-Patchs HEAD" 17

DECLUTTER_COUNT="$(grep -Fc -- "$DECLUTTER_RUNTIME" "$ROOT/$CSS_TARGET" || true)"
LAYOUT_COUNT="$(grep -Fc -- "$DECLUTTER_LAYOUT_HOOK" "$ROOT/$BOARD_TARGET" || true)"
TOOLBAR_COUNT="$(grep -Fc -- "$DECLUTTER_TOOLBAR_HOOK" "$ROOT/$PARTS_TARGET" || true)"

if [ "$DECLUTTER_COUNT" = "0" ] && [ "$LAYOUT_COUNT" = "0" ] && [ "$TOOLBAR_COUNT" = "0" ]; then
  # taskBoardParts must still be the reviewed committed baseline before we add the declutter-only editor variant.
  [ "$(git -C "$ROOT" rev-parse "HEAD:$PARTS_TARGET")" = "$EXPECTED_PARTS_HEAD_BLOB" ] || fail "Committed taskBoardParts baseline changed" 18
  [ "$(git -C "$ROOT" hash-object "$PARTS_TARGET")" = "$EXPECTED_PARTS_HEAD_BLOB" ] || fail "taskBoardParts worktree is not clean baseline" 19

  python3 - "$ROOT/$BOARD_TARGET" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text()

def replace_once(old, new, label):
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label} anchor count={count}")
    text = text.replace(old, new, 1)

replace_once(
    '  const [sidebarAdvancedOpen, setSidebarAdvancedOpen] = useState(false);\n  const [isFullScreenWorkspace, setIsFullScreenWorkspace] = useState(true);',
    '  const [sidebarAdvancedOpen, setSidebarAdvancedOpen] = useState(false);\n  const [taskSidebarExpanded, setTaskSidebarExpanded] = useState(false);\n  const [isFullScreenWorkspace, setIsFullScreenWorkspace] = useState(true);',
    'sidebar state',
)

replace_once(
    '    setSidebarAdvancedOpen(false);\n    setIsFullScreenWorkspace(true);',
    '    setSidebarAdvancedOpen(false);\n    setTaskSidebarExpanded(false);\n    setIsFullScreenWorkspace(true);',
    'sidebar reset',
)

replace_once(
    '<div className="grid gap-4 xl:grid-cols-[320px_minmax(0,1fr)]" dir="ltr">',
    '<div className="tos-task-details-layout grid gap-4 xl:grid-cols-[320px_minmax(0,1fr)]" dir="ltr">',
    'details layout',
)
replace_once(
    '<main className="min-w-0 space-y-4 text-right xl:order-2" dir={modalDirection}>',
    '<main className="tos-task-main-column min-w-0 space-y-4 text-right xl:order-2" dir={modalDirection}>',
    'main column',
)
replace_once(
    '<section className="rounded-[24px] border border-slate-200 bg-white p-4 shadow-sm shadow-slate-100/70 dark:border-white/10 dark:bg-zinc-950 dark:shadow-black/20">',
    '<section className="tos-task-summary-compact rounded-[24px] border border-slate-200 bg-white p-4 shadow-sm shadow-slate-100/70 dark:border-white/10 dark:bg-zinc-950 dark:shadow-black/20">',
    'summary card',
)

progress_old = '''<section className="rounded-[32px] border border-slate-200 bg-white p-5 shadow-sm shadow-slate-100/80 dark:border-white/10 dark:bg-zinc-950 dark:shadow-black/20">
                <div className="mb-5 text-center">
                  <h3 className="inline-flex items-center justify-center gap-2 text-2xl font-black text-slate-950 dark:text-white"><ClipboardList size={19} className="text-amber-600" /> {modalUi.workflowProgress}</h3>'''
progress_new = progress_old.replace('<section className="', '<section className="tos-task-progress-compact ', 1)
replace_once(progress_old, progress_new, 'progress card')

replace_once(
    '<nav className="sticky top-0 z-30 rounded-[26px] border border-slate-200 bg-white/90 p-2 shadow-sm shadow-slate-100/80 backdrop-blur-xl dark:border-white/10 dark:bg-zinc-950/90 dark:shadow-black/20" aria-label={modalUi.taskDetails}>',
    '<nav className="tos-task-detail-tabs sticky top-0 z-30 rounded-[26px] border border-slate-200 bg-white/90 p-2 shadow-sm shadow-slate-100/80 backdrop-blur-xl dark:border-white/10 dark:bg-zinc-950/90 dark:shadow-black/20" aria-label={modalUi.taskDetails}>',
    'task tabs',
)

replace_once(
    '{activeTaskTab === "overview" && (\n              <section className={referencePanelClass}>',
    '{activeTaskTab === "overview" && (\n              <section className={`${referencePanelClass} tos-task-description-panel`}>',
    'description panel',
)

editor_old = '<PremiumTaskRichTextEditor value={draft.description || ""} onChange={(value) => setDraft((current) => ({ ...current, description: value }))} placeholder={modalUi.descriptionPlaceholder} minHeight="min-h-[470px]" label={modalUi.descriptionEditor} ui={modalUi} onInlineImageUpload={handleDescriptionImageUpload} variant="advanced" designBriefFiles={designBriefFiles} />'
editor_new = editor_old.replace('min-h-[470px]', 'min-h-[320px]').replace('variant="advanced"', 'variant="decluttered"')
replace_once(editor_old, editor_new, 'description editor')

aside_old = '<aside className="min-w-0 space-y-5 text-right xl:order-1 xl:sticky xl:top-0 xl:self-start" dir={modalDirection}>'
aside_new = '''<aside className="tos-task-side-rail min-w-0 space-y-5 text-right xl:order-1 xl:sticky xl:top-0 xl:self-start" data-expanded={taskSidebarExpanded ? "true" : "false"} dir={modalDirection}>
              <div className="tos-task-side-rail-head">
                <button type="button" onClick={() => setTaskSidebarExpanded((current) => !current)} className="tos-task-side-rail-toggle" aria-expanded={taskSidebarExpanded}>
                  <span>{taskSidebarExpanded ? (isAr ? "إخفاء التفاصيل الجانبية" : "Hide side details") : (isAr ? "التفاصيل الجانبية" : "Side details")}</span>
                  <ChevronDown size={15} className={`transition-transform ${taskSidebarExpanded ? "rotate-180" : ""}`} />
                </button>
                {!taskSidebarExpanded && (
                  <div className="tos-task-side-rail-summary">
                    <span>{isAr ? "المكلفون" : "Assignees"}: {currentAssigneeIds.length}</span>
                    <span>{isAr ? "المشروع" : "Project"}: {draft.project?.name || modalUi.noProject || "—"}</span>
                    <span>{isAr ? "النشاط" : "Activity"}: {draft.activities?.length || 0}</span>
                  </div>
                )}
              </div>'''
replace_once(aside_old, aside_new, 'side rail')

path.write_text(text)
PY

  python3 - "$ROOT/$PARTS_TARGET" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text()

def replace_once(old, new, label):
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label} anchor count={count}")
    text = text.replace(old, new, 1)

replace_once(
    '  const isAdvanced = variant === "advanced";\n  const isCompact = variant === "compact";',
    '  const isDecluttered = variant === "decluttered";\n  const isAdvanced = variant === "advanced" || isDecluttered;\n  const isCompact = variant === "compact";',
    'editor variant',
)
replace_once(
    '  const [isFullscreen, setIsFullscreen] = useState(false);\n  const [stats, setStats] = useState({ words: 0, characters: 0 });',
    '  const [isFullscreen, setIsFullscreen] = useState(false);\n  const [showExtendedFormatting, setShowExtendedFormatting] = useState(false);\n  const [stats, setStats] = useState({ words: 0, characters: 0 });',
    'extended formatting state',
)
replace_once(
    '<div className="border-t border-slate-200/70 px-3 py-2.5 dark:border-white/10" onMouseDown={handleToolbarMouseDown}>',
    '<div className="tos-task-editor-toolbar border-t border-slate-200/70 px-3 py-2.5 dark:border-white/10" data-extended={showExtendedFormatting ? "true" : "false"} onMouseDown={handleToolbarMouseDown}>',
    'toolbar hook',
)

marker = '<div className={groupClass}>'
labels = ['history', 'block', 'inline', 'list', 'align', 'color', 'insert']
search_from = text.find('tos-task-editor-toolbar')
if search_from < 0:
    raise SystemExit('toolbar marker missing after hook insertion')
for label in labels:
    idx = text.find(marker, search_from)
    if idx < 0:
        raise SystemExit(f'editor group missing: {label}')
    replacement = f'<div className={{`${{groupClass}} tos-editor-group-{label}`}}>'
    text = text[:idx] + replacement + text[idx + len(marker):]
    search_from = idx + len(replacement)

more_anchor = '''            </div>
          </div>
        </div>

        {colorPanel && ('''
more_insert = '''            </div>
            {isDecluttered && (
              <button
                type="button"
                onClick={() => setShowExtendedFormatting((current) => !current)}
                className={`${textButtonClass(showExtendedFormatting)} tos-task-editor-more-button`}
                aria-expanded={showExtendedFormatting}
                title={showExtendedFormatting ? (isArabic ? "إخفاء أدوات التنسيق الإضافية" : "Hide extended formatting") : (isArabic ? "المزيد من التنسيق" : "More formatting")}
              >
                <Plus size={14} />
                {showExtendedFormatting ? (isArabic ? "أقل" : "Less") : (isArabic ? "المزيد" : "More")}
              </button>
            )}
          </div>
        </div>

        {colorPanel && ('''
replace_once(more_anchor, more_insert, 'more formatting control')

path.write_text(text)
PY

  printf '\n' >> "$ROOT/$CSS_TARGET"
  cat "$SOURCE_CSS" >> "$ROOT/$CSS_TARGET"
  PATCH_ACTION="APPLIED"
elif [ "$DECLUTTER_COUNT" = "1" ] && [ "$LAYOUT_COUNT" = "1" ] && [ "$TOOLBAR_COUNT" = "1" ]; then
  PATCH_ACTION="VALIDATED_EXISTING"
else
  fail "Partial Phase 03.1 declutter state detected" 20
fi

[ "$(grep -Fc -- "$DECLUTTER_RUNTIME" "$ROOT/$CSS_TARGET" || true)" = "1" ] || fail "Declutter runtime missing or duplicated" 21
[ "$(grep -Fc -- "$DECLUTTER_LAYOUT_HOOK" "$ROOT/$BOARD_TARGET" || true)" = "1" ] || fail "Declutter layout hook missing or duplicated" 22
[ "$(grep -Fc -- "$DECLUTTER_PROGRESS_HOOK" "$ROOT/$BOARD_TARGET" || true)" = "1" ] || fail "Compact progress hook missing or duplicated" 23
[ "$(grep -Fc -- "$DECLUTTER_SIDE_HOOK" "$ROOT/$BOARD_TARGET" || true)" -ge "1" ] || fail "Side rail hook missing" 24
[ "$(grep -Fc -- 'variant="decluttered"' "$ROOT/$BOARD_TARGET" || true)" = "1" ] || fail "Decluttered editor variant missing" 25
[ "$(grep -Fc -- "$DECLUTTER_TOOLBAR_HOOK" "$ROOT/$PARTS_TARGET" || true)" = "1" ] || fail "Editor toolbar hook missing or duplicated" 26
[ "$(grep -Fc -- 'isDecluttered' "$ROOT/$PARTS_TARGET" || true)" -ge "2" ] || fail "Decluttered editor behavior missing" 27

git -C "$ROOT" diff --check -- "$BOARD_TARGET" "$WORKSPACE_TARGET" "$CSS_TARGET" "$PARTS_TARGET"

cd "$ROOT/frontend"
npm run build
cd "$ROOT"

[ -f "$DIST/index.html" ] || fail "Built dist index missing" 28
grep -RFlq -- "$DECLUTTER_RUNTIME" "$DIST/assets" || fail "Declutter runtime missing from dist assets" 29
grep -RFlq -- "$DECLUTTER_LAYOUT_HOOK" "$DIST/assets" || fail "Declutter layout hook missing from dist assets" 30
grep -RFlq -- "$DECLUTTER_TOOLBAR_HOOK" "$DIST/assets" || fail "Declutter toolbar hook missing from dist assets" 31

rm -rf "$STAGE"
mkdir -p "$STAGE"
cp -a "$DIST/." "$STAGE/"
[ -f "$STAGE/index.html" ] || fail "Staged index missing" 32
grep -RFlq -- "$DECLUTTER_RUNTIME" "$STAGE/assets" || fail "Declutter runtime missing from staged assets" 33

mv "$LIVE" "$BACKUP"
if ! mv "$STAGE" "$LIVE"; then
  mv "$BACKUP" "$LIVE" || true
  fail "Failed to activate Phase 03.1 build; rollback attempted" 34
fi
if ! grep -RFlq -- "$DECLUTTER_RUNTIME" "$LIVE/assets"; then
  rm -rf "$LIVE"
  mv "$BACKUP" "$LIVE" || true
  fail "Live declutter runtime missing; rolled back" 35
fi

POST_CHANGED="$(git -C "$ROOT" diff --name-only | sort)"
for required in "$BOARD_TARGET" "$CSS_TARGET" "$PARTS_TARGET"; do
  printf '%s\n' "$POST_CHANGED" | grep -Fxq "$required" || fail "Required modified file missing after Phase 03.1: $required" 36
done
while IFS= read -r path; do
  [ -z "$path" ] && continue
  case "$path" in
    "$BOARD_TARGET"|"$WORKSPACE_TARGET"|"$CSS_TARGET"|"$PARTS_TARGET") ;;
    *) fail "Unexpected tracked file after Phase 03.1: $path" 37 ;;
  esac
done <<< "$POST_CHANGED"

git -C "$ROOT" diff --cached --quiet || fail "Unexpected staged changes after Phase 03.1" 38

BOARD_SHA="$(sha256sum "$ROOT/$BOARD_TARGET" | awk '{print $1}')"
WORKSPACE_SHA="$(sha256sum "$ROOT/$WORKSPACE_TARGET" | awk '{print $1}')"
CSS_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"
PARTS_SHA="$(sha256sum "$ROOT/$PARTS_TARGET" | awk '{print $1}')"

echo "PHASE03_1_TASK_DETAILS_DECLUTTER_V1=PASS"
echo "SCREEN=Task_Details"
echo "PATCH_ACTION=$PATCH_ACTION"
echo "CHANGE=Compact_summary_progress_collapsible_side_rail_tabs_first_decluttered_editor_sticky_save"
echo "BUSINESS_LOGIC_CHANGED=NO"
echo "BUILD_RESULT=PASS"
echo "LIVE_DEPLOY=PASS"
echo "BOARD_SHA256=$BOARD_SHA"
echo "MY_WORKSPACE_SHA256=$WORKSPACE_SHA"
echo "TASKS_CSS_SHA256=$CSS_SHA"
echo "TASK_BOARD_PARTS_SHA256=$PARTS_SHA"
echo "NO_COMMIT_OR_PUSH=YES"
echo "--- GIT STATUS ---"
git -C "$ROOT" status --short
