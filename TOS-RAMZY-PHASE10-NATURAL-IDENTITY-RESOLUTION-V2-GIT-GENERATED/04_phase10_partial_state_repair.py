#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path('/var/www/TOS')


def read(rel):
    return (ROOT / rel).read_text(encoding='utf-8')


def write(rel, text):
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def require(rel, marker, label):
    path = ROOT / rel
    if not path.exists():
        raise SystemExit(f'PHASE10_V2_REPAIR_ERROR={label}_MISSING')
    text = path.read_text(encoding='utf-8')
    if marker not in text:
        raise SystemExit(f'PHASE10_V2_REPAIR_ERROR={label}_MARKER_MISSING')
    return text


# This repair finalizer is intentionally for a known partial Phase 10 state.
# It never resets TOS and refuses to continue unless the foundational Phase 10
# files from the previous attempt are already present.
require(
    'backend/src/agency-operator/services/identityNameMatching.service.js',
    'RAMZY_IDENTITY_NAME_MATCHING_V1',
    'IDENTITY_MATCHER',
)
require(
    'backend/src/agency-operator/services/entityResolution.service.js',
    'RAMZY_ENTITY_RESOLUTION_V2',
    'ENTITY_RESOLUTION_V2',
)
require(
    'backend/src/agency-operator/services/entityResolution.service.js',
    'scoreIdentityNameMatch',
    'ENTITY_RESOLUTION_MATCHER',
)
require(
    'backend/src/agency-operator/services/entityAlias.service.js',
    'RAMZY_ALIAS_LEARNING_V2',
    'ENTITY_ALIAS_V2',
)
require(
    'backend/src/agency-operator/services/entityAlias.service.js',
    'resolutionScore',
    'ENTITY_ALIAS_SCORE',
)

# Repair ramzySystemIntelligence per occurrence instead of assuming an exact
# number of project/user alias blocks. This safely handles a file where one
# branch was already converted and another branch was edited independently.
rel = 'backend/src/agency-operator/services/ramzySystemIntelligence.service.js'
text = read(rel)

alias_match_pattern = re.compile(
    r'(?P<indent>[ \t]*)aliasMatch\s*:\s*aliases\.some\(\(alias\)\s*=>\s*alias\.entityId\s*===\s*candidate\.id\),'
)


def alias_confidence_replacement(match):
    indent = match.group('indent')
    return (
        f'{indent}aliasConfidence: aliases\n'
        f'{indent}  .filter((alias) => alias.entityId === candidate.id)\n'
        f'{indent}  .reduce((best, alias) => Math.max(best, Number(alias.resolutionScore || alias.confidence || 0)), 0),'
    )

text = alias_match_pattern.sub(alias_confidence_replacement, text)
text = text.replace('aliasField: "aliasMatch",', 'aliasField: "aliasConfidence",')
text = text.replace(
    'aliasUsed: Boolean(resolution.entity?.aliasMatch),',
    'aliasUsed: Number(resolution.entity?.aliasConfidence || 0) > 0,',
)

if 'aliasField: "aliasMatch"' in text:
    raise SystemExit('PHASE10_V2_REPAIR_ERROR=STALE_ALIAS_FIELD_PRESENT')
if 'aliasUsed: Boolean(resolution.entity?.aliasMatch)' in text:
    raise SystemExit('PHASE10_V2_REPAIR_ERROR=STALE_ALIAS_USED_PRESENT')
if 'findMatchingEntityAliases' in text and 'aliasConfidence' not in text:
    raise SystemExit('PHASE10_V2_REPAIR_ERROR=ALIAS_CONFIDENCE_NOT_ESTABLISHED')

write(rel, text)

# Finish the Phase 10 prompt contract if the earlier generator stopped before it.
rel = 'backend/src/agency-operator/prompts/ramzyPrompt.js'
text = read(rel)
if '- Phase 10:' not in text:
    anchor = '- المعرفة التي تحمل knowledgeOnly أو نوع KNOWLEDGE تشرح بنية النظام فقط ولا تثبت وجود سجل أو رقم أو حالة حالية.\n'
    if anchor not in text:
        raise SystemExit('PHASE10_V2_REPAIR_ERROR=RAMZY_PROMPT_ANCHOR_MISSING')
    insert = anchor + (
        '- Phase 10: افهم اختلاف كتابة ونطق أسماء الأشخاص والمشاريع بالعربي والإنجليزي والـArabizi والتهجئات القريبة، لكن اعتبر Identity Resolver وConfidence Guard في TOS هما الحكم النهائي وليس تخمين الموديل.\n'
        '- أمثلة مثل يوسف / Youssef / Yousef / Yusuf أو عبد الرحمن / Abdelrahman يمكن أن تكون نفس الهوية فقط إذا أعاد الـresolver تطابقًا مسموحًا. عند وجود أكثر من مرشح اسأل المستخدم باختيارات مرقمة ولا تختَر من نفسك.\n'
        '- الـAI Provider يساعد في فهم صياغة الطلب فقط؛ لا يجوز له توسيع قائمة الأشخاص أو المشاريع عن النطاق الذي أعادته أدوات TOS المصرح بها، ولا تجاوز RBAC بسبب تشابه اسم أو معلومة في الذاكرة.\n'
        '- اعتبر النص القادم لاحقًا من Speech-to-Text مثل أي نص مستخدم آخر: اختلاف النطق أو التهجئة لا يلغي التحقق من الهوية والصلاحيات قبل أي Action.\n'
    )
    text = text.replace(anchor, insert, 1)
write(rel, text)

# Create the focused identity behavior test if the previous attempt stopped
# before the test file was written.
test_rel = 'backend/src/agency-operator/tests/ramzyIdentityResolutionPhase10.test.js'
test_content = r'''import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { scoreIdentityNameMatch, normalizeIdentityNameInput } from "../services/identityNameMatching.service.js";
import { getEntityResolutionConfig, resolveEntityCandidates } from "../services/entityResolution.service.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "../..");
const read = (relative) => readFile(path.join(root, relative), "utf8");

test("Phase 10 resolves common Arabic-English identity variants", () => {
  for (const latin of ["Youssef", "Yousef", "Yusuf"]) {
    const match = scoreIdentityNameMatch("يوسف", latin);
    assert.ok(match && match.score >= 0.82, `${latin} should match يوسف`);
  }
  const compound = scoreIdentityNameMatch("عبد الرحمن", "Abdelrahman");
  assert.ok(compound && compound.score >= 0.82, "compound transliteration should match");
  assert.equal(normalizeIdentityNameInput("المهندس يوسف"), "يوسف");
});

test("Phase 10 rejects a partial multi-word identity false match", () => {
  assert.equal(scoreIdentityNameMatch("محمد حسن", "Mohamed Ali"), null);
});

test("Phase 10 clarifies duplicate authorized phonetic people", () => {
  const one = resolveEntityCandidates({
    query: "يوسف",
    candidates: [{ id: "u1", name: "Youssef Ahmed" }],
    fields: ["name"],
    exactFields: ["name"],
    entityType: "USER",
  });
  assert.equal(one.guardDecision, "AUTO_RESOLVE");
  assert.equal(one.entity?.id, "u1");

  const many = resolveEntityCandidates({
    query: "يوسف",
    candidates: [
      { id: "u1", name: "Youssef Ahmed" },
      { id: "u2", name: "Yousef Mohamed" },
    ],
    fields: ["name"],
    exactFields: ["name"],
    entityType: "USER",
  });
  assert.equal(many.entity, null);
  assert.equal(many.guardDecision, "CLARIFY");
});

test("Phase 10 keeps fuzzy aliases bounded and RBAC-first resolution present", async () => {
  const aliases = await read("agency-operator/services/entityAlias.service.js");
  const intelligence = await read("agency-operator/services/ramzySystemIntelligence.service.js");
  assert.match(aliases, /resolutionScore/);
  assert.match(aliases, /Math\.min\(0\.94/);
  assert.match(aliases, /workspaceId/);
  assert.match(intelligence, /ramzyVisibleUserWhere/);
  assert.match(intelligence, /aliasConfidence/);
  assert.doesNotMatch(intelligence, /aliasField: "aliasMatch"/);

  const config = getEntityResolutionConfig();
  assert.equal(config.version, "RAMZY_ENTITY_RESOLUTION_V2");
  assert.equal(config.identityNameMatchingVersion, "RAMZY_IDENTITY_NAME_MATCHING_V1");
});
'''

if (ROOT / test_rel).exists():
    existing = read(test_rel)
    if 'Phase 10' not in existing:
        raise SystemExit('PHASE10_V2_REPAIR_ERROR=IDENTITY_TEST_CONFLICT')
else:
    write(test_rel, test_content)

print('PHASE10_V2_PARTIAL_STATE_REPAIR=PASS')
