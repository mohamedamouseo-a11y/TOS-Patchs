from pathlib import Path
import subprocess
import sys

PATCH = "TOS-TASK-BOARD-R32-R5-R1-INSTALLER-VALIDATION-FIX"
VERSION = "TOS_TASK_BOARD_R32_R5_R1"
BASE_PATCH_COMMIT = "bfac9dbc1f756c707eb59b27defb385e37cee436"
TARGET = sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS"

HERE = Path(__file__).resolve().parent
PATCH_REPO = HERE.parent
R5_DIR = PATCH_REPO / "TOS-TASK-BOARD-R32-R5-INLINE-WINDOW-GEOMETRY-FIX"
ORIGINAL = R5_DIR / "apply_r32_r5_production.py"
PAYLOAD = R5_DIR / "taskBoardR32R5InlineWindowGeometryFix.css"
TEMP = R5_DIR / ".apply_r32_r5_r1_fixed.py"

if not ORIGINAL.exists():
    raise RuntimeError(f"required original R32_R5 installer missing: {ORIGINAL}")
if not PAYLOAD.exists():
    raise RuntimeError(f"required original R32_R5 payload missing: {PAYLOAD}")

source = ORIGINAL.read_text()

bad = '''    written = BOARD.read_text()\n    for contract in (r5_import, R5_DATA, R5_STORAGE_KEY, "taskWindowGeometryR32R5"):\n        if written.count(contract) != 1:\n            fail(f"R32_R5 source hook count invalid after write: {contract}")'''

good = '''    written = BOARD.read_text()\n    for contract in (r5_import, R5_DATA, R5_STORAGE_KEY):\n        if written.count(contract) != 1:\n            fail(f"R32_R5 source hook count invalid after write: {contract}")\n    geometry_decl = "const taskWindowGeometryR32R5 = (() => {"\n    if written.count(geometry_decl) != 1:\n        fail(f"R32_R5 geometry declaration count invalid after write: {written.count(geometry_decl)}")\n    for contract in (\n        'left: `${taskWindowGeometryR32R5.left}px`',\n        'top: `${taskWindowGeometryR32R5.top}px`',\n        'width: `${taskWindowGeometryR32R5.width}px`',\n        'height: `${taskWindowGeometryR32R5.height}px`',\n        '"--tos-r32-r5-window-width": `${taskWindowGeometryR32R5.width}px`',\n        '"--tos-r32-r5-window-height": `${taskWindowGeometryR32R5.height}px`',\n    ):\n        if contract not in written:\n            fail(f"R32_R5 geometry reference missing after write: {contract}")'''

if source.count(bad) != 1:
    raise RuntimeError(f"R32_R5 known faulty validation block count changed: {source.count(bad)}")

fixed = source.replace(bad, good, 1)
if fixed == source:
    raise RuntimeError("R32_R5 installer validation recovery produced no change")

TEMP.write_text(fixed)
try:
    result = subprocess.run([sys.executable, str(TEMP), TARGET], text=True, capture_output=True)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="", file=sys.stderr)
    if result.returncode != 0:
        raise SystemExit(result.returncode)
finally:
    try:
        TEMP.unlink()
    except FileNotFoundError:
        pass

print(f"RECOVERY_VERSION={VERSION}")
print(f"RECOVERY_PATCH_APPLIED={PATCH}")
print(f"BASE_PATCH_COMMIT={BASE_PATCH_COMMIT}")
print("VALIDATION_GUARD_FIXED=YES")
print("MANUAL_SOURCE_EDIT=NO")
print("PUSH=NO")
