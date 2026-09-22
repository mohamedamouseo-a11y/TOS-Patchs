#!/usr/bin/env python3
from pathlib import Path
import os
import shutil
import sys
from datetime import datetime

PATCH = "TOS-PROJECT-NAME-DUPLICATE-GUARD-V1"
DEFAULT_REPO = "/var/www/TOS"
TARGET_REL = "backend/src/routes/projects.routes.js"

repo = Path(os.environ.get("TOS_REPO", DEFAULT_REPO)).resolve()
target = repo / TARGET_REL

if not target.exists():
    print(f"PATCH={PATCH}")
    print("STATUS=ABORT")
    print(f"REASON=TARGET_NOT_FOUND:{target}")
    sys.exit(2)

text = target.read_text(encoding="utf-8")

generate_anchor = '''function generateProjectCode(name = "PROJECT") {
  const prefix = String(name || "PROJECT")
    .normalize("NFKD")
    .replace(/[^A-Za-z0-9]+/g, "")
    .slice(0, 4)
    .toUpperCase() || "TOS";
  return `${prefix}-${Date.now().toString(36).toUpperCase().slice(-6)}`;
}
'''

helper_block = '''function generateProjectCode(name = "PROJECT") {
  const prefix = String(name || "PROJECT")
    .normalize("NFKD")
    .replace(/[^A-Za-z0-9]+/g, "")
    .slice(0, 4)
    .toUpperCase() || "TOS";
  return `${prefix}-${Date.now().toString(36).toUpperCase().slice(-6)}`;
}

function normalizeProjectNameForDuplicateGuard(value = "") {
  return String(value || "")
    .normalize("NFKC")
    .toLowerCase()
    .replace(/[\\u064B-\\u065F\\u0670]/g, "")
    .replace(/[إأآٱ]/g, "ا")
    .replace(/ؤ/g, "و")
    .replace(/ئ/g, "ي")
    .replace(/ة/g, "ه")
    .replace(/ى/g, "ي")
    .replace(/ـ/g, "")
    .replace(/[^\\p{L}\\p{N}]+/gu, " ")
    .replace(/\\s+/g, " ")
    .trim();
}

async function assertNoActiveProjectNameDuplicate(tx, projectName, { excludeProjectId = null } = {}) {
  const normalizedName = normalizeProjectNameForDuplicateGuard(projectName);
  if (!normalizedName) throw new AppError("Project name is required", 400);

  // Serialize create/rename/restore operations for the same normalized name.
  // This closes the normal application-level race where two requests arrive together.
  const lockKey = `tos:project-name:${normalizedName}`;
  await tx.$executeRaw`SELECT pg_advisory_xact_lock(hashtext(${lockKey}))`;

  const candidates = await tx.project.findMany({
    where: {
      archivedAt: null,
      ...(excludeProjectId ? { id: { not: excludeProjectId } } : {}),
    },
    select: { id: true, name: true, createdAt: true },
    orderBy: { createdAt: "asc" },
  });

  const duplicate = candidates.find(
    (candidate) => normalizeProjectNameForDuplicateGuard(candidate.name) === normalizedName,
  );

  if (duplicate) {
    throw new AppError(
      `Active project already exists with the same normalized name: "${duplicate.name}"`,
      409,
    );
  }
}
'''

create_anchor = '''  const project = await prisma.$transaction(async (tx) => {
    const projectCode = generateProjectCode(data.name);
'''
create_replacement = '''  const project = await prisma.$transaction(async (tx) => {
    await assertNoActiveProjectNameDuplicate(tx, data.name);
    const projectCode = generateProjectCode(data.name);
'''

update_anchor = '''  const updated = await prisma.$transaction(async (tx) => {
    await tx.project.update({ where: { id: projectId }, data });
'''
update_replacement = '''  const updated = await prisma.$transaction(async (tx) => {
    if (Object.prototype.hasOwnProperty.call(data, "name")) {
      await assertNoActiveProjectNameDuplicate(tx, data.name, { excludeProjectId: projectId });
    }
    await tx.project.update({ where: { id: projectId }, data });
'''

restore_anchor = '''  const restored = await prisma.project.update({
    where: { id: projectId },
    data: { archivedAt: null, archivedById: null },
    include: projectInclude,
  });
'''
restore_replacement = '''  const restored = await prisma.$transaction(async (tx) => {
    const current = await tx.project.findUnique({
      where: { id: projectId },
      select: { id: true, name: true },
    });
    if (!current) throw new AppError("Project not found", 404);

    await assertNoActiveProjectNameDuplicate(tx, current.name, { excludeProjectId: projectId });

    return tx.project.update({
      where: { id: projectId },
      data: { archivedAt: null, archivedById: null },
      include: projectInclude,
    });
  });
'''

markers = [
    "normalizeProjectNameForDuplicateGuard",
    "assertNoActiveProjectNameDuplicate",
    "tos:project-name:",
]

if all(marker in text for marker in markers):
    print(f"PATCH={PATCH}")
    print("STATUS=ALREADY_APPLIED")
    print(f"TARGET={target}")
    sys.exit(0)

checks = [
    (generate_anchor, "generateProjectCode anchor"),
    (create_anchor, "create transaction anchor"),
    (update_anchor, "update transaction anchor"),
    (restore_anchor, "restore anchor"),
]
missing = [label for anchor, label in checks if anchor not in text]
if missing:
    print(f"PATCH={PATCH}")
    print("STATUS=ABORT")
    print("REASON=BASELINE_ANCHOR_MISMATCH")
    print("MISSING=" + ",".join(missing))
    sys.exit(3)

backup_dir = repo / "backups"
backup_dir.mkdir(parents=True, exist_ok=True)
stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup = backup_dir / f"projects.routes.js.pre-project-name-duplicate-guard-{stamp}.bak"
shutil.copy2(target, backup)

patched = text.replace(generate_anchor, helper_block, 1)
patched = patched.replace(create_anchor, create_replacement, 1)
patched = patched.replace(update_anchor, update_replacement, 1)
patched = patched.replace(restore_anchor, restore_replacement, 1)

target.write_text(patched, encoding="utf-8")

print(f"PATCH={PATCH}")
print("STATUS=APPLIED")
print(f"TARGET={target}")
print(f"BACKUP={backup}")
print("CREATE_GUARD=YES")
print("RENAME_GUARD=YES")
print("RESTORE_GUARD=YES")
print("ARABIC_NORMALIZATION=YES")
print("CONCURRENT_REQUEST_LOCK=YES")
print("DATABASE_SCHEMA_CHANGED=NO")
print("EXISTING_PROJECT_DATA_CHANGED=NO")
