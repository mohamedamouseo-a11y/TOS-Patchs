#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path("/var/www/TOS")
EXPECTED_HEAD = "293280da438adb8f8d9a8a821fe29e1deff41dd1"
TARGET = "frontend/src/App.jsx"
EXPECTED_TARGET_BLOB = "930f4da68dd9fcf021b967576e3edee2b1cbd630"

EXPECTED_PRE_MODIFIED = {
    "backend/src/routes/files.routes.js",
    "backend/src/routes/tasks.routes.js",
    "backend/src/routes/userProfile.routes.js",
    "backend/src/routes/users.routes.js",
    "backend/src/services/companyDepartments.service.js",
    "backend/src/utils/sanitize.js",
    "frontend/src/App.jsx",
    "frontend/src/lib/api.js",
    "frontend/src/pages/MyTaskWorkspace.jsx",
    "frontend/src/pages/TeamPage.jsx",
}

EXPECTED_BLOBS = {
    "backend/src/routes/files.routes.js": "12684b4f617766736dcc298a4c371143c000fca9",
    "backend/src/routes/tasks.routes.js": "805d70cead79aa0d225f9ba7ce63fbcafdfc8a8e",
    "backend/src/routes/users.routes.js": "2d65febb608d33aac2077e86eb70198feaaf50f6",
    "backend/src/services/companyDepartments.service.js": "c6d0979f71564f84293a72b05c5f142775d13ce9",
    "frontend/src/App.jsx": EXPECTED_TARGET_BLOB,
    "frontend/src/lib/api.js": "d5fa521cd22495237ab41e1ebb463485d587ef6d",
    "frontend/src/pages/MyTaskWorkspace.jsx": "e8a770c87264173c2c2925722c6bf408353bdf84",
    "frontend/src/pages/TeamPage.jsx": "e9e098e3a2e7ac7070ed6c6d6d6c674573a9a222",
}

def run(*args):
    return subprocess.check_output(list(args), cwd=ROOT, text=True).strip()

def git_blob(rel):
    return run("git", "hash-object", str(ROOT / rel))

def modified():
    out = run("git", "diff", "--name-only")
    return {line.strip() for line in out.splitlines() if line.strip()}

def staged():
    out = run("git", "diff", "--cached", "--name-only")
    return {line.strip() for line in out.splitlines() if line.strip()}

def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}_MATCH_COUNT expected=1 actual={count}")
    return text.replace(old, new, 1)

def guard_state():
    head = run("git", "rev-parse", "HEAD")
    if head != EXPECTED_HEAD:
        raise RuntimeError(f"HEAD_MISMATCH expected={EXPECTED_HEAD} actual={head}")
    current_modified = modified()
    if current_modified != EXPECTED_PRE_MODIFIED:
        raise RuntimeError("MODIFIED_SET_MISMATCH expected=" + ",".join(sorted(EXPECTED_PRE_MODIFIED)) + " actual=" + ",".join(sorted(current_modified)))
    current_staged = staged()
    if current_staged:
        raise RuntimeError("STAGED_FILES_PRESENT=" + ",".join(sorted(current_staged)))
    for rel, expected in EXPECTED_BLOBS.items():
        actual = git_blob(rel)
        if actual != expected:
            raise RuntimeError(f"BLOB_MISMATCH {rel}: expected={expected} actual={actual}")

    profile = (ROOT / "backend/src/routes/userProfile.routes.js").read_text(encoding="utf-8")
    for marker in (
        'const dataMatch = avatarUrl.match(/^data:image\\/(png|jpeg|jpg|webp);base64,(.+)$/is);',
        "return res.send(buffer);",
        "return res.redirect(302, avatarUrl);",
    ):
        if marker not in profile:
            raise RuntimeError(f"PHASE3_1_MARKER_MISSING {marker}")

    sanitize = (ROOT / "backend/src/utils/sanitize.js").read_text(encoding="utf-8")
    for marker in (
        "function compactChatAvatarUrl(user) {",
        'if (!/^data:image\\//i.test(avatarUrl)) return avatarUrl;',
        'return `/api/users/${encodeURIComponent(user.id)}/avatar`;',
        "avatar: compactChatAvatarUrl(user),",
    ):
        if marker not in sanitize:
            raise RuntimeError(f"PHASE4_MARKER_MISSING {marker}")

    tasks = (ROOT / "backend/src/routes/tasks.routes.js").read_text(encoding="utf-8")
    for marker in (
        "const myWorkspaceTaskSummarySelect = {",
        "function safeMyWorkspaceTask(task, orderMap = new Map(), currentUserId = null) {",
        'const summaryMode = req.query.summary === "1" || req.query.summary === "true";',
        "...(summaryMode ? { select: myWorkspaceTaskSummarySelect } : { include: taskInclude }),",
    ):
        if marker not in tasks:
            raise RuntimeError(f"PHASE5_MARKER_MISSING {marker}")

    workspace = (ROOT / "frontend/src/pages/MyTaskWorkspace.jsx").read_text(encoding="utf-8")
    if "const data = await tasksApi.getMyWorkspace({ summary: true });" not in workspace:
        raise RuntimeError("PHASE5_FRONTEND_MARKER_MISSING")

def build_change():
    path = ROOT / TARGET
    text = path.read_text(encoding="utf-8")

    replacements = []
    replacements.append((
        'import { ChatPanel } from "./components/ChatPanel";',
        'const ChatPanel = lazy(() => import("./components/ChatPanel").then(mod => ({ default: mod.ChatPanel })));',
        "CHAT_IMPORT",
    ))
    replacements.append((
        'import { DesignQueuePage } from "./pages/DesignQueuePage";',
        'const DesignQueuePage = lazy(() => import("./pages/DesignQueuePage").then(mod => ({ default: mod.DesignQueuePage })));',
        "DESIGN_QUEUE_IMPORT",
    ))
    replacements.append((
        'import { ProjectsPage } from "./pages/ProjectsPage";',
        'const ProjectsPage = lazy(() => import("./pages/ProjectsPage").then(mod => ({ default: mod.ProjectsPage })));',
        "PROJECTS_IMPORT",
    ))
    replacements.append((
        '''        <ChatPanelErrorBoundary key={`central-embed:${user?.id || "guest"}`}>
          <ChatPanel user={user} project={null} projectId="" projectName="" />
        </ChatPanelErrorBoundary>''',
        '''        <ChatPanelErrorBoundary key={`central-embed:${user?.id || "guest"}`}>
          <Suspense fallback={<div className="grid h-full place-items-center text-sm font-bold text-muted">{tr.loading ?? "Loading..."}</div>}>
            <ChatPanel user={user} project={null} projectId="" projectName="" />
          </Suspense>
        </ChatPanelErrorBoundary>''',
        "CENTRAL_CHAT_SUSPENSE",
    ))
    replacements.append((
        '''            {active === "designQueue" && hasDesignQueueAccess && (
              <DesignQueuePage user={user} projects={projects || []} />
            )}''',
        '''            {active === "designQueue" && hasDesignQueueAccess && (
              <Suspense fallback={<div className="p-6 text-sm font-bold text-muted">{tr.loading ?? "Loading..."}</div>}>
                <DesignQueuePage user={user} projects={projects || []} />
              </Suspense>
            )}''',
        "DESIGN_QUEUE_SUSPENSE",
    ))
    replacements.append((
        '''            {!loading && active === "projects" && (
              <ProjectsPage''',
        '''            {!loading && active === "projects" && (
              <Suspense fallback={<div className="p-6 text-sm font-bold text-muted">{tr.loading ?? "Loading..."}</div>}>
                <ProjectsPage''',
        "PROJECTS_SUSPENSE_OPEN",
    ))
    replacements.append((
        '''                onNavigateHome={() => setActive("dashboard")}
              />
            )}''',
        '''                  onNavigateHome={() => setActive("dashboard")}
                />
              </Suspense>
            )}''',
        "PROJECTS_SUSPENSE_CLOSE",
    ))
    replacements.append((
        '''            {!loading && active === "chat" && (
              <ChatPanelErrorBoundary key={`${activeProjectId || "no-project"}:${user?.id || "guest"}`}>
                <ChatPanel user={user} project={activeProject} projectId={activeProjectId || ""} projectName={activeProject?.name || ""} />
              </ChatPanelErrorBoundary>
            )}''',
        '''            {!loading && active === "chat" && (
              <ChatPanelErrorBoundary key={`${activeProjectId || "no-project"}:${user?.id || "guest"}`}>
                <Suspense fallback={<div className="p-6 text-sm font-bold text-muted">{tr.loading ?? "Loading..."}</div>}>
                  <ChatPanel user={user} project={activeProject} projectId={activeProjectId || ""} projectName={activeProject?.name || ""} />
                </Suspense>
              </ChatPanelErrorBoundary>
            )}''',
        "CHAT_ROUTE_SUSPENSE",
    ))

    for old, new, label in replacements:
        text = replace_once(text, old, new, label)

    for forbidden in (
        'import { ChatPanel } from "./components/ChatPanel";',
        'import { DesignQueuePage } from "./pages/DesignQueuePage";',
        'import { ProjectsPage } from "./pages/ProjectsPage";',
    ):
        if forbidden in text:
            raise RuntimeError(f"STATIC_IMPORT_REMAINS {forbidden}")

    for marker in (
        'const ChatPanel = lazy(() => import("./components/ChatPanel")',
        'const DesignQueuePage = lazy(() => import("./pages/DesignQueuePage")',
        'const ProjectsPage = lazy(() => import("./pages/ProjectsPage")',
    ):
        if marker not in text:
            raise RuntimeError(f"LAZY_IMPORT_MISSING {marker}")
    return text

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if args.check == args.apply:
        parser.error("use exactly one of --check or --apply")

    guard_state()
    content = build_change()
    print(f"PHASE6_TARGET={TARGET}")
    print("PHASE6_LAZY_COMPONENTS=ProjectsPage,DesignQueuePage,ChatPanel")

    if args.check:
        print("PHASE6_PATCH_CHECK=PASS")
        return 0

    path = ROOT / TARGET
    tmp = path.with_name(path.name + ".phase6.tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)
    print(f"UPDATED {TARGET} blob={git_blob(TARGET)}")
    print("PHASE6_PATCH_APPLIED=PASS")
    return 0

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"PHASE6_PATCH_ERROR={exc}", file=sys.stderr)
        raise SystemExit(1)
