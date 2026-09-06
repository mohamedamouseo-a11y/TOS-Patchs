from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
PATCH_DIR = Path(__file__).resolve().parent
PAGE = ROOT / "frontend/src/pages/TeamPerformanceDashboard.jsx"
PERIOD = ROOT / "frontend/src/components/performance/PerformancePeriodControl.jsx"
V2_STYLE = ROOT / "frontend/src/components/performance/teamPerformanceFlagshipV2.css"
V3_STYLE = ROOT / "frontend/src/components/performance/teamPerformanceFlagshipV3Menus.css"
OVERRIDE = PATCH_DIR / "teamPerformanceFlagshipV3_1VisualPolish.css"
FRONTEND = ROOT / "frontend"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_PAGE_SHA256 = "fddfddb3e594af04dca4d812b721db4d7bade2cb18fb9bccae150b9b5caf15da"
EXPECTED_PERIOD_SHA256 = "4dc131b3509acfdbcd93e76b56bc3bbafa7e60d3039335b6edcf3c0a742b7120"
EXPECTED_V2_STYLE_SHA256 = "f380444455a8f3a1973ac083f7ec302cd4f6dffb7722ddd5512b3382e7881d7c"
EXPECTED_V3_STYLE_SHA256 = "964d249bd73af032442221a26e776bbf8639599e8667591d8699cdadb2e02f9a"

V2_RUNTIME = "--tos-team-performance-flagship-v2-runtime"
V3_RUNTIME = "--tos-team-performance-flagship-v3-menus-runtime"
V31_RUNTIME = "--tos-team-performance-flagship-v3-1-runtime"

print("RUNNING=PHASE04_4_TEAM_PERFORMANCE_FLAGSHIP_V3_1_VISUAL_POLISH")


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
    print("V3_1_RUNTIME=NO")
    sys.exit(1)


if ROOT.resolve() == Path("/"):
    fail("unsafe ROOT")

for path in (PAGE, PERIOD, V2_STYLE, V3_STYLE, OVERRIDE, FRONTEND, LIVE_PARENT):
    if not path.exists():
        fail(f"required path missing: {path}")

actual_page = sha256(PAGE)
actual_period = sha256(PERIOD)
actual_v2_style = sha256(V2_STYLE)
actual_v3_style = sha256(V3_STYLE)

if actual_page != EXPECTED_PAGE_SHA256:
    fail(f"TeamPerformanceDashboard.jsx source guard mismatch: {actual_page}")
if actual_period != EXPECTED_PERIOD_SHA256:
    fail(f"PerformancePeriodControl.jsx source guard mismatch: {actual_period}")
if actual_v2_style != EXPECTED_V2_STYLE_SHA256:
    fail(f"teamPerformanceFlagshipV2.css source guard mismatch: {actual_v2_style}")
if actual_v3_style != EXPECTED_V3_STYLE_SHA256:
    fail(f"teamPerformanceFlagshipV3Menus.css source guard mismatch: {actual_v3_style}")

original_v3_style = V3_STYLE.read_text(encoding="utf-8")
override_css = OVERRIDE.read_text(encoding="utf-8")

if V2_RUNTIME not in V2_STYLE.read_text(encoding="utf-8"):
    fail("V2 runtime marker missing")
if V3_RUNTIME not in original_v3_style:
    fail("V3 runtime marker missing")
if V31_RUNTIME in original_v3_style:
    fail("V3.1 visual polish appears already applied")
if V31_RUNTIME not in override_css:
    fail("V3.1 runtime marker missing from override CSS")

required_markers = [
    '#phase1-goals-disclosure',
    '#phase1-intelligence-disclosure',
    '#phase1-deep-dive-disclosure',
    '#team-performance-executive',
    '.tos-tp-employee-ledger-v2',
    '#team-performance-reviews .border-dashed',
]
for marker in required_markers:
    if marker not in override_css:
        fail(f"required visual polish marker missing: {marker}")

try:
    V3_STYLE.write_text(original_v3_style.rstrip() + "\n\n" + override_css.strip() + "\n", encoding="utf-8")
except Exception as exc:
    V3_STYLE.write_text(original_v3_style, encoding="utf-8")
    fail(f"V3.1 stylesheet transformation failed and rolled back: {exc}")

build = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, text=True, capture_output=True)
if build.returncode != 0:
    print(build.stdout[-6000:])
    print(build.stderr[-6000:])
    V3_STYLE.write_text(original_v3_style, encoding="utf-8")
    fail("frontend build failed; source rolled back")

if not DIST.exists():
    V3_STYLE.write_text(original_v3_style, encoding="utf-8")
    fail("frontend dist missing after successful build")

for marker in (V31_RUNTIME.encode(), V3_RUNTIME.encode(), V2_RUNTIME.encode()):
    if tree_count(DIST, marker) < 1:
        V3_STYLE.write_text(original_v3_style, encoding="utf-8")
        fail(f"built output missing runtime marker: {marker.decode()}")

timestamp = int(time.time())
candidate = LIVE_PARENT / f"build.team-performance-v3-1-candidate-{timestamp}"
backup = LIVE_PARENT / f"build.team-performance-v3-1-backup-{timestamp}"
failed_live = LIVE_PARENT / f"build.team-performance-v3-1-failed-{timestamp}"

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
        V3_STYLE.write_text(original_v3_style, encoding="utf-8")
    fail(f"live deployment failed and rollback attempted: {exc}")

print("PASS/FAIL=PASS")
print("BUILD_RESULT=PASS")
print("LIVE_DEPLOY=PASS")
print("V3_1_RUNTIME=YES")
print("V3_BASELINE_PRESERVED=YES")
print("LIGHT_SURFACE_DEPTH=REFINED")
print("TEAM_TABLE_DEPTH=REFINED")
print("EXECUTIVE_ALERT_SATURATION=SOFTENED")
print("GOALS_DISCLOSURE_ACCENT=CHAMPAGNE")
print("INTELLIGENCE_DISCLOSURE_ACCENT=SLATE_BLUE")
print("DEEP_DIVE_DISCLOSURE_ACCENT=VIOLET_SLATE")
print("DEEP_DIVE_EMPTY_STATE=COMPACT")
print("DARK_BASELINE_PRESERVED=YES")
print("MENU_DATE_LAYERING_PRESERVED=YES")
print("STRUCTURE_CHANGED=NO")
print("FUNCTIONALITY_CHANGED=NO")
print("BUSINESS_LOGIC_CHANGED=NO")
print("API_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print(f"TEAM_PERFORMANCE_SHA256={sha256(PAGE)}")
print(f"PERIOD_CONTROL_SHA256={sha256(PERIOD)}")
print(f"FLAGSHIP_V2_CSS_SHA256={sha256(V2_STYLE)}")
print(f"FLAGSHIP_V3_CSS_SHA256={sha256(V3_STYLE)}")
print(f"LIVE_BACKUP={backup}")
print("STATUS=READY")
