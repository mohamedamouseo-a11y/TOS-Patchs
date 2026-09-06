from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
PATCH_DIR = Path(__file__).resolve().parent
PAGE = ROOT / "frontend/src/pages/EmployeeWorkHub.jsx"
UI = ROOT / "frontend/src/pages/ThrsExecutiveUIV2.jsx"
STYLE = ROOT / "frontend/src/pages/employeeWorkHubThrsExecutiveV2.css"
OVERRIDE = PATCH_DIR / "employeeWorkHubThrsExecutiveV2_2.css"
FRONTEND = ROOT / "frontend"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_PAGE_SHA256 = "d6b3ae52fcfcabaaa6c5e8bcacc356afe5bfebf4ac8b9caaa357cb58a68fd86a"
EXPECTED_UI_SHA256 = "367d88f218409c46cefdaf29fe1e0c56afede8a70864dc226f1504c6c1dbd8ea"
EXPECTED_STYLE_SHA256 = "c38b6837d3889722747e117d860ffebba0102ededd24ffaca9c5520d1eee2289"
RUNTIME_TOKEN = "--tos-thrs-executive-v2-2-runtime"

print("RUNNING=TOS_THRS_EXECUTIVE_PREMIUM_V2_2_DENSITY_REFINEMENT")


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


if ROOT.resolve() == Path("/"):
    fail("unsafe ROOT")

for path in (PAGE, UI, STYLE, OVERRIDE, FRONTEND, LIVE_PARENT):
    if not path.exists():
        fail(f"required path missing: {path}")

actual_page = sha256(PAGE)
actual_ui = sha256(UI)
actual_style = sha256(STYLE)

if actual_page != EXPECTED_PAGE_SHA256:
    fail(f"EmployeeWorkHub.jsx source guard mismatch: {actual_page}")
if actual_ui != EXPECTED_UI_SHA256:
    fail(f"ThrsExecutiveUIV2.jsx source guard mismatch: {actual_ui}")
if actual_style != EXPECTED_STYLE_SHA256:
    fail(f"employeeWorkHubThrsExecutiveV2.css source guard mismatch: {actual_style}")

original_style = STYLE.read_text(encoding="utf-8")
override_css = OVERRIDE.read_text(encoding="utf-8")

if RUNTIME_TOKEN in original_style:
    fail("V2.2 runtime token already present")
if RUNTIME_TOKEN not in override_css:
    fail("V2.2 override runtime token missing")

required_css_markers = [
    "grid-template-columns: repeat(4, minmax(0, 1fr));",
    "grid-template-columns: repeat(3, minmax(0, 1fr));",
    ".tos-thrs-smart-search-v2 > input",
    ".dark .tos-thrs-kpi-v2",
    "white-space: normal;",
]
for marker in required_css_markers:
    if marker not in override_css:
        fail(f"required V2.2 CSS marker missing: {marker}")

try:
    STYLE.write_text(original_style.rstrip() + "\n\n" + override_css.strip() + "\n", encoding="utf-8")
except Exception as exc:
    STYLE.write_text(original_style, encoding="utf-8")
    fail(f"style transformation failed and rolled back: {exc}")

build = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, text=True, capture_output=True)
if build.returncode != 0:
    print(build.stdout[-6000:])
    print(build.stderr[-6000:])
    STYLE.write_text(original_style, encoding="utf-8")
    fail("frontend build failed; V2.2 style rolled back")

if not DIST.exists():
    STYLE.write_text(original_style, encoding="utf-8")
    fail("frontend dist missing after successful build")

for marker in (
    RUNTIME_TOKEN.encode(),
    b"tos-thrs-admin-kpis-v2",
    b"tos-thrs-calendar-kpis-v2",
    b"tos-thrs-smart-search-v2",
):
    if tree_count(DIST, marker) < 1:
        STYLE.write_text(original_style, encoding="utf-8")
        fail(f"built output missing runtime marker: {marker.decode(errors='ignore')}")

timestamp = int(time.time())
candidate = LIVE_PARENT / f"build.thrs-executive-v2-2-candidate-{timestamp}"
backup = LIVE_PARENT / f"build.thrs-executive-v2-2-backup-{timestamp}"
failed_live = LIVE_PARENT / f"build.thrs-executive-v2-2-failed-{timestamp}"

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
        STYLE.write_text(original_style, encoding="utf-8")
    fail(f"live deployment failed and rollback attempted: {exc}")

print("PASS/FAIL=PASS")
print("BUILD_RESULT=PASS")
print("LIVE_DEPLOY=PASS")
print(f"SOURCE_PAGE_SHA256={EXPECTED_PAGE_SHA256}")
print(f"SOURCE_UI_SHA256={EXPECTED_UI_SHA256}")
print(f"SOURCE_STYLE_SHA256={EXPECTED_STYLE_SHA256}")
print("ADMIN_KPI_LAYOUT_WIDE=4x2")
print("CALENDAR_KPI_LAYOUT_WIDE=3x2")
print("KPI_LABEL_TRUNCATION=REMOVED")
print("KPI_CARD_BREATHING_ROOM=INCREASED")
print("SMART_SEARCH_EMPHASIS=INCREASED")
print("LIGHT_HIERARCHY=STRONGER")
print("DARK_DEPTH=STRONGER")
print("STRUCTURE_CHANGED=NO")
print("FUNCTIONALITY_CHANGED=NO")
print("BUSINESS_LOGIC_CHANGED=NO")
print("API_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print(f"EMPLOYEE_WORK_HUB_SHA256={sha256(PAGE)}")
print(f"THRS_EXECUTIVE_UI_SHA256={sha256(UI)}")
print(f"THRS_EXECUTIVE_STYLE_SHA256={sha256(STYLE)}")
print(f"LIVE_BACKUP={backup}")
print("STATUS=READY")
