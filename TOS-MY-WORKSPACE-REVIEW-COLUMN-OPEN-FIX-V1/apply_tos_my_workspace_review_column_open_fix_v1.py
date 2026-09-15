from pathlib import Path
import json, shutil, subprocess, sys, time

PATCH = "TOS-MY-WORKSPACE-REVIEW-COLUMN-OPEN-FIX-V1"
MARKER = "TOS_MY_WORKSPACE_REVIEW_COLUMN_OPEN_FIX_V1"
ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
TARGET = FRONTEND / "src/pages/MyTaskWorkspace.jsx"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"


def fail(msg):
    raise RuntimeError(msg)


def run(cmd, cwd=None):
    subprocess.run(cmd, cwd=cwd, check=True)


for path in (FRONTEND, TARGET, MANIFEST):
    if not path.exists():
        fail(f"required path missing: {path}")

source = TARGET.read_text()
if MARKER in source:
    fail("patch already appears to be applied")

old_card = '''  const openTitle = task.projectId && onOpenTask
    ? () => onOpenTask(task)
    : canManagePersonalTask && onOpenSettings
      ? () => onOpenSettings(task)
      : null;'''
new_card = '''  // TOS_MY_WORKSPACE_REVIEW_COLUMN_OPEN_FIX_V1
  const resolvedProjectId = String(task?.projectId || task?.project?.id || "").trim();
  const openTitle = resolvedProjectId && onOpenTask
    ? () => onOpenTask(task.projectId ? task : { ...task, projectId: resolvedProjectId })
    : canManagePersonalTask && onOpenSettings
      ? () => onOpenSettings(task)
      : null;'''

old_open = '''  function openTask(task) {
    if (!task?.projectId || !task?.id) return;
    if (typeof onOpenTask === "function") {
      onOpenTask(task);
      return;
    }
    if (typeof onOpenProject !== "function") return;
    if (typeof window !== "undefined") {
      window.sessionStorage.setItem(pendingTaskStorageKey, JSON.stringify({ projectId: task.projectId, taskId: task.id, at: Date.now() }));
    }
    onOpenProject(task.projectId);
  }'''
new_open = '''  function openTask(task) {
    const projectId = String(task?.projectId || task?.project?.id || "").trim();
    const taskId = String(task?.id || "").trim();
    if (!projectId || !taskId) return;
    const normalizedTask = task?.projectId ? task : { ...task, projectId };
    if (typeof onOpenTask === "function") {
      onOpenTask(normalizedTask);
      return;
    }
    if (typeof onOpenProject !== "function") return;
    if (typeof window !== "undefined") {
      window.sessionStorage.setItem(pendingTaskStorageKey, JSON.stringify({ projectId, taskId, at: Date.now() }));
    }
    onOpenProject(projectId);
  }'''

if source.count(old_card) != 1:
    fail(f"card open-gate anchor count={source.count(old_card)}")
if source.count(old_open) != 1:
    fail(f"openTask anchor count={source.count(old_open)}")

updated = source.replace(old_card, new_card, 1).replace(old_open, new_open, 1)
for contract in (MARKER, 'task?.projectId || task?.project?.id', 'const normalizedTask = task?.projectId ? task : { ...task, projectId };'):
    if contract not in updated:
        fail(f"missing source contract: {contract}")

manifest = json.loads(MANIFEST.read_text())
frontend_runtime = manifest.get("frontend") or {}
DIST = Path(str(frontend_runtime.get("buildOutputDir") or FRONTEND / "dist"))
LIVE = Path(str(frontend_runtime.get("publishedBuildDir") or "/opt/apps/tamiyouz-front/build"))
if str(frontend_runtime.get("buildCommand") or "npm run build") != "npm run build":
    fail("unexpected frontend build command")

stamp = int(time.time())
backup_root = Path(f"/var/backups/tos-patches/my-workspace-review-open-v1-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
shutil.copy2(TARGET, backup_root / TARGET.name)
LIVE.parent.mkdir(parents=True, exist_ok=True)
staging = LIVE.parent / f"build.my-workspace-review-open-v1-staging-{stamp}"
live_backup = LIVE.parent / f"build.my-workspace-review-open-v1-backup-{stamp}"
live_swapped = False

try:
    TARGET.write_text(updated)
    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")
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
    shutil.copy2(backup_root / TARGET.name, TARGET)
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
print("MY_WORKSPACE_REVIEW_PROJECT_ID_FALLBACK=YES")
print("BACKEND_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print("TCS_CHANGED=NO")
print("RAMZY_CHANGED=NO")
print("NO_BROWSER_QA=YES")
print("NO_SCREENSHOTS=YES")
print("PUSH=NO")
print(f"BACKUP={backup_root}")
