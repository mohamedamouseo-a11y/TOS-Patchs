#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/var/www/TOS}"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_REPO_ROOT="$(cd "$PATCH_DIR/.." && pwd)"
V5_DIR="$PATCH_REPO_ROOT/TOS-UXUI-PHASE-03-TASKS-FLAGSHIP-SIGNATURE-V5"
ORIGINAL="$V5_DIR/apply_phase03_tasks_flagship_signature_v5.sh"
MAIN_TARGET="frontend/src/main.jsx"
EXPECTED_MAIN_WORKTREE_BLOB="9c712d900da43e06f2f0b6f1983cf7dfd6c0641d"
OLD_EXPECTED='EXPECTED_MAIN_HEAD_BLOB="725b57d3b7927b802dcedc26cca49c6a7f10ee55"'

fail() {
  echo "PHASE03_TASKS_FLAGSHIP_SIGNATURE_V5R=FAIL"
  echo "ERROR=$1" >&2
  exit "${2:-1}"
}

[ -d "$ROOT/.git" ] || fail "TOS repository not found" 2
[ -d "$PATCH_REPO_ROOT/.git" ] || fail "TOS-Patchs repository not found" 3
[ -f "$ORIGINAL" ] || fail "Original V5 script missing" 4
[ -f "$ROOT/$MAIN_TARGET" ] || fail "main.jsx missing" 5

# V5 never edits main.jsx. Validate the actual reviewed worktree content instead
# of pinning the committed blob, because the TOS HEAD advanced after V4.
MAIN_WORKTREE_BLOB="$(git -C "$ROOT" hash-object "$MAIN_TARGET")"
[ "$MAIN_WORKTREE_BLOB" = "$EXPECTED_MAIN_WORKTREE_BLOB" ] || {
  echo "MAIN_WORKTREE_BLOB=$MAIN_WORKTREE_BLOB"
  fail "main.jsx worktree is not the exact reviewed Tasks import state" 6
}

[ "$(grep -Fxc 'import "./styles/tasks-projects-premium-reference.css";' "$ROOT/$MAIN_TARGET" || true)" = "1" ] || fail "Tasks premium CSS import missing or duplicated" 7

CURRENT_HEAD_MAIN_BLOB="$(git -C "$ROOT" rev-parse "HEAD:$MAIN_TARGET")"
TMP="$V5_DIR/.apply_phase03_tasks_flagship_signature_v5r.$$.sh"
trap 'rm -f "$TMP"' EXIT

python3 - "$ORIGINAL" "$TMP" "$CURRENT_HEAD_MAIN_BLOB" "$OLD_EXPECTED" <<'PY'
from pathlib import Path
import sys

source = Path(sys.argv[1])
target = Path(sys.argv[2])
current_blob = sys.argv[3]
old_expected = sys.argv[4]
text = source.read_text()
if text.count(old_expected) != 1:
    raise SystemExit(f"expected original main baseline guard once, got {text.count(old_expected)}")
new_expected = f'EXPECTED_MAIN_HEAD_BLOB="{current_blob}"'
text = text.replace(old_expected, new_expected, 1)
target.write_text(text)
PY

chmod +x "$TMP"
echo "V5R_REBASE_MAIN_HEAD_BLOB=$CURRENT_HEAD_MAIN_BLOB"
bash "$TMP" "$ROOT"
