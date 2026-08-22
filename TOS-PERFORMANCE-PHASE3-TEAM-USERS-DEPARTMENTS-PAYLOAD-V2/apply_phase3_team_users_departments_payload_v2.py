#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path("/var/www/TOS")
EXPECTED = {
    "backend/src/routes/users.routes.js": "66cfcab403a8aabae31a3647810b285f436d656a",
    "backend/src/services/companyDepartments.service.js": "602fb6e958e4e5904dc6de1eecdbd57376c7fc67",
    "frontend/src/lib/api.js": "aa0ab5f509ae7e98b7d191ba321df7b3917fc557",
    "frontend/src/pages/TeamPage.jsx": "73c9dc2bbc949a21975f09c17131cf0e3f03dcd2",
}


def git_blob(path: Path) -> str:
    return subprocess.check_output(["git", "hash-object", str(path)], cwd=ROOT, text=True).strip()


def replace_exact(text: str, old: str, new: str, label: str, count: int = 1) -> str:
    actual = text.count(old)
    if actual != count:
        raise RuntimeError(f"{label}: expected {count} exact match(es), found {actual}")
    return text.replace(old, new, count)


def replace_first_matches(text: str, old: str, new: str, label: str, count: int) -> str:
    actual = text.count(old)
    if actual < count:
        raise RuntimeError(f"{label}: expected at least {count} exact match(es), found {actual}")
    return text.replace(old, new, count)


def build_changes():
    for rel, expected in EXPECTED.items():
        actual = git_blob(ROOT / rel)
        if actual != expected:
            raise RuntimeError(f"BLOB_MISMATCH {rel}: expected={expected} actual={actual}")

    changes = {}

    rel = "backend/src/routes/users.routes.js"
    text = (ROOT / rel).read_text(encoding="utf-8")

    text = replace_exact(
        text,
        '''function serializeUser(user) {\n  return {\n    ...sanitizeUser(user),\n    projects: (user.projectMemberships || []).map((membership) => ({''',
        '''function compactTeamAvatarUrl(user) {\n  const avatarUrl = String(user?.avatarUrl || "").trim();\n  if (!avatarUrl) return null;\n  if (!/^data:image\\//i.test(avatarUrl)) return avatarUrl;\n  const version = user?.avatarUpdatedAt ? new Date(user.avatarUpdatedAt).getTime() : 0;\n  return `/api/users/${encodeURIComponent(user.id)}/avatar?v=${Number.isFinite(version) ? version : 0}`;\n}\n\nfunction serializeUser(user, { summary = false } = {}) {\n  const sanitized = sanitizeUser(user);\n  return {\n    ...sanitized,\n    ...(summary ? { avatarUrl: compactTeamAvatarUrl(user) } : {}),\n    projects: (user.projectMemberships || []).map((membership) => ({''',
        "users.serializeUser.compactAvatar",
    )

    text = replace_exact(
        text,
        '''const userWithProjects = { projectMemberships: { include: { project: { select: { id: true, name: true, status: true, stage: true, progress: true, dueDate: true, updatedAt: true } } } } };\n\n\nrouter.get("/notifications",''',
        '''const userWithProjects = { projectMemberships: { include: { project: { select: { id: true, name: true, status: true, stage: true, progress: true, dueDate: true, updatedAt: true } } } } };\n\nconst teamUserSummarySelect = {\n  id: true,\n  name: true,\n  email: true,\n  role: true,\n  status: true,\n  department: true,\n  avatarUrl: true,\n  avatarUpdatedAt: true,\n  presenceOverride: true,\n  phone: true,\n  lastLoginAt: true,\n  lastActivityAt: true,\n  statusChangedAt: true,\n  inviteExpiresAt: true,\n  invitedAt: true,\n  acceptedAt: true,\n  disabledAt: true,\n  createdAt: true,\n  projectMemberships: {\n    select: {\n      projectId: true,\n      role: true,\n      project: { select: { id: true, name: true, status: true, stage: true, progress: true, updatedAt: true } },\n    },\n  },\n};\n\n\nrouter.get("/notifications",''',
        "users.teamUserSummarySelect",
    )

    text = replace_exact(
        text,
        '''router.get("/", requireRole("SUPER_ADMIN", "ADMIN", "MANAGER", "PROJECT_MANAGER"), asyncHandler(async (req, res) => {\n  const users = await prisma.user.findMany({\n    where: await visibleTeamUserWhere(req.user),\n    include: userWithProjects,\n    orderBy: [{ role: "asc" }, { createdAt: "desc" }],\n  });\n  const io = req.app.get("io");\n  res.json(users.map((item) => ({\n    ...serializeUser(item),\n    isOnline: Boolean(io?.sockets?.adapter?.rooms?.get(`user:${item.id}`)?.size),\n  })));\n}));\n\nrouter.get("/departments", requireRole("SUPER_ADMIN", "ADMIN", "MANAGER", "PROJECT_MANAGER"), asyncHandler(async (_req, res) => {\n  res.json(await listCompanyDepartments());\n}));''',
        '''router.get("/", requireRole("SUPER_ADMIN", "ADMIN", "MANAGER", "PROJECT_MANAGER"), asyncHandler(async (req, res) => {\n  const summaryMode = req.query.summary === "1" || req.query.summary === "true";\n  const users = await prisma.user.findMany({\n    where: await visibleTeamUserWhere(req.user),\n    ...(summaryMode ? { select: teamUserSummarySelect } : { include: userWithProjects }),\n    orderBy: [{ role: "asc" }, { createdAt: "desc" }],\n  });\n  const io = req.app.get("io");\n  res.json(users.map((item) => ({\n    ...serializeUser(item, { summary: summaryMode }),\n    isOnline: Boolean(io?.sockets?.adapter?.rooms?.get(`user:${item.id}`)?.size),\n  })));\n}));\n\nrouter.get("/departments", requireRole("SUPER_ADMIN", "ADMIN", "MANAGER", "PROJECT_MANAGER"), asyncHandler(async (req, res) => {\n  const summaryMode = req.query.summary === "1" || req.query.summary === "true";\n  res.json(await listCompanyDepartments({ summary: summaryMode }));\n}));\n\nrouter.get("/:userId/avatar", requireRole("SUPER_ADMIN", "ADMIN", "MANAGER", "PROJECT_MANAGER"), asyncHandler(async (req, res) => {\n  const userId = required(req.params.userId, "userId");\n  const visibility = await visibleTeamUserWhere(req.user);\n  const target = await prisma.user.findFirst({\n    where: visibility ? { AND: [{ id: userId }, visibility] } : { id: userId },\n    select: { id: true, avatarUrl: true, avatarUpdatedAt: true },\n  });\n  const avatarUrl = String(target?.avatarUrl || "").trim();\n  if (!target || !avatarUrl) throw new AppError("Avatar not found", 404);\n\n  const dataMatch = avatarUrl.match(/^data:image\\/(png|jpeg|jpg|webp);base64,(.+)$/is);\n  if (!dataMatch) {\n    if (!/^https:\\/\\/[^\\s]+$/i.test(avatarUrl)) throw new AppError("Avatar not found", 404);\n    res.set("Cache-Control", "private, max-age=3600");\n    return res.redirect(302, avatarUrl);\n  }\n\n  const subtype = dataMatch[1].toLowerCase() === "jpg" ? "jpeg" : dataMatch[1].toLowerCase();\n  const buffer = Buffer.from(dataMatch[2].replace(/\\s+/g, ""), "base64");\n  if (!buffer.length) throw new AppError("Avatar not found", 404);\n  res.set({\n    "Content-Type": `image/${subtype}`,\n    "Content-Length": String(buffer.length),\n    "Cache-Control": "private, max-age=604800, immutable",\n  });\n  return res.send(buffer);\n}));''',
        "users.summaryRoutesAndAvatar",
    )
    changes[rel] = text

    rel = "backend/src/services/companyDepartments.service.js"
    text = (ROOT / rel).read_text(encoding="utf-8")

    text = replace_exact(
        text,
        '''export async function listCompanyDepartments() {\n  const departments = await ensureCompanyDepartments(prisma);''',
        '''function compactDepartmentAvatarUrl(user, { summary = false } = {}) {\n  const avatarUrl = String(user?.avatarUrl || "").trim();\n  if (!avatarUrl) return null;\n  if (!summary || !/^data:image\\//i.test(avatarUrl)) return avatarUrl;\n  const version = user?.avatarUpdatedAt ? new Date(user.avatarUpdatedAt).getTime() : 0;\n  return `/api/users/${encodeURIComponent(user.id)}/avatar?v=${Number.isFinite(version) ? version : 0}`;\n}\n\nexport async function listCompanyDepartments({ summary = false } = {}) {\n  const departments = await ensureCompanyDepartments(prisma);''',
        "departments.compactAvatarHelper",
    )

    # The same select shape also appears later in manager/deputy mutation helpers.
    # Only the first two occurrences belong to listCompanyDepartments(), which is
    # the read path Phase 3 is optimizing.
    text = replace_first_matches(
        text,
        '''select: { id: true, name: true, email: true, role: true, status: true, department: true, avatarUrl: true },''',
        '''select: { id: true, name: true, email: true, role: true, status: true, department: true, avatarUrl: true, avatarUpdatedAt: true },''',
        "departments.avatarUpdatedAtSelects",
        count=2,
    )

    text = replace_exact(
        text,
        '''avatarUrl: manager.avatarUrl || null,''',
        '''avatarUrl: compactDepartmentAvatarUrl(manager, { summary }),''',
        "departments.managerAvatar",
    )
    text = replace_exact(
        text,
        '''avatarUrl: deputyManager.avatarUrl || null,''',
        '''avatarUrl: compactDepartmentAvatarUrl(deputyManager, { summary }),''',
        "departments.deputyAvatar",
    )
    text = replace_exact(
        text,
        '''avatarUrl: item.avatarUrl || null,''',
        '''avatarUrl: compactDepartmentAvatarUrl(item, { summary }),''',
        "departments.memberAvatar",
    )
    changes[rel] = text

    rel = "frontend/src/lib/api.js"
    text = (ROOT / rel).read_text(encoding="utf-8")
    text = replace_exact(
        text,
        '''  users: {\n    list: () => request("/api/users"),\n    departments: () => request("/api/users/departments"),''',
        '''  users: {\n    list: (options = {}) => request(`/api/users${queryString({ summary: options.summary ? "1" : "" })}`),\n    departments: (options = {}) => request(`/api/users/departments${queryString({ summary: options.summary ? "1" : "" })}`),''',
        "api.usersSummaryOptions",
    )
    changes[rel] = text

    rel = "frontend/src/pages/TeamPage.jsx"
    text = (ROOT / rel).read_text(encoding="utf-8")
    text = replace_exact(
        text,
        '''      const [usersResult, projectsResult, departmentsResult] = await Promise.allSettled([api.users.list(), api.projects.list({ summary: true }), api.users.departments()]);''',
        '''      const [usersResult, projectsResult, departmentsResult] = await Promise.allSettled([api.users.list({ summary: true }), api.projects.list({ summary: true }), api.users.departments({ summary: true })]);''',
        "team.summaryUsersDepartments",
    )
    changes[rel] = text

    return changes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    if args.check == args.apply:
        parser.error("use exactly one of --check or --apply")

    changes = build_changes()
    print("PHASE3_TARGETS=" + ",".join(changes.keys()))
    if args.check:
        print("PHASE3_PATCH_CHECK=PASS")
        return 0

    for rel, content in changes.items():
        path = ROOT / rel
        tmp = path.with_name(path.name + ".phase3.tmp")
        tmp.write_text(content, encoding="utf-8")
        os.replace(tmp, path)
        print(f"UPDATED {rel} blob={git_blob(path)}")
    print("PHASE3_PATCH_APPLIED=PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"PHASE3_PATCH_ERROR={exc}", file=sys.stderr)
        raise SystemExit(1)
