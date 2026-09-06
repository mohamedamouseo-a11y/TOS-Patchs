#!/usr/bin/env bash
set -euo pipefail

PATCH_DIR="$(cd "$(dirname "$0")" && pwd)"
ORIGINAL_RUNNER="$PATCH_DIR/run_phase13_safe_confirmation_action_control_v1.sh"
REPAIR_GENERATOR="$PATCH_DIR/02_phase13_runtime_io_anchor_repair.py"
TMP_RUNNER="$(mktemp "$PATCH_DIR/.phase13-runtime-repair.XXXXXX.sh")"

cleanup() {
  rm -f "$TMP_RUNNER"
}
trap cleanup EXIT

[[ -f "$ORIGINAL_RUNNER" ]] || { echo "PHASE13_REPAIR=FAIL"; echo "REASON=ORIGINAL_RUNNER_NOT_FOUND"; exit 1; }
[[ -f "$REPAIR_GENERATOR" ]] || { echo "PHASE13_REPAIR=FAIL"; echo "REASON=REPAIR_GENERATOR_NOT_FOUND"; exit 1; }

python3 - "$ORIGINAL_RUNNER" "$TMP_RUNNER" <<'PY'
from pathlib import Path
import sys

source = Path(sys.argv[1]).read_text(encoding="utf-8")
out = Path(sys.argv[2])
old_generator = 'GENERATOR="$PATCH_DIR/01_phase13_safe_confirmation_action_control.py"'
new_generator = 'GENERATOR="$PATCH_DIR/02_phase13_runtime_io_anchor_repair.py"'
if source.count(old_generator) != 1:
    raise SystemExit("PHASE13_REPAIR_RUNNER_ERROR=GENERATOR_ANCHOR")
source = source.replace(old_generator, new_generator, 1)
source = source.replace(
    'echo "RUNNING=RAMZY_PHASE13_SAFE_CONFIRMATION_ACTION_CONTROL_V1"',
    'echo "RUNNING=RAMZY_PHASE13_SAFE_CONFIRMATION_ACTION_CONTROL_V1_REPAIR"',
    1,
)
out.write_text(source, encoding="utf-8")
PY

chmod +x "$TMP_RUNNER"
bash "$TMP_RUNNER"
