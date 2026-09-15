from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time

VERSION = "TOS_TASK_DETAILS_V2_12_PHASE1_R18_SCROLL_RESET_ON_TASK_CHANGE"
PATCH_NAME = "TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-R18-SCROLL-RESET-ON-TASK-CHANGE"
R16_MARKER = "--tos-task-details-v2-12-phase1-r16-r13-recovery-safe-bottom-flow-runtime"
R17_MARKER = "--tos-task-details-v2-12-phase1-r17-assignee-portal-viewport-floating-runtime"
R18_MARKER = "--tos-task-details-v2-12-phase1-r18-scroll-reset-on-task-change-runtime"
R18_JS_MARKER = "tosTaskDetailsScrollReset"

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
STYLE_DIR = FRONTEND / "src/styles"
BOARD = FRONTEND / "src/components/ProfessionalTaskBoard.jsx"
APP = FRONTEND / "src/App.jsx"
SIDEBAR = FRONTEND / "src/components/layout/Sidebar.jsx"
R16_STYLE = STYLE_DIR / "taskDetailsV2_12_Phase1R16R13RecoverySafeBottomFlow.css"
R17_STYLE = STYLE_DIR / "taskDetailsV2_12_Phase1R17AssigneePortalViewportFloating.css"
R18_STYLE = STYLE_DIR / "taskDetailsV2_12_Phase1R18ScrollResetOnTaskChange.css"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"
PATCH_DIR = Path(__file__).resolve().parent
PAYLOAD = PATCH_DIR / "taskDetailsV2_12_Phase1R18ScrollResetOnTaskChange.css"


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for path in (FRONTEND, STYLE_DIR, BOARD, APP, SIDEBAR, R16_STYLE, MANIFEST, PAYLOAD):
    if not path.exists():
        fail(f"required path missing: {path}")
for command in ("node", "npm"):
    if not shutil.which(command):
        fail(f"required command not found: {command}")

board_source = BOARD.read_text()
r16_source = R16_STYLE.read_text()
r17_present = R17_STYLE.exists()
r17_source = R17_STYLE.read_text() if r17_present else ""
payload_css = PAYLOAD.read_text()

if R16_MARKER not in r16_source:
    fail("required R16 baseline marker missing")
if r17_present and R17_MARKER not in r17_source:
    fail("R17 stylesheet exists but runtime marker is missing")
if R18_STYLE.exists() or R18_JS_MARKER in board_source:
    fail("Phase 1 R18 already appears to be applied")
if R18_MARKER not in payload_css:
    fail("R18 payload runtime marker missing")

anchor = '''  const taskDetailsBodyRef = useRef(null);\n  const [showBackToTop, setShowBackToTop] = useState(false);'''
replacement = '''  const taskDetailsBodyRef = useRef(null);\n\n  useEffect(() => {\n    let frameId = null;\n\n    const resetTaskDetailsScroll = () => {\n      const scroller = taskDetailsBodyRef.current;\n      if (!scroller) return;\n      scroller.scrollTop = 0;\n      scroller.scrollLeft = 0;\n      scroller.dataset.tosTaskDetailsScrollReset = "r18";\n    };\n\n    resetTaskDetailsScroll();\n    if (typeof window !== "undefined") {\n      frameId = window.requestAnimationFrame(resetTaskDetailsScroll);\n    }\n\n    return () => {\n      if (frameId !== null && typeof window !== "undefined") {\n        window.cancelAnimationFrame(frameId);\n      }\n    };\n  }, [task?.id]);\n\n  const [showBackToTop, setShowBackToTop] = useState(false);'''

if board_source.count(anchor) != 1:
    fail(f"expected exactly one Task Details scroll ref anchor, found {board_source.count(anchor)}")
updated_board = board_source.replace(anchor, replacement, 1)

r16_import = 'import "../styles/taskDetailsV2_12_Phase1R16R13RecoverySafeBottomFlow.css";'
r17_import = 'import "../styles/taskDetailsV2_12_Phase1R17AssigneePortalViewportFloating.css";'
r18_import = 'import "../styles/taskDetailsV2_12_Phase1R18ScrollResetOnTaskChange.css";'
if r18_import in updated_board:
    fail("R18 stylesheet import already exists")
if r17_import in updated_board:
    updated_board = updated_board.replace(r17_import, r17_import + "\n" + r18_import, 1)
elif r16_import in updated_board:
    updated_board = updated_board.replace(r16_import, r16_import + "\n" + r18_import, 1)
else:
    fail("neither R16 nor optional R17 stylesheet import anchor found")

for contract in (
    'scroller.scrollTop = 0;',
    'scroller.scrollLeft = 0;',
    'scroller.dataset.tosTaskDetailsScrollReset = "r18";',
    'window.requestAnimationFrame(resetTaskDetailsScroll)',
    '}, [task?.id]);',
    r18_import,
):
    if contract not in updated_board:
        fail(f"R18 source contract missing after edit: {contract}")

app_hash = sha256(APP)
sidebar_hash = sha256(SIDEBAR)
prior_styles = sorted(p for p in STYLE_DIR.glob("taskDetailsV2_12_Phase1*.css") if p != R18_STYLE)
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
backup_root = Path(f"/var/backups/tos-patches/task-details-v2-12-phase1-r18-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
board_backup = backup_root / BOARD.name
shutil.copy2(BOARD, board_backup)

LIVE.parent.mkdir(parents=True, exist_ok=True)
staging = LIVE.parent / f"build.task-details-v2-12-phase1-r18-staging-{stamp}"
live_backup = LIVE.parent / f"build.task-details-v2-12-phase1-r18-backup-{stamp}"
live_swapped = False
r18_written = False

try:
    BOARD.write_text(updated_board)
    R18_STYLE.write_text(payload_css.rstrip() + "\n")
    r18_written = True

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
    for marker in (R18_MARKER, R16_MARKER):
        if marker not in built_css:
            fail(f"required runtime marker missing from built CSS: {marker}")
    if r17_present and R17_MARKER not in built_css:
        fail("optional R17 was present in source but missing from built CSS")
    if R18_JS_MARKER not in built_js:
        fail("R18 scroll reset behavior missing from built JS")

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
    for marker in (R18_MARKER, R16_MARKER):
        if marker not in live_css:
            fail(f"required runtime marker missing from live CSS: {marker}")
    if r17_present and R17_MARKER not in live_css:
        fail("optional R17 was present in source but missing from live CSS")
    if R18_JS_MARKER not in live_js:
        fail("R18 scroll reset behavior missing from live JS")

    if sha256(APP) != app_hash or sha256(SIDEBAR) != sidebar_hash:
        fail("frozen app shell source changed after deploy")
    for path, digest in prior_style_hashes.items():
        if sha256(path) != digest:
            fail(f"prior Phase1 stylesheet changed after deploy: {path.name}")

except Exception:
    shutil.copy2(board_backup, BOARD)
    if r18_written and R18_STYLE.exists():
        R18_STYLE.unlink()
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
print("TASK_DETAILS_SCROLL_RESET_ON_MOUNT=YES")
print("TASK_DETAILS_SCROLL_RESET_ON_TASK_CHANGE=YES")
print("TASK_DETAILS_SCROLL_TOP=0")
print("TASK_DETAILS_SCROLL_LEFT=0")
print(f"R17_ASSIGNEE_PORTAL_PRESENT={'YES' if r17_present else 'NO'}")
print("R16_BASELINE_PRESERVED=YES")
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
