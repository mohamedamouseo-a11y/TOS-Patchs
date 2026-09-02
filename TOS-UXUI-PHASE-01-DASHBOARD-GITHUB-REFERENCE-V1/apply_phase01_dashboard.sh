#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/var/www/TOS}"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_CSS="$PATCH_DIR/dashboard-github-reference.css"
MAIN_TARGET="frontend/src/main.jsx"
CSS_TARGET="frontend/src/styles/dashboard-github-reference.css"
EXPECTED_HEAD="8b29fd2ec2c96ce422b927711310b35fe6c52c61"
EXPECTED_MAIN_BLOB="0035c796b14f106b276d53421b8ba4bf1ae99514"
IMPORT_LINE='import "./styles/dashboard-github-reference.css";'

fail() {
  echo "PHASE01_DASHBOARD=FAIL"
  echo "ERROR=$1" >&2
  exit "${2:-1}"
}

[ -d "$ROOT/.git" ] || fail "TOS repository not found at $ROOT" 2
[ -f "$ROOT/$MAIN_TARGET" ] || fail "Missing $MAIN_TARGET" 3
[ -f "$SOURCE_CSS" ] || fail "Patch stylesheet missing: $SOURCE_CSS" 4

HEAD="$(git -C "$ROOT" rev-parse HEAD)"
echo "TOS_HEAD=$HEAD"
[ "$HEAD" = "$EXPECTED_HEAD" ] || fail "HEAD mismatch. Expected $EXPECTED_HEAD, got $HEAD. Stop and report; do not force." 5

MAIN_BLOB="$(git -C "$ROOT" hash-object "$MAIN_TARGET")"
echo "MAIN_BLOB=$MAIN_BLOB"
[ "$MAIN_BLOB" = "$EXPECTED_MAIN_BLOB" ] || fail "main.jsx baseline mismatch. Stop and report; do not overwrite local work." 6

if ! git -C "$ROOT" diff --quiet -- "$MAIN_TARGET"; then
  fail "$MAIN_TARGET has tracked local changes" 7
fi
if ! git -C "$ROOT" diff --cached --quiet -- "$MAIN_TARGET"; then
  fail "$MAIN_TARGET has staged changes" 8
fi
if [ -e "$ROOT/$CSS_TARGET" ]; then
  fail "$CSS_TARGET already exists; patch may already be applied or conflicts with local work" 9
fi
if grep -Fq "$IMPORT_LINE" "$ROOT/$MAIN_TARGET"; then
  fail "Dashboard premium import already exists" 10
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

grep -Fq "$IMPORT_LINE" "$ROOT/$MAIN_TARGET" || fail "Import insertion verification failed" 11
cmp -s "$SOURCE_CSS" "$ROOT/$CSS_TARGET" || fail "Stylesheet copy verification failed" 12

git -C "$ROOT" diff --check -- "$MAIN_TARGET" "$CSS_TARGET"

cd "$ROOT/frontend"
npm run build

cd "$ROOT"
echo "PHASE01_DASHBOARD=PASS"
echo "SCREEN=Dashboard"
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
echo "NEXT_ACTION=Return this report and git diff output for review. Do not commit or push TOS."
echo "--- GIT STATUS ---"
git status --short -- "$MAIN_TARGET" "$CSS_TARGET"
echo "--- GIT DIFF MAIN ---"
git diff -- "$MAIN_TARGET"
echo "--- CSS SHA256 ---"
sha256sum "$CSS_TARGET"
