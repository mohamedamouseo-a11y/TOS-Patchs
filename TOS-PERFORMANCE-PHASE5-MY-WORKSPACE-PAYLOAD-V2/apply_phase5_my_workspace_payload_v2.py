#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path("/var/www/TOS")
EXPECTED_HEAD = "293280da438adb8f8d9a8a821fe29e1deff41dd1"

EXPECTED_BLOBS = {
    "backend/src/routes/files.routes.js": "12684b4f617766736dcc298a4c371143c000fca9",
    "backend/src/routes/users.routes.js": "2d65febb608d33aac2077e86eb70198feaaf50f6",
    "backend/src/services/companyDepartments.service.js": "c6d0979f71564f84293a72b05c5f142775d13ce9",
    "frontend/src/App.jsx": "930f4da68dd9fcf021b967576e3edee2b1cbd630",
    "frontend/src/lib/api.js": "d5fa521cd22495237ab41e1ebb463485d587ef6d",
    "frontend/src/pages/TeamPage.jsx": "e9e098e3a2e7ac7070ed6c6d6d6c674573a9a222",
}

EXPECTED_PRE_MODIFIED = {
    "backend/src/routes/files.routes.js",
    "backend/src/routes/userProfile.routes.js",
    "backend/src/routes/users.routes.js",
    "backend/src/services/companyDepartments.service.js",
    "backend/src/utils/sanitize.js",
    "frontend/src/App.jsx",
    "frontend/src/lib/api.js",
    "frontend/src/pages/TeamPage.jsx",
}

BACKEND_TARGET = "backend/src/routes/tasks.routes.js"
FRONTEND_TARGET = "frontend/src/pages/MyTaskWorkspace.jsx"
PROFILE_ROUTE = "backend/src/routes/userProfile.routes.js"
SANITIZE = "backend/src/utils/sanitize.js"


def run(*args):
    return subprocess.check_output(list(args), cwd=ROOT, text=True).strip()


def git_blob(rel):
    return run("git", "hash-object", str(ROOT / rel))


def tracked_modified():
    output = run("git", "diff", "--name-only")
    return {line.strip() for line in output.splitlines() if line.strip()}


def staged_modified():
    output = run("git", "diff", "--cached", "--name-only")
    return {line.strip() for line in output.splitlines() if line.strip()}


def guard_state():
    head = run("git", "rev-parse", "HEAD")
    if head != EXPECTED_HEAD:
        raise RuntimeError(f"HEAD_MISMATCH expected={EXPECTED_HEAD} actual={head}")

    modified = tracked_modified()
    if modified != EXPECTED_PRE_MODIFIED:
        raise RuntimeError(
            "MODIFIED_SET_MISMATCH expected="
            + ",".join(sorted(EXPECTED_PRE_MODIFIED))
            + " actual="
            + ",".join(sorted(modified))
        )

    staged = staged_modified()
    if staged:
        raise RuntimeError("STAGED_FILES_PRESENT=" + ",".join(sorted(staged)))

    for rel, expected in EXPECTED_BLOBS.items():
        actual = git_blob(rel)
        if actual != expected:
            raise RuntimeError(f"BLOB_MISMATCH {rel}: expected={expected} actual={actual}")

    for rel in (BACKEND_TARGET, FRONTEND_TARGET):
        actual = git_blob(rel)
        expected = run("git", "rev-parse", f"HEAD:{rel}")
        if actual != expected:
            raise RuntimeError(f"TARGET_NOT_PRISTINE {rel}: head={expected} actual={actual}")

    profile = (ROOT / PROFILE_ROUTE).read_text(encoding="utf-8")
    profile_markers = [
        'const dataMatch = avatarUrl.match(/^data:image\\/(png|jpeg|jpg|webp);base64,(.+)$/is);',
        'return res.send(buffer);',
        'return res.redirect(302, avatarUrl);',
    ]
    for marker in profile_markers:
        if marker not in profile:
            raise RuntimeError(f"PHASE3_1_MARKER_MISSING {marker}")
    if 'if (target.avatarUrl) return res.redirect(target.avatarUrl);' in profile:
        raise RuntimeError("PHASE3_1_LEGACY_REDIRECT_STILL_PRESENT")

    sanitize = (ROOT / SANITIZE).read_text(encoding="utf-8")
    sanitize_markers = [
        "function compactChatAvatarUrl(user) {",
        'if (!/^data:image\\//i.test(avatarUrl)) return avatarUrl;',
        'return `/api/users/${encodeURIComponent(user.id)}/avatar`;',
        "avatar: compactChatAvatarUrl(user),",
    ]
    for marker in sanitize_markers:
        if marker not in sanitize:
            raise RuntimeError(f"PHASE4_MARKER_MISSING {marker}")


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}_MATCH_COUNT expected=1 actual={count}")
    return text.replace(old, new, 1)


def build_backend_change():
    path = ROOT / BACKEND_TARGET
    text = path.read_text(encoding="utf-8")

    old_sort = '''function personalWorkspaceTaskSort(tasks = [], orderMap = new Map()) {
  return [...tasks].sort((a, b) => {
    const aPosition = orderMap.has(a.id) ? orderMap.get(a.id) : Number.MAX_SAFE_INTEGER;
    const bPosition = orderMap.has(b.id) ? orderMap.get(b.id) : Number.MAX_SAFE_INTEGER;
    if (aPosition !== bPosition) return aPosition - bPosition;
    const aDue = a.dueDate ? new Date(a.dueDate).getTime() : Number.MAX_SAFE_INTEGER - 1;
    const bDue = b.dueDate ? new Date(b.dueDate).getTime() : Number.MAX_SAFE_INTEGER - 1;
    if (aDue !== bDue) return aDue - bDue;
    return new Date(b.updatedAt || b.createdAt || 0).getTime() - new Date(a.updatedAt || a.createdAt || 0).getTime();
  });
}'''

    new_sort = old_sort + '''

const myWorkspaceTaskSummarySelect = {
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
};

function safeMyWorkspaceTask(task, orderMap = new Map(), currentUserId = null) {
  const isPersonalOwner = Boolean(currentUserId && task?.personalOwnerId === currentUserId);
  return {
    id: task.id,
    title: task.title,
    description: isPersonalOwner ? (task.description || "") : "",
    status: task.status,
    approvalStatus: task.approvalStatus || null,
    priority: task.priority,
    dueDate: task.dueDate || null,
    estimatedHours: task.estimatedHours ?? null,
    blockedReason: isPersonalOwner ? (task.blockedReason || null) : null,
    projectId: task.projectId || null,
    personalOwnerId: task.personalOwnerId || null,
    assigneeId: task.assigneeId || null,
    assigneeIds: taskAssigneeIds(task),
    project: task.project ? { id: task.project.id, name: task.project.name } : null,
    personalPosition: orderMap.get(task.id) ?? null,
  };
}'''
    text = replace_once(text, old_sort, new_sort, "WORKSPACE_SUMMARY_HELPERS")

    old_header = '''router.get("/my-workspace", asyncHandler(async (req, res) => {
  if (req.user?.role === "CLIENT" || req.user?.role === "FORMER_EMPLOYEE") throw new AppError("Not allowed", 403);
  const status = optionalString(req.query.status);'''
    new_header = '''router.get("/my-workspace", asyncHandler(async (req, res) => {
  if (req.user?.role === "CLIENT" || req.user?.role === "FORMER_EMPLOYEE") throw new AppError("Not allowed", 403);
  const summaryMode = req.query.summary === "1" || req.query.summary === "true";
  const status = optionalString(req.query.status);'''
    text = replace_once(text, old_header, new_header, "WORKSPACE_SUMMARY_MODE")

    old_query = '''    prisma.task.findMany({ where, include: taskInclude, orderBy: [{ dueDate: "asc" }, { updatedAt: "desc" }], take: 300 }),'''
    new_query = '''    prisma.task.findMany({
      where,
      ...(summaryMode ? { select: myWorkspaceTaskSummarySelect } : { include: taskInclude }),
      orderBy: [{ dueDate: "asc" }, { updatedAt: "desc" }],
      take: 300,
    }),'''
    text = replace_once(text, old_query, new_query, "WORKSPACE_COMPACT_QUERY")

    old_safe = '''  const safeTasks = sorted.map((task) => ({
    ...safeTask(task, { includeInternalNotes: false, currentUser: req.user }),
    personalPosition: orderMap.get(task.id) ?? null,
  }));'''
    new_safe = '''  const safeTasks = sorted.map((task) => (
    summaryMode
      ? safeMyWorkspaceTask(task, orderMap, req.user.id)
      : {
          ...safeTask(task, { includeInternalNotes: false, currentUser: req.user }),
          personalPosition: orderMap.get(task.id) ?? null,
        }
  ));'''
    text = replace_once(text, old_safe, new_safe, "WORKSPACE_COMPACT_SERIALIZER")

    return text


def build_frontend_change():
    path = ROOT / FRONTEND_TARGET
    text = path.read_text(encoding="utf-8")
    old = "const data = await tasksApi.getMyWorkspace({});"
    new = "const data = await tasksApi.getMyWorkspace({ summary: true });"
    return replace_once(text, old, new, "WORKSPACE_FRONTEND_SUMMARY_REQUEST")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if args.check == args.apply:
        parser.error("use exactly one of --check or --apply")

    guard_state()
    backend_content = build_backend_change()
    frontend_content = build_frontend_change()

    print(f"PHASE5_BACKEND_TARGET={BACKEND_TARGET}")
    print(f"PHASE5_FRONTEND_TARGET={FRONTEND_TARGET}")

    if args.check:
        print("PHASE5_PATCH_CHECK=PASS")
        return 0

    for rel, content in (
        (BACKEND_TARGET, backend_content),
        (FRONTEND_TARGET, frontend_content),
    ):
        path = ROOT / rel
        tmp = path.with_name(path.name + ".phase5.tmp")
        tmp.write_text(content, encoding="utf-8")
        os.replace(tmp, path)
        print(f"UPDATED {rel} blob={git_blob(rel)}")

    print("PHASE5_PATCH_APPLIED=PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"PHASE5_PATCH_ERROR={exc}", file=sys.stderr)
        raise SystemExit(1)
