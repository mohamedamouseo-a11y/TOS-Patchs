#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path('/var/www/TOS')
SCHEMA = ROOT / 'backend/prisma/schema.prisma'
CRM_ROUTE = ROOT / 'backend/src/routes/crmProjectsIntegration.routes.js'
MIGRATION_DIR = ROOT / 'backend/prisma/migrations/202609151023_project_ownership_type'
MIGRATION = MIGRATION_DIR / 'migration.sql'
BASE_HEAD = 'b8f8c3d5c475d73fc97ab1ccf1f41ef95615feb5'
MARKER = 'TOS_PROJECT_LIFECYCLE_PHASE2_PROJECT_TYPE_V1'

for path in (SCHEMA, CRM_ROUTE):
    if not path.exists():
        raise SystemExit(f'PHASE2_ERROR=MISSING_{path.name}')

schema = SCHEMA.read_text(encoding='utf-8')
route = CRM_ROUTE.read_text(encoding='utf-8')

already = (
    'enum ProjectType {' in schema
    and 'projectType               ProjectType   @default(INTERNAL)' in schema
    and '@@index([projectType])' in schema
    and route.count('projectType: "CLIENT",') >= 3
    and MIGRATION.exists()
)
if already:
    print('PATCH_STATUS=ALREADY_APPLIED')
    print(f'PATCH_MARKER={MARKER}')
    raise SystemExit(0)

# Refuse partial/unknown states instead of guessing.
partial = [
    'enum ProjectType {' in schema,
    'projectType               ProjectType   @default(INTERNAL)' in schema,
    '@@index([projectType])' in schema,
    'projectType: "CLIENT",' in route,
    MIGRATION.exists(),
]
if any(partial):
    raise SystemExit('PHASE2_ERROR=PARTIAL_STATE_DETECTED')

status_enum = '''enum ProjectStatus {
  PLANNING
  ACTIVE
  ON_HOLD
  DELAYED
  COMPLETED
  CANCELLED
}
'''
project_type_enum = status_enum + '''
enum ProjectType {
  CLIENT
  INTERNAL
}
'''
if schema.count(status_enum) != 1:
    raise SystemExit('PHASE2_ERROR=PROJECT_STATUS_ENUM_ANCHOR')
schema = schema.replace(status_enum, project_type_enum, 1)

project_type_anchor = '''  code                      String?       @unique
  type                      String?
  description               String?
'''
project_type_replacement = '''  code                      String?       @unique
  type                      String?
  projectType               ProjectType   @default(INTERNAL)
  description               String?
'''
if schema.count(project_type_anchor) != 1:
    raise SystemExit('PHASE2_ERROR=PROJECT_MODEL_ANCHOR')
schema = schema.replace(project_type_anchor, project_type_replacement, 1)

index_anchor = '''  @@index([clientId])
  @@index([projectManagerId])
'''
index_replacement = '''  @@index([clientId])
  @@index([projectType])
  @@index([projectManagerId])
'''
if schema.count(index_anchor) != 1:
    raise SystemExit('PHASE2_ERROR=PROJECT_INDEX_ANCHOR')
schema = schema.replace(index_anchor, index_replacement, 1)

create_anchor = '''          projectManagerId: manager?.id || null,
          progress: 0,
'''
create_replacement = '''          projectManagerId: manager?.id || null,
          projectType: "CLIENT",
          progress: 0,
'''
if route.count(create_anchor) != 1:
    raise SystemExit('PHASE2_ERROR=CRM_CREATE_ANCHOR')
route = route.replace(create_anchor, create_replacement, 1)

# Existing CRM sync must assert CLIENT ownership but must NOT mutate archive state.
# Archive remains an independent TOS concept.
update_pattern = re.compile(
    r'(?P<indent>[ \t]+)name: projectName,\n'
    r'(?P=indent)\.\.\.await buildProjectDataFromCrmPayload\(req\.body, \{ forUpdate: true \}\),\n'
    r'(?P=indent)archivedAt: null,\n'
    r'(?P=indent)archivedById: null,'
)

def update_replacement(match):
    i = match.group('indent')
    return (
        f'{i}name: projectName,\n'
        f'{i}...await buildProjectDataFromCrmPayload(req.body, {{ forUpdate: true }}),\n'
        f'{i}projectType: "CLIENT",'
    )

route, update_count = update_pattern.subn(update_replacement, route)
if update_count != 2:
    raise SystemExit(f'PHASE2_ERROR=CRM_UPDATE_ANCHOR_COUNT_{update_count}')

# CRM event-driven lifecycle updates also self-heal the ownership invariant.
event_anchor = '''        data: { status: eventProjectStatus },
'''
event_replacement = '''        data: { status: eventProjectStatus, projectType: "CLIENT" },
'''
if route.count(event_anchor) != 1:
    raise SystemExit('PHASE2_ERROR=CRM_EVENT_STATUS_ANCHOR')
route = route.replace(event_anchor, event_replacement, 1)

SCHEMA.write_text(schema, encoding='utf-8')
CRM_ROUTE.write_text(route, encoding='utf-8')

MIGRATION_DIR.mkdir(parents=True, exist_ok=False)
MIGRATION.write_text('''-- TOS_PROJECT_LIFECYCLE_PHASE2_PROJECT_TYPE_V1
-- Ownership/type is independent from lifecycle status and archive state.
CREATE TYPE "ProjectType" AS ENUM ('CLIENT', 'INTERNAL');

ALTER TABLE "Project"
ADD COLUMN "projectType" "ProjectType" NOT NULL DEFAULT 'INTERNAL';

-- Canonical CRM linkage lives in tos_crm_project_deliveries.
-- Phase-1 audit proved 66 unique mapped projects and zero mapping conflicts.
UPDATE "Project" AS p
SET "projectType" = 'CLIENT'
WHERE EXISTS (
  SELECT 1
  FROM tos_crm_project_deliveries AS d
  WHERE d.project_id = p.id
);

CREATE INDEX "Project_projectType_idx" ON "Project"("projectType");
''', encoding='utf-8')

print('PATCH_STATUS=APPLIED_TO_WORKTREE')
print(f'PATCH_MARKER={MARKER}')
print(f'BASE_HEAD={BASE_HEAD}')
print('EXPECTED_CLIENT_PROJECTS_AFTER_MIGRATION=66')
print('EXPECTED_INTERNAL_PROJECTS_AFTER_MIGRATION=30')
print('ARCHIVE_SEMANTICS=INDEPENDENT')
