from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time

VERSION = "TOS_TASK_DETAILS_V2_12_PHASE1_R21_R20_RECOVERY_SCROLL_STABILIZE"
PATCH_NAME = "TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-R21-R20-RECOVERY-SCROLL-STABILIZE"
R19_MARKER = "--tos-task-details-v2-12-phase1-r19-reset-actual-scroll-owners-runtime"
R20_MARKER = "--tos-task-details-v2-12-phase1-r20-keyed-scroll-container-remount-runtime"
R21_MARKER = "--tos-task-details-v2-12-phase1-r21-r20-recovery-scroll-stabilize-runtime"

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
STYLE_DIR = FRONTEND / "src/styles"
BOARD = FRONTEND / "src/components/ProfessionalTaskBoard.jsx"
APP = FRONTEND / "src/App.jsx"
SIDEBAR = FRONTEND / "src/components/layout/Sidebar.jsx"
R19_STYLE = STYLE_DIR / "taskDetailsV2_12_Phase1R19ResetActualScrollOwners.css"
R20_STYLE = STYLE_DIR / "taskDetailsV2_12_Phase1R20KeyedScrollContainerRemount.css"
R21_STYLE = STYLE_DIR / "taskDetailsV2_12_Phase1R21R20RecoveryScrollStabilize.css"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"
PATCH_DIR = Path(__file__).resolve().parent
PAYLOAD = PATCH_DIR / "taskDetailsV2_12_Phase1R21R20RecoveryScrollStabilize.css"


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for path in (FRONTEND, STYLE_DIR, BOARD, APP, SIDEBAR, R19_STYLE, R20_STYLE, MANIFEST, PAYLOAD):
    if not path.exists():
        fail(f"required path missing: {path}")
for command in ("node", "npm"):
    if not shutil.which(command):
        fail(f"required command not found: {command}")

board_source = BOARD.read_text()
r19_source = R19_STYLE.read_text()
r20_source = R20_STYLE.read_text()
payload_css = PAYLOAD.read_text()

if R19_MARKER not in r19_source:
    fail("required R19 baseline marker missing")
if R20_MARKER not in r20_source:
    fail("required R20 marker missing")
if R21_STYLE.exists() or R21_MARKER in board_source:
    fail("Phase 1 R21 already appears to be applied")
if R21_MARKER not in payload_css:
    fail("R21 payload runtime marker missing")

keyed_body = '<div key={String(task?.id || "task-details")} ref={taskDetailsBodyRef} onScroll={handleTaskDetailsScroll} className="min-h-0 flex-1 overflow-y-auto p-3 dark:from-zinc-950 dark:via-zinc-950 dark:to-blue-950/20 sm:p-4">'
recovered_body = '<div data-tos-task-scroll-owner="true" ref={taskDetailsBodyRef} onScroll={handleTaskDetailsScroll} className="min-h-0 flex-1 overflow-y-auto p-3 dark:from-zinc-950 dark:via-zinc-950 dark:to-blue-950/20 sm:p-4">'
if board_source.count(keyed_body) != 1:
    fail(f"expected exactly one R20 keyed Task Details scroll container, found {board_source.count(keyed_body)}")
updated_board = board_source.replace(keyed_body, recovered_body, 1)

old_effect = '''  useEffect(() => {\n    let frameOne = null;\n    let frameTwo = null;\n    let timeoutId = null;\n\n    const resetNodeScroll = (node) => {\n      if (!node) return;\n      try {\n        node.scrollTop = 0;\n        node.scrollLeft = 0;\n      } catch {\n        // Non-scrollable nodes are harmless; continue to the real owner.\n      }\n    };\n\n    const resetTaskDetailsScrollOwners = () => {\n      if (typeof document === "undefined" || typeof window === "undefined") return;\n\n      const scroller = taskDetailsBodyRef.current;\n      resetNodeScroll(scroller);\n      if (scroller) scroller.dataset.tosTaskDetailsScrollReset = "r19";\n\n      const visited = new Set();\n      let ancestor = scroller?.parentElement || null;\n      while (ancestor && ancestor !== document.body && !visited.has(ancestor)) {\n        visited.add(ancestor);\n        const styles = window.getComputedStyle(ancestor);\n        const overflowY = styles.overflowY;\n        const canScroll = ancestor.scrollHeight > ancestor.clientHeight || overflowY === "auto" || overflowY === "scroll";\n        if (canScroll) resetNodeScroll(ancestor);\n        ancestor = ancestor.parentElement;\n      }\n\n      resetNodeScroll(modalRef.current);\n      resetNodeScroll(document.querySelector(".tos-task-details-fullpage"));\n      resetNodeScroll(document.querySelector(".tos-task-details-reference-v1"));\n      resetNodeScroll(document.querySelector(".tos-premium-page-viewport"));\n      resetNodeScroll(document.scrollingElement);\n\n      try {\n        window.scrollTo({ top: 0, left: 0, behavior: "auto" });\n      } catch {\n        window.scrollTo(0, 0);\n      }\n    };\n\n    resetTaskDetailsScrollOwners();\n    frameOne = window.requestAnimationFrame(() => {\n      resetTaskDetailsScrollOwners();\n      frameTwo = window.requestAnimationFrame(resetTaskDetailsScrollOwners);\n    });\n    timeoutId = window.setTimeout(resetTaskDetailsScrollOwners, 120);\n\n    return () => {\n      if (frameOne !== null) window.cancelAnimationFrame(frameOne);\n      if (frameTwo !== null) window.cancelAnimationFrame(frameTwo);\n      if (timeoutId !== null) window.clearTimeout(timeoutId);\n    };\n  }, [task?.id]);'''

new_effect = '''  useEffect(() => {\n    const frameIds = [];\n    const timeoutIds = [];\n\n    const resetNodeScroll = (node) => {\n      if (!node) return;\n      try {\n        node.scrollTop = 0;\n        node.scrollLeft = 0;\n        if (typeof node.scrollTo === "function") node.scrollTo({ top: 0, left: 0, behavior: "auto" });\n      } catch {\n        // Non-scrollable nodes are harmless; continue to the real owner.\n      }\n    };\n\n    const resetTaskDetailsScrollOwners = () => {\n      if (typeof document === "undefined" || typeof window === "undefined") return;\n\n      const scroller = taskDetailsBodyRef.current;\n      resetNodeScroll(scroller);\n      if (scroller) {\n        scroller.dataset.tosTaskDetailsScrollReset = "r21";\n        scroller.style.overflowAnchor = "none";\n      }\n\n      const visited = new Set();\n      let ancestor = scroller?.parentElement || null;\n      while (ancestor && ancestor !== document.body && !visited.has(ancestor)) {\n        visited.add(ancestor);\n        const styles = window.getComputedStyle(ancestor);\n        const overflowY = styles.overflowY;\n        const canScroll = ancestor.scrollHeight > ancestor.clientHeight || overflowY === "auto" || overflowY === "scroll";\n        if (canScroll) resetNodeScroll(ancestor);\n        ancestor = ancestor.parentElement;\n      }\n\n      resetNodeScroll(modalRef.current);\n      resetNodeScroll(document.querySelector(".tos-task-details-fullpage"));\n      resetNodeScroll(document.querySelector(".tos-task-details-reference-v1"));\n      resetNodeScroll(document.querySelector(".tos-premium-page-viewport"));\n      resetNodeScroll(document.scrollingElement);\n\n      try {\n        window.scrollTo({ top: 0, left: 0, behavior: "auto" });\n      } catch {\n        window.scrollTo(0, 0);\n      }\n    };\n\n    resetTaskDetailsScrollOwners();\n    frameIds.push(window.requestAnimationFrame(() => {\n      resetTaskDetailsScrollOwners();\n      frameIds.push(window.requestAnimationFrame(resetTaskDetailsScrollOwners));\n    }));\n    [60, 180, 420, 800].forEach((delay) => {\n      timeoutIds.push(window.setTimeout(resetTaskDetailsScrollOwners, delay));\n    });\n\n    return () => {\n      frameIds.forEach((id) => window.cancelAnimationFrame(id));\n      timeoutIds.forEach((id) => window.clearTimeout(id));\n    };\n  }, [task?.id]);'''

if updated_board.count(old_effect) != 1:
    fail(f"expected exactly one R19 multi-owner reset effect, found {updated_board.count(old_effect)}")
updated_board = updated_board.replace(old_effect, new_effect, 1)

r19_import = 'import "../styles/taskDetailsV2_12_Phase1R19ResetActualScrollOwners.css";'
r20_import = 'import "../styles/taskDetailsV2_12_Phase1R20KeyedScrollContainerRemount.css";'
r21_import = 'import "../styles/taskDetailsV2_12_Phase1R21R20RecoveryScrollStabilize.css";'
if r19_import not in updated_board:
    fail("R19 stylesheet import missing")
if r20_import not in updated_board:
    fail("R20 stylesheet import missing")
if r21_import in updated_board:
    fail("R21 stylesheet import already exists")
updated_board = updated_board.replace(r20_import + "\n", "", 1)
updated_board = updated_board.replace(r19_import, r19_import + "\n" + r21_import, 1)

for contract in (
    'data-tos-task-scroll-owner="true"',
    'scroller.dataset.tosTaskDetailsScrollReset = "r21";',
    'scroller.style.overflowAnchor = "none";',
    '[60, 180, 420, 800]',
    r21_import,
):
    if contract not in updated_board:
        fail(f"R21 source contract missing after edit: {contract}")
if 'key={String(task?.id || "task-details")}' in updated_board:
    fail("R20 keyed remount still present after R21 recovery")
if r20_import in updated_board:
    fail("R20 stylesheet import still present after R21 recovery")

app_hash = sha256(APP)
sidebar_hash = sha256(SIDEBAR)
prior_styles = sorted(p for p in STYLE_DIR.glob("taskDetailsV2_12_Phase1*.css") if p != R21_STYLE)
prior_style_hashes = {p: sha256(p) for p in prior_styles}

manifest = json.loads(MANIFEST.read_text())
if manifest.get("application") != "TOS" or manifest.get("environment") != "production":
    fail("unexpected production runtime manifest")
if manifest.get("sourceRoot") != str(ROOT):
    fail("runtime sourceRoot does not match target")
frontend_runtime = manifest.get("frontend") or {}
if Path(str(frontend_runtime.get("sourceDir") or "")) != FRONTEND:
    fail("frontend runtime sourceDir mismatch")
if str(frontend_runtime.get("buildCommand") or "") != "npm run build":
    fail("unexpected frontend build command")
DIST = Path(str(frontend_runtime.get("buildOutputDir") or ""))
LIVE = Path(str(frontend_runtime.get("publishedBuildDir") or ""))
if DIST != FRONTEND / "dist":
    fail(f"unexpected frontend build output: {DIST}")
if LIVE != Path("/opt/apps/tamiyouz-front/build"):
    fail(f"unexpected live frontend path: {LIVE}")

stamp = int(time.time())
backup_root = Path(f"/var/backups/tos-patches/task-details-v2-12-phase1-r21-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
board_backup = backup_root / BOARD.name
shutil.copy2(BOARD, board_backup)

LIVE.parent.mkdir(parents=True, exist_ok=True)
staging = LIVE.parent / f"build.task-details-v2-12-phase1-r21-staging-{stamp}"
live_backup = LIVE.parent / f"build.task-details-v2-12-phase1-r21-backup-{stamp}"
live_swapped = False
r21_written = False

try:
    BOARD.write_text(updated_board)
    R21_STYLE.write_text(payload_css.rstrip() + "\n")
    r21_written = True

    if sha256(APP) != app_hash or sha256(SIDEBAR) != sidebar_hash:
        fail("frozen app shell source changed unexpectedly")
    for path, digest in prior_style_hashes.items():
        if sha256(path) != digest:
            fail(f"prior Phase1 stylesheet changed unexpectedly: {path.name}")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    built_css = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.css"))
    built_js = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.js"))
    if R21_MARKER not in built_css:
        fail("R21 runtime marker missing from built CSS")
    if R19_MARKER not in built_css:
        fail("R19 baseline marker missing from built CSS")
    if R20_MARKER in built_css:
        fail("R20 marker unexpectedly still present in built CSS")
    if "tosTaskDetailsScrollReset" not in built_js or "r21" not in built_js:
        fail("R21 scroll stabilization missing from built JS")

    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(DIST, staging)
    if LIVE.exists():
        if live_backup.exists():
            shutil.rmtree(live_backup)
        LIVE.rename(live_backup)
    staging.rename(LIVE)
    live_swapped = True

    live_css = "\n".join(p.read_text(errors="ignore") for p in LIVE.rglob("*.css"))
    live_js = "\n".join(p.read_text(errors="ignore") for p in LIVE.rglob("*.js"))
    if R21_MARKER not in live_css:
        fail("R21 runtime marker missing from live CSS")
    if R20_MARKER in live_css:
        fail("R20 marker unexpectedly still present in live CSS")
    if "tosTaskDetailsScrollReset" not in live_js or "r21" not in live_js:
        fail("R21 scroll stabilization missing from live JS")

    if sha256(APP) != app_hash or sha256(SIDEBAR) != sidebar_hash:
        fail("frozen app shell source changed after deploy")
    for path, digest in prior_style_hashes.items():
        if sha256(path) != digest:
            fail(f"prior Phase1 stylesheet changed after deploy: {path.name}")

except Exception:
    shutil.copy2(board_backup, BOARD)
    if r21_written and R21_STYLE.exists():
        R21_STYLE.unlink()
    if live_swapped:
        if LIVE.exists():
            shutil.rmtree(LIVE)
        if live_backup.exists():
            live_backup.rename(LIVE)
    elif staging.exists():
        shutil.rmtree(staging)
    raise

print(f"VERSION={VERSION}")
print(f"PATCH={PATCH_NAME}")
print("PASS/FAIL=PASS")
print("BUILD_RESULT=PASS")
print("LIVE_DEPLOY=PASS")
print("R20_KEYED_REMOUNT_REMOVED=YES")
print("R20_STYLESHEET_IMPORT_REMOVED=YES")
print("TASK_DETAILS_RENDER_RECOVERY=YES")
print("TASK_SCROLL_ANCHOR_DISABLED=YES")
print("TASK_SCROLL_MULTI_OWNER_RESET=YES")
print("POST_LAYOUT_RETRIES=60,180,420,800")
print("LAYOUT_CHANGED=NO")
print("APP_JS_CHANGED=NO")
print("SIDEBAR_JS_CHANGED=NO")
print("BACKEND_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print("TCS_CHANGED=NO")
print("RAMZY_CHANGED=NO")
print("NO_BROWSER_QA=YES")
print("NO_SCREENSHOTS=YES")
print("PUSH=NO")
print(f"BACKUP={backup_root}")
print("STATUS=DEPLOYED__MANUAL_VISUAL_QA_REQUIRED")
