#!/usr/bin/env bash
set -euo pipefail

ROOT="${1:-/var/www/TOS}"
PATCH_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PATCH_REPO_ROOT="$(cd "$PATCH_DIR/.." && pwd)"
SOURCE_CSS="$PATCH_REPO_ROOT/TOS-UXUI-PHASE-01-DASHBOARD-GITHUB-REFERENCE-V1/dashboard-github-reference.css"
MAIN_TARGET="frontend/src/main.jsx"
CSS_TARGET="frontend/src/styles/dashboard-github-reference.css"
EXPECTED_HEAD="495201cfa490f643d9e28252eb523a4e278f385c"
EXPECTED_BASE_MAIN_BLOB="0035c796b14f106b276d53421b8ba4bf1ae99514"
IMPORT_LINE='import "./styles/dashboard-github-reference.css";'

fail() {
  echo "PHASE01_DASHBOARD_V3=FAIL"
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

BASE_MAIN_BLOB="$(git -C "$ROOT" rev-parse "HEAD:$MAIN_TARGET")"
echo "BASE_MAIN_BLOB=$BASE_MAIN_BLOB"
[ "$BASE_MAIN_BLOB" = "$EXPECTED_BASE_MAIN_BLOB" ] || fail "HEAD version of main.jsx changed unexpectedly. Stop and report." 7

# Only two working-tree paths are allowed for this phase. Use --untracked-files=all
# so Git does not collapse the new styles directory to `?? frontend/src/styles/`.
validate_allowed_status() {
  local label="$1"
  local status line
  status="$(git -C "$ROOT" status --porcelain=v1 --untracked-files=all)"
  if [ -n "$status" ]; then
    while IFS= read -r line; do
      [ -z "$line" ] && continue
      case "$line" in
        " M $MAIN_TARGET") ;;
        "?? $CSS_TARGET") ;;
        *)
          echo "--- $label GIT STATUS ---"
          printf '%s\n' "$status"
          fail "Unexpected or staged working-tree change detected: $line. Do not reset, stash, overwrite, commit, or push." 8
          ;;
      esac
    done <<< "$status"
  fi
  printf '%s' "$status"
}

PRE_STATUS="$(validate_allowed_status PRE)"
if [ -n "$PRE_STATUS" ]; then
  echo "--- PRE-EXISTING ALLOWED STATUS ---"
  printf '%s\n' "$PRE_STATUS"
fi

# Determine whether V2 already applied the intended files. Compare main.jsx against
# the exact HEAD version plus one import line, rather than relying on a dirty-tree blob.
STATE="$(python3 - "$ROOT" "$MAIN_TARGET" "$CSS_TARGET" <<'PY'
from pathlib import Path
import subprocess
import sys

root, main_target, css_target = sys.argv[1:]
actual = (Path(root) / main_target).read_text(encoding="utf-8")
baseline = subprocess.check_output(
    ["git", "-C", root, "show", f"HEAD:{main_target}"], text=True
)
anchor = 'import "./index.css";\n'
line = 'import "./styles/dashboard-github-reference.css";\n'
if baseline.count(anchor) != 1:
    print("INVALID_BASELINE_ANCHOR")
    raise SystemExit(0)
expected = baseline.replace(anchor, anchor + line, 1)
css_exists = (Path(root) / css_target).is_file()
if actual == baseline and not css_exists:
    print("UNAPPLIED")
elif actual == expected and css_exists:
    print("ALREADY_APPLIED")
elif actual == baseline and css_exists:
    print("MIXED_CSS_ONLY")
elif actual == expected and not css_exists:
    print("MIXED_IMPORT_ONLY")
else:
    print("UNEXPECTED_MAIN_CONTENT")
PY
)"
echo "PATCH_STATE=$STATE"

case "$STATE" in
  UNAPPLIED)
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
    echo "PATCH_ACTION=APPLIED_NOW"
    ;;
  ALREADY_APPLIED)
    echo "PATCH_ACTION=V2_CHANGES_PRESERVED_AND_VALIDATED"
    ;;
  MIXED_CSS_ONLY|MIXED_IMPORT_ONLY|INVALID_BASELINE_ANCHOR|UNEXPECTED_MAIN_CONTENT)
    fail "Unexpected partial or conflicting Phase 01 state: $STATE. Stop and report; do not modify further." 9
    ;;
  *)
    fail "Unknown patch state: $STATE" 10
    ;;
esac

# Exact content validation.
grep -Fqx "$IMPORT_LINE" "$ROOT/$MAIN_TARGET" || fail "Dashboard premium import missing after recovery/apply" 11
cmp -s "$SOURCE_CSS" "$ROOT/$CSS_TARGET" || fail "Dashboard stylesheet does not exactly match the approved patch source" 12

python3 - "$ROOT" "$MAIN_TARGET" <<'PY'
from pathlib import Path
import subprocess
import sys
root, main_target = sys.argv[1:]
actual = (Path(root) / main_target).read_text(encoding="utf-8")
baseline = subprocess.check_output(["git", "-C", root, "show", f"HEAD:{main_target}"], text=True)
anchor = 'import "./index.css";\n'
line = 'import "./styles/dashboard-github-reference.css";\n'
expected = baseline.replace(anchor, anchor + line, 1)
if actual != expected:
    raise SystemExit("MAIN_EXACT_CONTENT_CHECK=FAIL")
print("MAIN_EXACT_CONTENT_CHECK=PASS")
PY

git -C "$ROOT" diff --check -- "$MAIN_TARGET"

POST_APPLY_STATUS="$(validate_allowed_status POST_APPLY)"
[ -n "$POST_APPLY_STATUS" ] || fail "Expected Dashboard changes are missing from git status" 13

echo "--- EXPECTED POST-APPLY STATUS ---"
printf '%s\n' "$POST_APPLY_STATUS"

cd "$ROOT/frontend"
npm run build
cd "$ROOT"

FINAL_STATUS="$(validate_allowed_status FINAL)"
EXPECTED_STATUS="$(printf ' M %s\n?? %s' "$MAIN_TARGET" "$CSS_TARGET")"
if [ "$FINAL_STATUS" != "$EXPECTED_STATUS" ]; then
  echo "--- FINAL STATUS ---"
  printf '%s\n' "$FINAL_STATUS"
  echo "--- EXPECTED STATUS ---"
  printf '%s\n' "$EXPECTED_STATUS"
  fail "Final status does not contain exactly the two intended Dashboard files." 14
fi

echo "PHASE01_DASHBOARD_V3=PASS"
echo "SCREEN=Dashboard"
echo "BASELINE_CURRENT=$EXPECTED_HEAD"
echo "REFERENCE=GitHub_Developer_Hub"
echo "PATCH_RECOVERY=IDEMPOTENT"
echo "LIGHT_MODE=PREMIUM_WARM_IVORY_GOLD"
echo "DARK_MODE=PREMIUM_SLATE_GOLD"
echo "TEXT_CONTRAST=HARDENED"
echo "BUSINESS_LOGIC_CHANGED=NO"
echo "RAMZY_CHANGED=NO"
echo "TCS_CHANGED=NO"
echo "COMMIT_CREATED=NO"
echo "PUSH_PERFORMED=NO"
echo "CHANGED_FILES=$MAIN_TARGET,$CSS_TARGET"
echo "READY_FOR_VISUAL_REVIEW=YES"
echo "--- GIT STATUS ---"
printf '%s\n' "$FINAL_STATUS"
echo "--- GIT DIFF MAIN ---"
git diff -- "$MAIN_TARGET"
echo "--- CSS SHA256 ---"
sha256sum "$CSS_TARGET"
echo "NEXT_ACTION=Return this report for review. Do not commit or push TOS."