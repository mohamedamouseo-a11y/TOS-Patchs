#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path('/var/www/TOS')
ROUTE = ROOT / 'backend/src/routes/crmProjectsIntegration.routes.js'
BASE_MAIN = 'c7031b922d81f6e63f985a5fdee90f5a52f13f18'
MARKER = 'TOS_PROJECT_LIFECYCLE_PHASE3_STATUS_HISTORY_V1'

if not ROUTE.exists():
    raise SystemExit('PHASE3_ERROR=MISSING_CRM_ROUTE')

text = ROUTE.read_text(encoding='utf-8')

if MARKER in text:
    print('PATCH_STATUS=ALREADY_APPLIED')
    print(f'PATCH_MARKER={MARKER}')
    raise SystemExit(0)

pattern = re.compile(
    r'(?P<i>[ \t]+)await tx\.project\.update\(\{\n'
    r'(?P=i)  where: \{ id: existingProjectId \},\n'
    r'(?P=i)  data: \{\n'
    r'(?P=i)    name: projectName,\n'
    r'(?P=i)    \.\.\.await buildProjectDataFromCrmPayload\(req\.body, \{ forUpdate: true \}\),\n'
    r'(?P=i)    projectType: "CLIENT",\n'
    r'(?P=i)  \},\n'
    r'(?P=i)\}\);'
)


def replacement(match):
    i = match.group('i')
    return f'''{i}// {MARKER}\n{i}const previousProject = await tx.project.findUnique({{\n{i}  where: {{ id: existingProjectId }},\n{i}  select: {{ status: true }},\n{i}}});\n{i}const crmProjectData = await buildProjectDataFromCrmPayload(req.body, {{ forUpdate: true }});\n{i}await tx.project.update({{\n{i}  where: {{ id: existingProjectId }},\n{i}  data: {{\n{i}    name: projectName,\n{i}    ...crmProjectData,\n{i}    projectType: "CLIENT",\n{i}  }},\n{i}}});\n{i}if (crmProjectData.status && previousProject?.status !== crmProjectData.status) {{\n{i}  await tx.projectActivity.create({{\n{i}    data: {{\n{i}      projectId: existingProjectId,\n{i}      userId: null,\n{i}      type: "STATUS_CHANGED",\n{i}      title: "TCRM lifecycle status synced",\n{i}      message: `Project status changed from ${{previousProject?.status || "UNKNOWN"}} to ${{crmProjectData.status}} from TCRM.`,\n{i}      metadata: {{\n{i}        source: "TCRM",\n{i}        syncVersion: "{MARKER}",\n{i}        previousStatus: previousProject?.status || null,\n{i}        nextStatus: crmProjectData.status,\n{i}        crmClientId,\n{i}        identityResolutionMode: result.mode,\n{i}      }},\n{i}    }},\n{i}  }});\n{i}}}'''

text, count = pattern.subn(replacement, text)
if count != 2:
    raise SystemExit(f'PHASE3_ERROR=EXPECTED_2_UPDATE_PATHS_FOUND_{count}')

ROUTE.write_text(text, encoding='utf-8')

print('PATCH_STATUS=APPLIED_TO_WORKTREE')
print(f'PATCH_MARKER={MARKER}')
print(f'REVIEWED_MAIN={BASE_MAIN}')
print('UPDATE_PATHS_PATCHED=2')
print('DB_SCHEMA_CHANGE=NO')
print('MIGRATION_REQUIRED=NO')
