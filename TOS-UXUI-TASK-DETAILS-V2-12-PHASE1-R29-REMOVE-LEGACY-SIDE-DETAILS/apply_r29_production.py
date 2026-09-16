from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time

PATCH = "TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-R29-REMOVE-LEGACY-SIDE-DETAILS"
R28_MARKER = "--tos-task-details-v2-12-phase1-r28-more-no-scroll-jump-runtime"
R29_MARKER = "--tos-task-details-v2-12-phase1-r29-remove-legacy-side-details-runtime"

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
STYLE_DIR = FRONTEND / "src/styles"
BOARD = FRONTEND / "src/components/ProfessionalTaskBoard.jsx"
APP = FRONTEND / "src/App.jsx"
SIDEBAR = FRONTEND / "src/components/layout/Sidebar.jsx"
R28_STYLE = STYLE_DIR / "taskDetailsV2_12_Phase1R28MoreNoScrollJump.css"
R29_STYLE = STYLE_DIR / "taskDetailsV2_12_Phase1R29RemoveLegacySideDetails.css"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"
PAYLOAD = Path(__file__).resolve().parent / "taskDetailsV2_12_Phase1R29RemoveLegacySideDetails.css"


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


for path in (FRONTEND, STYLE_DIR, BOARD, APP, SIDEBAR, R28_STYLE, MANIFEST, PAYLOAD):
    if not path.exists():
        fail(f"required path missing: {path}")
for command in ("node", "npm"):
    if not shutil.which(command):
        fail(f"required command missing: {command}")

board_source = BOARD.read_text()
r28_source = R28_STYLE.read_text()
payload_css = PAYLOAD.read_text()

if R28_MARKER not in r28_source:
    fail("R28 production baseline marker missing")
if R29_MARKER not in payload_css:
    fail("R29 payload marker missing")
if R29_STYLE.exists():
    fail("R29 stylesheet already exists")

r28_import = 'import "../styles/taskDetailsV2_12_Phase1R28MoreNoScrollJump.css";'
r29_import = 'import "../styles/taskDetailsV2_12_Phase1R29RemoveLegacySideDetails.css";'
if board_source.count(r28_import) != 1:
    fail(f"expected exactly one R28 import, found {board_source.count(r28_import)}")
if r29_import in board_source:
    fail("R29 import already exists")

updated = board_source.replace(r28_import, r28_import + "\n" + r29_import, 1)
if r29_import not in updated:
    fail("R29 import insertion failed")

app_hash = sha256(APP)
sidebar_hash = sha256(SIDEBAR)
prior_styles = sorted(p for p in STYLE_DIR.glob("taskDetailsV2_12_Phase1*.css") if p != R29_STYLE)
prior_style_hashes = {p: sha256(p) for p in prior_styles}

manifest = json.loads(MANIFEST.read_text())
if manifest.get("application") != "TOS" or manifest.get("environment") != "production":
    fail("unexpected production runtime manifest")
frontend_runtime = manifest.get("frontend") or {}
DIST = Path(str(frontend_runtime.get("buildOutputDir") or FRONTEND / "dist"))
LIVE = Path(str(frontend_runtime.get("publishedBuildDir") or "/opt/apps/tamiyouz-front/build"))
if str(frontend_runtime.get("buildCommand") or "npm run build") != "npm run build":
    fail("unexpected frontend build command")

stamp = int(time.time())
backup_root = Path(f"/var/backups/tos-patches/task-details-v2-12-phase1-r29-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
shutil.copy2(BOARD, backup_root / BOARD.name)

LIVE.parent.mkdir(parents=True, exist_ok=True)
staging = LIVE.parent / f"build.task-details-r29-staging-{stamp}"
live_backup = LIVE.parent / f"build.task-details-r29-backup-{stamp}"
live_swapped = False
r29_written = False

try:
    BOARD.write_text(updated)
    R29_STYLE.write_text(payload_css.rstrip() + "\n")
    r29_written = True

    if sha256(APP) != app_hash or sha256(SIDEBAR) != sidebar_hash:
        fail("app shell changed unexpectedly")
    for path, digest in prior_style_hashes.items():
        if sha256(path) != digest:
            fail(f"prior Phase1 stylesheet changed unexpectedly: {path.name}")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    built_css = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.css"))
    if R29_MARKER not in built_css or R28_MARKER not in built_css:
        fail("R28/R29 runtime marker missing from build")
    if ".tos-task-side-rail" not in built_css:
        fail("R29 legacy side-rail selector missing from build CSS")

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
    if R29_MARKER not in live_css or R28_MARKER not in live_css:
        fail("R28/R29 runtime marker missing from live build")
    if ".tos-task-side-rail" not in live_css:
        fail("R29 legacy side-rail selector missing from live CSS")

    if sha256(APP) != app_hash or sha256(SIDEBAR) != sidebar_hash:
        fail("app shell changed after deploy")
    for path, digest in prior_style_hashes.items():
        if sha256(path) != digest:
            fail(f"prior Phase1 stylesheet changed after deploy: {path.name}")

except Exception:
    shutil.copy2(backup_root / BOARD.name, BOARD)
    if r29_written and R29_STYLE.exists():
        R29_STYLE.unlink()
    if live_swapped:
        if LIVE.exists():
            shutil.rmtree(LIVE)
        if live_backup.exists():
            live_backup.rename(LIVE)
    elif staging.exists():
        shutil.rmtree(staging)
    raise

print(f"PATCH_APPLIED={PATCH}")
print("BUILD_STATUS=PASS")
print("DEPLOY_STATUS=PASS")
print("LEGACY_SIDE_DETAILS_HIDDEN=YES")
print("R28_PRESERVED=YES")
print("R26_PRESERVED=YES")
print("BACKEND_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print("TCS_CHANGED=NO")
print("RAMZY_CHANGED=NO")
print("PUSH=NO")
