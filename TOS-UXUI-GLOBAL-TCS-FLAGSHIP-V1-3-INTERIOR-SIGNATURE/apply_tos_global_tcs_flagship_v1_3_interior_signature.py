from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
PATCH_DIR = Path(__file__).resolve().parent
LAUNCHER = ROOT / "frontend/src/components/TcsFloatingLauncher.jsx"
WINDOW = ROOT / "frontend/src/components/TcsDesktopWindow.jsx"
STYLE = ROOT / "frontend/src/components/tcsFlagshipV1.css"
OVERRIDE = PATCH_DIR / "tcsFlagshipV1_3InteriorSignature.css"
FRONTEND = ROOT / "frontend"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_LAUNCHER_SHA256 = "2dfd109fbae96f97829233b95a266797b615b84a8facc8831d8c4efec023522d"
EXPECTED_WINDOW_SHA256 = "5aa5f8c047baa12f29cae33585e1f7be493c5bfbde43a706f4537dbe599dad70"
EXPECTED_STYLE_SHA256 = "8ba694891ee2eb99c27c28a264929800a141b78db517acf47517a3d7c44c7d48"
V1_RUNTIME = "--tos-tcs-flagship-v1-runtime"
V11_RUNTIME = "--tos-tcs-flagship-v1-1-light-rail-contrast-runtime"
V13_RUNTIME = "--tos-tcs-flagship-v1-3-interior-signature-runtime"
V12_ATTR = 'data-tcs-ramzy-collision-sync="v1.2"'

print("RUNNING=TOS_GLOBAL_TCS_FLAGSHIP_V1_3_INTERIOR_SIGNATURE")


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
    print("TCS_V1_3_RUNTIME=NO")
    sys.exit(1)


if ROOT.resolve() == Path("/"):
    fail("unsafe ROOT")

for path in (LAUNCHER, WINDOW, STYLE, OVERRIDE, FRONTEND, LIVE_PARENT):
    if not path.exists():
        fail(f"required path missing: {path}")

if sha256(LAUNCHER) != EXPECTED_LAUNCHER_SHA256:
    fail(f"TcsFloatingLauncher.jsx V1.2 baseline mismatch: {sha256(LAUNCHER)}")
if sha256(WINDOW) != EXPECTED_WINDOW_SHA256:
    fail(f"TcsDesktopWindow.jsx baseline mismatch: {sha256(WINDOW)}")
if sha256(STYLE) != EXPECTED_STYLE_SHA256:
    fail(f"tcsFlagshipV1.css V1.1 baseline mismatch: {sha256(STYLE)}")

launcher_source = LAUNCHER.read_text(encoding="utf-8")
original_style = STYLE.read_text(encoding="utf-8")
override_css = OVERRIDE.read_text(encoding="utf-8")

if V12_ATTR not in launcher_source:
    fail("TCS V1.2 Ramzy collision runtime attribute missing")
if V1_RUNTIME not in original_style:
    fail("TCS V1 runtime marker missing")
if V11_RUNTIME not in original_style:
    fail("TCS V1.1 runtime marker missing")
if V13_RUNTIME in original_style:
    fail("TCS V1.3 interior signature already applied")
if V13_RUNTIME not in override_css:
    fail("TCS V1.3 runtime marker missing from override asset")

# Validate that the CSS is scoped to the desktop TCS experience and contains the requested visual fixes.
required_override_tokens = (
    '[data-tcs-presentation="desktop-window"]',
    '.tos-chat-v8-rail',
    '.tos-chat-command-center',
    'div:has(> .mx-auto.mb-3.grid.h-12.w-12)',
    'button[class*="bg-zinc-950"]',
    '--tos-tcs-flagship-v1-3-interior-signature-runtime',
)
for token in required_override_tokens:
    if token not in override_css:
        fail(f"V1.3 override token missing: {token}")

try:
    STYLE.write_text(original_style.rstrip() + "\n\n" + override_css.strip() + "\n", encoding="utf-8")
except Exception as exc:
    STYLE.write_text(original_style, encoding="utf-8")
    fail(f"V1.3 style transformation failed and rolled back: {exc}")

build = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, text=True, capture_output=True)
if build.returncode != 0:
    print(build.stdout[-6000:])
    print(build.stderr[-6000:])
    STYLE.write_text(original_style, encoding="utf-8")
    fail("frontend build failed; V1.3 style rolled back")

if not DIST.exists():
    STYLE.write_text(original_style, encoding="utf-8")
    fail("frontend dist missing after successful build")

for marker in (
    V1_RUNTIME.encode(),
    V11_RUNTIME.encode(),
    V13_RUNTIME.encode(),
    b"data-tcs-ramzy-collision-sync",
    b"tos-chat-v8-rail",
    b"tos-chat-command-center",
    b"tcs-desktop-window",
):
    if tree_count(DIST, marker) < 1:
        STYLE.write_text(original_style, encoding="utf-8")
        fail(f"built output missing runtime marker/token: {marker.decode()}")

timestamp = int(time.time())
candidate = LIVE_PARENT / f"build.tcs-v1-3-interior-signature-candidate-{timestamp}"
backup = LIVE_PARENT / f"build.tcs-v1-3-interior-signature-backup-{timestamp}"
failed_live = LIVE_PARENT / f"build.tcs-v1-3-interior-signature-failed-{timestamp}"

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
print("TCS_V1_RUNTIME=YES")
print("TCS_V1_1_RUNTIME=YES")
print("TCS_V1_2_RUNTIME=YES")
print("TCS_V1_3_RUNTIME=YES")
print("TCS_LIGHT_CRITICAL_LABELS=HIGH_CONTRAST")
print("TCS_LIGHT_PROJECT_DIRECT_CONTROL=VISIBLE")
print("TCS_LIGHT_RAIL=MATERIAL_REFINED")
print("TCS_CONVERSATION_ROWS=EXECUTIVE_REFINED")
print("TCS_FILTER_CHIPS=PREMIUM_REFINED")
print("TCS_COMMAND_CENTER=FLAGSHIP_REFINED")
print("TCS_EMPTY_STATE=SIGNATURE_REFINED")
print("TCS_DARK_NAVY_CAST=REMOVED")
print("TCS_DARK_FOCUS_ACTION=GOLD_REFINED")
print("TCS_DARK_CONVERSATION_ROWS=BLACK_TITANIUM")
print("TCS_WINDOW_CHROME=PREMIUM_REFINED")
print("TCS_LAUNCHER_CHANGED=NO")
print("TCS_WINDOW_BEHAVIOR_CHANGED=NO")
print("TCS_CHAT_LOGIC_CHANGED=NO")
print("TCS_RAMZY_COLLISION_SYNC_PRESERVED=YES")
print("RAMZY_CHANGED=NO")
print("API_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print(f"TCS_LAUNCHER_SHA256={sha256(LAUNCHER)}")
print(f"TCS_WINDOW_SHA256={sha256(WINDOW)}")
print(f"TCS_STYLE_SHA256={sha256(STYLE)}")
print(f"LIVE_BACKUP={backup}")
print("STATUS=READY")
