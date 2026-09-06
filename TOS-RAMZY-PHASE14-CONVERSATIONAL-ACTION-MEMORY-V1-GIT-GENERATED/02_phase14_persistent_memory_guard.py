#!/usr/bin/env python3
from pathlib import Path

ROOT = Path('/var/www/TOS')
MEMORY = ROOT / 'backend/src/agency-operator/services/ramzyMemory.service.js'
TEST = ROOT / 'backend/src/agency-operator/tests/ramzyActionDraftPersistentMemoryPhase14.test.js'

text = MEMORY.read_text(encoding='utf-8')
if 'publicActionDraftView' not in text or 'conversation_action_draft' not in text:
    raise SystemExit('PHASE14_PERSISTENT_GUARD_ERROR=PHASE14_MEMORY_PATCH_NOT_APPLIED')

helper = r'''
function looksLikeActionDraftMessage(text) {
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

if 'function looksLikeActionDraftMessage' not in text:
    anchor = 'function isHighConfidenceMemory(text) {'
    if text.count(anchor) != 1:
        raise SystemExit(f'PHASE14_PERSISTENT_GUARD_ERROR=HELPER_ANCHOR_COUNT_{text.count(anchor)}')
    text = text.replace(anchor, helper + '\n' + anchor, 1)

old = '  if (!enabled || !isHighConfidenceMemory(message)) return 0;'
new = '  if (!enabled || looksLikeActionDraftMessage(message) || !isHighConfidenceMemory(message)) return 0;'
if new not in text:
    if text.count(old) != 1:
        raise SystemExit(f'PHASE14_PERSISTENT_GUARD_ERROR=PERSIST_ANCHOR_COUNT_{text.count(old)}')
    text = text.replace(old, new, 1)

old_testables = '  isHighConfidenceMemory,\n  memoryPromptContext,'
new_testables = '  isHighConfidenceMemory,\n  looksLikeActionDraftMessage,\n  memoryPromptContext,'
if new_testables not in text:
    if text.count(old_testables) != 1:
        raise SystemExit(f'PHASE14_PERSISTENT_GUARD_ERROR=TESTABLE_ANCHOR_COUNT_{text.count(old_testables)}')
    text = text.replace(old_testables, new_testables, 1)

required = [
    'function looksLikeActionDraftMessage',
    'const startsWithVerb = (verbs)',
    'taskToken.test(value)',
    'looksLikeActionDraftMessage(message) || !isHighConfidenceMemory(message)',
    'looksLikeActionDraftMessage,',
]
for marker in required:
    if marker not in text:
        raise SystemExit(f'PHASE14_PERSISTENT_GUARD_ERROR=MARKER_MISSING:{marker}')

if TEST.exists():
    raise SystemExit('PHASE14_PERSISTENT_GUARD_ERROR=TEST_ALREADY_EXISTS')

test_content = r'''import test from "node:test";
import assert from "node:assert/strict";
import { __testables } from "../services/ramzyMemory.service.js";

test("Phase 14 task action commands are not promoted into long-term RamzyMemory", () => {
  assert.equal(__testables.looksLikeActionDraftMessage("عايز اعمل تاسك ليوسف"), true);
  assert.equal(__testables.looksLikeActionDraftMessage("create task for Youssef"), true);
  assert.equal(__testables.looksLikeActionDraftMessage("اسند التاسك ليوسف"), true);
  assert.equal(__testables.looksLikeActionDraftMessage("ضيف comment على التاسك"), true);
  assert.equal(__testables.looksLikeActionDraftMessage("غير موعد التاسك لبكرة"), true);
});

test("Phase 14 does not suppress genuine long-term workflow preferences just because they mention tasks", () => {
  assert.equal(__testables.looksLikeActionDraftMessage("دائمًا لما أقول اعمل تاسك اسألني عن المشروع الأول"), false);
  assert.equal(__testables.looksLikeActionDraftMessage("أفضل أن تكون كل المهام المهمة High"), false);
});
'''

MEMORY.write_text(text, encoding='utf-8')
TEST.write_text(test_content, encoding='utf-8')
print('PHASE14_PERSISTENT_ACTION_MEMORY_GUARD=PASS')
