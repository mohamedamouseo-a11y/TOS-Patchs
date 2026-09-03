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
        raise SystemExit(f'PHASE10_PATCH_ERROR={label}_ANCHOR_COUNT_{count}')
    return text.replace(old, new, 1)


identity_service = r'''import { detectEntityScript, scoreMultilingualMatch, weightedEditSimilarity } from "./multilingualMatching.service.js";

const HONORIFICS = new Set([
  "م", "مهندس", "المهندس", "استاذ", "الاستاذ", "أستاذ", "الأستاذ", "استاذه", "الاستاذه", "أستاذة", "الأستاذة",
  "د", "دكتور", "الدكتور", "دكتوره", "الدكتوره", "دكتورة", "الدكتورة",
  "mr", "mrs", "ms", "miss", "eng", "engineer", "dr", "doctor",
]);

function baseNormalize(value) {
  return String(value || "")
    .normalize("NFKC")
    .toLowerCase()
    .replace(/[ًٌٍَُِّْـ]/g, "")
    .replace(/[أإآٱ]/g, "ا")
    .replace(/ى/g, "ي")
    .replace(/ة/g, "ه")
    .replace(/[ؤئ]/g, "ء")
    .replace(/[^\p{L}\p{N}\s@._-]/gu, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function words(value) {
  return baseNormalize(value).split(/\s+/).filter(Boolean);
}

export function normalizeIdentityNameInput(value) {
  const parts = words(value);
  while (parts.length > 1 && HONORIFICS.has(parts[0])) parts.shift();
  return parts.join(" ");
}

function compact(value) {
  return normalizeIdentityNameInput(value).replace(/\s+/g, "");
}

function simpleWordSimilarity(left, right) {
  const a = normalizeIdentityNameInput(left);
  const b = normalizeIdentityNameInput(right);
  if (!a || !b) return 0;
  if (a === b) return 1;
  const multilingual = scoreMultilingualMatch(a, b);
  if (multilingual?.score) return multilingual.score;
  return weightedEditSimilarity(a, b);
}

function tokenCoverage(queryWords, valueWords) {
  const used = new Set();
  const scores = [];
  for (const queryWord of queryWords) {
    let bestIndex = -1;
    let bestScore = 0;
    for (let index = 0; index < valueWords.length; index += 1) {
      if (used.has(index)) continue;
      const score = simpleWordSimilarity(queryWord, valueWords[index]);
      if (score > bestScore) {
        bestScore = score;
        bestIndex = index;
      }
    }
    if (bestIndex >= 0 && bestScore >= 0.78) {
      used.add(bestIndex);
      scores.push(bestScore);
    }
  }
  const matched = scores.length;
  return {
    matched,
    queryCoverage: queryWords.length ? matched / queryWords.length : 0,
    valueCoverage: valueWords.length ? matched / valueWords.length : 0,
    meanScore: matched ? scores.reduce((sum, value) => sum + value, 0) / matched : 0,
  };
}

function identityMatchType(query, value) {
  const queryScript = detectEntityScript(query);
  const valueScript = detectEntityScript(value);
  const crossScript = queryScript !== valueScript
    && !["OTHER", "MIXED"].includes(queryScript)
    && !["OTHER", "MIXED"].includes(valueScript);
  return crossScript ? "TRANSLITERATION_FUZZY" : "PHONETIC_FUZZY";
}

export function scoreIdentityNameMatch(queryRaw, valueRaw) {
  const query = normalizeIdentityNameInput(queryRaw);
  const value = normalizeIdentityNameInput(valueRaw);
  if (!query || !value || query.includes("@") || value.includes("@")) return null;

  const queryWords = query.split(/\s+/).filter(Boolean);
  const valueWords = value.split(/\s+/).filter(Boolean);
  const direct = scoreMultilingualMatch(query, value);

  // A single spoken/written first name is allowed to match a longer canonical
  // name. Ambiguity between multiple people is still handled by the shared
  // confidence guard after all authorized candidates are ranked.
  if (queryWords.length <= 1) return direct;

  const compactQuery = compact(query);
  const compactValue = compact(value);
  const compactMatch = compactQuery && compactValue
    ? scoreMultilingualMatch(compactQuery, compactValue)
    : null;

  // Handles spacing differences such as "عبد الرحمن" vs "Abdelrahman".
  if (valueWords.length <= 1) {
    if (compactMatch?.score >= 0.82) return { ...compactMatch, identityStrategy: "COMPACT_NAME" };
    return null;
  }

  // For multi-word names, never accept a high score solely because one common
  // token matched (e.g. "محمد حسن" must not resolve to "Mohamed Ali").
  if (compactMatch?.score >= 0.84) {
    return { ...compactMatch, identityStrategy: "COMPACT_NAME" };
  }

  const coverage = tokenCoverage(queryWords, valueWords);
  if (coverage.queryCoverage < 0.85 || coverage.valueCoverage < 0.34 || coverage.meanScore < 0.8) return null;

  const score = Math.min(
    0.89,
    0.69
      + coverage.queryCoverage * 0.09
      + coverage.valueCoverage * 0.04
      + coverage.meanScore * 0.08,
  );
  return {
    score,
    matchType: identityMatchType(query, value),
    similarity: coverage.meanScore,
    identityStrategy: "TOKEN_COVERAGE",
    queryCoverage: coverage.queryCoverage,
    valueCoverage: coverage.valueCoverage,
  };
}

export function getIdentityNameMatchingConfig() {
  return {
    version: "RAMZY_IDENTITY_NAME_MATCHING_V1",
    providerCalls: 0,
    strategies: ["HONORIFIC_NORMALIZATION", "COMPACT_NAME", "TOKEN_COVERAGE", "MULTILINGUAL_PHONETIC"],
    safety: {
      multiWordPartialMatchAutoResolve: false,
      ambiguityHandledBySharedGuard: true,
      authorizationCandidatesOnly: true,
    },
  };
}
'''

identity_path = 'backend/src/agency-operator/services/identityNameMatching.service.js'
if (ROOT / identity_path).exists():
    existing = read(identity_path)
    if 'RAMZY_IDENTITY_NAME_MATCHING_V1' not in existing:
        raise SystemExit('PHASE10_PATCH_ERROR=IDENTITY_SERVICE_ALREADY_EXISTS_UNEXPECTED')
else:
    write(identity_path, identity_service)

# entityResolution.service.js
rel = 'backend/src/agency-operator/services/entityResolution.service.js'
text = read(rel)
text = replace_once(
    text,
    'import { scoreMultilingualMatch } from "./multilingualMatching.service.js";\n',
    'import { scoreIdentityNameMatch } from "./identityNameMatching.service.js";\n',
    'ENTITY_RESOLUTION_IMPORT',
)
text = replace_once(
    text,
    '  const multilingual = scoreMultilingualMatch(queryRaw, valueRaw, { queryNormalized: query, valueNormalized: value });\n',
    '  const multilingual = scoreIdentityNameMatch(queryRaw, valueRaw);\n',
    'ENTITY_RESOLUTION_MATCHER',
)
text = replace_once(
    text,
    '''  if (aliasField && candidate?.[aliasField] && best.score < 0.98) {\n    best = { score: 0.98, matchType: "ALIAS", matchedField: aliasField, matchedValue: true };\n  }\n''',
    '''  if (aliasField && candidate?.[aliasField]) {\n    const rawAliasScore = candidate[aliasField];\n    const aliasScore = typeof rawAliasScore === "number"\n      ? Math.max(0, Math.min(0.99, rawAliasScore))\n      : 0.98;\n    if (aliasScore > best.score) {\n      best = { score: aliasScore, matchType: "ALIAS", matchedField: aliasField, matchedValue: true };\n    }\n  }\n''',
    'ENTITY_RESOLUTION_ALIAS_SCORE',
)
text = replace_once(
    text,
    '      ...scoreEntityCandidate(normalizedQuery, candidate, { fields, aliasField }),\n',
    '      ...scoreEntityCandidate(query, candidate, { fields, aliasField }),\n',
    'ENTITY_RESOLUTION_RAW_QUERY',
)
text = replace_once(text, 'version: "RAMZY_ENTITY_RESOLUTION_V1",', 'version: "RAMZY_ENTITY_RESOLUTION_V2",', 'ENTITY_RESOLUTION_VERSION')
text = replace_once(
    text,
    '    fuzzyMultilingualVersion: "RAMZY_FUZZY_MULTILINGUAL_V1",\n',
    '    fuzzyMultilingualVersion: "RAMZY_FUZZY_MULTILINGUAL_V1",\n    identityNameMatchingVersion: "RAMZY_IDENTITY_NAME_MATCHING_V1",\n',
    'ENTITY_RESOLUTION_CONFIG',
)
write(rel, text)

# entityAlias.service.js
rel = 'backend/src/agency-operator/services/entityAlias.service.js'
text = read(rel)
text = replace_once(
    text,
    'import { normalizeEntityText } from "./entityResolution.service.js";\n',
    'import { normalizeEntityText } from "./entityResolution.service.js";\nimport { scoreIdentityNameMatch } from "./identityNameMatching.service.js";\n',
    'ENTITY_ALIAS_IMPORT',
)
old_fn = '''export async function findMatchingEntityAliases({ user, workspaceId, entityType, query, limit = 20 }) {\n  const normalizedAlias = normalizeEntityText(query);\n  const type = normalizeEntityType(entityType);\n  if (!user?.id || !workspaceId || !type || !normalizedAlias) return [];\n  return prisma.ramzyEntityAlias.findMany({\n    where: {\n      workspaceId,\n      entityType: type,\n      normalizedAlias,\n      isActive: true,\n      OR: [{ userId: user.id }, { userId: null }],\n    },\n    orderBy: [{ confidence: "desc" }, { updatedAt: "desc" }],\n    take: Math.max(1, Math.min(50, Number(limit) || 20)),\n  });\n}\n'''
new_fn = '''export async function findMatchingEntityAliases({ user, workspaceId, entityType, query, limit = 20 }) {\n  const normalizedAlias = normalizeEntityText(query);\n  const type = normalizeEntityType(entityType);\n  if (!user?.id || !workspaceId || !type || !normalizedAlias) return [];\n  const boundedLimit = Math.max(1, Math.min(50, Number(limit) || 20));\n  const scopeWhere = {\n    workspaceId,\n    entityType: type,\n    isActive: true,\n    OR: [{ userId: user.id }, { userId: null }],\n  };\n\n  const exact = await prisma.ramzyEntityAlias.findMany({\n    where: { ...scopeWhere, normalizedAlias },\n    orderBy: [{ confidence: "desc" }, { updatedAt: "desc" }],\n    take: boundedLimit,\n  });\n  if (exact.length) {\n    return exact.map((row) => ({\n      ...row,\n      resolutionScore: Math.max(0.98, Math.min(0.99, Number(row.confidence || 0.98))),\n      resolutionMatchType: "ALIAS_EXACT",\n    }));\n  }\n\n  // Spelling/transliteration fallback remains strictly workspace + user/global\n  // scoped. Fuzzy aliases are intentionally capped below the ALIAS auto-resolve\n  // threshold, so they can surface a candidate but cannot silently bypass the\n  // shared ambiguity/confidence guard.\n  const candidates = await prisma.ramzyEntityAlias.findMany({\n    where: scopeWhere,\n    orderBy: [{ updatedAt: "desc" }],\n    take: Math.max(40, Math.min(120, boundedLimit * 6)),\n  });\n  return candidates\n    .map((row) => {\n      const match = scoreIdentityNameMatch(query, row.alias);\n      const score = Math.min(0.94, Number(match?.score || 0));\n      return { ...row, resolutionScore: score, resolutionMatchType: match?.matchType || null };\n    })\n    .filter((row) => row.resolutionScore >= 0.82)\n    .sort((a, b) => b.resolutionScore - a.resolutionScore || Number(b.confidence || 0) - Number(a.confidence || 0))\n    .slice(0, boundedLimit);\n}\n'''
text = replace_once(text, old_fn, new_fn, 'ENTITY_ALIAS_FIND')
text = replace_once(text, 'version: "RAMZY_ALIAS_LEARNING_V1",', 'version: "RAMZY_ALIAS_LEARNING_V2",', 'ENTITY_ALIAS_VERSION')
text = replace_once(
    text,
    '    learningMode: "EXPLICIT_USER_ONLY",\n',
    '    learningMode: "EXPLICIT_USER_ONLY",\n    spellingAwareLookup: true,\n    fuzzyAliasAutoResolve: false,\n',
    'ENTITY_ALIAS_CONFIG',
)
write(rel, text)

# ramzySystemIntelligence.service.js — keep alias scores instead of turning every fuzzy alias into 0.98.
rel = 'backend/src/agency-operator/services/ramzySystemIntelligence.service.js'
text = read(rel)
old_enriched = '''  const enriched = candidates.map((candidate) => ({\n    ...candidate,\n    aliasMatch: aliases.some((alias) => alias.entityId === candidate.id),\n  }));\n'''
new_enriched = '''  const enriched = candidates.map((candidate) => ({\n    ...candidate,\n    aliasConfidence: aliases\n      .filter((alias) => alias.entityId === candidate.id)\n      .reduce((best, alias) => Math.max(best, Number(alias.resolutionScore || alias.confidence || 0)), 0),\n  }));\n'''
if text.count(old_enriched) != 2:
    raise SystemExit(f'PHASE10_PATCH_ERROR=SYSTEM_INTELLIGENCE_ALIAS_ENRICHED_COUNT_{text.count(old_enriched)}')
text = text.replace(old_enriched, new_enriched)
if text.count('aliasField: "aliasMatch",') != 2:
    raise SystemExit('PHASE10_PATCH_ERROR=SYSTEM_INTELLIGENCE_ALIAS_FIELD_COUNT')
text = text.replace('aliasField: "aliasMatch",', 'aliasField: "aliasConfidence",')
if text.count('aliasUsed: Boolean(resolution.entity?.aliasMatch),') != 2:
    raise SystemExit('PHASE10_PATCH_ERROR=SYSTEM_INTELLIGENCE_ALIAS_USED_COUNT')
text = text.replace('aliasUsed: Boolean(resolution.entity?.aliasMatch),', 'aliasUsed: Number(resolution.entity?.aliasConfidence || 0) > 0,')
write(rel, text)

# ramzyPrompt.js
rel = 'backend/src/agency-operator/prompts/ramzyPrompt.js'
text = read(rel)
anchor = '- المعرفة التي تحمل knowledgeOnly أو نوع KNOWLEDGE تشرح بنية النظام فقط ولا تثبت وجود سجل أو رقم أو حالة حالية.\n'
insert = anchor + '''- Phase 10: افهم اختلاف كتابة ونطق أسماء الأشخاص والمشاريع بالعربي والإنجليزي والـArabizi والتهجئات القريبة، لكن اعتبر Identity Resolver وConfidence Guard في TOS هما الحكم النهائي وليس تخمين الموديل.\n- أمثلة مثل يوسف / Youssef / Yousef أو عبد الرحمن / Abdelrahman يمكن أن تكون نفس الهوية فقط إذا أعاد الـresolver تطابقًا مسموحًا. عند وجود أكثر من مرشح اسأل المستخدم باختيارات مرقمة ولا تختَر من نفسك.\n- الـAI Provider يساعد في فهم صياغة الطلب فقط؛ لا يجوز له توسيع قائمة الأشخاص أو المشاريع عن النطاق الذي أعادته أدوات TOS المصرح بها، ولا تجاوز RBAC بسبب تشابه اسم أو معلومة في الذاكرة.\n- اعتبر النص القادم لاحقًا من Speech-to-Text مثل أي نص مستخدم آخر: اختلاف النطق أو التهجئة لا يلغي التحقق من الهوية والصلاحيات قبل أي Action.\n'''
text = replace_once(text, anchor, insert, 'RAMZY_PROMPT_PHASE10')
write(rel, text)

# Phase 10 behavior/static tests.
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

test("Phase 10 resolves common Arabic-English spelling and phonetic variants", () => {
  for (const latin of ["Youssef", "Yousef", "Yusuf"]) {
    const match = scoreIdentityNameMatch("يوسف", latin);
    assert.ok(match && match.score >= 0.84, `${latin} should match يوسف`);
  }
  const compact = scoreIdentityNameMatch("عبد الرحمن", "Abdelrahman");
  assert.ok(compact && compact.score >= 0.82, "spacing/transliteration variant should match");
  assert.equal(normalizeIdentityNameInput("المهندس يوسف"), "يوسف");
});

test("Phase 10 blocks partial multi-word false identity matches", () => {
  const wrong = scoreIdentityNameMatch("محمد حسن", "Mohamed Ali");
  assert.equal(wrong, null);
});

test("Phase 10 auto-resolves one authorized phonetic candidate but clarifies duplicates", () => {
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

test("Phase 10 fuzzy aliases cannot silently become high-confidence exact aliases", async () => {
  const aliases = await read("agency-operator/services/entityAlias.service.js");
  const intelligence = await read("agency-operator/services/ramzySystemIntelligence.service.js");
  assert.match(aliases, /resolutionScore/);
  assert.match(aliases, /Math\.min\(0\.94/);
  assert.match(aliases, /workspaceId/);
  assert.match(aliases, /OR: \[\{ userId: user\.id \}, \{ userId: null \}\]/);
  assert.match(intelligence, /aliasConfidence/);
  assert.doesNotMatch(intelligence, /aliasField: "aliasMatch"/);
});

test("Phase 10 preserves RBAC-first visible-person resolution and publishes V2 config", async () => {
  const intelligence = await read("agency-operator/services/ramzySystemIntelligence.service.js");
  const prompt = await read("agency-operator/prompts/ramzyPrompt.js");
  assert.match(intelligence, /ramzyVisibleUserWhere/);
  assert.match(intelligence, /assertAgentProjectAccess/);
  assert.match(intelligence, /assertAgentWorkspaceAccess/);
  assert.match(intelligence, /status: "ACTIVE"/);
  assert.match(prompt, /Identity Resolver/);
  assert.match(prompt, /Speech-to-Text/);
  const config = getEntityResolutionConfig();
  assert.equal(config.version, "RAMZY_ENTITY_RESOLUTION_V2");
  assert.equal(config.identityNameMatchingVersion, "RAMZY_IDENTITY_NAME_MATCHING_V1");
});
'''
if (ROOT / test_rel).exists():
    existing = read(test_rel)
    if 'Phase 10 resolves common Arabic-English' not in existing:
        raise SystemExit('PHASE10_PATCH_ERROR=TEST_ALREADY_EXISTS_UNEXPECTED')
else:
    write(test_rel, test_content)

print('PHASE10_NATURAL_IDENTITY_RESOLUTION_PATCH=PASS')
