#!/usr/bin/env python3
from pathlib import Path
import os
import shutil
import sys
from datetime import datetime

PATCH = "TOS-TCRM-CLIENT-IDENTITY-DUPLICATE-GUARD-V1-R1-CRMCLIENT-FIRST-GIT-GENERATED"
DEFAULT_REPO = "/var/www/TOS"
TARGET_REL = "backend/src/routes/crmProjectsIntegration.routes.js"

repo = Path(os.environ.get("TOS_REPO", DEFAULT_REPO)).resolve()
target = repo / TARGET_REL

if not target.exists():
    print(f"PATCH={PATCH}")
    print("STATUS=ABORT")
    print(f"REASON=TARGET_NOT_FOUND:{target}")
    sys.exit(2)

text = target.read_text(encoding="utf-8")

required_markers = [
    'const TCRM_PROJECT_UPSERT_VERSION = "TCRM_CLIENT_IDENTITY_DUPLICATE_GUARD_V1";',
    'const crmClientId = requiredText(req.body.crmClientId || req.body.clientPoolId || req.body.crmClientNumber || req.body.clientId, "crmClientId");',
    'findUnlinkedLegacyProjectCandidates',
    'TCRM_LEGACY_PROJECT_LINK_REQUIRED',
]

missing = [m for m in required_markers if m not in text]
if missing:
    already = 'TCRM_CLIENT_IDENTITY_DUPLICATE_GUARD_V1_R1_CRM_CLIENT_FIRST' in text and 'WHEN d.crm_client_id = ${crmClientId} THEN 0' in text
    if already:
        print(f"PATCH={PATCH}")
        print("STATUS=ALREADY_APPLIED")
        print(f"TARGET={target}")
        sys.exit(0)
    print(f"PATCH={PATCH}")
    print("STATUS=ABORT")
    print("REASON=V1_BASELINE_NOT_PRESENT")
    print("MISSING_MARKERS=" + " | ".join(missing))
    sys.exit(3)

old_version = 'const TCRM_PROJECT_UPSERT_VERSION = "TCRM_CLIENT_IDENTITY_DUPLICATE_GUARD_V1";'
new_version = 'const TCRM_PROJECT_UPSERT_VERSION = "TCRM_CLIENT_IDENTITY_DUPLICATE_GUARD_V1_R1_CRM_CLIENT_FIRST";'

old_order = '''    ORDER BY CASE WHEN d.source_key = ${sourceKey} THEN 0 ELSE 1 END, d.updated_at DESC
    LIMIT 1'''
new_order = '''    ORDER BY CASE
      WHEN d.crm_client_id = ${crmClientId} THEN 0
      WHEN d.source_key = ${sourceKey} THEN 1
      ELSE 2
    END,
    d.updated_at DESC
    LIMIT 1'''

if old_order not in text:
    already = new_order in text and new_version in text
    if already:
        print(f"PATCH={PATCH}")
        print("STATUS=ALREADY_APPLIED")
        print(f"TARGET={target}")
        sys.exit(0)
    print(f"PATCH={PATCH}")
    print("STATUS=ABORT")
    print("REASON=LOOKUP_ORDER_ANCHOR_MISMATCH")
    sys.exit(4)

backup_dir = repo / "backups"
backup_dir.mkdir(parents=True, exist_ok=True)
stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
backup = backup_dir / f"crmProjectsIntegration.routes.js.pre-crmclient-first-r1-{stamp}.bak"
shutil.copy2(target, backup)

patched = text.replace(old_version, new_version, 1)
patched = patched.replace(old_order, new_order, 1)
target.write_text(patched, encoding="utf-8")

print(f"PATCH={PATCH}")
print("STATUS=APPLIED")
print(f"TARGET={target}")
print(f"BACKUP={backup}")
print("CRM_CLIENT_ID_MATCH_PRIORITY=FIRST")
print("SOURCE_KEY_MATCH_PRIORITY=SECONDARY")
print("LEGACY_DUPLICATE_GUARD_PRESERVED=YES")
print("DATABASE_SCHEMA_CHANGED=NO")
print("PROJECT_DATA_CHANGED=NO")
print("DEPLOY=NOT_RUN")
print("SERVICE_RESTART=NO")
print("GIT_PUSH=NO")
