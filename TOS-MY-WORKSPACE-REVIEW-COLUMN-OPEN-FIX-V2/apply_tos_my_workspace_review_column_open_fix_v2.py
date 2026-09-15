from pathlib import Path
import json, shutil, subprocess, sys, time

PATCH = "TOS-MY-WORKSPACE-REVIEW-COLUMN-OPEN-FIX-V2"
V1_MARKER = "TOS_MY_WORKSPACE_REVIEW_COLUMN_OPEN_FIX_V1"
V2_MARKER = "TOS_MY_WORKSPACE_REVIEW_COLUMN_OPEN_FIX_V2"
ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
MYWS = FRONTEND / "src/pages/MyTaskWorkspace.jsx"
APP = FRONTEND / "src/App.jsx"
BOARD = FRONTEND / "src/components/ProfessionalTaskBoard.jsx"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"


def fail(msg):
    raise RuntimeError(msg)


def run(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True)


for path in (FRONTEND, MYWS, APP, BOARD, MANIFEST):
    if not path.exists():
        fail(f"required path missing: {path}")

myws = MYWS.read_text()
app = APP.read_text()
board = BOARD.read_text()

if V1_MARKER not in myws:
    fail("V1 baseline marker missing from MyTaskWorkspace.jsx")
if V2_MARKER in myws or V2_MARKER in app or V2_MARKER in board:
    fail("V2 already appears to be applied")

old_myws_resolver = 'String(task?.projectId || task?.project?.id || "").trim()'
new_myws_resolver = 'String(task?.projectId || task?.project?.id || task?.board?.projectId || "").trim()'
count_myws = myws.count(old_myws_resolver)
if count_myws != 2:
    fail(f"expected 2 My Workspace project resolver anchors, found {count_myws}")
myws = myws.replace(old_myws_resolver, new_myws_resolver)
myws = myws.replace(
    "  // TOS_MY_WORKSPACE_REVIEW_COLUMN_OPEN_FIX_V1\n",
    "  // TOS_MY_WORKSPACE_REVIEW_COLUMN_OPEN_FIX_V1\n  // TOS_MY_WORKSPACE_REVIEW_COLUMN_OPEN_FIX_V2: review tasks may inherit project context from board.projectId.\n",
    1,
)

old_app_resolver = 'const projectId = String(task?.project?.id || task?.projectId || "").trim();'
new_app_resolver = 'const projectId = String(task?.project?.id || task?.projectId || task?.board?.projectId || "").trim(); // TOS_MY_WORKSPACE_REVIEW_COLUMN_OPEN_FIX_V2'
if app.count(old_app_resolver) != 1:
    fail(f"App task handoff anchor count={app.count(old_app_resolver)}")
app = app.replace(old_app_resolver, new_app_resolver, 1)

old_board_resolver = 'const resolvedProjectId = String(fullTask?.projectId || fullTask?.project?.id || "").trim();'
new_board_resolver = 'const resolvedProjectId = String(fullTask?.projectId || fullTask?.project?.id || fullTask?.board?.projectId || "").trim(); // TOS_MY_WORKSPACE_REVIEW_COLUMN_OPEN_FIX_V2'
count_board = board.count(old_board_resolver)
if count_board != 2:
    fail(f"expected 2 Task Board project-context anchors, found {count_board}")
board = board.replace(old_board_resolver, new_board_resolver)

for source_name, source in (("MyTaskWorkspace", myws), ("App", app), ("ProfessionalTaskBoard", board)):
    if "board?.projectId" not in source:
        fail(f"board project fallback missing after edit: {source_name}")

manifest = json.loads(MANIFEST.read_text())
frontend_runtime = manifest.get("frontend") or {}
if str(frontend_runtime.get("buildCommand") or "npm run build") != "npm run build":
    fail("unexpected frontend build command")
DIST = Path(str(frontend_runtime.get("buildOutputDir") or FRONTEND / "dist"))
LIVE = Path(str(frontend_runtime.get("publishedBuildDir") or "/opt/apps/tamiyouz-front/build"))

stamp = int(time.time())
backup_root = Path(f"/var/backups/tos-patches/my-workspace-review-open-v2-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
for path in (MYWS, APP, BOARD):
    shutil.copy2(path, backup_root / path.name)

LIVE.parent.mkdir(parents=True, exist_ok=True)
staging = LIVE.parent / f"build.my-workspace-review-open-v2-staging-{stamp}"
live_backup = LIVE.parent / f"build.my-workspace-review-open-v2-backup-{stamp}"
live_swapped = False

try:
    MYWS.write_text(myws)
    APP.write_text(app)
    BOARD.write_text(board)

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    built_js = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.js"))
    if "board?.projectId" not in built_js and "board.projectId" not in built_js:
        fail("board project fallback missing from built JS")

    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(DIST, staging)
    if LIVE.exists():
        if live_backup.exists():
            shutil.rmtree(live_backup)
        LIVE.rename(live_backup)
    staging.rename(LIVE)
    live_swapped = True

except Exception:
    for path in (MYWS, APP, BOARD):
        shutil.copy2(backup_root / path.name, path)
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
print("REVIEW_PROJECT_CONTEXT_BOARD_FALLBACK=YES")
print("MY_WORKSPACE_HANDOFF_FIXED=YES")
print("APP_TASK_HANDOFF_FIXED=YES")
print("TASK_BOARD_CONTEXT_VALIDATION_FIXED=YES")
print("BACKEND_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print("TCS_CHANGED=NO")
print("RAMZY_CHANGED=NO")
print("TASK_DETAILS_SCROLL_PATCHES_CHANGED=NO")
print("NO_BROWSER_QA=YES")
print("NO_SCREENSHOTS=YES")
print("PUSH=NO")
print(f"BACKUP={backup_root}")
