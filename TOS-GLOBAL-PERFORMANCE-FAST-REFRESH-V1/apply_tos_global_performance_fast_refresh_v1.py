from pathlib import Path
import hashlib
import re
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
APP = ROOT / "frontend/src/App.jsx"
PROJECTS_HOOK = ROOT / "frontend/src/hooks/useProjects.js"
CHAT = ROOT / "frontend/src/components/ChatPanel.jsx"
TCS_STYLE = ROOT / "frontend/src/components/tcsFlagshipV1.css"
FRONTEND = ROOT / "frontend"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_APP_BLOB_SHA = "3629bc295294c38e1dd5825583f205d4548845f5"
EXPECTED_PROJECTS_HOOK_BLOB_SHA = "41f231add3240b8c57d834523669d2dc0623e25b"
EXPECTED_CHAT_SHA256 = "9618610036d00b8699c120f6c40773cf0c31d671101c01b9a6efb2f75d807c13"
EXPECTED_TCS_STYLE_SHA256 = "b48c2af2bde12b297202e134b00aab842f342d60f037aa5192b965906497c65a"

print("RUNNING=TOS_GLOBAL_PERFORMANCE_FAST_REFRESH_V1")


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


def fail(message: str):
    print("PASS/FAIL=FAIL")
    print("ERROR=" + str(message))
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("FAST_REFRESH_RUNTIME=NO")
    sys.exit(1)


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        fail(f"{label} anchor mismatch: {count}")
    return source.replace(old, new, 1)


if ROOT.resolve() == Path("/"):
    fail("unsafe ROOT")
for path in (APP, PROJECTS_HOOK, CHAT, TCS_STYLE, FRONTEND, LIVE_PARENT):
    if not path.exists():
        fail(f"required path missing: {path}")

if git_blob_sha(APP) != EXPECTED_APP_BLOB_SHA:
    fail(f"App.jsx baseline mismatch: {git_blob_sha(APP)}")
if git_blob_sha(PROJECTS_HOOK) != EXPECTED_PROJECTS_HOOK_BLOB_SHA:
    fail(f"useProjects.js baseline mismatch: {git_blob_sha(PROJECTS_HOOK)}")
if sha256(CHAT) != EXPECTED_CHAT_SHA256:
    fail(f"ChatPanel V1.6 baseline mismatch: {sha256(CHAT)}")
if sha256(TCS_STYLE) != EXPECTED_TCS_STYLE_SHA256:
    fail(f"TCS style V1.6 baseline mismatch: {sha256(TCS_STYLE)}")

original_app = APP.read_text(encoding="utf-8")
original_hook = PROJECTS_HOOK.read_text(encoding="utf-8")

# Guard the exact refresh bottleneck: projects are globally blocking several pages,
# while Ramzy / notification / help-center payloads are eagerly included in the entry bundle.
for token in (
    'const PROJECT_LOADING_BLOCKED_PAGES = new Set(["dashboard", "teamPerformance", "projects", "tasks", "myWorkspace", "chat", "files", "tws", "tgws"]);',
    'const { projects, activeProjectId, setActiveProjectId, loading, error, createProject, updateProject, archiveProject, restoreProject, reload } = useProjects();',
    '{loading && PROJECT_LOADING_BLOCKED_PAGES.has(active) && <SystemPageLoading label={tr.loading} />}',
    '{!loading && active === "dashboard" && (',
    '<RamzyAssistant user={user} projectId={activeProjectId || ""} />',
):
    if token not in original_app:
        fail(f"required App refresh token missing: {token[:80]}")
for token in ('api.projects.list({ summary: true })', 'useEffect(() => { loadProjects({ showLoading: true }); }, []);'):
    if token not in original_hook:
        fail(f"required useProjects token missing: {token}")

app = original_app

# Split heavy, non-critical global UI out of the initial JS entry bundle.
app = replace_once(
    app,
    'import { RamzyAssistant } from "./components/RamzyAssistant";',
    'const RamzyAssistant = lazy(() => import("./components/RamzyAssistant").then(mod => ({ default: mod.RamzyAssistant })));',
    "lazy Ramzy import",
)
app = replace_once(
    app,
    'import { TncNotificationCenter } from "./components/TncNotificationCenter";',
    'const TncNotificationCenter = lazy(() => import("./components/TncNotificationCenter").then(mod => ({ default: mod.TncNotificationCenter })));',
    "lazy notification center import",
)
app = replace_once(
    app,
    'import { TeamPerformanceHelpCenter } from "./components/performance/TeamPerformanceHelpCenter";',
    'const TeamPerformanceHelpCenter = lazy(() => import("./components/performance/TeamPerformanceHelpCenter").then(mod => ({ default: mod.TeamPerformanceHelpCenter })));',
    "lazy help center import",
)

old_help_return = '''  return (\n    <TeamPerformanceHelpCenter\n      open={open}\n      onClose={() => setOpen(false)}\n      lang={lang}\n      initialArticle={article}\n    />\n  );'''
new_help_return = '''  return (\n    <Suspense fallback={null}>\n      <TeamPerformanceHelpCenter\n        open={open}\n        onClose={() => setOpen(false)}\n        lang={lang}\n        initialArticle={article}\n      />\n    </Suspense>\n  );'''
app = replace_once(app, old_help_return, new_help_return, "help center suspense")

# User-scoped stale-while-revalidate project summary cache.
app = replace_once(
    app,
    'const { projects, activeProjectId, setActiveProjectId, loading, error, createProject, updateProject, archiveProject, restoreProject, reload } = useProjects();',
    'const { projects, activeProjectId, setActiveProjectId, loading, error, createProject, updateProject, archiveProject, restoreProject, reload } = useProjects(user?.id);',
    "user-scoped project cache hook",
)

# Dashboard shell must paint immediately on cold refresh; project data hydrates in the background.
app = replace_once(
    app,
    '{loading && PROJECT_LOADING_BLOCKED_PAGES.has(active) && <SystemPageLoading label={tr.loading} />}',
    '{loading && projects.length === 0 && PROJECT_LOADING_BLOCKED_PAGES.has(active) && active !== "dashboard" && <SystemPageLoading label={tr.loading} />}',
    "nonblocking dashboard refresh",
)
app = replace_once(app, '{!loading && active === "dashboard" && (', '{active === "dashboard" && (', "dashboard immediate paint")

# Lazy global overlays should never hold the first paint.
app = replace_once(
    app,
    '{tncOpen && <TncNotificationCenter onClose={() => setTncOpen(false)} onOpenItem={openTncItem} />}',
    '{tncOpen && <Suspense fallback={null}><TncNotificationCenter onClose={() => setTncOpen(false)} onOpenItem={openTncItem} /></Suspense>}',
    "notification center suspense",
)
app = replace_once(
    app,
    '<RamzyAssistant user={user} projectId={activeProjectId || ""} />',
    '<Suspense fallback={null}><RamzyAssistant user={user} projectId={activeProjectId || ""} /></Suspense>',
    "Ramzy suspense",
)

hook = r'''import { useEffect, useRef, useState } from "react";
import { api } from "../lib/api";
import { getErrorMessage } from "../lib/errors";

const PROJECT_SUMMARY_CACHE_PREFIX = "tos.projects.summary.fast-refresh.v1";
const PROJECT_SUMMARY_CACHE_MAX_AGE_MS = 30 * 60 * 1000;

function projectCacheKey(userId = "") {
  return `${PROJECT_SUMMARY_CACHE_PREFIX}.${String(userId || "anonymous")}`;
}

function readProjectCache(userId = "") {
  if (typeof window === "undefined") return { hit: false, projects: [] };
  try {
    const raw = window.sessionStorage.getItem(projectCacheKey(userId));
    if (!raw) return { hit: false, projects: [] };
    const parsed = JSON.parse(raw);
    const savedAt = Number(parsed?.savedAt || 0);
    const projects = Array.isArray(parsed?.projects) ? parsed.projects : null;
    if (!projects || !savedAt || Date.now() - savedAt > PROJECT_SUMMARY_CACHE_MAX_AGE_MS) {
      window.sessionStorage.removeItem(projectCacheKey(userId));
      return { hit: false, projects: [] };
    }
    return { hit: true, projects };
  } catch {
    return { hit: false, projects: [] };
  }
}

function writeProjectCache(userId = "", projects = []) {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.setItem(projectCacheKey(userId), JSON.stringify({ savedAt: Date.now(), projects }));
  } catch {
    // Cache is optional; API remains the source of truth.
  }
}

export function useProjects(userId = "") {
  const initialCacheRef = useRef(null);
  if (initialCacheRef.current === null) initialCacheRef.current = readProjectCache(userId);
  const initialCache = initialCacheRef.current;
  const [projects, setProjects] = useState(() => initialCache.projects);
  const [activeProjectId, setActiveProjectId] = useState(null);
  const [loading, setLoading] = useState(() => !initialCache.hit);
  const [error, setError] = useState("");

  async function loadProjects({ showLoading = false } = {}) {
    try {
      setError("");
      if (showLoading) setLoading(true);
      const data = await api.projects.list({ summary: true });
      const next = Array.isArray(data) ? data : [];
      setProjects(next);
      writeProjectCache(userId, next);
      setActiveProjectId((old) => next.some((project) => project.id === old) ? old : null);
    } catch (err) {
      setError(getErrorMessage(err, "تعذر تحميل المشاريع."));
    } finally {
      setLoading(false);
    }
  }

  function commitProjects(updater) {
    setProjects((previous) => {
      const next = typeof updater === "function" ? updater(previous) : updater;
      writeProjectCache(userId, next);
      return next;
    });
  }

  async function createProject(payload) {
    const project = await api.projects.create(payload);
    commitProjects((prev) => [project, ...prev]);
    setActiveProjectId(project.id);
    return project;
  }

  async function updateProject(projectId, payload) {
    const project = await api.projects.update(projectId, payload);
    commitProjects((prev) => prev.map((item) => item.id === projectId ? project : item));
    return project;
  }

  async function archiveProject(projectId) {
    const project = await api.projects.archive(projectId);
    await loadProjects({ showLoading: false });
    return project;
  }

  async function restoreProject(projectId) {
    const project = await api.projects.restore(projectId);
    await loadProjects({ showLoading: false });
    return project;
  }

  useEffect(() => {
    const cached = readProjectCache(userId);
    if (cached.hit) {
      setProjects(cached.projects);
      setLoading(false);
      loadProjects({ showLoading: false });
    } else {
      setProjects([]);
      setLoading(true);
      loadProjects({ showLoading: true });
    }
  }, [userId]);

  return { projects, activeProjectId, setActiveProjectId, loading, error, reload: loadProjects, createProject, updateProject, archiveProject, restoreProject };
}
'''

for token in (
    'lazy(() => import("./components/RamzyAssistant")',
    'lazy(() => import("./components/TncNotificationCenter")',
    'lazy(() => import("./components/performance/TeamPerformanceHelpCenter")',
    'useProjects(user?.id)',
    'active !== "dashboard"',
    '<Suspense fallback={null}><RamzyAssistant',
):
    if token not in app:
        fail(f"post-transform App token missing: {token}")
for token in (
    'PROJECT_SUMMARY_CACHE_PREFIX',
    'window.sessionStorage',
    'api.projects.list({ summary: true })',
    'loadProjects({ showLoading: false })',
):
    if token not in hook:
        fail(f"post-transform useProjects token missing: {token}")

try:
    APP.write_text(app, encoding="utf-8")
    PROJECTS_HOOK.write_text(hook, encoding="utf-8")
except Exception as exc:
    APP.write_text(original_app, encoding="utf-8")
    PROJECTS_HOOK.write_text(original_hook, encoding="utf-8")
    fail(f"source transform failed and rolled back: {exc}")

build = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, text=True, capture_output=True)
if build.returncode != 0:
    print(build.stdout[-10000:])
    print(build.stderr[-10000:])
    APP.write_text(original_app, encoding="utf-8")
    PROJECTS_HOOK.write_text(original_hook, encoding="utf-8")
    fail("frontend build failed; App/useProjects rolled back")

if not DIST.exists():
    APP.write_text(original_app, encoding="utf-8")
    PROJECTS_HOOK.write_text(original_hook, encoding="utf-8")
    fail("frontend dist missing after successful build")

# Build/runtime verification.
for marker in (
    b"tos.projects.summary.fast-refresh.v1",
    b"tcs-desktop-window",
    b"data-tcs-ramzy-collision-sync",
    b"tcs-v16-voice-button",
):
    if tree_count(DIST, marker) < 1:
        APP.write_text(original_app, encoding="utf-8")
        PROJECTS_HOOK.write_text(original_hook, encoding="utf-8")
        fail(f"runtime marker missing from dist: {marker.decode(errors='ignore')}")

# Verify Ramzy code is code-split away from the main entry chunk.
index_html = (DIST / "index.html").read_text(encoding="utf-8", errors="ignore")
entry_match = re.search(r'<script[^>]+type="module"[^>]+src="([^"]+\.js)"', index_html)
if not entry_match:
    entry_match = re.search(r'<script[^>]+src="([^"]+\.js)"[^>]+type="module"', index_html)
if not entry_match:
    APP.write_text(original_app, encoding="utf-8")
    PROJECTS_HOOK.write_text(original_hook, encoding="utf-8")
    fail("could not identify Vite main entry chunk")
entry_rel = entry_match.group(1).lstrip("/")
entry_path = DIST / entry_rel
if not entry_path.exists():
    APP.write_text(original_app, encoding="utf-8")
    PROJECTS_HOOK.write_text(original_hook, encoding="utf-8")
    fail(f"main entry chunk missing: {entry_rel}")
entry_bytes = entry_path.read_bytes()
if b"tos.ramzy.position" in entry_bytes:
    APP.write_text(original_app, encoding="utf-8")
    PROJECTS_HOOK.write_text(original_hook, encoding="utf-8")
    fail("Ramzy implementation still present in main entry chunk")
if tree_count(DIST / "assets", b"tos.ramzy.position") < 1:
    APP.write_text(original_app, encoding="utf-8")
    PROJECTS_HOOK.write_text(original_hook, encoding="utf-8")
    fail("Ramzy lazy chunk marker missing")

# Safe live deployment using candidate + atomic rename, never deleting the live directory.
stamp = int(time.time())
candidate = LIVE_PARENT / f"build.fast-refresh-v1-candidate-{stamp}"
backup = LIVE_PARENT / f"build.fast-refresh-v1-backup-{stamp}"
if candidate.exists() or backup.exists():
    APP.write_text(original_app, encoding="utf-8")
    PROJECTS_HOOK.write_text(original_hook, encoding="utf-8")
    fail("candidate/backup path collision")

try:
    shutil.copytree(DIST, candidate)
    if not (candidate / "index.html").exists():
        raise RuntimeError("candidate index.html missing")
    if LIVE.exists():
        LIVE.rename(backup)
    candidate.rename(LIVE)
except Exception as exc:
    try:
        if not LIVE.exists() and backup.exists():
            backup.rename(LIVE)
    except Exception:
        pass
    APP.write_text(original_app, encoding="utf-8")
    PROJECTS_HOOK.write_text(original_hook, encoding="utf-8")
    fail(f"live deploy failed and rollback attempted: {exc}")

print("PASS/FAIL=PASS")
print("BUILD_RESULT=PASS")
print("LIVE_DEPLOY=PASS")
print("FAST_REFRESH_RUNTIME=YES")
print("DASHBOARD_FIRST_PAINT=NON_BLOCKING")
print("PROJECT_SUMMARY_CACHE=USER_SCOPED_SESSION_SWR")
print("PROJECT_API_SOURCE_OF_TRUTH=PRESERVED")
print("PROJECT_BACKGROUND_REVALIDATION=YES")
print("RAMZY_INITIAL_BUNDLE=LAZY_SPLIT")
print("NOTIFICATION_CENTER_INITIAL_BUNDLE=LAZY_SPLIT")
print("HELP_CENTER_INITIAL_BUNDLE=LAZY_SPLIT")
print("AUTH_FLOW_CHANGED=NO")
print("TCS_V1_6_PRESERVED=YES")
print("TCS_WINDOW_BEHAVIOR_CHANGED=NO")
print("RAMZY_BEHAVIOR_CHANGED=NO")
print("API_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print(f"APP_SHA256={sha256(APP)}")
print(f"PROJECTS_HOOK_SHA256={sha256(PROJECTS_HOOK)}")
print(f"ENTRY_CHUNK={entry_rel}")
print(f"ENTRY_CHUNK_BYTES={entry_path.stat().st_size}")
print(f"LIVE_BACKUP={backup}")
print("STATUS=READY")
