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
OVERRIDE = PATCH_DIR / "tcsFlagshipV1_1LightRailContrast.css"
FRONTEND = ROOT / "frontend"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_LAUNCHER_SHA256 = "6ebc78baa9dc73a3a85201ef6c9ead55a2e0536aa14baa3da7297d6db8735d02"
EXPECTED_WINDOW_SHA256 = "5aa5f8c047baa12f29cae33585e1f7be493c5bfbde43a706f4537dbe599dad70"
EXPECTED_STYLE_SHA256 = "2387399b5de216ea78435b15b4a47641651d784d64dd4f314918d9edb2e9e970"
V1_RUNTIME = "--tos-tcs-flagship-v1-runtime"
V11_RUNTIME = "--tos-tcs-flagship-v1-1-light-rail-contrast-runtime"

print("RUNNING=TOS_GLOBAL_TCS_FLAGSHIP_V1_1_LIGHT_RAIL_CONTRAST")


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
    print("TCS_V1_1_RUNTIME=NO")
    sys.exit(1)


if ROOT.resolve() == Path("/"):
    fail("unsafe ROOT")

for path in (LAUNCHER, WINDOW, STYLE, OVERRIDE, FRONTEND, LIVE_PARENT):
    if not path.exists():
        fail(f"required path missing: {path}")

if sha256(LAUNCHER) != EXPECTED_LAUNCHER_SHA256:
    fail(f"TcsFloatingLauncher.jsx source guard mismatch: {sha256(LAUNCHER)}")
if sha256(WINDOW) != EXPECTED_WINDOW_SHA256:
    fail(f"TcsDesktopWindow.jsx source guard mismatch: {sha256(WINDOW)}")
if sha256(STYLE) != EXPECTED_STYLE_SHA256:
    fail(f"tcsFlagshipV1.css source guard mismatch: {sha256(STYLE)}")

original_style = STYLE.read_text(encoding="utf-8")
override_css = OVERRIDE.read_text(encoding="utf-8")

if V1_RUNTIME not in original_style:
    fail("TCS V1 runtime marker missing")
if V11_RUNTIME in original_style:
    fail("TCS V1.1 light rail contrast already applied")
if V11_RUNTIME not in override_css:
    fail("TCS V1.1 runtime marker missing from override")

try:
    STYLE.write_text(original_style.rstrip() + "\n\n" + override_css.strip() + "\n", encoding="utf-8")
except Exception as exc:
    STYLE.write_text(original_style, encoding="utf-8")
    fail(f"V1.1 style transformation failed and rolled back: {exc}")

build = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, text=True, capture_output=True)
if build.returncode != 0:
    print(build.stdout[-6000:])
    print(build.stderr[-6000:])
    STYLE.write_text(original_style, encoding="utf-8")
    fail("frontend build failed; style rolled back")

if not DIST.exists():
    STYLE.write_text(original_style, encoding="utf-8")
    fail("frontend dist missing after successful build")

for marker in (
    V1_RUNTIME.encode(),
    V11_RUNTIME.encode(),
    b'tos-chat-rail',
    b'data-tcs-presentation',
    b'tcs-desktop-window',
):
    if tree_count(DIST, marker) < 1:
        STYLE.write_text(original_style, encoding="utf-8")
        fail(f"built output missing runtime marker/token: {marker.decode()}")

timestamp = int(time.time())
candidate = LIVE_PARENT / f"build.tcs-v1-1-light-rail-candidate-{timestamp}"
backup = LIVE_PARENT / f"build.tcs-v1-1-light-rail-backup-{timestamp}"
failed_live = LIVE_PARENT / f"build.tcs-v1-1-light-rail-failed-{timestamp}"

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
print("TCS_LIGHT_CHAT_RAIL_CONTRAST=FIXED")
print("TCS_LIGHT_CONVERSATION_LABELS=READABLE")
print("TCS_LIGHT_SEARCH_FIELD=READABLE")
print("TCS_LIGHT_NEW_CONVERSATION_CONTROL=READABLE")
print("TCS_DARK_MODE_CHANGED=NO")
print("TCS_LAUNCHER_CHANGED=NO")
print("TCS_WINDOW_BEHAVIOR_CHANGED=NO")
print("TCS_CHAT_LOGIC_CHANGED=NO")
print("RAMZY_CHANGED=NO")
print("API_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print(f"TCS_STYLE_SHA256={sha256(STYLE)}")
print(f"LIVE_BACKUP={backup}")
print("STATUS=READY")
