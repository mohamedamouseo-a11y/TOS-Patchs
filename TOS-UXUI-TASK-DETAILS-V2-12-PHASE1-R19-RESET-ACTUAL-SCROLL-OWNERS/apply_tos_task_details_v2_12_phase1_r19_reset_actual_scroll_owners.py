from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time

VERSION = "TOS_TASK_DETAILS_V2_12_PHASE1_R19_RESET_ACTUAL_SCROLL_OWNERS"
PATCH_NAME = "TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-R19-RESET-ACTUAL-SCROLL-OWNERS"
R18_MARKER = "--tos-task-details-v2-12-phase1-r18-scroll-reset-on-task-change-runtime"
R19_MARKER = "--tos-task-details-v2-12-phase1-r19-reset-actual-scroll-owners-runtime"
R19_JS_MARKER = "tosTaskDetailsScrollReset = \"r19\""

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
STYLE_DIR = FRONTEND / "src/styles"
BOARD = FRONTEND / "src/components/ProfessionalTaskBoard.jsx"
APP = FRONTEND / "src/App.jsx"
SIDEBAR = FRONTEND / "src/components/layout/Sidebar.jsx"
R18_STYLE = STYLE_DIR / "taskDetailsV2_12_Phase1R18ScrollResetOnTaskChange.css"
R19_STYLE = STYLE_DIR / "taskDetailsV2_12_Phase1R19ResetActualScrollOwners.css"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"
PATCH_DIR = Path(__file__).resolve().parent
PAYLOAD = PATCH_DIR / "taskDetailsV2_12_Phase1R19ResetActualScrollOwners.css"


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for path in (FRONTEND, STYLE_DIR, BOARD, APP, SIDEBAR, R18_STYLE, MANIFEST, PAYLOAD):
    if not path.exists():
        fail(f"required path missing: {path}")
for command in ("node", "npm"):
    if not shutil.which(command):
        fail(f"required command not found: {command}")

board_source = BOARD.read_text()
r18_source = R18_STYLE.read_text()
payload_css = PAYLOAD.read_text()

if R18_MARKER not in r18_source:
    fail("required R18 baseline marker missing")
if R19_STYLE.exists() or 'tosTaskDetailsScrollReset = "r19"' in board_source:
    fail("Phase 1 R19 already appears to be applied")
if R19_MARKER not in payload_css:
    fail("R19 payload runtime marker missing")

old_effect = '''  useEffect(() => {\n    let frameId = null;\n\n    const resetTaskDetailsScroll = () => {\n      const scroller = taskDetailsBodyRef.current;\n      if (!scroller) return;\n      scroller.scrollTop = 0;\n      scroller.scrollLeft = 0;\n      scroller.dataset.tosTaskDetailsScrollReset = "r18";\n    };\n\n    resetTaskDetailsScroll();\n    if (typeof window !== "undefined") {\n      frameId = window.requestAnimationFrame(resetTaskDetailsScroll);\n    }\n\n    return () => {\n      if (frameId !== null && typeof window !== "undefined") {\n        window.cancelAnimationFrame(frameId);\n      }\n    };\n  }, [task?.id]);'''

new_effect = '''  useEffect(() => {\n    let frameOne = null;\n    let frameTwo = null;\n    let timeoutId = null;\n\n    const resetNodeScroll = (node) => {\n      if (!node) return;\n      try {\n        node.scrollTop = 0;\n        node.scrollLeft = 0;\n      } catch {\n        // Non-scrollable nodes are harmless; continue to the real owner.\n      }\n    };\n\n    const resetTaskDetailsScrollOwners = () => {\n      if (typeof document === "undefined" || typeof window === "undefined") return;\n\n      const scroller = taskDetailsBodyRef.current;\n      resetNodeScroll(scroller);\n      if (scroller) scroller.dataset.tosTaskDetailsScrollReset = "r19";\n\n      const visited = new Set();\n      let ancestor = scroller?.parentElement || null;\n      while (ancestor && ancestor !== document.body && !visited.has(ancestor)) {\n        visited.add(ancestor);\n        const styles = window.getComputedStyle(ancestor);\n        const overflowY = styles.overflowY;\n        const canScroll = ancestor.scrollHeight > ancestor.clientHeight || overflowY === "auto" || overflowY === "scroll";\n        if (canScroll) resetNodeScroll(ancestor);\n        ancestor = ancestor.parentElement;\n      }\n\n      resetNodeScroll(modalRef.current);\n      resetNodeScroll(document.querySelector(".tos-task-details-fullpage"));\n      resetNodeScroll(document.querySelector(".tos-task-details-reference-v1"));\n      resetNodeScroll(document.querySelector(".tos-premium-page-viewport"));\n      resetNodeScroll(document.scrollingElement);\n\n      try {\n        window.scrollTo({ top: 0, left: 0, behavior: "auto" });\n      } catch {\n        window.scrollTo(0, 0);\n      }\n    };\n\n    resetTaskDetailsScrollOwners();\n    frameOne = window.requestAnimationFrame(() => {\n      resetTaskDetailsScrollOwners();\n      frameTwo = window.requestAnimationFrame(resetTaskDetailsScrollOwners);\n    });\n    timeoutId = window.setTimeout(resetTaskDetailsScrollOwners, 120);\n\n    return () => {\n      if (frameOne !== null) window.cancelAnimationFrame(frameOne);\n      if (frameTwo !== null) window.cancelAnimationFrame(frameTwo);\n      if (timeoutId !== null) window.clearTimeout(timeoutId);\n    };\n  }, [task?.id]);'''

if board_source.count(old_effect) != 1:
    fail(f"expected exactly one R18 scroll reset effect, found {board_source.count(old_effect)}")
updated_board = board_source.replace(old_effect, new_effect, 1)

r18_import = 'import "../styles/taskDetailsV2_12_Phase1R18ScrollResetOnTaskChange.css";'
r19_import = 'import "../styles/taskDetailsV2_12_Phase1R19ResetActualScrollOwners.css";'
if r18_import not in updated_board:
    fail("R18 stylesheet import missing")
if r19_import in updated_board:
    fail("R19 stylesheet import already exists")
updated_board = updated_board.replace(r18_import, r18_import + "\n" + r19_import, 1)

for contract in (
    'scroller.dataset.tosTaskDetailsScrollReset = "r19";',
    'document.querySelector(".tos-task-details-fullpage")',
    'document.querySelector(".tos-premium-page-viewport")',
    'document.scrollingElement',
    'window.setTimeout(resetTaskDetailsScrollOwners, 120)',
    'frameTwo = window.requestAnimationFrame(resetTaskDetailsScrollOwners)',
    r19_import,
):
    if contract not in updated_board:
        fail(f"R19 source contract missing after edit: {contract}")

app_hash = sha256(APP)
sidebar_hash = sha256(SIDEBAR)
prior_styles = sorted(p for p in STYLE_DIR.glob("taskDetailsV2_12_Phase1*.css") if p != R19_STYLE)
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
backup_root = Path(f"/var/backups/tos-patches/task-details-v2-12-phase1-r19-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
board_backup = backup_root / BOARD.name
shutil.copy2(BOARD, board_backup)

LIVE.parent.mkdir(parents=True, exist_ok=True)
staging = LIVE.parent / f"build.task-details-v2-12-phase1-r19-staging-{stamp}"
live_backup = LIVE.parent / f"build.task-details-v2-12-phase1-r19-backup-{stamp}"
live_swapped = False
r19_written = False

try:
    BOARD.write_text(updated_board)
    R19_STYLE.write_text(payload_css.rstrip() + "\n")
    r19_written = True

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
    for marker in (R19_MARKER, R18_MARKER):
        if marker not in built_css:
            fail(f"required runtime marker missing from built CSS: {marker}")
    if 'tosTaskDetailsScrollReset="r19"' not in built_js.replace(" ", "") and 'tosTaskDetailsScrollReset:"r19"' not in built_js.replace(" ", ""):
        if "r19" not in built_js or "tosTaskDetailsScrollReset" not in built_js:
            fail("R19 multi-owner scroll reset missing from built JS")

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
    for marker in (R19_MARKER, R18_MARKER):
        if marker not in live_css:
            fail(f"required runtime marker missing from live CSS: {marker}")
    if "r19" not in live_js or "tosTaskDetailsScrollReset" not in live_js:
        fail("R19 multi-owner scroll reset missing from live JS")

    if sha256(APP) != app_hash or sha256(SIDEBAR) != sidebar_hash:
        fail("frozen app shell source changed after deploy")
    for path, digest in prior_style_hashes.items():
        if sha256(path) != digest:
            fail(f"prior Phase1 stylesheet changed after deploy: {path.name}")

except Exception:
    shutil.copy2(board_backup, BOARD)
    if r19_written and R19_STYLE.exists():
        R19_STYLE.unlink()
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
print("R18_SINGLE_OWNER_RESET_REPLACED=YES")
print("TASK_BODY_RESET=YES")
print("SCROLLABLE_ANCESTORS_RESET=YES")
print("TASK_FULLSCREEN_SHELL_RESET=YES")
print("PREMIUM_PAGE_VIEWPORT_RESET=YES")
print("DOCUMENT_SCROLL_RESET=YES")
print("WINDOW_SCROLL_RESET=YES")
print("POST_LAYOUT_RETRY=YES")
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
