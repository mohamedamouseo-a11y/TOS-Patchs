from pathlib import Path
import subprocess
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
HERE = Path(__file__).resolve().parent
V9_DIR = "TOS-UXUI-PHASE-04-1-DESIGN-QUEUE-FLAGSHIP-V9"
V9_NAME = "apply_phase04_1_design_queue_flagship_v9.py"
TMP = HERE / ".v9_recovery_v1_runtime.py"

print("RUNNING=PHASE04_1_DESIGN_QUEUE_FLAGSHIP_V9_RECOVERY_V1")


def fail(message: str):
    if TMP.exists():
        TMP.unlink()
    print("PASS/FAIL=FAIL")
    print("BUILD_RESULT=SKIPPED")
    print("LIVE_DEPLOY=SKIPPED")
    print("V9_RECOVERY_V1=NO")
    print(f"ERROR={message}")
    sys.exit(1)


# The original V9 installer was already executed on this target, so its exact
# patch folder should exist. Also support a full patch-repo checkout.
candidates = [
    ROOT / V9_DIR / V9_NAME,
    HERE.parent / V9_DIR / V9_NAME,
]
try:
    candidates.extend(ROOT.rglob(V9_NAME))
except OSError:
    pass

v9_path = next((p for p in candidates if p.exists() and p.is_file()), None)
if not v9_path:
    fail("original V9 installer not found on target")

source = v9_path.read_text()

# Root cause: the literal marker TOS_DQ_PREMIUM_MENU_V9 appears once in source
# (the const declaration). Runtime uses the variable DQ_PREMIUM_MENU_VERSION,
# so requiring >=2 literal occurrences is an invalid verification condition.
old_guard = '''    if DQ.read_text().count(V9_MARKER) < 2:\n        raise RuntimeError("V9 marker missing from source")\n'''
new_guard = '''    if DQ.read_text().count(V9_MARKER) != 1:\n        raise RuntimeError("V9 source marker count must be exactly 1")\n'''
if source.count(old_guard) != 1:
    fail(f"V9 marker guard expected once, found {source.count(old_guard)}")
source = source.replace(old_guard, new_guard, 1)

# Make this run/report explicitly distinguishable from the failed V9 attempt.
source = source.replace(
    'print("RUNNING=PHASE04_1_DESIGN_QUEUE_FLAGSHIP_V9")',
    'print("RUNNING=PHASE04_1_DESIGN_QUEUE_FLAGSHIP_V9_RECOVERY_V1")',
    1,
)
source = source.replace(
    'print("V9_RUNTIME=YES")',
    'print("V9_RUNTIME=YES")\nprint("V9_RECOVERY_V1=YES")',
    1,
)

TMP.write_text(source)
try:
    result = subprocess.run(
        [sys.executable, str(TMP), str(ROOT)],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
    )
    if result.stdout:
        print(result.stdout.rstrip())
    if result.stderr:
        print(result.stderr.rstrip())
    code = result.returncode
finally:
    if TMP.exists():
        TMP.unlink()

if code != 0:
    sys.exit(code)
