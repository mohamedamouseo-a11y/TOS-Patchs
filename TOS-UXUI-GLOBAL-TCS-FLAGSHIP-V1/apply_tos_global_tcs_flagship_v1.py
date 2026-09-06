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
STYLE_TARGET = ROOT / "frontend/src/components/tcsFlagshipV1.css"
STYLE_ASSET = PATCH_DIR / "tcsFlagshipV1.css"
FRONTEND = ROOT / "frontend"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_LAUNCHER_GIT_BLOB_SHA1 = "c7b21730c17ee548253d008624d8a87648f68ec6"
EXPECTED_WINDOW_GIT_BLOB_SHA1 = "c645512af4f8838d6980c6e500806efc326f3d2c"
V1_RUNTIME = "--tos-tcs-flagship-v1-runtime"
STYLE_IMPORT = 'import "./tcsFlagshipV1.css";'

print("RUNNING=TOS_GLOBAL_TCS_FLAGSHIP_V1")


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
    print("TCS_V1_RUNTIME=NO")
    sys.exit(1)


if ROOT.resolve() == Path("/"):
    fail("unsafe ROOT")

for path in (LAUNCHER, WINDOW, STYLE_ASSET, FRONTEND, LIVE_PARENT):
    if not path.exists():
        fail(f"required path missing: {path}")

if STYLE_TARGET.exists():
    fail("tcsFlagshipV1.css already exists; refusing duplicate apply")

actual_launcher_blob = git_blob_sha1(LAUNCHER)
actual_window_blob = git_blob_sha1(WINDOW)
if actual_launcher_blob != EXPECTED_LAUNCHER_GIT_BLOB_SHA1:
    fail(f"TcsFloatingLauncher.jsx source guard mismatch: {actual_launcher_blob}")
if actual_window_blob != EXPECTED_WINDOW_GIT_BLOB_SHA1:
    fail(f"TcsDesktopWindow.jsx source guard mismatch: {actual_window_blob}")

original_launcher = LAUNCHER.read_text(encoding="utf-8")
original_window = WINDOW.read_text(encoding="utf-8")
style_css = STYLE_ASSET.read_text(encoding="utf-8")

if V1_RUNTIME not in style_css:
    fail("TCS V1 runtime marker missing from style asset")
if STYLE_IMPORT in original_launcher or STYLE_IMPORT in original_window:
    fail("TCS Flagship V1 appears already or partially applied")

launcher_anchor = 'import { usePreferences } from "../contexts/PreferencesContext";'
window_anchor = 'import { usePreferences } from "../contexts/PreferencesContext";'
if original_launcher.count(launcher_anchor) != 1:
    fail(f"launcher import anchor mismatch: found {original_launcher.count(launcher_anchor)}")
if original_window.count(window_anchor) != 1:
    fail(f"window import anchor mismatch: found {original_window.count(window_anchor)}")

next_launcher = original_launcher.replace(launcher_anchor, launcher_anchor + "\n" + STYLE_IMPORT, 1)
next_window = original_window.replace(window_anchor, window_anchor + "\n" + STYLE_IMPORT, 1)

# Guard behavior-critical anchors before writing. The patch is visual only.
behavior_guards = {
    "launcher_drag": "onPointerDown={handlePointerDown}",
    "launcher_open_close": "(active ? onClose : onOpen)?.();",
    "launcher_unread": "tcs-floating-launcher-badge",
    "window_drag": "onPointerDown={handleDragStart}",
    "window_resize": "onPointerDown={handleResizeStart}",
    "window_minimize": "onClick={toggleMinimize}",
    "window_maximize": "onClick={toggleMaximize}",
    "window_close": "onClick={onClose}",
}
for label, token in behavior_guards.items():
    source = original_launcher if label.startswith("launcher_") else original_window
    if token not in source:
        fail(f"behavior guard missing: {label}")

try:
    LAUNCHER.write_text(next_launcher, encoding="utf-8")
    WINDOW.write_text(next_window, encoding="utf-8")
    STYLE_TARGET.write_text(style_css, encoding="utf-8")
except Exception as exc:
    LAUNCHER.write_text(original_launcher, encoding="utf-8")
    WINDOW.write_text(original_window, encoding="utf-8")
    if STYLE_TARGET.exists():
        STYLE_TARGET.unlink()
    fail(f"TCS V1 source transformation failed and rolled back: {exc}")

build = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, text=True, capture_output=True)
if build.returncode != 0:
    print(build.stdout[-6000:])
    print(build.stderr[-6000:])
    LAUNCHER.write_text(original_launcher, encoding="utf-8")
    WINDOW.write_text(original_window, encoding="utf-8")
    if STYLE_TARGET.exists():
        STYLE_TARGET.unlink()
    fail("frontend build failed; exact TCS sources rolled back")

if not DIST.exists():
    LAUNCHER.write_text(original_launcher, encoding="utf-8")
    WINDOW.write_text(original_window, encoding="utf-8")
    if STYLE_TARGET.exists():
        STYLE_TARGET.unlink()
    fail("frontend dist missing after successful build")

for marker in (
    V1_RUNTIME.encode(),
    b"tcs-floating-launcher",
    b"tcs-desktop-window-v8",
    b"tcs-desktop-window-titlebar",
    b"tcs-desktop-window-resize-handle",
):
    if tree_count(DIST, marker) < 1:
        LAUNCHER.write_text(original_launcher, encoding="utf-8")
        WINDOW.write_text(original_window, encoding="utf-8")
        if STYLE_TARGET.exists():
            STYLE_TARGET.unlink()
        fail(f"built output missing runtime marker/token: {marker.decode()}")

timestamp = int(time.time())
candidate = LIVE_PARENT / f"build.tcs-flagship-v1-candidate-{timestamp}"
backup = LIVE_PARENT / f"build.tcs-flagship-v1-backup-{timestamp}"
failed_live = LIVE_PARENT / f"build.tcs-flagship-v1-failed-{timestamp}"

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
        LAUNCHER.write_text(original_launcher, encoding="utf-8")
        WINDOW.write_text(original_window, encoding="utf-8")
        if STYLE_TARGET.exists():
            STYLE_TARGET.unlink()
    fail(f"live deployment failed and rollback attempted: {exc}")

print("PASS/FAIL=PASS")
print("BUILD_RESULT=PASS")
print("LIVE_DEPLOY=PASS")
print("TCS_V1_RUNTIME=YES")
print("TCS_LAUNCHER=FLAGSHIP_REFINED")
print("TCS_DESKTOP_SHELL=FLAGSHIP_REFINED")
print("TCS_TITLEBAR=PREMIUM")
print("TCS_WINDOW_CONTROLS=PREMIUM")
print("TCS_LIGHT_MODE=IVORY_CHAMPAGNE")
print("TCS_DARK_MODE=OBSIDIAN_TITANIUM")
print("TCS_UNREAD_BADGE_PRESERVED=YES")
print("TCS_DRAG_PRESERVED=YES")
print("TCS_RESIZE_PRESERVED=YES")
print("TCS_MINIMIZE_PRESERVED=YES")
print("TCS_MAXIMIZE_PRESERVED=YES")
print("TCS_CLOSE_PRESERVED=YES")
print("TCS_GEOMETRY_PERSISTENCE_CHANGED=NO")
print("TCS_CHAT_LOGIC_CHANGED=NO")
print("RAMZY_CHANGED=NO")
print("API_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print(f"TCS_LAUNCHER_SHA256={sha256(LAUNCHER)}")
print(f"TCS_WINDOW_SHA256={sha256(WINDOW)}")
print(f"TCS_STYLE_SHA256={sha256(STYLE_TARGET)}")
print(f"LIVE_BACKUP={backup}")
print("STATUS=READY")
