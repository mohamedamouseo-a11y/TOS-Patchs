#!/usr/bin/env python3
from pathlib import Path
import os
import shutil
import sys
from datetime import datetime

PATCH = "TOS-TCRM-CLIENT-BRIEF-MAPPING-V1-RECEIVER-GIT-GENERATED"
DEFAULT_REPO = "/var/www/TOS"
ROUTE_REL = "backend/src/routes/crmProjectsIntegration.routes.js"
SCHEMA_REL = "backend/prisma/schema.prisma"
MIGRATION_REL = "backend/prisma/migrations/202609131300_add_crm_handover_brief/migration.sql"

repo = Path(os.environ.get("TOS_REPO", DEFAULT_REPO)).resolve()
route = repo / ROUTE_REL
schema = repo / SCHEMA_REL
migration = repo / MIGRATION_REL

for target in (route, schema):
    if not target.exists():
        print(f"PATCH={PATCH}")
        print("STATUS=ABORT")
        print(f"REASON=TARGET_NOT_FOUND:{target}")
        sys.exit(2)

route_text = route.read_text(encoding="utf-8")
schema_text = schema.read_text(encoding="utf-8")

old_version = 'const STRUCTURED_PROJECT_SYNC_VERSION = "TCRM_TOS_STRUCTURED_PROJECT_SYNC_V1C_NOTES_SUMMARY";'
new_version = 'const STRUCTURED_PROJECT_SYNC_VERSION = "TCRM_TOS_STRUCTURED_PROJECT_SYNC_V2_HANDOVER_BRIEF";'

schema_anchor = '''  clientAccessDetails       String?\n  clientNotes               String?\n  archivedAt                DateTime?'''
schema_replacement = '''  clientAccessDetails       String?\n  clientNotes               String?\n  crmHandoverBrief          Json?\n  archivedAt                DateTime?'''

helper_anchor = '''function buildProjectDescription(payload) {\n  return crmOverviewNotesFromPayload(payload);\n}\n'''
helper_replacement = '''function buildProjectDescription(payload) {\n  return crmOverviewNotesFromPayload(payload);\n}\n\nfunction crmHandoverBriefFromPayload(payload) {\n  const sources = [\n    payload, payload?.metadata, payload?.payload, payload?.data, payload?.body, payload?.input,\n  ].filter((item, index, list) => item && typeof item === "object" && list.indexOf(item) === index);\n  const keys = ["crmHandoverBrief", "crm_handover_brief", "handoverBrief", "handover_brief", "clientBrief", "client_brief"];\n  for (const source of sources) {\n    for (const key of keys) {\n      if (!Object.prototype.hasOwnProperty.call(source, key)) continue;\n      const value = source[key];\n      if (value === null) return null;\n      if (!value || typeof value !== "object" || Array.isArray(value)) throw new AppError("crmHandoverBrief must be a JSON object or null", 400);\n      if (JSON.stringify(value).length > 50000) throw new AppError("crmHandoverBrief is too large", 400);\n      return value;\n    }\n  }\n  return undefined;\n}\n'''

project_data_anchor = '''  const clientWebsite = optionalPayloadText(payload, "clientWebsite", "client_website");\n  if (hasPayloadKey(payload, "clientWebsite", "client_website") || !forUpdate) data.clientWebsite = clientWebsite || null;\n\n  return data;'''
project_data_replacement = '''  const clientWebsite = optionalPayloadText(payload, "clientWebsite", "client_website");\n  if (hasPayloadKey(payload, "clientWebsite", "client_website") || !forUpdate) data.clientWebsite = clientWebsite || null;\n\n  // Store the sanitized structured TCRM Client Handover Brief as JSON.\n  // TCRM is authoritative for this CRM-origin brief; TOS keeps operational work independent.\n  const crmHandoverBrief = crmHandoverBriefFromPayload(payload);\n  if (crmHandoverBrief !== undefined) data.crmHandoverBrief = crmHandoverBrief;\n  else if (!forUpdate) data.crmHandoverBrief = null;\n\n  return data;'''

already_applied = new_version in route_text and "function crmHandoverBriefFromPayload(payload)" in route_text and "data.crmHandoverBrief" in route_text and "crmHandoverBrief          Json?" in schema_text
if already_applied:
    print(f"PATCH={PATCH}")
    print("STATUS=ALREADY_APPLIED")
    print(f"PROJECT_PATH={repo}")
    sys.exit(0)

missing = []
for anchor, label in [(old_version, "structured sync version anchor"), (helper_anchor, "buildProjectDescription anchor"), (project_data_anchor, "buildProjectDataFromCrmPayload anchor")]:
    if anchor not in route_text: missing.append(label)
if schema_anchor not in schema_text: missing.append("Project schema clientNotes anchor")
if missing:
    print(f"PATCH={PATCH}")
    print("STATUS=ABORT")
    print("REASON=BASELINE_ANCHOR_MISMATCH")
    print("MISSING=" + ",".join(missing))
    sys.exit(3)

backup_dir = repo / "backups"
backup_dir.mkdir(parents=True, exist_ok=True)
stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
route_backup = backup_dir / f"crmProjectsIntegration.routes.js.pre-brief-mapping-{stamp}.bak"
schema_backup = backup_dir / f"schema.prisma.pre-brief-mapping-{stamp}.bak"
shutil.copy2(route, route_backup)
shutil.copy2(schema, schema_backup)

route.write_text(route_text.replace(old_version, new_version, 1).replace(helper_anchor, helper_replacement, 1).replace(project_data_anchor, project_data_replacement, 1), encoding="utf-8")
schema.write_text(schema_text.replace(schema_anchor, schema_replacement, 1), encoding="utf-8")

migration.parent.mkdir(parents=True, exist_ok=True)
expected = 'ALTER TABLE "Project" ADD COLUMN IF NOT EXISTS "crmHandoverBrief" JSONB;\n'
if migration.exists() and migration.read_text(encoding="utf-8") != expected:
    print(f"PATCH={PATCH}")
    print("STATUS=ABORT")
    print("REASON=MIGRATION_PATH_ALREADY_EXISTS_WITH_DIFFERENT_CONTENT")
    sys.exit(4)
if not migration.exists(): migration.write_text(expected, encoding="utf-8")

print(f"PATCH={PATCH}")
print("STATUS=APPLIED")
print(f"PROJECT_PATH={repo}")
print(f"ROUTE_BACKUP={route_backup}")
print(f"SCHEMA_BACKUP={schema_backup}")
print(f"MIGRATION_FILE={migration}")
print("CRM_HANDOVER_BRIEF_FIELD=crmHandoverBrief")
print("CRM_HANDOVER_BRIEF_TYPE=JSONB")
print("MIGRATION_EXECUTED=NO")
print("PROJECT_DATA_CHANGED=NO")
print("TCRM_CODE_CHANGED=NO")
