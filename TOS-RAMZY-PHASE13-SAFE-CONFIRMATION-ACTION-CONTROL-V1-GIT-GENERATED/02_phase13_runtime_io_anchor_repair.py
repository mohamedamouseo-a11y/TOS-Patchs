#!/usr/bin/env python3
from pathlib import Path

PATCH_DIR = Path(__file__).resolve().parent
SOURCE = PATCH_DIR / "01_phase13_safe_confirmation_action_control.py"

source = SOURCE.read_text(encoding="utf-8")

old = r'''text = replace_all_exact(
    text,
    '        actionGrounding: intelligence.actionGrounding || null,\n        settings:',
    '        actionGrounding: intelligence.actionGrounding || null,\n        io,\n        settings:',
    'RUNTIME_IO_CONTEXT',
    2,
)
'''

new = r'''text = replace_exact(
    text,
    '        settings: { ...settings, provider: primaryProvider },\n        actionGrounding: intelligence.actionGrounding || null,',
    '        settings: { ...settings, provider: primaryProvider },\n        actionGrounding: intelligence.actionGrounding || null,\n        io,',
    'RUNTIME_PRIMARY_IO_CONTEXT',
)
text = replace_exact(
    text,
    '            actionGrounding: intelligence.actionGrounding || null,\n            settings: {',
    '            actionGrounding: intelligence.actionGrounding || null,\n            io,\n            settings: {',
    'RUNTIME_FALLBACK_IO_CONTEXT',
)
'''

count = source.count(old)
if count != 1:
    raise SystemExit(f"PHASE13_RUNTIME_IO_REPAIR_ERROR=FAULTY_BLOCK_COUNT_{count}")

fixed = source.replace(old, new, 1)
if "RUNTIME_IO_CONTEXT" in fixed:
    raise SystemExit("PHASE13_RUNTIME_IO_REPAIR_ERROR=STALE_RUNTIME_IO_CONTEXT")
if "RUNTIME_PRIMARY_IO_CONTEXT" not in fixed or "RUNTIME_FALLBACK_IO_CONTEXT" not in fixed:
    raise SystemExit("PHASE13_RUNTIME_IO_REPAIR_ERROR=FIXED_MARKERS_MISSING")

# Execute the corrected generator entirely in memory. It retains the original
# generator's atomic transformation checks, so no TOS file is written unless
# every Phase 13 anchor succeeds.
namespace = {
    "__name__": "__main__",
    "__file__": str(SOURCE),
}
exec(compile(fixed, str(SOURCE), "exec"), namespace, namespace)
print("PHASE13_RUNTIME_IO_ANCHOR_REPAIR=PASS")
