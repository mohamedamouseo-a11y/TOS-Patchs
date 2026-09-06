#!/usr/bin/env python3
from pathlib import Path

ROOT = Path('/var/www/TOS')
MEMORY = ROOT / 'backend/src/agency-operator/services/ramzyMemory.service.js'
TEST = ROOT / 'backend/src/agency-operator/tests/ramzyActionDraftPersistentMemoryPhase14.test.js'
DRAFT = ROOT / 'backend/src/agency-operator/services/ramzyActionDraft.service.js'

for path in (MEMORY, TEST, DRAFT):
    if not path.exists():
        raise SystemExit(f'PHASE14_TOKEN_GUARD_FIX_ERROR=MISSING:{path.relative_to(ROOT)}')

text = MEMORY.read_text(encoding='utf-8')
if 'RAMZY_CONVERSATIONAL_ACTION_DRAFT_V1' not in DRAFT.read_text(encoding='utf-8'):
    raise SystemExit('PHASE14_TOKEN_GUARD_FIX_ERROR=PHASE14_DRAFT_SERVICE_MISSING')
if 'looksLikeActionDraftMessage(message) || !isHighConfidenceMemory(message)' not in text:
    raise SystemExit('PHASE14_TOKEN_GUARD_FIX_ERROR=PERSIST_SKIP_GUARD_MISSING')

start = text.find('function looksLikeActionDraftMessage(text) {')
end_marker = '\n\nfunction isHighConfidenceMemory(text) {'
end = text.find(end_marker, start)
if start < 0 or end < 0:
    raise SystemExit('PHASE14_TOKEN_GUARD_FIX_ERROR=HELPER_RANGE_NOT_FOUND')

old_helper = text[start:end]
if 'Space/end boundaries are Unicode-safe here.' not in old_helper:
    if 'const startsWithVerb = (verbs)' in old_helper and 'taskToken.test(value)' in old_helper:
        print('PHASE14_PERSISTENT_GUARD_TOKEN_FIX=ALREADY_FIXED')
        raise SystemExit(0)
    raise SystemExit('PHASE14_TOKEN_GUARD_FIX_ERROR=KNOWN_BROKEN_HELPER_NOT_FOUND')

new_helper = r'''function looksLikeActionDraftMessage(text) {
  const original = String(text || "").trim().replace(/\s+/g, " ");
  if (!original) return false;
  const value = original.replace(/^(?:من فضلك|لو سمحت|please|عايز|أريد|اريد|i want to)\s+/iu, "");
  const startsWithVerb = (verbs) => verbs.some((verb) => value === verb || value.startsWith(`${verb} `));
  const taskToken = /(?:^|\s)(?:task|tasks|تاسك|التاسك|تاسكات|التاسكات|مهمه|مهمة|المهمه|المهمة|مهام|المهام)(?=\s|$)/iu;
  const commentChecklistToken = /(?:^|\s)(?:comment|تعليق|checklist|check list|تشيك ليست)(?=\s|$)/iu;
  const dueToken = /(?:^|\s)(?:due|deadline|موعد|ميعاد|تسليم)(?=\s|$)/iu;

  if (startsWithVerb(["اعمل", "انشئ", "أنشئ", "create", "make"]) && taskToken.test(value)) return true;
  if (startsWithVerb(["اسند", "إسند", "assign", "حوّل", "حول", "انقل"])) return true;
  if (startsWithVerb(["خلي", "خلّي", "خليها", "خلّيها", "خليه", "خلّيه"]) && taskToken.test(value)) return true;
  if (startsWithVerb(["ضيف", "اضف", "أضف", "add"]) && commentChecklistToken.test(value)) return true;
  if (startsWithVerb(["غير", "غيّر", "عدل", "عدّل", "change", "set", "move"]) && dueToken.test(value)) return true;
  return false;
}'''

text = text[:start] + new_helper + text[end:]
MEMORY.write_text(text, encoding='utf-8')

final = MEMORY.read_text(encoding='utf-8')
for marker in [
    'const startsWithVerb = (verbs)',
    'const taskToken =',
    'taskToken.test(value)',
    'commentChecklistToken.test(value)',
    'dueToken.test(value)',
    'looksLikeActionDraftMessage(message) || !isHighConfidenceMemory(message)',
]:
    if marker not in final:
        raise SystemExit(f'PHASE14_TOKEN_GUARD_FIX_ERROR=FINAL_MARKER_MISSING:{marker}')

print('PHASE14_PERSISTENT_GUARD_TOKEN_FIX=PASS')
