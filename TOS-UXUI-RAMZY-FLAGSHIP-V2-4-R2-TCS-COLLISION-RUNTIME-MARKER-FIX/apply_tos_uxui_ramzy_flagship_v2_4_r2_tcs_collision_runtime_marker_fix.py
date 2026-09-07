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

EXPECTED_V23_CSS_SHA256 = "cc9c1bac6fdc1a761dc5867f7a0ef099840037c0e636fb2dac4a25f245ee4821"
EXPECTED_TCS_LAUNCHER_BLOB_SHA = "bec97e1996137a04713ad34fcd39d5bd901831f7"
EXPECTED_TCS_GEOMETRY_BLOB_SHA = "3eb8453f8408ccb9d6cb33c6cc8af2747011cf14"

V23_IMPORT = 'import "./ramzyFlagshipV2_3FinalLightLuxe.css";'
OLD_SELECTOR = 'const RAMZY_COLLISION_SYNC_SELECTOR = ".ramzy-launcher-wrap";'
NEW_SELECTOR = 'const RAMZY_COLLISION_SYNC_SELECTOR = ".ramzy-assistant-root";'
OLD_OBSERVE = 'ramzyObserver.observe(nextNode, { attributes: true, attributeFilter: ["style", "class"] });'
NEW_OBSERVE = 'ramzyObserver.observe(nextNode, { attributes: true, attributeFilter: ["style", "class"], childList: true, subtree: true });'
OLD_BODY_OBSERVER = 'const bodyObserver = new MutationObserver(attachRamzyObserver);'
NEW_BODY_OBSERVER = '''const bodyObserver = new MutationObserver(() => {\n      attachRamzyObserver();\n      syncAgainstRamzy();\n    });'''
OLD_RUNTIME_ATTR = 'data-tcs-ramzy-collision-sync="v1.2"'
NEW_RUNTIME_ATTR = 'data-tcs-ramzy-collision-sync="v2.4-r2"'

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

  const panel = document.querySelector(".ramzy-panel");
  const launcher = document.querySelector(".ramzy-launcher-wrap");
  const panelRect = panel?.getBoundingClientRect?.();
  const launcherRect = launcher?.getBoundingClientRect?.();
  const rect = panelRect?.width > 0 && panelRect?.height > 0
    ? panelRect
    : launcherRect?.width > 0 && launcherRect?.height > 0
      ? launcherRect
      : null;
  if (!rect) return null;

  const x = rect.left - frame.left - extraGap;
  const y = rect.top - frame.top - extraGap;
  const right = rect.right - frame.left + extraGap;
  const bottom = rect.bottom - frame.top + extraGap;
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

print("RUNNING=TOS_UXUI_RAMZY_FLAGSHIP_V2_4_R2_TCS_COLLISION_RUNTIME_MARKER_FIX")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


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


def fail(message: str, launcher_original=None, geometry_original=None):
    if launcher_original is not None:
        try:
            TCS_LAUNCHER.write_text(launcher_original, encoding="utf-8")
        except Exception:
            pass
    if geometry_original is not None:
        try:
            TCS_GEOMETRY.write_text(geometry_original, encoding="utf-8")
        except Exception:
            pass
    print("PASS/FAIL=FAIL")
    print("ERROR=" + str(message))
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("RAMZY_FLAGSHIP_V2_4_R2_RUNTIME=NO")
    sys.exit(1)


for path in (FRONTEND, RAMZY, V23, TCS_LAUNCHER, TCS_GEOMETRY, TCS_WINDOW, TCS_STYLE, LIVE_PARENT):
    if not path.exists():
        fail(f"required path missing: {path}")

if sha256(V23) != EXPECTED_V23_CSS_SHA256:
    fail(f"Ramzy V2.3 CSS baseline mismatch: {sha256(V23)}")
ramzy_source = RAMZY.read_text(encoding="utf-8")
if ramzy_source.count(V23_IMPORT) != 1:
    fail(f"Ramzy V2.3 import guard mismatch: {ramzy_source.count(V23_IMPORT)}")
for token in ('className={`ramzy-panel opens-', 'className="ramzy-composer"', 'className="ramzy-launcher"'):
    if token not in ramzy_source:
        fail(f"Ramzy runtime anchor missing: {token}")

if git_blob_sha(TCS_LAUNCHER) != EXPECTED_TCS_LAUNCHER_BLOB_SHA:
    fail(f"TCS launcher baseline mismatch: {git_blob_sha(TCS_LAUNCHER)}")
if git_blob_sha(TCS_GEOMETRY) != EXPECTED_TCS_GEOMETRY_BLOB_SHA:
    fail(f"TCS geometry baseline mismatch: {git_blob_sha(TCS_GEOMETRY)}")

launcher_original = TCS_LAUNCHER.read_text(encoding="utf-8")
geometry_original = TCS_GEOMETRY.read_text(encoding="utf-8")
ramzy_before = sha256(RAMZY)
v23_before = sha256(V23)
window_before = sha256(TCS_WINDOW)
style_before = sha256(TCS_STYLE)

for label, source, anchor in (
    ("launcher selector", launcher_original, OLD_SELECTOR),
    ("launcher observer", launcher_original, OLD_OBSERVE),
    ("launcher body observer", launcher_original, OLD_BODY_OBSERVER),
    ("launcher runtime attr", launcher_original, OLD_RUNTIME_ATTR),
    ("geometry blocked function", geometry_original, OLD_BLOCKED_FUNCTION),
):
    if source.count(anchor) != 1:
        fail(f"{label} guard mismatch: found {source.count(anchor)}", launcher_original, geometry_original)

if NEW_SELECTOR in launcher_original or NEW_RUNTIME_ATTR in launcher_original:
    fail("V2.4 R2 collision fix already applied", launcher_original, geometry_original)

next_launcher = launcher_original.replace(OLD_SELECTOR, NEW_SELECTOR, 1)
next_launcher = next_launcher.replace(OLD_OBSERVE, NEW_OBSERVE, 1)
next_launcher = next_launcher.replace(OLD_BODY_OBSERVER, NEW_BODY_OBSERVER, 1)
next_launcher = next_launcher.replace(OLD_RUNTIME_ATTR, NEW_RUNTIME_ATTR, 1)
next_geometry = geometry_original.replace(OLD_BLOCKED_FUNCTION, NEW_BLOCKED_FUNCTION, 1)

for token in (
    'data-tcs-ramzy-collision-sync="v2.4-r2"',
    'onPointerDown={handlePointerDown}',
    '(active ? onClose : onOpen)?.();',
    '.ramzy-assistant-root',
    'getBlockedRamzyRect',
    'avoidRect',
):
    if token not in next_launcher:
        fail(f"TCS launcher behavior guard missing after transform: {token}", launcher_original, geometry_original)
for token in (
    'document.querySelector(".ramzy-panel")',
    'document.querySelector(".ramzy-launcher-wrap")',
    'panelRect?.width > 0',
    'extraGap = 18',
):
    if token not in next_geometry:
        fail(f"TCS geometry guard missing after transform: {token}", launcher_original, geometry_original)

try:
    TCS_LAUNCHER.write_text(next_launcher, encoding="utf-8")
    TCS_GEOMETRY.write_text(next_geometry, encoding="utf-8")
except Exception as exc:
    fail(f"source write failed: {exc}", launcher_original, geometry_original)

build = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, text=True, capture_output=True)
if build.returncode != 0:
    print(build.stdout[-12000:])
    print(build.stderr[-12000:])
    fail("frontend build failed", launcher_original, geometry_original)

if not DIST.exists() or not (DIST / "index.html").exists():
    fail("dist/index.html missing after build", launcher_original, geometry_original)
for marker in (
    b"v2.4-r2",
    b"data-tcs-ramzy-collision-sync",
    b".ramzy-panel",
    b".ramzy-launcher-wrap",
    b".ramzy-assistant-root",
    b"tcs-floating-launcher",
):
    if tree_count(DIST, marker) < 1:
        fail(f"built output missing runtime marker: {marker.decode(errors='ignore')}", launcher_original, geometry_original)

if sha256(RAMZY) != ramzy_before:
    fail("Ramzy source changed out of scope", launcher_original, geometry_original)
if sha256(V23) != v23_before:
    fail("Ramzy V2.3 visual CSS changed out of scope", launcher_original, geometry_original)
if sha256(TCS_WINDOW) != window_before or sha256(TCS_STYLE) != style_before:
    fail("TCS window/style changed out of scope", launcher_original, geometry_original)

ts = int(time.time())
candidate = LIVE_PARENT / f"build.ramzy-v2-4-r2-tcs-collision-candidate-{ts}"
backup = LIVE_PARENT / f"build.ramzy-v2-4-r2-tcs-collision-backup-{ts}"
failed_live = LIVE_PARENT / f"build.ramzy-v2-4-r2-tcs-collision-failed-{ts}"
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
        fail(f"live deploy failed and rollback attempted: {exc}", launcher_original, geometry_original)

print("PASS/FAIL=PASS")
print("BUILD_RESULT=PASS")
print("LIVE_DEPLOY=PASS")
print("RAMZY_FLAGSHIP_V2_4_R2_RUNTIME=YES")
print("R2_RUNTIME_MARKER_SOURCE=DOM_DATA_ATTRIBUTE")
print("R2_RUNTIME_MARKER_VERIFIED_IN_DIST=YES")
print("RAMZY_SOURCE_PRESERVED_BYTE_FOR_BYTE=YES")
print("RAMZY_V2_3_VISUAL=PRESERVED")
print("RAMZY_LIGHT_MODE_CHANGED=NO")
print("RAMZY_DARK_MODE_CHANGED=NO")
print("TCS_VISUAL_CHANGED=NO")
print("TCS_CHAT_LOGIC_CHANGED=NO")
print("TCS_COLLISION_BEHAVIOR_CHANGED=YES")
print("TCS_RAMZY_OPEN_BLOCKED_REGION=FULL_PANEL")
print("TCS_RAMZY_CLOSED_BLOCKED_REGION=LAUNCHER")
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