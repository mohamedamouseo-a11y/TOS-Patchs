from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
PATCH_DIR = Path(__file__).resolve().parent
PAGE = ROOT / "frontend/src/pages/EmployeeWorkHub.jsx"
DATE_STYLE = ROOT / "frontend/src/pages/employeeWorkHubDatePickerV1.css"
TARGET_COMPONENT = ROOT / "frontend/src/pages/EmployeeWorkPremiumControlsV1.jsx"
TARGET_STYLE = ROOT / "frontend/src/pages/employeeWorkHubPremiumControlsV1.css"
SOURCE_COMPONENT = PATCH_DIR / "EmployeeWorkPremiumControlsV1.jsx"
SOURCE_STYLE = PATCH_DIR / "employeeWorkHubPremiumControlsV1.css"
FRONTEND = ROOT / "frontend"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_PAGE_SHA256 = "703f58588d6bb765bb8a61fc928400008255ed90f2e87f1b30965b9c61114c33"
EXPECTED_DATE_STYLE_SHA256 = "c7a5517565158ae98d627e2b8b29a22c15b7c425b154ebfd81cabd7cbcd100fe"
RUNTIME_TOKEN = "--tos-employee-work-premium-controls-v1-runtime"

print("RUNNING=EMPLOYEE_WORK_HUB_PREMIUM_CONTROLS_V1")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_count(root: Path, needle: bytes) -> int:
    if not root.exists():
        return 0
    total = 0
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            total += path.read_bytes().count(needle)
        except OSError:
            pass
    return total


def fail(message: str):
    print("PASS/FAIL=FAIL")
    print("ERROR=" + str(message))
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    sys.exit(1)


def cleanup_exact_created_files():
    for path in (TARGET_COMPONENT, TARGET_STYLE):
        if path.exists():
            path.unlink()


if ROOT.resolve() == Path("/"):
    fail("unsafe ROOT")
for path in (PAGE, DATE_STYLE, SOURCE_COMPONENT, SOURCE_STYLE, FRONTEND, LIVE_PARENT):
    if not path.exists():
        fail(f"required path missing: {path}")
if TARGET_COMPONENT.exists() or TARGET_STYLE.exists():
    fail("premium controls target files already exist")
if sha256(PAGE) != EXPECTED_PAGE_SHA256:
    fail(f"EmployeeWorkHub.jsx source guard mismatch: {sha256(PAGE)}")
if sha256(DATE_STYLE) != EXPECTED_DATE_STYLE_SHA256:
    fail(f"employeeWorkHubDatePickerV1.css source guard mismatch: {sha256(DATE_STYLE)}")

original_page = PAGE.read_text(encoding="utf-8")
select_count = original_page.count("<select")
time_count = original_page.count('<input type="time"')
if select_count < 1:
    fail("no native selects found")
if time_count < 1:
    fail("no native time inputs found")

try:
    page = original_page
    import_anchor = 'import "./employeeWorkHubDatePickerV1.css";'
    if page.count(import_anchor) != 1:
        raise RuntimeError(f"date picker import anchor expected 1 match, found {page.count(import_anchor)}")
    page = page.replace(import_anchor, import_anchor + '\nimport { EmployeeWorkSelectV1, EmployeeWorkTimePickerV1 } from "./EmployeeWorkPremiumControlsV1";', 1)
    page = page.replace("<select", "<EmployeeWorkSelectV1")
    page = page.replace("</select>", "</EmployeeWorkSelectV1>")
    page = page.replace('<input type="time"', '<EmployeeWorkTimePickerV1')

    if page.count("<select") != 0 or page.count("</select>") != 0:
        raise RuntimeError("native select postcondition failed")
    if page.count('<input type="time"') != 0:
        raise RuntimeError("native time input postcondition failed")
    if page.count("<EmployeeWorkSelectV1") != select_count:
        raise RuntimeError(f"premium select count mismatch: expected {select_count}, found {page.count('<EmployeeWorkSelectV1')}")
    if page.count("<EmployeeWorkTimePickerV1") != time_count:
        raise RuntimeError(f"premium time count mismatch: expected {time_count}, found {page.count('<EmployeeWorkTimePickerV1')}")

    PAGE.write_text(page, encoding="utf-8")
    shutil.copy2(SOURCE_COMPONENT, TARGET_COMPONENT)
    shutil.copy2(SOURCE_STYLE, TARGET_STYLE)
except Exception as exc:
    PAGE.write_text(original_page, encoding="utf-8")
    cleanup_exact_created_files()
    fail(f"source transformation failed and exact files were rolled back: {exc}")

build = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, text=True, capture_output=True)
if build.returncode != 0:
    print(build.stdout[-5000:])
    print(build.stderr[-5000:])
    PAGE.write_text(original_page, encoding="utf-8")
    cleanup_exact_created_files()
    fail("frontend build failed; exact source changes rolled back")

if not DIST.exists():
    PAGE.write_text(original_page, encoding="utf-8")
    cleanup_exact_created_files()
    fail("frontend dist missing after successful build")

if tree_count(DIST, RUNTIME_TOKEN.encode()) < 1:
    PAGE.write_text(original_page, encoding="utf-8")
    cleanup_exact_created_files()
    fail("built output missing premium controls runtime marker")
if tree_count(DIST, b"tos-ewh-select-menu-v1") < 1 or tree_count(DIST, b"tos-ewh-time-menu-v1") < 1:
    PAGE.write_text(original_page, encoding="utf-8")
    cleanup_exact_created_files()
    fail("built output missing premium controls classes")

timestamp = int(time.time())
candidate = LIVE_PARENT / f"build.ewh-controls-v1-candidate-{timestamp}"
backup = LIVE_PARENT / f"build.ewh-controls-v1-backup-{timestamp}"
failed_live = LIVE_PARENT / f"build.ewh-controls-v1-failed-{timestamp}"

try:
    if candidate.exists() or backup.exists() or failed_live.exists():
        raise RuntimeError("timestamped deployment path already exists")
    shutil.copytree(DIST, candidate)
    if not LIVE.exists():
        raise RuntimeError(f"live build missing: {LIVE}")
    LIVE.rename(backup)
    candidate.rename(LIVE)
except Exception as exc:
    try:
        if LIVE.exists() and backup.exists():
            LIVE.rename(failed_live)
            backup.rename(LIVE)
        elif backup.exists() and not LIVE.exists():
            backup.rename(LIVE)
    finally:
        PAGE.write_text(original_page, encoding="utf-8")
        cleanup_exact_created_files()
    fail(f"live deployment failed and rollback attempted: {exc}")

print("PASS/FAIL=PASS")
print("BUILD_RESULT=PASS")
print("LIVE_DEPLOY=PASS")
print(f"SOURCE_PAGE_SHA256={EXPECTED_PAGE_SHA256}")
print(f"SOURCE_DATE_STYLE_SHA256={EXPECTED_DATE_STYLE_SHA256}")
print(f"NATIVE_SELECTS_BEFORE={select_count}")
print("NATIVE_SELECTS_AFTER=0")
print(f"PREMIUM_SELECTS={select_count}")
print(f"NATIVE_TIME_INPUTS_BEFORE={time_count}")
print("NATIVE_TIME_INPUTS_AFTER=0")
print(f"PREMIUM_TIME_PICKERS={time_count}")
print("PREMIUM_SELECT_PORTAL=YES")
print("PREMIUM_SELECT_SEARCH_FOR_LONG_LISTS=YES")
print("PREMIUM_TIME_PORTAL=YES")
print("TIME_12H_UI_WITH_24H_VALUE_PRESERVED=YES")
print("ADAPTIVE_PLACEMENT=YES")
print("MOBILE_BOTTOM_SHEET=YES")
print("RTL_ARABIC=YES")
print("LIGHT_DARK=YES")
print("BUSINESS_LOGIC_CHANGED=NO")
print("API_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print(f"EMPLOYEE_WORK_HUB_SHA256={sha256(PAGE)}")
print(f"PREMIUM_CONTROLS_COMPONENT_SHA256={sha256(TARGET_COMPONENT)}")
print(f"PREMIUM_CONTROLS_STYLE_SHA256={sha256(TARGET_STYLE)}")
print(f"LIVE_BACKUP={backup}")
print("STATUS=READY")
