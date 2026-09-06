#!/usr/bin/env python3
from pathlib import Path

ROOT = Path('/var/www/TOS')


def read(rel):
    return (ROOT / rel).read_text(encoding='utf-8')


def write(rel, text):
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'PHASE10_V2_PATCH_ERROR={label}_ANCHOR_COUNT_{count}')
    return text.replace(old, new, 1)


rel = 'backend/src/agency-operator/services/ramzyTeamPerformance.service.js'
text = read(rel)

if 'import { resolveEntityCandidates } from "./entityResolution.service.js";' not in text:
    text = replace_once(
        text,
        'import { buildTeamPerformanceExportDataset, buildWorkforceForecast } from "../../routes/tasks.routes.js";\n',
        'import { buildTeamPerformanceExportDataset, buildWorkforceForecast } from "../../routes/tasks.routes.js";\nimport { resolveEntityCandidates } from "./entityResolution.service.js";\n',
        'TEAM_PERFORMANCE_IMPORT',
    )

old_resolver = '''function resolveEmployee(rows, { employeeId = null, employeeQuery = null } = {}) {\n  const list = Array.isArray(rows) ? rows : [];\n  if (employeeId) {\n    const match = list.find((row) => row.id === employeeId) || null;\n    return match ? { match, ambiguous: false, candidates: [] } : { match: null, ambiguous: false, candidates: [] };\n  }\n  const query = clean(employeeQuery);\n  if (!query) return { match: null, ambiguous: false, candidates: [] };\n  const exact = list.filter((row) => [row.name, row.email].some((value) => clean(value) === query));\n  if (exact.length === 1) return { match: exact[0], ambiguous: false, candidates: [] };\n  if (exact.length > 1) return { match: null, ambiguous: true, candidates: exact.slice(0, 5) };\n  const starts = list.filter((row) => clean(row.name).startsWith(query));\n  if (starts.length === 1) return { match: starts[0], ambiguous: false, candidates: [] };\n  if (starts.length > 1) return { match: null, ambiguous: true, candidates: starts.slice(0, 5) };\n  const contains = list.filter((row) => clean(row.name).includes(query) || clean(row.email).includes(query));\n  if (contains.length === 1) return { match: contains[0], ambiguous: false, candidates: [] };\n  if (contains.length > 1) return { match: null, ambiguous: true, candidates: contains.slice(0, 5) };\n  return { match: null, ambiguous: false, candidates: [] };\n}\n'''

new_resolver = '''function resolveEmployee(rows, { employeeId = null, employeeQuery = null } = {}) {\n  const list = Array.isArray(rows) ? rows : [];\n  if (employeeId) {\n    const match = list.find((row) => row.id === employeeId) || null;\n    return match\n      ? { match, ambiguous: false, candidates: [], confidence: 1, matchType: "EXPLICIT_ID" }\n      : { match: null, ambiguous: false, candidates: [], confidence: 0, matchType: "NONE" };\n  }\n  if (!String(employeeQuery || "").trim()) {\n    return { match: null, ambiguous: false, candidates: [], confidence: 0, matchType: "NONE" };\n  }\n\n  // Phase 10: Team Performance must use the same multilingual, phonetic and\n  // ambiguity-aware identity resolver as the rest of Ramzy. Candidate discovery\n  // remains the already-authorized ACTIVE Team Performance dataset, so this\n  // changes name matching only and does not widen RBAC scope.\n  const resolution = resolveEntityCandidates({\n    query: employeeQuery,\n    candidates: list,\n    fields: ["name", "email"],\n    exactFields: ["name", "email"],\n    entityType: "USER",\n    limit: 5,\n    ambiguityDelta: 0.05,\n    ambiguityAutoResolveThreshold: 0.95,\n  });\n\n  return {\n    match: resolution.entity || null,\n    ambiguous: resolution.guardDecision === "CLARIFY",\n    candidates: (resolution.candidates || []).slice(0, 5),\n    confidence: Number(resolution.confidence || 0),\n    matchType: resolution.matchType || "NONE",\n    guardDecision: resolution.guardDecision || null,\n    guardReason: resolution.guardReason || null,\n  };\n}\n'''

if old_resolver in text:
    text = replace_once(text, old_resolver, new_resolver, 'TEAM_PERFORMANCE_RESOLVER')
elif 'Phase 10: Team Performance must use the same multilingual' not in text:
    raise SystemExit('PHASE10_V2_PATCH_ERROR=TEAM_PERFORMANCE_RESOLVER_STATE_UNKNOWN')

old_message = 'message: "More than one authorized ACTIVE employee matches the requested name. Ask the user to choose by number or provide a fuller name.",'
new_message = 'message: "The requested employee name is ambiguous or low-confidence inside the authorized ACTIVE Team Performance scope. Ask the user to choose by number or provide a fuller name; never guess.",'
if old_message in text:
    text = replace_once(text, old_message, new_message, 'TEAM_PERFORMANCE_AMBIGUITY_MESSAGE')
elif new_message not in text:
    raise SystemExit('PHASE10_V2_PATCH_ERROR=TEAM_PERFORMANCE_AMBIGUITY_MESSAGE_STATE_UNKNOWN')

write(rel, text)

# Add a focused static bridge test. The existing Phase 10 tests validate the
# multilingual resolver behavior itself; this test ensures Team Performance is
# wired to that resolver rather than maintaining a parallel exact/contains path.
test_rel = 'backend/src/agency-operator/tests/ramzyTeamPerformanceIdentityPhase10.test.js'
test_text = r'''import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "../..");
const read = (relative) => readFile(path.join(root, relative), "utf8");

test("Phase 10 Team Performance uses shared multilingual identity resolution inside existing RBAC scope", async () => {
  const service = await read("agency-operator/services/ramzyTeamPerformance.service.js");
  assert.match(service, /resolveEntityCandidates/);
  assert.match(service, /entityType: "USER"/);
  assert.match(service, /fields: \["name", "email"\]/);
  assert.match(service, /guardDecision === "CLARIFY"/);
  assert.match(service, /already-authorized ACTIVE Team Performance dataset/);
  assert.doesNotMatch(service, /clean\(row\.name\)\.startsWith\(query\)/);
  assert.doesNotMatch(service, /clean\(row\.name\)\.includes\(query\)/);
});

test("Phase 10 Team Performance keeps permissions server-side and does not grant ADMIN all-company scope", async () => {
  const tasks = await read("routes/tasks.routes.js");
  const permissions = await read("services/permissions.service.js");
  assert.match(tasks, /performance\.view_all/);
  assert.match(tasks, /performance\.view_team/);
  assert.match(tasks, /members: \{ some: \{ userId: req\.user\.id \} \}/);
  assert.match(permissions, /ADMIN:[\s\S]*"performance\.view_self"[\s\S]*"performance\.view_team"/);
  assert.doesNotMatch(permissions, /ADMIN:[\s\S]{0,900}"performance\.view_all"/);
});
'''

if (ROOT / test_rel).exists():
    existing = read(test_rel)
    if existing != test_text:
        raise SystemExit('PHASE10_V2_PATCH_ERROR=TEAM_PERFORMANCE_TEST_ALREADY_EXISTS_UNEXPECTED')
else:
    write(test_rel, test_text)

print('PHASE10_TEAM_PERFORMANCE_IDENTITY_BRIDGE=PASS')
