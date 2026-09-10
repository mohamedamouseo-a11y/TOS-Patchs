from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import time
import urllib.request

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
BACKEND = ROOT / "backend"
PAGE = FRONTEND / "src/pages/MyTaskWorkspace.jsx"
TASKS_ROUTE = BACKEND / "src/routes/tasks.routes.js"
FILES_ROUTE = BACKEND / "src/routes/files.routes.js"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"
DIST = FRONTEND / "dist"

EXPECTED_BLOBS = {
    PAGE: "5694f8696dc7bc435437669faa9c9125589fe889",
    TASKS_ROUTE: "8d55b1eb4d99ec3b62ecf3fd6dad9eb5da17ac56",
    MANIFEST: "66a1659214dd90b162376310274be1b6689ac1d3",
}

FRONTEND_MARKER = "tos-my-workspace-attachment-cover-v1"
BACKEND_MARKER = "TOS_MY_WORKSPACE_ATTACHMENT_COVER_PREVIEW_V1"

SUMMARY_OLD = '''const myWorkspaceTaskSummarySelect = {
  id: true,
  title: true,
  description: true,
  status: true,
  approvalStatus: true,
  priority: true,
  dueDate: true,
  estimatedHours: true,
  blockedReason: true,
  projectId: true,
  personalOwnerId: true,
  assigneeId: true,
  createdAt: true,
  updatedAt: true,
  project: { select: { id: true, name: true } },
  assignees: { select: { userId: true }, orderBy: { createdAt: "asc" } },
};'''

SUMMARY_NEW = '''const myWorkspaceTaskSummarySelect = {
  id: true,
  title: true,
  description: true,
  status: true,
  approvalStatus: true,
  priority: true,
  dueDate: true,
  estimatedHours: true,
  blockedReason: true,
  projectId: true,
  personalOwnerId: true,
  assigneeId: true,
  createdAt: true,
  updatedAt: true,
  project: { select: { id: true, name: true } },
  assignees: { select: { userId: true }, orderBy: { createdAt: "asc" } },
  // TOS_MY_WORKSPACE_ATTACHMENT_COVER_PREVIEW_V1
  // One compact relation fetch: newest previewable image only, no browser N+1 task requests.
  files: {
    where: {
      deletedAt: null,
      mimeType: { startsWith: "image/" },
      fileAccessMode: { not: "DOWNLOAD_ONLY" },
    },
    select: { id: true, name: true, mimeType: true, createdAt: true },
    orderBy: { createdAt: "desc" },
    take: 1,
  },
};'''

SAFE_HEAD_OLD = '''function safeMyWorkspaceTask(task, orderMap = new Map(), currentUserId = null) {
  const isPersonalOwner = Boolean(currentUserId && task?.personalOwnerId === currentUserId);
  return {'''
SAFE_HEAD_NEW = '''function safeMyWorkspaceTask(task, orderMap = new Map(), currentUserId = null) {
  const isPersonalOwner = Boolean(currentUserId && task?.personalOwnerId === currentUserId);
  const coverAttachment = Array.isArray(task?.files) && task.files.length ? task.files[0] : null;
  return {'''

SAFE_TAIL_OLD = '''    project: task.project ? { id: task.project.id, name: task.project.name } : null,
    personalPosition: orderMap.get(task.id) ?? null,'''
SAFE_TAIL_NEW = '''    project: task.project ? { id: task.project.id, name: task.project.name } : null,
    coverAttachment: coverAttachment ? {
      id: coverAttachment.id,
      name: coverAttachment.name || "",
      mimeType: coverAttachment.mimeType || "image/*",
      createdAt: coverAttachment.createdAt || null,
      previewUrl: `/api/files/${encodeURIComponent(coverAttachment.id)}/preview`,
    } : null,
    personalPosition: orderMap.get(task.id) ?? null,'''

CARD_LOGIC_OLD = '''  const titleClass = "line-clamp-2 text-start text-sm font-black leading-6 text-blue-700 underline-offset-4 transition group-hover:underline dark:text-blue-300";

  return ('''
CARD_LOGIC_NEW = '''  const titleClass = "line-clamp-2 text-start text-sm font-black leading-6 text-blue-700 underline-offset-4 transition group-hover:underline dark:text-blue-300";
  const coverAttachment = task?.coverAttachment?.id ? task.coverAttachment : null;
  const coverPreviewUrl = coverAttachment?.previewUrl
    || (coverAttachment?.id ? `/api/files/${encodeURIComponent(coverAttachment.id)}/preview` : "");
  const [coverFailed, setCoverFailed] = useState(false);

  useEffect(() => {
    setCoverFailed(false);
  }, [coverAttachment?.id]);

  const coverPreview = coverAttachment && coverPreviewUrl && !coverFailed ? (
    <div className="relative grid min-h-[116px] max-h-[220px] place-items-center overflow-hidden bg-zinc-50 dark:bg-zinc-900">
      <img
        src={coverPreviewUrl}
        alt={coverAttachment.name || task.title || ""}
        loading="lazy"
        decoding="async"
        onError={() => setCoverFailed(true)}
        className="block max-h-[220px] w-full object-contain"
      />
    </div>
  ) : null;

  return ('''

CARD_ARTICLE_OLD = '''    <article className="group rounded-[16px] border border-zinc-100 bg-white px-2.5 py-2.5 shadow-sm shadow-zinc-200/35 transition hover:-translate-y-0.5 hover:border-amber-200 hover:shadow-md hover:shadow-amber-100/35 dark:border-white/10 dark:bg-zinc-950 dark:shadow-black/20 dark:hover:border-amber-400/40">
      <div className="flex items-start gap-2">'''
CARD_ARTICLE_NEW = '''    <article className="group rounded-[16px] border border-zinc-100 bg-white px-2.5 py-2.5 shadow-sm shadow-zinc-200/35 transition hover:-translate-y-0.5 hover:border-amber-200 hover:shadow-md hover:shadow-amber-100/35 dark:border-white/10 dark:bg-zinc-950 dark:shadow-black/20 dark:hover:border-amber-400/40">
      {coverPreview ? (
        openTitle ? (
          <button
            type="button"
            onClick={openTitle}
            className="tos-my-workspace-attachment-cover-v1 mb-2.5 block w-full overflow-hidden rounded-[14px] border border-zinc-100 bg-zinc-50 text-start shadow-inner transition hover:border-amber-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-400 dark:border-white/10 dark:bg-zinc-900 dark:hover:border-amber-400/35"
            title={isAr ? "فتح المهمة من معاينة التصميم" : "Open task from design preview"}
            aria-label={isAr ? `فتح المهمة: ${task.title || "—"}` : `Open task: ${task.title || "—"}`}
          >
            {coverPreview}
          </button>
        ) : (
          <div className="tos-my-workspace-attachment-cover-v1 mb-2.5 overflow-hidden rounded-[14px] border border-zinc-100 bg-zinc-50 shadow-inner dark:border-white/10 dark:bg-zinc-900">
            {coverPreview}
          </div>
        )
      ) : null}

      <div className="flex items-start gap-2">'''


def fail(message):
    raise RuntimeError(message)


def git_blob_sha(path):
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


def replace_once(source, old, new, label):
    count = source.count(old)
    if count != 1:
        fail(f"{label} marker count changed unexpectedly: {count}")
    return source.replace(old, new, 1)


def health_ok(url):
    try:
        with urllib.request.urlopen(url, timeout=3) as response:
            return 200 <= int(response.status) < 300
    except Exception:
        return False


def wait_health(url, attempts=30):
    for _ in range(attempts):
        if health_ok(url):
            return True
        time.sleep(1)
    return False


for path, expected in EXPECTED_BLOBS.items():
    if not path.exists():
        fail(f"required baseline file missing: {path}")
    actual = git_blob_sha(path)
    if actual != expected:
        fail(f"baseline changed for {path}: expected={expected} actual={actual}")

for command in ("node", "npm", "pm2"):
    if not shutil.which(command):
        fail(f"required command not found: {command}")

if not FILES_ROUTE.exists():
    fail(f"secure files route missing: {FILES_ROUTE}")
files_source = FILES_ROUTE.read_text()
if 'router.get("/:fileId/preview", asyncHandler(async (req, res, next) => {' not in files_source:
    fail("secure file preview endpoint missing")
if 'const file = await assertFileAccess(req.user' not in files_source:
    fail("secure file preview access guard missing")

manifest = json.loads(MANIFEST.read_text())
backend_runtime = manifest.get("backend") or {}
frontend_runtime = manifest.get("frontend") or {}
if manifest.get("application") != "TOS" or manifest.get("environment") != "production":
    fail("unexpected production runtime manifest")
if manifest.get("sourceRoot") != str(ROOT):
    fail("runtime sourceRoot does not match target")
if Path(str(backend_runtime.get("sourceDir") or "")) != BACKEND:
    fail("backend runtime sourceDir mismatch")
if Path(str(frontend_runtime.get("sourceDir") or "")) != FRONTEND:
    fail("frontend runtime sourceDir mismatch")
backend_pm2 = str(backend_runtime.get("pm2App") or "")
backend_health = str(backend_runtime.get("healthUrl") or "")
live = Path(str(frontend_runtime.get("publishedBuildDir") or ""))
if backend_pm2 != "tamiyouz-system":
    fail(f"unexpected backend PM2 app: {backend_pm2}")
if backend_health != "http://127.0.0.1:5006/health":
    fail(f"unexpected backend health URL: {backend_health}")
if live != Path("/opt/apps/tamiyouz-front/build"):
    fail(f"unexpected live frontend path: {live}")

backend_source = TASKS_ROUTE.read_text()
frontend_source = PAGE.read_text()
if BACKEND_MARKER in backend_source or FRONTEND_MARKER in frontend_source:
    fail("attachment cover preview V1 is already present")

for marker in [
    'router.get("/my-workspace", asyncHandler(async (req, res) => {',
    '...(summaryMode ? { select: myWorkspaceTaskSummarySelect } : { include: taskInclude }),',
    'summaryMode\n      ? safeMyWorkspaceTask(task, orderMap, req.user.id)',
]:
    if marker not in backend_source:
        fail(f"My Workspace backend contract marker missing: {marker}")

for marker in [
    'const data = await tasksApi.getMyWorkspace({ summary: true });',
    'function WorkspaceTaskCard({ task, ui, isAr, onOpenTask, onOpenSettings, canManagePersonalTask })',
    'const openTitle = task.projectId && onOpenTask',
    'formatPriorityLabel(priority, ui)',
    'due.label',
]:
    if marker not in frontend_source:
        fail(f"My Workspace frontend behavior marker missing: {marker}")

stamp = int(time.time())
backup_root = Path(f"/var/backups/tos-patches/my-workspace-attachment-cover-v1-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
backend_backup = backup_root / "tasks.routes.js"
frontend_backup = backup_root / "MyTaskWorkspace.jsx"
shutil.copy2(TASKS_ROUTE, backend_backup)
shutil.copy2(PAGE, frontend_backup)

live.parent.mkdir(parents=True, exist_ok=True)
staging = live.parent / f"build.my-workspace-attachment-cover-v1-staging-{stamp}"
live_backup = live.parent / f"build.my-workspace-attachment-cover-v1-backup-{stamp}"
backend_restarted = False
live_swapped = False

try:
    backend_updated = replace_once(backend_source, SUMMARY_OLD, SUMMARY_NEW, "My Workspace summary select")
    backend_updated = replace_once(backend_updated, SAFE_HEAD_OLD, SAFE_HEAD_NEW, "safeMyWorkspaceTask header")
    backend_updated = replace_once(backend_updated, SAFE_TAIL_OLD, SAFE_TAIL_NEW, "safeMyWorkspaceTask cover payload")

    frontend_updated = replace_once(frontend_source, CARD_LOGIC_OLD, CARD_LOGIC_NEW, "WorkspaceTaskCard cover logic")
    frontend_updated = replace_once(frontend_updated, CARD_ARTICLE_OLD, CARD_ARTICLE_NEW, "WorkspaceTaskCard cover render")

    if backend_updated.count(BACKEND_MARKER) != 1:
        fail("backend runtime marker count invalid")
    if frontend_updated.count(FRONTEND_MARKER) != 2:
        fail("frontend runtime marker count invalid")
    if 'mimeType: { startsWith: "image/" }' not in backend_updated or 'take: 1' not in backend_updated:
        fail("latest-image summary query missing")
    if 'previewUrl: `/api/files/${encodeURIComponent(coverAttachment.id)}/preview`' not in backend_updated:
        fail("secure preview URL missing")

    for marker in [
        'const data = await tasksApi.getMyWorkspace({ summary: true });',
        'formatPriorityLabel(priority, ui)',
        'due.label',
        'onClick={() => onOpenSettings(task)}',
    ]:
        if marker not in frontend_updated:
            fail(f"protected frontend behavior changed: {marker}")

    TASKS_ROUTE.write_text(backend_updated)
    PAGE.write_text(frontend_updated)

    run(["node", "--check", str(TASKS_ROUTE)], cwd=BACKEND)
    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    built_js = "\n".join(path.read_text(errors="ignore") for path in DIST.rglob("*.js"))
    if FRONTEND_MARKER not in built_js:
        fail("attachment cover runtime marker missing from built JS")

    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(DIST, staging)
    if live.exists():
        live.rename(live_backup)
    staging.rename(live)
    live_swapped = True

    run(["pm2", "restart", backend_pm2])
    backend_restarted = True
    if not wait_health(backend_health):
        fail(f"backend health failed after restart: {backend_health}")

    live_js = "\n".join(path.read_text(errors="ignore") for path in live.rglob("*.js"))
    if FRONTEND_MARKER not in live_js:
        fail("attachment cover runtime marker missing from live JS")

    print("PASS/FAIL=PASS")
    print("BACKEND_CHECK=PASS")
    print("BACKEND_RESTART=PASS")
    print("BACKEND_HEALTH=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("MY_WORKSPACE_ATTACHMENT_COVER_V1_RUNTIME=YES")
    print("MY_WORKSPACE_CARD_COVER=REAL_IMAGE_ATTACHMENT")
    print("MY_WORKSPACE_CARD_COVER_SELECTION=LATEST_PREVIEWABLE_IMAGE")
    print("MY_WORKSPACE_CARD_NO_IMAGE_FALLBACK=PRESERVED")
    print("MY_WORKSPACE_CARD_OPEN_BEHAVIOR=PRESERVED")
    print("MY_WORKSPACE_API_CONTRACT_CHANGE=ADDITIVE_COVER_METADATA_ONLY")
    print("MY_WORKSPACE_BROWSER_N_PLUS_ONE_REQUESTS=NO")
    print("MY_WORKSPACE_COVER_IMAGE_REQUESTS=LAZY_PER_VISIBLE_COVER")
    print("MY_WORKSPACE_STATUS_LOGIC_CHANGED=NO")
    print("MY_WORKSPACE_PRIORITY_LOGIC_CHANGED=NO")
    print("MY_WORKSPACE_DUE_DATE_LOGIC_CHANGED=NO")
    print("MY_WORKSPACE_PROJECT_LOGIC_CHANGED=NO")
    print("TASK_UPLOAD_LOGIC_CHANGED=NO")
    print("DATABASE_SCHEMA_CHANGED=NO")
    print("TWS_CHANGED=NO")
    print("SLA_CHANGED=NO")
    print("RAMZY_CHANGED=NO")
    print("TCS_CHANGED=NO")
    print(f"SOURCE_BACKUP={backup_root}")
    print(f"LIVE_BACKUP={live_backup if live_backup.exists() else 'N/A'}")
    print("STATUS=READY")

except Exception as exc:
    try:
        shutil.copy2(backend_backup, TASKS_ROUTE)
    except Exception as restore_exc:
        print(f"ROLLBACK_BACKEND_SOURCE_ERROR={restore_exc}")
    try:
        shutil.copy2(frontend_backup, PAGE)
    except Exception as restore_exc:
        print(f"ROLLBACK_FRONTEND_SOURCE_ERROR={restore_exc}")

    try:
        if live_swapped:
            if live.exists():
                shutil.rmtree(live)
            if live_backup.exists():
                live_backup.rename(live)
    except Exception as restore_exc:
        print(f"ROLLBACK_LIVE_FRONTEND_ERROR={restore_exc}")

    try:
        if staging.exists():
            shutil.rmtree(staging)
    except Exception as cleanup_exc:
        print(f"ROLLBACK_STAGING_CLEANUP_ERROR={cleanup_exc}")

    if backend_restarted:
        try:
            run(["pm2", "restart", backend_pm2])
            print("ROLLBACK_BACKEND_RESTART=PASS" if wait_health(backend_health) else "ROLLBACK_BACKEND_RESTART=HEALTH_FAIL")
        except Exception as restart_exc:
            print(f"ROLLBACK_BACKEND_RESTART_ERROR={restart_exc}")

    print("PASS/FAIL=FAIL")
    print(f"ERROR={exc}")
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("STATUS=STOPPED")
    sys.exit(1)
