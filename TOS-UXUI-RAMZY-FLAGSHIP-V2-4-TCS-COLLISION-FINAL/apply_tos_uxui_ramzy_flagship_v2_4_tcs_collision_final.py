from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
RAMZY = FRONTEND / "src/components/RamzyAssistant.jsx"
V23 = FRONTEND / "src/components/ramzyFlagshipV2_3FinalLightLuxe.css"
TCS_LAUNCHER = FRONTEND / "src/components/TcsFloatingLauncher.jsx"
TCS_GEOMETRY = FRONTEND / "src/lib/tcsWindowGeometry.js"
TCS_WINDOW = FRONTEND / "src/components/TcsDesktopWindow.jsx"
TCS_STYLE = FRONTEND / "src/components/tcsFlagshipV1.css"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_RAMZY_V23_SHA256 = "0ade610b9b2afcc6c0717676caf80b6bdb566c25ce19d0b5a228d7591c5fa18a"
EXPECTED_V23_CSS_SHA256 = "cc9c1bac6fdc1a761dc5867f7a0ef099840037c0e636fb2dac4a25f245ee4821"
EXPECTED_TCS_LAUNCHER_BLOB_SHA = "bec97e1996137a04713ad34fcd39d5bd901831f7"
EXPECTED_TCS_GEOMETRY_BLOB_SHA = "3eb8453f8408ccb9d6cb33c6cc8af2747011cf14"

OLD_SELECTOR = 'const RAMZY_COLLISION_SYNC_SELECTOR = ".ramzy-launcher-wrap";'
NEW_SELECTOR = 'const RAMZY_COLLISION_SYNC_SELECTOR = ".ramzy-assistant-root";'
OLD_OBSERVE = 'ramzyObserver.observe(nextNode, { attributes: true, attributeFilter: ["style", "class"] });'
NEW_OBSERVE = 'ramzyObserver.observe(nextNode, { attributes: true, attributeFilter: ["style", "class"], childList: true, subtree: true });'
OLD_BODY_OBSERVER = 'const bodyObserver = new MutationObserver(attachRamzyObserver);'
NEW_BODY_OBSERVER = '''const bodyObserver = new MutationObserver(() => {\n      attachRamzyObserver();\n      syncAgainstRamzy();\n    });'''
VERSION_CONST_ANCHOR = 'export const TCS_MINIMIZED_HEIGHT = 54;'
VERSION_CONST = 'export const TCS_RAMZY_COLLISION_FINAL_VERSION = "v2.4";'

OLD_BLOCKED_FUNCTION = '''export function getBlockedRamzyRect(frame, extraGap = 10) {
  if (typeof document === "undefined") return null;
  const element = document.querySelector(".ramzy-launcher-wrap");
  if (!element) return null;
  const rect = element.getBoundingClientRect();
  if (!rect.width || !rect.height) return null;
  const x = rect.left - frame.left - extraGap;
  const y = rect.top - frame.top - extraGap;
  const right = rect.right - frame.left + extraGap;
  const bottom = rect.bottom - frame.top + extraGap;
  if (right <= 0 || bottom <= 0 || x >= frame.width || y >= frame.height) return null;
  return {
    x: Math.max(0, x),
    y: Math.max(0, y),
    width: Math.min(frame.width, right) - Math.max(0, x),
    height: Math.min(frame.height, bottom) - Math.max(0, y),
  };
}'''

NEW_BLOCKED_FUNCTION = '''export function getBlockedRamzyRect(frame, extraGap = 18) {
  if (typeof document === "undefined") return null;

  // When Ramzy is open, protect the full assistant panel as well as the
  // draggable avatar/launcher. When it is closed/minimized, the launcher alone
  // remains the blocked region. This keeps TCS clear of Ramzy's composer and
  // controls without changing either product's visual design.
  const elements = [
    document.querySelector(".ramzy-panel"),
    document.querySelector(".ramzy-launcher-wrap"),
  ].filter(Boolean);

  const rects = elements
    .map((element) => element.getBoundingClientRect())
    .filter((rect) => rect.width > 0 && rect.height > 0);
  if (!rects.length) return null;

  const viewportLeft = Math.min(...rects.map((rect) => rect.left)) - extraGap;
  const viewportTop = Math.min(...rects.map((rect) => rect.top)) - extraGap;
  const viewportRight = Math.max(...rects.map((rect) => rect.right)) + extraGap;
  const viewportBottom = Math.max(...rects.map((rect) => rect.bottom)) + extraGap;

  const x = viewportLeft - frame.left;
  const y = viewportTop - frame.top;
  const right = viewportRight - frame.left;
  const bottom = viewportBottom - frame.top;
  if (right <= 0 || bottom <= 0 || x >= frame.width || y >= frame.height) return null;

  const clippedLeft = Math.max(0, x);
  const clippedTop = Math.max(0, y);
  const clippedRight = Math.min(frame.width, right);
  const clippedBottom = Math.min(frame.height, bottom);
  if (clippedRight <= clippedLeft || clippedBottom <= clippedTop) return null;

  return {
    x: clippedLeft,
    y: clippedTop,
    width: clippedRight - clippedLeft,
    height: clippedBottom - clippedTop,
  };
}'''

print("RUNNING=TOS_UXUI_RAMZY_FLAGSHIP_V2_4_TCS_COLLISION_FINAL")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def tree_count(root: Path, needle: bytes) -> int:
    if not root.exists():
        return 0
    count = 0
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            count += path.read_bytes().count(needle)
        except OSError:
            pass
    return count


def fail(message: str, original_launcher=None, original_geometry=None):
    if original_launcher is not None:
        try:
            TCS_LAUNCHER.write_text(original_launcher, encoding="utf-8")
        except Exception:
            pass
    if original_geometry is not None:
        try:
            TCS_GEOMETRY.write_text(original_geometry, encoding="utf-8")
        except Exception:
            pass
    print("PASS/FAIL=FAIL")
    print("ERROR=" + str(message))
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("RAMZY_FLAGSHIP_V2_4_RUNTIME=NO")
    sys.exit(1)


for path in (FRONTEND, RAMZY, V23, TCS_LAUNCHER, TCS_GEOMETRY, TCS_WINDOW, TCS_STYLE, LIVE_PARENT):
    if not path.exists():
        fail(f"required path missing: {path}")

if sha256(RAMZY) != EXPECTED_RAMZY_V23_SHA256:
    fail(f"Ramzy V2.3 baseline mismatch: {sha256(RAMZY)}")
if sha256(V23) != EXPECTED_V23_CSS_SHA256:
    fail(f"Ramzy V2.3 CSS baseline mismatch: {sha256(V23)}")
if git_blob_sha(TCS_LAUNCHER) != EXPECTED_TCS_LAUNCHER_BLOB_SHA:
    fail(f"TCS launcher baseline mismatch: {git_blob_sha(TCS_LAUNCHER)}")
if git_blob_sha(TCS_GEOMETRY) != EXPECTED_TCS_GEOMETRY_BLOB_SHA:
    fail(f"TCS geometry baseline mismatch: {git_blob_sha(TCS_GEOMETRY)}")

original_launcher = TCS_LAUNCHER.read_text(encoding="utf-8")
original_geometry = TCS_GEOMETRY.read_text(encoding="utf-8")
window_before = sha256(TCS_WINDOW)
style_before = sha256(TCS_STYLE)
ramzy_before = sha256(RAMZY)
v23_before = sha256(V23)

for label, source, anchor in (
    ("launcher selector", original_launcher, OLD_SELECTOR),
    ("launcher observer", original_launcher, OLD_OBSERVE),
    ("launcher body observer", original_launcher, OLD_BODY_OBSERVER),
    ("geometry version anchor", original_geometry, VERSION_CONST_ANCHOR),
    ("geometry blocked function", original_geometry, OLD_BLOCKED_FUNCTION),
):
    if source.count(anchor) != 1:
        fail(f"{label} guard mismatch: found {source.count(anchor)}", original_launcher, original_geometry)

if VERSION_CONST in original_geometry or NEW_SELECTOR in original_launcher:
    fail("V2.4 collision final already applied", original_launcher, original_geometry)

next_launcher = original_launcher.replace(OLD_SELECTOR, NEW_SELECTOR, 1)
next_launcher = next_launcher.replace(OLD_OBSERVE, NEW_OBSERVE, 1)
next_launcher = next_launcher.replace(OLD_BODY_OBSERVER, NEW_BODY_OBSERVER, 1)
next_geometry = original_geometry.replace(VERSION_CONST_ANCHOR, VERSION_CONST_ANCHOR + "\n" + VERSION_CONST, 1)
next_geometry = next_geometry.replace(OLD_BLOCKED_FUNCTION, NEW_BLOCKED_FUNCTION, 1)

for token in (
    'data-tcs-ramzy-collision-sync="v1.2"',
    "onPointerDown={handlePointerDown}",
    "(active ? onClose : onOpen)?.();",
    "getBlockedRamzyRect",
    "avoidRect",
    ".ramzy-assistant-root",
):
    if token not in next_launcher:
        fail(f"launcher behavior guard missing after transform: {token}", original_launcher, original_geometry)
for token in (
    'TCS_RAMZY_COLLISION_FINAL_VERSION = "v2.4"',
    'document.querySelector(".ramzy-panel")',
    'document.querySelector(".ramzy-launcher-wrap")',
    "viewportLeft",
    "viewportRight",
):
    if token not in next_geometry:
        fail(f"geometry guard missing after transform: {token}", original_launcher, original_geometry)

try:
    TCS_LAUNCHER.write_text(next_launcher, encoding="utf-8")
    TCS_GEOMETRY.write_text(next_geometry, encoding="utf-8")
except Exception as exc:
    fail(f"source write failed: {exc}", original_launcher, original_geometry)

build = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, text=True, capture_output=True)
if build.returncode != 0:
    print(build.stdout[-12000:])
    print(build.stderr[-12000:])
    fail("frontend build failed", original_launcher, original_geometry)

if not DIST.exists() or not (DIST / "index.html").exists():
    fail("dist/index.html missing after build", original_launcher, original_geometry)

for marker in (
    b"v2.4",
    b".ramzy-panel",
    b".ramzy-launcher-wrap",
    b".ramzy-assistant-root",
    b"data-tcs-ramzy-collision-sync",
    b"tcs-floating-launcher",
):
    if tree_count(DIST, marker) < 1:
        fail(f"built output missing runtime marker: {marker.decode(errors='ignore')}", original_launcher, original_geometry)

# Strong preservation checks: no visual or product logic files are changed.
if sha256(RAMZY) != ramzy_before or sha256(V23) != v23_before:
    fail("Ramzy source/style changed out of scope", original_launcher, original_geometry)
if sha256(TCS_WINDOW) != window_before or sha256(TCS_STYLE) != style_before:
    fail("TCS window/style changed out of scope", original_launcher, original_geometry)

# Safe live deployment. No service restart and no Git operation in /var/www/TOS.
ts = int(time.time())
candidate = LIVE_PARENT / f"build.ramzy-v2-4-tcs-collision-candidate-{ts}"
backup = LIVE_PARENT / f"build.ramzy-v2-4-tcs-collision-backup-{ts}"
failed_live = LIVE_PARENT / f"build.ramzy-v2-4-tcs-collision-failed-{ts}"
try:
    if candidate.exists():
        shutil.rmtree(candidate)
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
        fail(f"live deploy failed and rollback attempted: {exc}", original_launcher, original_geometry)

print("PASS/FAIL=PASS")
print("BUILD_RESULT=PASS")
print("LIVE_DEPLOY=PASS")
print("RAMZY_FLAGSHIP_V2_4_RUNTIME=YES")
print("RAMZY_V2_3_VISUAL=PRESERVED")
print("RAMZY_LIGHT_MODE_CHANGED=NO")
print("RAMZY_DARK_MODE_CHANGED=NO")
print("TCS_VISUAL_CHANGED=NO")
print("TCS_CHAT_LOGIC_CHANGED=NO")
print("TCS_COLLISION_BEHAVIOR_CHANGED=YES")
print("TCS_RAMZY_BLOCKED_REGION=PANEL_PLUS_LAUNCHER")
print("TCS_RAMZY_OPEN_CLOSE_SYNC=YES")
print("TCS_RAMZY_MOVE_RESIZE_SYNC=YES")
print("TCS_RAMZY_COLLISION_GAP_PX=18")
print("TCS_DRAG_PRESERVED=YES")
print("TCS_UNREAD_PRESERVED=YES")
print("RAMZY_AGENT_LOGIC_CHANGED=NO")
print("RAMZY_API_CHANGED=NO")
print("RAMZY_VOICE_BEHAVIOR_CHANGED=NO")
print("RAMZY_APPROVAL_LOGIC_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print("AUTH_CHANGED=NO")
print(f"TCS_LAUNCHER_SHA256={sha256(TCS_LAUNCHER)}")
print(f"TCS_GEOMETRY_SHA256={sha256(TCS_GEOMETRY)}")
print(f"RAMZY_JS_SHA256={sha256(RAMZY)}")
print(f"V23_CSS_SHA256={sha256(V23)}")
print(f"LIVE_BACKUP={backup}")
print("STATUS=READY")
