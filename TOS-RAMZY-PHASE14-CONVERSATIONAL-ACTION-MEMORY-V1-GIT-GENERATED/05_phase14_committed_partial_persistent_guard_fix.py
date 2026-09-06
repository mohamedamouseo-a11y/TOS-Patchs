#!/usr/bin/env python3
from pathlib import Path

ROOT = Path('/var/www/TOS')
MEMORY = ROOT / 'backend/src/agency-operator/services/ramzyMemory.service.js'
TEST = ROOT / 'backend/src/agency-operator/tests/ramzyActionDraftPersistentMemoryPhase14.test.js'
DRAFT = ROOT / 'backend/src/agency-operator/services/ramzyActionDraft.service.js'

for path in (MEMORY, TEST, DRAFT):
    if not path.exists():
        raise SystemExit(f'PHASE14_COMMITTED_GUARD_FIX_ERROR=MISSING:{path.relative_to(ROOT)}')

memory = MEMORY.read_text(encoding='utf-8')
test = TEST.read_text(encoding='utf-8')
draft = DRAFT.read_text(encoding='utf-8')

if 'RAMZY_CONVERSATIONAL_ACTION_DRAFT_V1' not in draft:
    raise SystemExit('PHASE14_COMMITTED_GUARD_FIX_ERROR=PHASE14_DRAFT_SERVICE_MISSING')
if 'looksLikeActionDraftMessage(message) || !isHighConfidenceMemory(message)' not in memory:
    raise SystemExit('PHASE14_COMMITTED_GUARD_FIX_ERROR=PERSIST_SKIP_GUARD_MISSING')
for marker in [
    'looksLikeActionDraftMessage("عايز اعمل تاسك ليوسف"), true',
    'looksLikeActionDraftMessage("create task for Youssef"), true',
    'looksLikeActionDraftMessage("دائمًا لما أقول اعمل تاسك اسألني عن المشروع الأول"), false',
]:
    if marker not in test:
        raise SystemExit(f'PHASE14_COMMITTED_GUARD_FIX_ERROR=REGRESSION_TEST_MARKER_MISSING:{marker}')

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
}
'''

start_marker = 'function looksLikeActionDraftMessage(text) {'
end_marker = '\nfunction isHighConfidenceMemory(text) {'

if new_helper.strip() in memory:
    print('PHASE14_COMMITTED_PERSISTENT_GUARD=ALREADY_FIXED')
else:
    start = memory.find(start_marker)
    end = memory.find(end_marker, start)
    if start < 0 or end < 0:
        raise SystemExit('PHASE14_COMMITTED_GUARD_FIX_ERROR=KNOWN_HELPER_BLOCK_NOT_FOUND')
    current_helper = memory[start:end].strip()
    if 'Space/end boundaries are Unicode-safe here.' not in current_helper or 'const startsWithVerb = (verbs)' in current_helper:
        raise SystemExit('PHASE14_COMMITTED_GUARD_FIX_ERROR=UNKNOWN_HELPER_STATE')
    memory = memory[:start] + new_helper.rstrip() + memory[end:]
    MEMORY.write_text(memory, encoding='utf-8')
    print('PHASE14_COMMITTED_PERSISTENT_GUARD=PASS')

final = MEMORY.read_text(encoding='utf-8')
for marker in [
    'const startsWithVerb = (verbs)',
    'taskToken.test(value)',
    'commentChecklistToken.test(value)',
    'dueToken.test(value)',
    'looksLikeActionDraftMessage(message) || !isHighConfidenceMemory(message)',
]:
    if marker not in final:
        raise SystemExit(f'PHASE14_COMMITTED_GUARD_FIX_ERROR=FINAL_MARKER_MISSING:{marker}')

print('PHASE14_COMMITTED_PARTIAL_PERSISTENT_GUARD_FIX=PASS')
