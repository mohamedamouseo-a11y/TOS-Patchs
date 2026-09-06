#!/usr/bin/env python3
from pathlib import Path

ROOT = Path('/var/www/TOS')


def read(rel):
    return (ROOT / rel).read_text(encoding='utf-8')


def write(rel, text):
    (ROOT / rel).write_text(text, encoding='utf-8')


def replace_once(text, old, new, label):
    if new in text:
        return text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'PHASE12_PARSER_FIX_ERROR={label}_COUNT_{count}')
    return text.replace(old, new, 1)

# Fix CREATE_TASK assignee extraction for attached Arabic lam prefix (ليوسف)
# and stop the assignee value before project/date tail phrases.
rel = 'backend/src/agency-operator/services/semanticIntentResolver.service.js'
text = read(rel)

old_create = '    /(?:اعمل|انشئ|أنشئ|create|make)\\s+(?:(?:لي|a|new|جديده|جديدة)\\s+)?(?:task|تاسك|التاسك|مهمه|مهمة|المهمه|المهمة)[^،,؟?!]*?(?:لـ?|ل|إلى|الى|for|to)\\s+([^،,؟?!]+)/iu,'
new_create = '''    /(?:اعمل|انشئ|أنشئ)\\s+(?:(?:لي|جديده|جديدة)\\s+)?(?:task|تاسك|التاسك|مهمه|مهمة|المهمه|المهمة)[^،,؟?!]*?\\s(?:لـ?|ل)\\s*([^،,؟?!]+)/iu,
    /(?:create|make)\\s+(?:(?:a|new)\\s+)?task[^,?!]*?\\s(?:for|to)\\s+([^,?!]+)/iu,'''
text = replace_once(text, old_create, new_create, 'CREATE_ASSIGNEE_PATTERN')

old_tail = '      .split(/\\s+(?:في|على\\s+مشروع|project|بكره|بكرة|غدا|غدًا)\\b/iu)[0]'
new_tail = '      .split(/\\s+(?=(?:في|على)\\s+(?:مشروع|project)(?:\\s|$)|project(?:\\s|$)|بكره(?:\\s|$)|بكرة(?:\\s|$)|غدا(?:\\s|$)|غدًا(?:\\s|$))/iu)[0]'
text = replace_once(text, old_tail, new_tail, 'ASSIGNEE_TAIL_SPLIT')
write(rel, text)

# Strengthen Phase 12 regression coverage so this parser bug cannot return.
test_rel = 'backend/src/agency-operator/tests/ramzyVoiceTaskActionsPhase12.static.test.js'
test_text = read(test_rel)
anchor = '''  assert.ok(String(intent.slots?.assigneeQuery || "").includes("يوسف"));
  assert.ok(getSemanticIntentConfig().supportedProposalOperations.includes("CREATE_TASK"));'''
replacement = '''  assert.equal(intent.slots?.assigneeQuery, "يوسف");

  const spacedArabic = resolveSemanticIntent({ message: "اعمل تاسك ل يوسف" });
  assert.equal(spacedArabic.slots?.assigneeQuery, "يوسف");

  const projectTail = resolveSemanticIntent({ message: "اعمل تاسك مراجعة البنر ليوسف في مشروع Cuir" });
  assert.equal(projectTail.slots?.assigneeQuery, "يوسف");

  const english = resolveSemanticIntent({ message: "create a task review banner for Youssef project Cuir" });
  assert.equal(english.slots?.assigneeQuery, "Youssef");

  assert.ok(getSemanticIntentConfig().supportedProposalOperations.includes("CREATE_TASK"));'''
test_text = replace_once(test_text, anchor, replacement, 'REGRESSION_ASSERTIONS')
write(test_rel, test_text)

print('PHASE12_CREATE_ASSIGNEE_PARSER_FIX=PASS')
