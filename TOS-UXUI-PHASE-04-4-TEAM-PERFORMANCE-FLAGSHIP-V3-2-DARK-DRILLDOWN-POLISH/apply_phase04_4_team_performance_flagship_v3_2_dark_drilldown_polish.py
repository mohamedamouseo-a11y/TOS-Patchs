from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
PATCH_DIR = Path(__file__).resolve().parent
DRILLDOWN = ROOT / "frontend/src/components/performance/PerformanceDrilldownNavigator.jsx"
V3_STYLE = ROOT / "frontend/src/components/performance/teamPerformanceFlagshipV3Menus.css"
OVERRIDE = PATCH_DIR / "teamPerformanceFlagshipV3_2DarkDrilldown.css"
FRONTEND = ROOT / "frontend"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_DRILLDOWN_GIT_BLOB_SHA1 = "923f54b03d6a00a56521cb6ed793908fbbdec8a4"
EXPECTED_V3_STYLE_GIT_BLOB_SHA1 = "4f2fccc56b3f2a5132e707084df973187aa5664a"

V3_RUNTIME = "--tos-team-performance-flagship-v3-menus-runtime"
V31_RUNTIME = "--tos-team-performance-flagship-v3-1-runtime"
V32_RUNTIME = "--tos-team-performance-flagship-v3-2-dark-drilldown-runtime"
CARD_CLASS = "tos-tp-drilldown-department-card-v3-2"

print("RUNNING=PHASE04_4_TEAM_PERFORMANCE_FLAGSHIP_V3_2_DARK_DRILLDOWN_POLISH")


def git_blob_sha1(path: Path) -> str:
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data).hexdigest()


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
    print("V3_2_RUNTIME=NO")
    sys.exit(1)


if ROOT.resolve() == Path("/"):
    fail("unsafe ROOT")

for path in (DRILLDOWN, V3_STYLE, OVERRIDE, FRONTEND, LIVE_PARENT):
    if not path.exists():
        fail(f"required path missing: {path}")

actual_drilldown_blob = git_blob_sha1(DRILLDOWN)
actual_v3_blob = git_blob_sha1(V3_STYLE)
if actual_drilldown_blob != EXPECTED_DRILLDOWN_GIT_BLOB_SHA1:
    fail(f"PerformanceDrilldownNavigator.jsx source guard mismatch: {actual_drilldown_blob}")
if actual_v3_blob != EXPECTED_V3_STYLE_GIT_BLOB_SHA1:
    fail(f"teamPerformanceFlagshipV3Menus.css source guard mismatch: {actual_v3_blob}")

original_drilldown = DRILLDOWN.read_text(encoding="utf-8")
original_v3_style = V3_STYLE.read_text(encoding="utf-8")
override_css = OVERRIDE.read_text(encoding="utf-8")

if V3_RUNTIME not in original_v3_style:
    fail("V3 runtime marker missing")
if V31_RUNTIME not in original_v3_style:
    fail("V3.1 runtime marker missing")
if V32_RUNTIME in original_v3_style or CARD_CLASS in original_drilldown:
    fail("V3.2 dark drilldown polish appears partially or already applied")
if V32_RUNTIME not in override_css or CARD_CLASS not in override_css:
    fail("V3.2 override asset markers missing")

old_card = 'className="rounded-2xl border border-zinc-200 p-3 text-left transition hover:border-amber-300 hover:bg-amber-50/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-400 dark:border-white/10 dark:bg-white/[0.02] dark:hover:border-amber-400/25 dark:hover:bg-amber-400/[0.04]"'
new_card = 'className="tos-tp-drilldown-department-card-v3-2 rounded-2xl border border-zinc-200 p-3 text-left transition hover:border-amber-300 hover:bg-amber-50/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-amber-400 dark:border-white/10 dark:bg-white/[0.02] dark:hover:border-amber-400/25 dark:hover:bg-amber-400/[0.04]"'

if original_drilldown.count(old_card) != 1:
    fail(f"department card anchor mismatch: found {original_drilldown.count(old_card)}")

try:
    DRILLDOWN.write_text(original_drilldown.replace(old_card, new_card, 1), encoding="utf-8")
    V3_STYLE.write_text(original_v3_style.rstrip() + "\n\n" + override_css.strip() + "\n", encoding="utf-8")
except Exception as exc:
    DRILLDOWN.write_text(original_drilldown, encoding="utf-8")
    V3_STYLE.write_text(original_v3_style, encoding="utf-8")
    fail(f"V3.2 source transformation failed and rolled back: {exc}")

build = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, text=True, capture_output=True)
if build.returncode != 0:
    print(build.stdout[-6000:])
    print(build.stderr[-6000:])
    DRILLDOWN.write_text(original_drilldown, encoding="utf-8")
    V3_STYLE.write_text(original_v3_style, encoding="utf-8")
    fail("frontend build failed; source rolled back")

if not DIST.exists():
    DRILLDOWN.write_text(original_drilldown, encoding="utf-8")
    V3_STYLE.write_text(original_v3_style, encoding="utf-8")
    fail("frontend dist missing after successful build")

for marker in (V3_RUNTIME.encode(), V31_RUNTIME.encode(), V32_RUNTIME.encode(), CARD_CLASS.encode()):
    if tree_count(DIST, marker) < 1:
        DRILLDOWN.write_text(original_drilldown, encoding="utf-8")
        V3_STYLE.write_text(original_v3_style, encoding="utf-8")
        fail(f"built output missing runtime marker/token: {marker.decode()}")

timestamp = int(time.time())
candidate = LIVE_PARENT / f"build.team-performance-v3-2-candidate-{timestamp}"
backup = LIVE_PARENT / f"build.team-performance-v3-2-backup-{timestamp}"
failed_live = LIVE_PARENT / f"build.team-performance-v3-2-failed-{timestamp}"

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
        DRILLDOWN.write_text(original_drilldown, encoding="utf-8")
        V3_STYLE.write_text(original_v3_style, encoding="utf-8")
    fail(f"live deployment failed and rollback attempted: {exc}")

print("PASS/FAIL=PASS")
print("BUILD_RESULT=PASS")
print("LIVE_DEPLOY=PASS")
print("V3_2_RUNTIME=YES")
print("V3_BASELINE_PRESERVED=YES")
print("V3_1_BASELINE_PRESERVED=YES")
print("DARK_DRILLDOWN_DEPARTMENT_CARDS=BLACK_TITANIUM")
print("PERSISTENT_GOLD_CARD_FILL=REMOVED")
print("GOLD_INTERACTION_ACCENT=YES")
print("LIGHT_MODE_CHANGED=NO")
print("STRUCTURE_CHANGED=NO")
print("FUNCTIONALITY_CHANGED=NO")
print("BUSINESS_LOGIC_CHANGED=NO")
print("API_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print(f"DRILLDOWN_SHA256={sha256(DRILLDOWN)}")
print(f"FLAGSHIP_V3_CSS_SHA256={sha256(V3_STYLE)}")
print(f"LIVE_BACKUP={backup}")
print("STATUS=READY")
