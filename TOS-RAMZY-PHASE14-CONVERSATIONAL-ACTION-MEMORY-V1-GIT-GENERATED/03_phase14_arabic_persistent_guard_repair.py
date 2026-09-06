#!/usr/bin/env python3
from pathlib import Path

ROOT = Path('/var/www/TOS')
MEMORY = ROOT / 'backend/src/agency-operator/services/ramzyMemory.service.js'
TEST = ROOT / 'backend/src/agency-operator/tests/ramzyActionDraftPersistentMemoryPhase14.test.js'
DRAFT = ROOT / 'backend/src/agency-operator/services/ramzyActionDraft.service.js'

for path in (MEMORY, TEST, DRAFT):
    if not path.exists():
        raise SystemExit(f'PHASE14_ARABIC_GUARD_REPAIR_ERROR=MISSING:{path.relative_to(ROOT)}')

text = MEMORY.read_text(encoding='utf-8')
if 'RAMZY_CONVERSATIONAL_ACTION_DRAFT_V1' not in DRAFT.read_text(encoding='utf-8'):
    raise SystemExit('PHASE14_ARABIC_GUARD_REPAIR_ERROR=PHASE14_DRAFT_SERVICE_MISSING')
if 'looksLikeActionDraftMessage(message) || !isHighConfidenceMemory(message)' not in text:
    raise SystemExit('PHASE14_ARABIC_GUARD_REPAIR_ERROR=PERSIST_SKIP_GUARD_MISSING')

old_helper = r'''function looksLikeActionDraftMessage(text) {
  const value = String(text || "").trim();
  if (!value) return false;
  return /^(?:(?:من فضلك|لو سمحت|please|عايز|أريد|اريد|i want to)\s+)?(?:اعمل|انشئ|أنشئ|create|make)\b[\s\S]{0,160}\b(?:task|تاسك|مهمه|مهمة)\b/iu.test(value)
    || /^(?:(?:من فضلك|لو سمحت|please|عايز|أريد|اريد|i want to)\s+)?(?:اسند|إسند|assign|حوّل|حول|انقل)\b[\s\S]{0,180}/iu.test(value)
    || /^(?:(?:من فضلك|لو سمحت|please|عايز|أريد|اريد|i want to)\s+)?(?:ضيف|اضف|أضف|add)\b[\s\S]{0,140}\b(?:comment|تعليق|checklist|check list|تشيك ليست)\b/iu.test(value)
    || /^(?:(?:من فضلك|لو سمحت|please|عايز|أريد|اريد|i want to)\s+)?(?:غير|غيّر|عدل|عدّل|change|set|move)\b[\s\S]{0,160}\b(?:due|deadline|موعد|ميعاد|assignee|منفذ)\b/iu.test(value);
}'''

new_helper = r'''function looksLikeActionDraftMessage(text) {
  const value = String(text || "").trim();
  if (!value) return false;
  // Do not use JS \\b around Arabic words: \\b is based on ASCII-style word characters
  // and can miss valid Arabic action commands. Space/end boundaries are Unicode-safe here.
  return /^(?:(?:من فضلك|لو سمحت|please|عايز|أريد|اريد|i want to)\s+)?(?:اعمل|انشئ|أنشئ|create|make)(?:\s|$)[\s\S]{0,160}(?:^|\s)(?:task|تاسك|التاسك|مهمه|مهمة|المهمه|المهمة)(?:\s|$)/iu.test(value)
    || /^(?:(?:من فضلك|لو سمحت|please|عايز|أريد|اريد|i want to)\s+)?(?:اسند|إسند|assign|حوّل|حول|انقل)(?:\s|$)[\s\S]{0,180}/iu.test(value)
    || /^(?:(?:من فضلك|لو سمحت|please|عايز|أريد|اريد|i want to)\s+)?(?:ضيف|اضف|أضف|add)(?:\s|$)[\s\S]{0,140}(?:^|\s)(?:comment|تعليق|checklist|check list|تشيك ليست)(?:\s|$)/iu.test(value)
    || /^(?:(?:من فضلك|لو سمحت|please|عايز|أريد|اريد|i want to)\s+)?(?:غير|غيّر|عدل|عدّل|خلي|خلّي|change|set|move)(?:\s|$)[\s\S]{0,160}(?:^|\s)(?:due|deadline|موعد|ميعاد|assignee|منفذ)(?:\s|$)/iu.test(value);
}'''

if new_helper in text:
    print('PHASE14_ARABIC_PERSISTENT_GUARD=ALREADY_FIXED')
elif old_helper in text:
    if text.count(old_helper) != 1:
        raise SystemExit(f'PHASE14_ARABIC_GUARD_REPAIR_ERROR=OLD_HELPER_COUNT_{text.count(old_helper)}')
    text = text.replace(old_helper, new_helper, 1)
    MEMORY.write_text(text, encoding='utf-8')
    print('PHASE14_ARABIC_PERSISTENT_GUARD=PASS')
else:
    raise SystemExit('PHASE14_ARABIC_GUARD_REPAIR_ERROR=KNOWN_HELPER_STATE_NOT_FOUND')

final = MEMORY.read_text(encoding='utf-8')
for marker in [
    'Space/end boundaries are Unicode-safe here.',
    '(?:اعمل|انشئ|أنشئ|create|make)(?:\\s|$)',
    '(?:اسند|إسند|assign|حوّل|حول|انقل)(?:\\s|$)',
    'looksLikeActionDraftMessage(message) || !isHighConfidenceMemory(message)',
]:
    if marker not in final:
        raise SystemExit(f'PHASE14_ARABIC_GUARD_REPAIR_ERROR=FINAL_MARKER_MISSING:{marker}')

print('PHASE14_ARABIC_PERSISTENT_GUARD_REPAIR=PASS')
