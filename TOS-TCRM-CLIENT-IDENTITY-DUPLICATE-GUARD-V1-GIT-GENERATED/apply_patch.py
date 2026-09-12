#!/usr/bin/env python3
from pathlib import Path
import os
import shutil
import sys
from datetime import datetime

PATCH = "TOS-TCRM-CLIENT-IDENTITY-DUPLICATE-GUARD-V1-GIT-GENERATED"
DEFAULT_REPO = "/var/www/TOS"
TARGET_REL = "backend/src/routes/crmProjectsIntegration.routes.js"

repo = Path(os.environ.get("TOS_REPO", DEFAULT_REPO)).resolve()
target = repo / TARGET_REL

if not target.exists():
    print(f"PATCH={PATCH}")
    print(f"STATUS=ABORT")
    print(f"REASON=TARGET_NOT_FOUND:{target}")
    sys.exit(2)

text = target.read_text(encoding="utf-8")

old_version = 'const TCRM_PROJECT_UPSERT_VERSION = "TCRM_AUTHORITATIVE_PROJECT_RESYNC_ADD_ONLY_TEAM_V1";'
new_version = 'const TCRM_PROJECT_UPSERT_VERSION = "TCRM_CLIENT_IDENTITY_DUPLICATE_GUARD_V1";'

old_client_id = '  const crmClientId = normalizedText(req.body.crmClientId || req.body.clientPoolId || req.body.crmClientNumber || req.body.clientId);'
new_client_id = '  const crmClientId = requiredText(req.body.crmClientId || req.body.clientPoolId || req.body.crmClientNumber || req.body.clientId, "crmClientId");'

build_source_anchor = '''function buildSourceKey({ crmProjectId, crmDealId, crmClientId, projectName }) {
  if (crmProjectId) return `crmProject:${crmProjectId}`;
  if (crmDealId) return `crmDeal:${crmDealId}`;
  return `crmClientProject:${crmClientId || "unknown"}:${projectName.toLowerCase()}`;
}
'''

legacy_helper = '''function buildSourceKey({ crmProjectId, crmDealId, crmClientId, projectName }) {
  if (crmProjectId) return `crmProject:${crmProjectId}`;
  if (crmDealId) return `crmDeal:${crmDealId}`;
  return `crmClientProject:${crmClientId || "unknown"}:${projectName.toLowerCase()}`;
}

async function findUnlinkedLegacyProjectCandidates(db, { projectName, clientName }) {
  const normalizedProjectName = normalizedText(projectName).toLowerCase();
  const normalizedClientName = normalizedText(clientName).toLowerCase();
  const clientNameClause = normalizedClientName
    ? Prisma.sql`OR LOWER(BTRIM(COALESCE(p."clientName", ''))) = ${normalizedClientName}`
    : Prisma.empty;

  return db.$queryRaw(Prisma.sql`
    SELECT
      p.id,
      p.name,
      p."clientName",
      p.status,
      p.stage,
      p."archivedAt",
      p."createdAt",
      p."updatedAt"
    FROM "Project" p
    LEFT JOIN tos_crm_project_deliveries d ON d.project_id = p.id
    WHERE d.project_id IS NULL
      AND p."archivedAt" IS NULL
      AND (
        LOWER(BTRIM(p.name)) = ${normalizedProjectName}
        ${clientNameClause}
      )
    ORDER BY p."updatedAt" DESC
    LIMIT 10
  `);
}
'''

create_anchor = '  const createdSync = await prisma.$transaction(async (tx) => {'
legacy_guard = '''  // CLIENT IDENTITY CONTRACT V1:
  // One TCRM crmClientId represents exactly one operational TOS project.
  // Legacy/manual projects may predate the delivery mapping table. If an
  // unlinked project looks like the same business project, never create a new
  // shell automatically. Stop and require an explicit one-time link/adoption.
  const legacyCandidates = await findUnlinkedLegacyProjectCandidates(prisma, {
    projectName,
    clientName: optionalPayloadText(req.body, "clientName", "client_name"),
  });

  if (legacyCandidates.length > 0) {
    await recordKeyUse({
      keyId: req.integrationKey.keyId,
      req,
      status: "FAILED",
      message: `Legacy project link required for crmClientId ${crmClientId}`,
    });

    return res.status(409).json({
      success: false,
      code: "TCRM_LEGACY_PROJECT_LINK_REQUIRED",
      message: "An unlinked legacy TOS project may already represent this TCRM client. Automatic project creation was blocked to prevent a duplicate.",
      crmClientId,
      projectName,
      candidateCount: legacyCandidates.length,
      candidates: legacyCandidates.map((candidate) => ({
        projectId: candidate.id,
        name: candidate.name,
        clientName: candidate.clientName || null,
        status: candidate.status,
        stage: candidate.stage,
        archivedAt: candidate.archivedAt || null,
        createdAt: candidate.createdAt || null,
        updatedAt: candidate.updatedAt || null,
      })),
      requiredAction: "LINK_EXISTING_PROJECT_OR_CONFIRM_NEW_CLIENT_PROJECT",
      projectCreated: false,
    });
  }

  const createdSync = await prisma.$transaction(async (tx) => {'''

checks = [
    (old_version, "version anchor"),
    (old_client_id, "crmClientId anchor"),
    (build_source_anchor, "buildSourceKey anchor"),
    (create_anchor, "create branch anchor"),
]
missing = [label for anchor, label in checks if anchor not in text]
if missing:
    # Allow idempotent re-run if all new markers are already present.
    already = (
        new_version in text
        and new_client_id in text
        and "findUnlinkedLegacyProjectCandidates" in text
        and "TCRM_LEGACY_PROJECT_LINK_REQUIRED" in text
    )
    if already:
        print(f"PATCH={PATCH}")
        print("STATUS=ALREADY_APPLIED")
        print(f"TARGET={target}")
        sys.exit(0)
    print(f"PATCH={PATCH}")
    print("STATUS=ABORT")
    print("REASON=BASELINE_ANCHOR_MISMATCH")
    print("MISSING=" + ",".join(missing))
    sys.exit(3)

backup_dir = repo / "backups"
backup_dir.mkdir(parents=True, exist_ok=True)
stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup = backup_dir / f"crmProjectsIntegration.routes.js.pre-client-identity-guard-{stamp}.bak"
shutil.copy2(target, backup)

patched = text.replace(old_version, new_version, 1)
patched = patched.replace(old_client_id, new_client_id, 1)
patched = patched.replace(build_source_anchor, legacy_helper, 1)
patched = patched.replace(create_anchor, legacy_guard, 1)

target.write_text(patched, encoding="utf-8")

print(f"PATCH={PATCH}")
print("STATUS=APPLIED")
print(f"TARGET={target}")
print(f"BACKUP={backup}")
print("CRM_CLIENT_ID_REQUIRED=YES")
print("LEGACY_DUPLICATE_CREATE_GUARD=YES")
print("AUTO_ADOPT_LEGACY_PROJECT=NO")
print("DATABASE_SCHEMA_CHANGED=NO")
print("EXISTING_PROJECT_DATA_CHANGED=NO")
print("CLEANUP_EXECUTED=NO")
