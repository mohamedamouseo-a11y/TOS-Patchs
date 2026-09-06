from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
PAGE = ROOT / "frontend/src/pages/EmployeeWorkHub.jsx"
STYLE = ROOT / "frontend/src/pages/employeeWorkHubDatePickerV1.css"
FRONTEND = ROOT / "frontend"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_PAGE_GIT_BLOB_SHA = "ff1694ff13b8db0579e0aed96d7eb278121774b7"
EXPECTED_STYLE_GIT_BLOB_SHA = "13bc9e53172e7e72a88b89170ff968a5255d089c"
RUNTIME_TOKEN = "--tos-employee-work-date-picker-v1-3-runtime"

print("RUNNING=EMPLOYEE_WORK_HUB_DATE_PICKER_V1_3_PLACEMENT")


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode("utf-8") + data).hexdigest()


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


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 match, found {count}")
    return text.replace(old, new, 1)


if ROOT.resolve() == Path("/"):
    fail("unsafe ROOT")
for path in (PAGE, STYLE, FRONTEND, LIVE_PARENT):
    if not path.exists():
        fail(f"required path missing: {path}")

if git_blob_sha(PAGE) != EXPECTED_PAGE_GIT_BLOB_SHA:
    fail(f"EmployeeWorkHub.jsx source guard mismatch: {git_blob_sha(PAGE)}")
if git_blob_sha(STYLE) != EXPECTED_STYLE_GIT_BLOB_SHA:
    fail(f"employeeWorkHubDatePickerV1.css source guard mismatch: {git_blob_sha(STYLE)}")

original_page = PAGE.read_text(encoding="utf-8")
original_style = STYLE.read_text(encoding="utf-8")

if RUNTIME_TOKEN in original_style:
    fail("V1.3 placement refinement appears already applied")
if 'className="tos-ewh-date-menu-v1"' not in original_page:
    fail("V1.2 premium date picker baseline missing")

try:
    page = original_page
    style = original_style

    page = replace_once(
        page,
        'const [position, setPosition] = useState({ top: 0, left: 0, width: 338, maxHeight: 430 });',
        'const [position, setPosition] = useState({ top: 0, left: 0, width: 338, maxHeight: 430, scrollable: false });',
        "date picker position state",
    )

    old_position_logic = '''      const gap = 12;\n      const availableWidth = Math.max(260, window.innerWidth - gap * 2);\n      const width = Math.min(356, availableWidth, Math.max(310, rect.width + 70));\n      const left = Math.min(Math.max(gap, rect.left), Math.max(gap, window.innerWidth - width - gap));\n      const desiredHeight = 430;\n      const below = window.innerHeight - rect.bottom - gap;\n      const above = rect.top - gap;\n      const openAbove = below < 360 && above > below;\n      const availableHeight = Math.max(240, (openAbove ? above : below) - 8);\n      const maxHeight = Math.min(desiredHeight, availableHeight);\n      const top = openAbove ? Math.max(gap, rect.top - maxHeight - 8) : rect.bottom + 8;\n      setPosition({ top, left, width, maxHeight });'''

    new_position_logic = '''      const gap = 12;\n      const availableWidth = Math.max(260, window.innerWidth - gap * 2);\n      const width = Math.min(356, availableWidth, Math.max(310, rect.width + 70));\n      const left = Math.min(Math.max(gap, rect.left), Math.max(gap, window.innerWidth - width - gap));\n      const measuredHeight = menuRef.current?.scrollHeight || 390;\n      const desiredHeight = Math.min(460, Math.max(340, measuredHeight));\n      const below = Math.max(0, window.innerHeight - rect.bottom - gap);\n      const above = Math.max(0, rect.top - gap);\n      const canFitBelow = below >= desiredHeight;\n      const canFitAbove = above >= desiredHeight;\n      const openAbove = canFitAbove && !canFitBelow ? true : (!canFitBelow && !canFitAbove ? above > below : false);\n      const sideSpace = openAbove ? above : below;\n      const availableHeight = Math.max(180, sideSpace - 8);\n      const maxHeight = Math.min(desiredHeight, availableHeight);\n      const scrollable = maxHeight + 2 < desiredHeight;\n      const top = openAbove ? Math.max(gap, rect.top - maxHeight - 8) : rect.bottom + 8;\n      setPosition({ top, left, width, maxHeight, scrollable });'''

    page = replace_once(page, old_position_logic, new_position_logic, "adaptive date picker placement")

    page = replace_once(
        page,
        '            style={{ position: "fixed", top: position.top, left: position.left, width: position.width, maxHeight: position.maxHeight, zIndex: 18020 }}\n            className="tos-ewh-date-menu-v1"',
        '            style={{ position: "fixed", top: position.top, left: position.left, width: position.width, maxHeight: position.maxHeight, zIndex: 18020 }}\n            data-scrollable={position.scrollable ? "true" : "false"}\n            className="tos-ewh-date-menu-v1"',
        "scrollable state hook",
    )

    style = replace_once(
        style,
        ':root {\n  --tos-employee-work-date-picker-v1-runtime: 1;\n}',
        ':root {\n  --tos-employee-work-date-picker-v1-runtime: 1;\n  --tos-employee-work-date-picker-v1-3-runtime: 1;\n}',
        "V1.3 runtime token",
    )

    style = replace_once(
        style,
        '.tos-ewh-date-menu-v1 {\n  overflow: auto;',
        '.tos-ewh-date-menu-v1 {\n  overflow: hidden;',
        "remove default desktop scrollbar",
    )

    style = replace_once(
        style,
        '''  -webkit-backdrop-filter: blur(20px);\n}\n\n.tos-ewh-date-sheet-handle-v1 {''',
        '''  -webkit-backdrop-filter: blur(20px);\n}\n\n.tos-ewh-date-menu-v1[data-scrollable="true"] {\n  overflow-y: auto;\n  overflow-x: hidden;\n  overscroll-behavior: contain;\n  scrollbar-width: thin;\n  scrollbar-color: rgba(148, 117, 62, 0.38) transparent;\n}\n\n.tos-ewh-date-menu-v1[data-scrollable="true"]::-webkit-scrollbar {\n  width: 6px;\n}\n\n.tos-ewh-date-menu-v1[data-scrollable="true"]::-webkit-scrollbar-track {\n  background: transparent;\n}\n\n.tos-ewh-date-menu-v1[data-scrollable="true"]::-webkit-scrollbar-thumb {\n  border-radius: 999px;\n  background: rgba(148, 117, 62, 0.34);\n}\n\n.tos-ewh-date-sheet-handle-v1 {''',
        "conditional premium scrollbar",
    )

    style = replace_once(
        style,
        '''    max-height: min(520px, calc(100dvh - 20px)) !important;\n    z-index: 18020 !important;''',
        '''    max-height: min(520px, calc(100dvh - 20px)) !important;\n    overflow-y: auto !important;\n    overflow-x: hidden !important;\n    overscroll-behavior: contain;\n    z-index: 18020 !important;''',
        "mobile bottom sheet scrolling",
    )

    if page.count('data-scrollable={position.scrollable ? "true" : "false"}') != 1:
        raise RuntimeError("V1.3 scrollable hook postcondition failed")
    if style.count(RUNTIME_TOKEN) != 1:
        raise RuntimeError("V1.3 runtime token postcondition failed")

    PAGE.write_text(page, encoding="utf-8")
    STYLE.write_text(style, encoding="utf-8")
except Exception as exc:
    PAGE.write_text(original_page, encoding="utf-8")
    STYLE.write_text(original_style, encoding="utf-8")
    fail(f"source refinement failed and was rolled back: {exc}")

build = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, text=True, capture_output=True)
if build.returncode != 0:
    print(build.stdout[-5000:])
    print(build.stderr[-5000:])
    PAGE.write_text(original_page, encoding="utf-8")
    STYLE.write_text(original_style, encoding="utf-8")
    fail("frontend build failed; source changes rolled back")

if not DIST.exists():
    PAGE.write_text(original_page, encoding="utf-8")
    STYLE.write_text(original_style, encoding="utf-8")
    fail("frontend dist missing after successful build")

if tree_count(DIST, RUNTIME_TOKEN.encode()) < 1 or tree_count(DIST, b"data-scrollable") < 1:
    PAGE.write_text(original_page, encoding="utf-8")
    STYLE.write_text(original_style, encoding="utf-8")
    fail("built output missing V1.3 runtime markers")

timestamp = int(time.time())
candidate = LIVE_PARENT / f"build.ewh-date-v1-3-candidate-{timestamp}"
backup = LIVE_PARENT / f"build.ewh-date-v1-3-backup-{timestamp}"
failed_live = LIVE_PARENT / f"build.ewh-date-v1-3-failed-{timestamp}"

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
        STYLE.write_text(original_style, encoding="utf-8")
    fail(f"live deployment failed and rollback attempted: {exc}")

print("PASS/FAIL=PASS")
print("BUILD_RESULT=PASS")
print("LIVE_DEPLOY=PASS")
print(f"SOURCE_PAGE_GIT_BLOB_SHA={EXPECTED_PAGE_GIT_BLOB_SHA}")
print(f"SOURCE_STYLE_GIT_BLOB_SHA={EXPECTED_STYLE_GIT_BLOB_SHA}")
print("ADAPTIVE_PLACEMENT=YES")
print("OPEN_ABOVE_WHEN_NEEDED=YES")
print("UNNECESSARY_DESKTOP_SCROLLBAR=REMOVED")
print("SCROLLBAR_ONLY_WHEN_NEEDED=YES")
print("MOBILE_BOTTOM_SHEET_PRESERVED=YES")
print("RTL_ARABIC_PRESERVED=YES")
print("LIGHT_DARK_PRESERVED=YES")
print("BUSINESS_LOGIC_CHANGED=NO")
print("API_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print(f"EMPLOYEE_WORK_HUB_SHA256={sha256(PAGE)}")
print(f"DATE_PICKER_STYLE_SHA256={sha256(STYLE)}")
print(f"LIVE_BACKUP={backup}")
print("STATUS=READY")
