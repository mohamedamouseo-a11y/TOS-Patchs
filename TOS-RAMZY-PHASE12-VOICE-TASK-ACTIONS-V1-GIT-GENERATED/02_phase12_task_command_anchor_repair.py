#!/usr/bin/env python3
from pathlib import Path
import subprocess
import tempfile

PATCH_DIR = Path(__file__).resolve().parent
ORIGINAL = PATCH_DIR / "01_phase12_voice_task_actions.py"

source = ORIGINAL.read_text(encoding="utf-8")
old = '''text = replace_once(
    text,
    '  if (actionType === "ADD_COMMENT") {',
    create_normalize + '  if (actionType === "ADD_COMMENT") {',
    'TASK_COMMAND_CREATE_PAYLOAD',
)
'''
new = '''text = replace_once(
    text,
    'function normalizeTaskActionPayload(actionType, rawPayload = {}) {\\n  const payload = ensurePlainPayload(rawPayload);\\n  if (actionType === "ADD_COMMENT") {',
    'function normalizeTaskActionPayload(actionType, rawPayload = {}) {\\n  const payload = ensurePlainPayload(rawPayload);\\n' + create_normalize + '  if (actionType === "ADD_COMMENT") {',
    'TASK_COMMAND_CREATE_PAYLOAD',
)
'''

count = source.count(old)
if count != 1:
    raise SystemExit(f"PHASE12_REPAIR_ERROR=GENERATOR_ANCHOR_COUNT_{count}")

fixed = source.replace(old, new, 1)
with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as handle:
    handle.write(fixed)
    temp_path = Path(handle.name)

try:
    subprocess.run(["python3", str(temp_path)], check=True)
finally:
    temp_path.unlink(missing_ok=True)

print("PHASE12_TASK_COMMAND_ANCHOR_REPAIR=PASS")
