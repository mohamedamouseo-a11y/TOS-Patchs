#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/var/www/TOS}"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_REPO_ROOT="$(cd "$PATCH_DIR/.." && pwd)"
SOURCE_CSS="$PATCH_DIR/projects-github-reference.css"
MAIN_TARGET="frontend/src/main.jsx"
PROJECTS_TARGET="frontend/src/pages/ProjectsPage.jsx"
CSS_TARGET="frontend/src/styles/projects-github-reference.css"
EXPECTED_MAIN_HEAD_BLOB="10a76aae2e1c5a20ce84d28e304c565a96aef500"
EXPECTED_PROJECTS_HEAD_BLOB="1720111a2bab77133eac9f7c754ddd89a58fa179"
IMPORT_LINE='import "./styles/projects-github-reference.css";'
IMPORT_ANCHOR='import "./styles/dashboard-github-reference.css";'
DIST="$ROOT/frontend/dist"
LIVE="/opt/apps/tamiyouz-front/build"
BACKUP="/opt/apps/tamiyouz-front/build.phase02-projects-v1.backup-$(date +%Y%m%d-%H%M%S)"

fail() {
  echo "PHASE02_PROJECTS_V1=FAIL"
  echo "ERROR=$1" >&2
  exit "${2:-1}"
}

[ -d "$ROOT/.git" ] || fail "TOS repository not found" 2
[ -d "$PATCH_REPO_ROOT/.git" ] || fail "TOS-Patchs repository not found" 3
[ -f "$SOURCE_CSS" ] || fail "Missing Projects stylesheet source" 4
[ -f "$ROOT/$MAIN_TARGET" ] || fail "Missing main.jsx" 5
[ -f "$ROOT/$PROJECTS_TARGET" ] || fail "Missing ProjectsPage.jsx" 6
[ -d "$LIVE" ] || fail "Live frontend root missing" 7

SOURCE_REL="${SOURCE_CSS#$PATCH_REPO_ROOT/}"
[ "$(git -C "$PATCH_REPO_ROOT" hash-object "$SOURCE_CSS")" = "$(git -C "$PATCH_REPO_ROOT" rev-parse "HEAD:$SOURCE_REL")" ] || fail "Patch source differs from TOS-Patchs HEAD" 8

HEAD="$(git -C "$ROOT" rev-parse HEAD)"
MAIN_HEAD_BLOB="$(git -C "$ROOT" rev-parse "HEAD:$MAIN_TARGET")"
PROJECTS_HEAD_BLOB="$(git -C "$ROOT" rev-parse "HEAD:$PROJECTS_TARGET")"
echo "TOS_HEAD=$HEAD"
echo "MAIN_HEAD_BLOB=$MAIN_HEAD_BLOB"
echo "PROJECTS_HEAD_BLOB=$PROJECTS_HEAD_BLOB"

[ "$MAIN_HEAD_BLOB" = "$EXPECTED_MAIN_HEAD_BLOB" ] || fail "Committed main.jsx baseline changed; regenerate Phase 02" 9
[ "$PROJECTS_HEAD_BLOB" = "$EXPECTED_PROJECTS_HEAD_BLOB" ] || fail "Committed ProjectsPage.jsx baseline changed; regenerate Phase 02" 10
grep -Fq 'tos-projects-ui03' "$ROOT/$PROJECTS_TARGET" || fail "Projects root scope missing" 11
grep -Fq "$IMPORT_ANCHOR" "$ROOT/$MAIN_TARGET" || fail "Dashboard import anchor missing" 12
git -C "$ROOT" diff --cached --quiet || fail "Staged changes exist" 13

STATUS="$(git -C "$ROOT" status --porcelain=v1 --untracked-files=all)"
PATHS="$(printf '%s\n' "$STATUS" | sed '/^$/d' | cut -c4- | sort -u)"
EXPECTED_PATHS="$(printf '%s\n%s\n' "$MAIN_TARGET" "$CSS_TARGET" | sort)"

if [ -z "$STATUS" ]; then
  [ "$(grep -Fxc "$IMPORT_LINE" "$ROOT/$MAIN_TARGET" || true)" = "0" ] || fail "Projects import already exists unexpectedly" 14
  [ ! -e "$ROOT/$CSS_TARGET" ] || fail "Projects stylesheet already exists unexpectedly" 15
  python3 - "$ROOT/$MAIN_TARGET" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
s = p.read_text(encoding="utf-8")
anchor = 'import "./styles/dashboard-github-reference.css";\n'
line = 'import "./styles/projects-github-reference.css";\n'
if s.count(anchor) != 1:
    raise SystemExit(f"IMPORT_ANCHOR_COUNT={s.count(anchor)}")
p.write_text(s.replace(anchor, anchor + line, 1), encoding="utf-8", newline="\n")
PY
  mkdir -p "$ROOT/$(dirname "$CSS_TARGET")"
  cp "$SOURCE_CSS" "$ROOT/$CSS_TARGET"
  PATCH_ACTION="APPLIED_NOW"
elif [ "$PATHS" = "$EXPECTED_PATHS" ]; then
  PATCH_ACTION="VALIDATED_EXISTING"
else
  echo "--- PRE-EXISTING STATUS ---"
  printf '%s\n' "$STATUS"
  fail "Unexpected working-tree changes; do not reset/stash" 16
fi

[ "$(grep -Fxc "$IMPORT_LINE" "$ROOT/$MAIN_TARGET" || true)" = "1" ] || fail "Expected exactly one Projects import" 17
[ -f "$ROOT/$CSS_TARGET" ] || fail "Projects stylesheet missing" 18
cmp -s "$SOURCE_CSS" "$ROOT/$CSS_TARGET" || fail "Applied stylesheet differs from patch source" 19
grep -Fq '.tos-projects-ui03' "$ROOT/$CSS_TARGET" || fail "Projects scope selector missing" 20
grep -Fq 'html.dark .tos-projects-ui03' "$ROOT/$CSS_TARGET" || fail "Projects dark selector missing" 21
git -C "$ROOT" diff --check -- "$MAIN_TARGET" "$CSS_TARGET"

cd "$ROOT/frontend"
npm run build
cd "$ROOT"

[ -f "$DIST/index.html" ] || fail "Build output missing" 22
grep -RFlq 'tos-projects-ui03' "$DIST/assets" || fail "Projects selector missing from build" 23
grep -RFlq '#1d2b36' "$DIST/assets" || fail "Projects dark palette missing from build" 24

# The public TOS domain serves /opt/apps/tamiyouz-front/build, not frontend/dist.
# Keep a full backup, then copy the fresh build into the live root without touching git.
cp -a "$LIVE" "$BACKUP"
cp -a "$DIST/." "$LIVE/"

if [ ! -f "$LIVE/index.html" ] || ! grep -RFlq 'tos-projects-ui03' "$LIVE/assets" || ! grep -RFlq '#1d2b36' "$LIVE/assets"; then
  cp -a "$BACKUP/." "$LIVE/" || true
  fail "Live verification failed; backup copied back" 25
fi

DIST_ASSETS="$(grep -oE '/assets/[^\" ]+' "$DIST/index.html" | tr '\n' ',' || true)"
LIVE_ASSETS="$(grep -oE '/assets/[^\" ]+' "$LIVE/index.html" | tr '\n' ',' || true)"
[ "$DIST_ASSETS" = "$LIVE_ASSETS" ] || fail "Live index assets differ from build" 26

FINAL_STATUS="$(git -C "$ROOT" status --porcelain=v1 --untracked-files=all)"
FINAL_PATHS="$(printf '%s\n' "$FINAL_STATUS" | sed '/^$/d' | cut -c4- | sort -u)"
[ "$FINAL_PATHS" = "$EXPECTED_PATHS" ] || fail "Unexpected source files changed" 27
[ "$(git -C "$ROOT" diff --numstat -- "$MAIN_TARGET")" = $'1\t0\tfrontend/src/main.jsx' ] || fail "main.jsx diff is not one import line" 28

CSS_SHA="$(sha256sum "$ROOT/$CSS_TARGET" | awk '{print $1}')"
echo "PHASE02_PROJECTS_V1=PASS"
echo "SCREEN=Projects"
echo "PATCH_ACTION=$PATCH_ACTION"
echo "BUILD_RESULT=PASS"
echo "LIVE_DEPLOY=PASS"
echo "LIVE_ROOT=$LIVE"
echo "BACKUP_ROOT=$BACKUP"
echo "CHANGED_FILES=$MAIN_TARGET,$CSS_TARGET"
echo "CSS_SHA256=$CSS_SHA"
echo "BUSINESS_LOGIC_CHANGED=NO"
echo "RAMZY_CHANGED=NO"
echo "TCS_CHANGED=NO"
echo "COMMIT_CREATED=NO"
echo "PUSH_PERFORMED=NO"
echo "READY_FOR_VISUAL_REVIEW=YES"
echo "--- GIT STATUS ---"
printf '%s\n' "$FINAL_STATUS"
