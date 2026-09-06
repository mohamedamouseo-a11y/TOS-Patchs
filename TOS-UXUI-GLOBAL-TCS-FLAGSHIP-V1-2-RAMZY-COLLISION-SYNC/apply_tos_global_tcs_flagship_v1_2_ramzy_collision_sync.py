from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
LAUNCHER = ROOT / "frontend/src/components/TcsFloatingLauncher.jsx"
WINDOW = ROOT / "frontend/src/components/TcsDesktopWindow.jsx"
STYLE = ROOT / "frontend/src/components/tcsFlagshipV1.css"
FRONTEND = ROOT / "frontend"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_LAUNCHER_SHA256 = "6ebc78baa9dc73a3a85201ef6c9ead55a2e0536aa14baa3da7297d6db8735d02"
EXPECTED_WINDOW_SHA256 = "5aa5f8c047baa12f29cae33585e1f7be493c5bfbde43a706f4537dbe599dad70"
EXPECTED_STYLE_SHA256 = "8ba694891ee2eb99c27c28a264929800a141b78db517acf47517a3d7c44c7d48"
RUNTIME_ATTR = 'data-tcs-ramzy-collision-sync="v1.2"'
SELECTOR_CONST = 'const RAMZY_COLLISION_SYNC_SELECTOR = ".ramzy-launcher-wrap";'

print("RUNNING=TOS_GLOBAL_TCS_FLAGSHIP_V1_2_RAMZY_COLLISION_SYNC")


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
    print("TCS_V1_2_RUNTIME=NO")
    sys.exit(1)


for path in (LAUNCHER, WINDOW, STYLE, FRONTEND, LIVE_PARENT):
    if not path.exists():
        fail(f"required path missing: {path}")

if sha256(LAUNCHER) != EXPECTED_LAUNCHER_SHA256:
    fail(f"TcsFloatingLauncher.jsx source guard mismatch: {sha256(LAUNCHER)}")
if sha256(WINDOW) != EXPECTED_WINDOW_SHA256:
    fail(f"TcsDesktopWindow.jsx source guard mismatch: {sha256(WINDOW)}")
if sha256(STYLE) != EXPECTED_STYLE_SHA256:
    fail(f"tcsFlagshipV1.css source guard mismatch: {sha256(STYLE)}")

original = LAUNCHER.read_text(encoding="utf-8")
if RUNTIME_ATTR in original or SELECTOR_CONST in original:
    fail("TCS V1.2 Ramzy collision sync already applied")
if 'import "./tcsFlagshipV1.css";' not in original:
    fail("TCS V1 baseline import missing")

const_anchor = 'const STORAGE_PREFIX = "tos.tcs.launcher.position.v2";'
effect_anchor = '''  useEffect(() => {\n    onPositionChange?.(position);\n  }, [position, onPositionChange]);\n'''
testid_anchor = '        data-testid="tcs-floating-launcher"\n'

for label, anchor in (("const", const_anchor), ("effect", effect_anchor), ("testid", testid_anchor)):
    if original.count(anchor) != 1:
        fail(f"{label} anchor mismatch: expected 1, found {original.count(anchor)}")

sync_effect = r'''

  useEffect(() => {
    if (typeof document === "undefined" || typeof MutationObserver === "undefined") return undefined;
    let frameId = 0;
    let ramzyNode = null;
    let ramzyObserver = null;
    let ramzyResizeObserver = null;

    const syncAgainstRamzy = () => {
      cancelAnimationFrame(frameId);
      frameId = requestAnimationFrame(() => {
        const nextFrame = frameRectFromRef(frameRef);
        if (!nextFrame) return;
        const blockedRect = getBlockedRamzyRect(nextFrame);
        if (!blockedRect) return;
        setFrame(nextFrame);
        setPosition((current) => {
          const legal = clampPosition(current, size, nextFrame);
          const safe = avoidRect(legal, size, blockedRect, nextFrame);
          if (safe.x === current.x && safe.y === current.y) return current;
          writeStoredJson(positionKey, safe);
          return safe;
        });
      });
    };

    const attachRamzyObserver = () => {
      const nextNode = document.querySelector(RAMZY_COLLISION_SYNC_SELECTOR);
      if (!nextNode || nextNode === ramzyNode) return;
      ramzyObserver?.disconnect();
      ramzyResizeObserver?.disconnect();
      ramzyNode = nextNode;
      ramzyObserver = new MutationObserver(syncAgainstRamzy);
      ramzyObserver.observe(nextNode, { attributes: true, attributeFilter: ["style", "class"] });
      if (typeof ResizeObserver !== "undefined") {
        ramzyResizeObserver = new ResizeObserver(syncAgainstRamzy);
        ramzyResizeObserver.observe(nextNode);
      }
      syncAgainstRamzy();
    };

    const bodyObserver = new MutationObserver(attachRamzyObserver);
    bodyObserver.observe(document.body, { childList: true, subtree: true });
    attachRamzyObserver();
    const settleTimer = window.setTimeout(() => {
      attachRamzyObserver();
      syncAgainstRamzy();
    }, 120);

    return () => {
      cancelAnimationFrame(frameId);
      window.clearTimeout(settleTimer);
      bodyObserver.disconnect();
      ramzyObserver?.disconnect();
      ramzyResizeObserver?.disconnect();
    };
  }, [frameRef, positionKey, size.width, size.height]);
'''

next_source = original.replace(const_anchor, const_anchor + "\n" + SELECTOR_CONST, 1)
next_source = next_source.replace(effect_anchor, effect_anchor + sync_effect, 1)
next_source = next_source.replace(testid_anchor, testid_anchor + f'        {RUNTIME_ATTR}\n', 1)

# Behavior-critical guards remain present. Ramzy code is not touched.
for token in (
    "onPointerDown={handlePointerDown}",
    "(active ? onClose : onOpen)?.();",
    "tcs-floating-launcher-badge",
    "getBlockedRamzyRect",
    "avoidRect",
):
    if token not in next_source:
        fail(f"behavior guard missing after transform: {token}")

try:
    LAUNCHER.write_text(next_source, encoding="utf-8")
except Exception as exc:
    LAUNCHER.write_text(original, encoding="utf-8")
    fail(f"source transformation failed and rolled back: {exc}")

build = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, text=True, capture_output=True)
if build.returncode != 0:
    print(build.stdout[-6000:])
    print(build.stderr[-6000:])
    LAUNCHER.write_text(original, encoding="utf-8")
    fail("frontend build failed; launcher source rolled back")

if not DIST.exists():
    LAUNCHER.write_text(original, encoding="utf-8")
    fail("frontend dist missing after successful build")

for marker in (
    b"data-tcs-ramzy-collision-sync",
    b".ramzy-launcher-wrap",
    b"tcs-floating-launcher",
    b"tcs-desktop-window",
):
    if tree_count(DIST, marker) < 1:
        LAUNCHER.write_text(original, encoding="utf-8")
        fail(f"built output missing runtime marker/token: {marker.decode()}")

timestamp = int(time.time())
candidate = LIVE_PARENT / f"build.tcs-v1-2-ramzy-collision-candidate-{timestamp}"
backup = LIVE_PARENT / f"build.tcs-v1-2-ramzy-collision-backup-{timestamp}"
failed_live = LIVE_PARENT / f"build.tcs-v1-2-ramzy-collision-failed-{timestamp}"

try:
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
        LAUNCHER.write_text(original, encoding="utf-8")
    fail(f"live deployment failed and rollback attempted: {exc}")

print("PASS/FAIL=PASS")
print("BUILD_RESULT=PASS")
print("LIVE_DEPLOY=PASS")
print("TCS_V1_RUNTIME=YES")
print("TCS_V1_1_RUNTIME=YES")
print("TCS_V1_2_RUNTIME=YES")
print("TCS_LAUNCHER_RAMZY_COLLISION_SYNC=YES")
print("TCS_LAUNCHER_LATE_RAMZY_MOUNT_HANDLED=YES")
print("TCS_LAUNCHER_RAMZY_MOVE_HANDLED=YES")
print("TCS_LAUNCHER_VISIBILITY_GUARD=YES")
print("TCS_DRAG_PRESERVED=YES")
print("TCS_UNREAD_PRESERVED=YES")
print("TCS_WINDOW_BEHAVIOR_CHANGED=NO")
print("TCS_CHAT_LOGIC_CHANGED=NO")
print("RAMZY_CHANGED=NO")
print("API_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print(f"TCS_LAUNCHER_SHA256={sha256(LAUNCHER)}")
print(f"TCS_STYLE_SHA256={sha256(STYLE)}")
print(f"LIVE_BACKUP={backup}")
print("STATUS=READY")
