from pathlib import Path
import hashlib
import subprocess
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
PATCHS_ROOT = Path(__file__).resolve().parent.parent
V1_DIR = PATCHS_ROOT / "TOS-UXUI-TASK-DETAILS-PREMIUM-SAAS-REFERENCE-V1"
BASE_INSTALLER = V1_DIR / "apply_tos_uxui_task_details_premium_saas_reference_v1.py"
STYLE_PAYLOAD = V1_DIR / "taskDetailsPremiumSaasReferenceV1.css"

EXPECTED_BASE_INSTALLER_BLOB = "d4a82dac9e72d5553c66d32c03ab05e5b0aa10ab"
EXPECTED_STYLE_PAYLOAD_BLOB = "eac2c8de879a670962509fd884da360b4a779840"

OLD_NAV_END = 'NAV_END = \'\\n\\n              {activeTaskTab === "overview" && (\''
NEW_NAV_END = 'NAV_END = \'\\n              </nav>\''
OLD_NAV_INDEX = '    nav_end = updated.index(NAV_END, nav_start)\n'
NEW_NAV_INDEX = '    nav_end = updated.index(NAV_END, nav_start) + len(NAV_END)\n'
SURGERY_LINE = '    updated = updated[:nav_start] + reference_nav + updated[nav_end:]\n'


def fail(message):
    print("PASS/FAIL=FAIL")
    print(f"ERROR={message}")
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("R1_STATUS=STOPPED")
    raise SystemExit(1)


def git_blob_sha(path):
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


if not BASE_INSTALLER.exists():
    fail(f"V1 base installer missing: {BASE_INSTALLER}")
if not STYLE_PAYLOAD.exists():
    fail(f"V1 style payload missing: {STYLE_PAYLOAD}")
if git_blob_sha(BASE_INSTALLER) != EXPECTED_BASE_INSTALLER_BLOB:
    fail("V1 base installer changed; refusing to apply R1 surgery")
if git_blob_sha(STYLE_PAYLOAD) != EXPECTED_STYLE_PAYLOAD_BLOB:
    fail("V1 style payload changed; refusing to apply R1 surgery")

source = BASE_INSTALLER.read_text()
for old, label in (
    (OLD_NAV_END, "buggy NAV_END marker"),
    (OLD_NAV_INDEX, "buggy nav_end index line"),
    (SURGERY_LINE, "nav replacement surgery line"),
):
    count = source.count(old)
    if count != 1:
        fail(f"{label} count changed unexpectedly: {count}")

# Root cause fix:
# V1 used the first Overview section as the end boundary for replacing the tabs nav.
# The Checklist section sits between </nav> and Overview, so that broad slice deleted the
# freshly transformed Checklist/Subtasks block. R1 limits replacement to the nav element only.
corrected = source.replace(OLD_NAV_END, NEW_NAV_END, 1)
corrected = corrected.replace(OLD_NAV_INDEX, NEW_NAV_INDEX, 1)

if corrected == source:
    fail("R1 produced no installer change")
if '["checklist", "subtasks"].includes(activeTaskTab)' not in corrected:
    fail("R1 corrected installer lost Checklist/Subtasks post-transform guard")
if 'nav_end = updated.index(NAV_END, nav_start) + len(NAV_END)' not in corrected:
    fail("R1 nav boundary fix missing after transform")

runtime_installer = V1_DIR / ".apply_tos_uxui_task_details_premium_saas_reference_v1_r1_runtime.py"
if runtime_installer.exists():
    fail(f"temporary R1 runtime installer already exists: {runtime_installer}")

try:
    runtime_installer.write_text(corrected)
    completed = subprocess.run([sys.executable, str(runtime_installer), str(ROOT)])
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)
finally:
    try:
        runtime_installer.unlink(missing_ok=True)
    except Exception:
        pass

print("TASK_DETAILS_PREMIUM_SAAS_REFERENCE_V1_R1_SURGERY_FIX=YES")
print("R1_NAV_REPLACEMENT_BOUNDARY=NAV_ELEMENT_ONLY")
print("R1_CHECKLIST_SUBTASKS_BLOCK_PRESERVED=YES")
print("R1_MANUAL_FIXES=NO")
print("R1_STATUS=READY_FOR_VISUAL_QA")
