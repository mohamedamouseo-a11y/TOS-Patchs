#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/var/www/TOS}"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_REPO_ROOT="$(cd "$PATCH_DIR/.." && pwd)"
SOURCE_CSS="$PATCH_REPO_ROOT/TOS-UXUI-PHASE-01-DASHBOARD-GITHUB-REFERENCE-V1/dashboard-github-reference.css"
MAIN_TARGET="frontend/src/main.jsx"
CSS_TARGET="frontend/src/styles/dashboard-github-reference.css"
EXPECTED_HEAD="495201cfa490f643d9e28252eb523a4e278f385c"
EXPECTED_MAIN_BLOB="0035c796b14f106b276d53421b8ba4bf1ae99514"
EXPECTED_SOURCE_CSS_BLOB="595b772283a8280db8fb247c37746ca2de1b2eb7"
IMPORT_LINE='import "./styles/dashboard-github-reference.css";'

fail() {
  echo "PHASE01_DASHBOARD_V2=FAIL"
  echo "ERROR=$1" >&2
  exit "${2:-1}"
}

[ -d "$ROOT/.git" ] || fail "TOS repository not found at $ROOT" 2
[ -d "$PATCH_REPO_ROOT/.git" ] || fail "TOS-Patchs repository not found at $PATCH_REPO_ROOT" 3
[ -f "$ROOT/$MAIN_TARGET" ] || fail "Missing $MAIN_TARGET" 4
[ -f "$SOURCE_CSS" ] || fail "Source stylesheet missing: $SOURCE_CSS" 5

HEAD="$(git -C "$ROOT" rev-parse HEAD)"
echo "TOS_HEAD=$HEAD"
[ "$HEAD" = "$EXPECTED_HEAD" ] || fail "HEAD mismatch. Expected $EXPECTED_HEAD, got $HEAD. Stop and report; do not force." 6

SOURCE_CSS_BLOB="$(git -C "$PATCH_REPO_ROOT" hash-object "$SOURCE_CSS")"
echo "SOURCE_CSS_BLOB=$SOURCE_CSS_BLOB"
[ "$SOURCE_CSS_BLOB" = "$EXPECTED_SOURCE_CSS_BLOB" ] || fail "Patch stylesheet changed unexpectedly. Stop and report." 7

MAIN_BLOB="$(git -C "$ROOT" hash-object "$MAIN_TARGET")"
echo "MAIN_BLOB=$MAIN_BLOB"
[ "$MAIN_BLOB" = "$EXPECTED_MAIN_BLOB" ] || fail "main.jsx baseline mismatch. Stop and report; do not overwrite local work." 8

PRE_STATUS="$(git -C "$ROOT" status --porcelain)"
if [ -n "$PRE_STATUS" ]; then
  echo "--- PRE-EXISTING GIT STATUS ---"
  printf '%s\n' "$PRE_STATUS"
  fail "TOS working tree is not clean. Stop and report; do not reset, stash, or overwrite." 9
fi

if [ -e "$ROOT/$CSS_TARGET" ]; then
  fail "$CSS_TARGET already exists; patch may already be applied or conflicts with local work" 10
fi
if grep -Fq "$IMPORT_LINE" "$ROOT/$MAIN_TARGET"; then
  fail "Dashboard premium import already exists" 11
fi

python3 - "$ROOT/$MAIN_TARGET" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
source = path.read_text(encoding="utf-8")
anchor = 'import "./index.css";\n'
line = 'import "./styles/dashboard-github-reference.css";\n'
if source.count(anchor) != 1:
    raise SystemExit(f"IMPORT_ANCHOR_COUNT={source.count(anchor)}")
path.write_text(source.replace(anchor, anchor + line, 1), encoding="utf-8", newline="\n")
PY

mkdir -p "$ROOT/$(dirname "$CSS_TARGET")"
cp "$SOURCE_CSS" "$ROOT/$CSS_TARGET"

grep -Fq "$IMPORT_LINE" "$ROOT/$MAIN_TARGET" || fail "Import insertion verification failed" 12
cmp -s "$SOURCE_CSS" "$ROOT/$CSS_TARGET" || fail "Stylesheet copy verification failed" 13

git -C "$ROOT" diff --check -- "$MAIN_TARGET"

cd "$ROOT/frontend"
npm run build

cd "$ROOT"
POST_STATUS="$(git status --porcelain)"
CHANGED_PATHS="$(printf '%s\n' "$POST_STATUS" | sed -E 's/^.. //' | sort)"
EXPECTED_PATHS="$(printf '%s\n%s\n' "$MAIN_TARGET" "$CSS_TARGET" | sort)"

if [ "$CHANGED_PATHS" != "$EXPECTED_PATHS" ]; then
  echo "--- UNEXPECTED POST-PATCH STATUS ---"
  printf '%s\n' "$POST_STATUS"
  fail "Unexpected changed files after patch/build. Do not commit or push." 14
fi

echo "PHASE01_DASHBOARD_V2=PASS"
echo "SCREEN=Dashboard"
echo "BASELINE_REBASED_FROM=8b29fd2ec2c96ce422b927711310b35fe6c52c61"
echo "BASELINE_CURRENT=495201cfa490f643d9e28252eb523a4e278f385c"
echo "REFERENCE=GitHub_Developer_Hub"
echo "LIGHT_MODE=PREMIUM_WARM_IVORY_GOLD"
echo "DARK_MODE=PREMIUM_SLATE_GOLD"
echo "TEXT_CONTRAST=HARDENED"
echo "BUSINESS_LOGIC_CHANGED=NO"
echo "RAMZY_CHANGED=NO"
echo "TCS_CHANGED=NO"
echo "COMMIT_CREATED=NO"
echo "PUSH_PERFORMED=NO"
echo "CHANGED_FILES=$MAIN_TARGET,$CSS_TARGET"
echo "NEXT_ACTION=Return this report and git status/diff for review. Do not commit or push TOS."
echo "--- GIT STATUS ---"
printf '%s\n' "$POST_STATUS"
echo "--- GIT DIFF MAIN ---"
git diff -- "$MAIN_TARGET"
echo "--- CSS SHA256 ---"
sha256sum "$CSS_TARGET"
