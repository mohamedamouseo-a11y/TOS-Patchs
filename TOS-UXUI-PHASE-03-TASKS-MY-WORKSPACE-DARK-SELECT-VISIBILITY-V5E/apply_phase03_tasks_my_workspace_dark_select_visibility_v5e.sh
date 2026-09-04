#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/var/www/TOS}"
TARGET="frontend/src/pages/MyTaskWorkspace.jsx"
EXPECTED_TARGET_HEAD_BLOB="7b5e0d1c4d62a439dbdfc3fa056a9a4eea4cbf0e"
HOOK="tos-my-workspace-native-select"
DIST="$ROOT/frontend/dist"
LIVE_PARENT="/opt/apps/tamiyouz-front"
LIVE="$LIVE_PARENT/build"
STAMP="$(date +%Y%m%d-%H%M%S)"
STAGE="$LIVE_PARENT/build.phase03-v5e.new.$$"
BACKUP="$LIVE_PARENT/build.phase03-v5e.backup-$STAMP"

fail() {
  echo "PHASE03_TASKS_MY_WORKSPACE_DARK_SELECT_VISIBILITY_V5E=FAIL"
  echo "ERROR=$1" >&2
  exit "${2:-1}"
}

[ -d "$ROOT/.git" ] || fail "TOS repository not found" 2
[ -f "$ROOT/$TARGET" ] || fail "MyTaskWorkspace.jsx missing" 3
[ -d "$LIVE" ] || fail "Live frontend root missing" 4

git -C "$ROOT" diff --cached --quiet || fail "Staged changes exist; stop" 5
[ "$(git -C "$ROOT" rev-parse "HEAD:$TARGET")" = "$EXPECTED_TARGET_HEAD_BLOB" ] || fail "Committed MyTaskWorkspace baseline changed" 6

# V5D may already have modified the Tasks board + premium stylesheet. Allow only
# those reviewed tracked changes before this focused visibility fix.
PRE_DIRTY="$(git -C "$ROOT" diff --name-only | sort)"
while IFS= read -r path; do
  [ -z "$path" ] && continue
  case "$path" in
    frontend/src/components/ProfessionalTaskBoard.jsx|frontend/src/styles/tasks-projects-premium-reference.css) ;;
    *) fail "Unexpected pre-existing tracked change: $path" 7 ;;
  esac
done <<< "$PRE_DIRTY"

HOOK_COUNT="$(grep -Fc -- "$HOOK" "$ROOT/$TARGET" || true)"
if [ "$HOOK_COUNT" = "0" ]; then
  [ "$(git -C "$ROOT" hash-object "$TARGET")" = "$EXPECTED_TARGET_HEAD_BLOB" ] || fail "MyTaskWorkspace worktree differs from reviewed baseline" 8

  python3 - "$ROOT/$TARGET" <<'PY'
from pathlib import Path
import re
import sys

path = Path(sys.argv[1])
text = path.read_text()

anchor = 'const personalProjectFilterValue = "__personal__";\n'
addition = (
    'const personalProjectFilterValue = "__personal__";\n'
    'const nativeDarkSelectClass = "tos-my-workspace-native-select dark:[color-scheme:dark] dark:!border-zinc-600 dark:!bg-zinc-900 dark:!text-zinc-100 dark:[&>option]:!bg-zinc-900 dark:[&>option]:!text-zinc-100";\n'
)
if text.count(anchor) != 1:
    raise SystemExit(f"native select constant anchor count={text.count(anchor)}")
text = text.replace(anchor, addition, 1)

# Two selects inside the task editor use the shared fieldClass.
modal_replacements = [
    (
        '<select value={form.status} onChange={(event) => updateField("status", event.target.value)} className={fieldClass}>',
        '<select value={form.status} onChange={(event) => updateField("status", event.target.value)} className={`${fieldClass} ${nativeDarkSelectClass}`}>',
    ),
    (
        '<select value={form.priority} onChange={(event) => updateField("priority", event.target.value)} className={fieldClass}>',
        '<select value={form.priority} onChange={(event) => updateField("priority", event.target.value)} className={`${fieldClass} ${nativeDarkSelectClass}`}>',
    ),
]
for old, new in modal_replacements:
    if text.count(old) != 1:
        raise SystemExit(f"modal select anchor count={text.count(old)}")
    text = text.replace(old, new, 1)

# Three main My Workspace filters have literal className strings.
pattern = re.compile(r'(<select value=\{filters\.(?:projectId|day|month)\}[^>]*?) className="([^"]+)"(>)')
matches = list(pattern.finditer(text))
if len(matches) != 3:
    raise SystemExit(f"workspace filter select count={len(matches)}")
text = pattern.sub(lambda m: f'{m.group(1)} className={{`{m.group(2)} ${{nativeDarkSelectClass}}`}}{m.group(3)}', text)

if text.count('nativeDarkSelectClass') != 6:
    raise SystemExit(f"nativeDarkSelectClass expected 6 references, got {text.count('nativeDarkSelectClass')}")
if text.count('<select') != 5:
    raise SystemExit(f"expected 5 selects in MyTaskWorkspace, got {text.count('<select')}")

path.write_text(text)
PY
  PATCH_ACTION="APPLIED"
else
  [ "$HOOK_COUNT" = "1" ] || fail "Dark select hook duplicated" 9
  PATCH_ACTION="VALIDATED_EXISTING"
fi

[ "$(grep -Fc -- "$HOOK" "$ROOT/$TARGET" || true)" = "1" ] || fail "Dark select hook missing or duplicated" 10
[ "$(grep -Fc -- 'nativeDarkSelectClass' "$ROOT/$TARGET" || true)" = "6" ] || fail "Dark select class references invalid" 11
git -C "$ROOT" diff --check -- "$TARGET"

cd "$ROOT/frontend"
npm run build
cd "$ROOT"

[ -f "$DIST/index.html" ] || fail "Built dist index missing" 12
grep -RFlq -- "$HOOK" "$DIST/assets" || fail "Dark select hook missing from built assets" 13
if ! grep -RFlq -- 'color-scheme:dark' "$DIST/assets" && ! grep -RFlq -- 'color-scheme: dark' "$DIST/assets"; then
  fail "Dark native color-scheme utility missing from built assets" 14
fi

rm -rf "$STAGE"
mkdir -p "$STAGE"
cp -a "$DIST/." "$STAGE/"
[ -f "$STAGE/index.html" ] || fail "Staged index missing" 15
grep -RFlq -- "$HOOK" "$STAGE/assets" || fail "Dark select hook missing from staged assets" 16

mv "$LIVE" "$BACKUP"
if ! mv "$STAGE" "$LIVE"; then
  mv "$BACKUP" "$LIVE" || true
  fail "Failed to activate V5E build; rollback attempted" 17
fi
if ! grep -RFlq -- "$HOOK" "$LIVE/assets"; then
  rm -rf "$LIVE"
  mv "$BACKUP" "$LIVE" || true
  fail "Live V5E hook missing; rolled back" 18
fi

# Preserve V5D tracked changes and add only MyTaskWorkspace.jsx.
TRACKED_CHANGED="$(git -C "$ROOT" diff --name-only | sort)"
while IFS= read -r path; do
  [ -z "$path" ] && continue
  case "$path" in
    frontend/src/components/ProfessionalTaskBoard.jsx|frontend/src/styles/tasks-projects-premium-reference.css|frontend/src/pages/MyTaskWorkspace.jsx) ;;
    *) fail "Unexpected tracked file after V5E: $path" 19 ;;
  esac
done <<< "$TRACKED_CHANGED"

git -C "$ROOT" diff --cached --quiet || fail "Unexpected staged changes after patch" 20

FINAL_SHA="$(sha256sum "$ROOT/$TARGET" | awk '{print $1}')"
echo "PHASE03_TASKS_MY_WORKSPACE_DARK_SELECT_VISIBILITY_V5E=PASS"
echo "SCREEN=My_Workspace"
echo "FIX=Dark_native_select_and_option_visibility"
echo "PATCH_ACTION=$PATCH_ACTION"
echo "LIGHT_MODE_CHANGED=NO_VISUAL_INTENT"
echo "BUSINESS_LOGIC_CHANGED=NO"
echo "BUILD_RESULT=PASS"
echo "LIVE_DEPLOY=PASS"
echo "MY_WORKSPACE_SHA256=$FINAL_SHA"
echo "NO_COMMIT_OR_PUSH=YES"
echo "--- GIT STATUS ---"
git -C "$ROOT" status --short
