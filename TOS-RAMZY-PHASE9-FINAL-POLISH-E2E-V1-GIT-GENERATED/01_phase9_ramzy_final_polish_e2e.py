#!/usr/bin/env python3
from pathlib import Path
import os

ROOT = Path(os.environ.get("TOS_ROOT", "/var/www/TOS"))


def read(rel):
    path = ROOT / rel
    if not path.exists():
        raise SystemExit(f"PHASE9_PATCH_ERROR=MISSING_FILE:{rel}")
    return path.read_text(encoding="utf-8")


def write(rel, text):
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"PHASE9_PATCH_ERROR=ANCHOR_{label}_COUNT_{count}")
    return text.replace(old, new, 1)

# 1) Remove the remaining source-level database-ID request from alias clarification.
intel_rel = "backend/src/agency-operator/services/ramzySystemIntelligence.service.js"
intel = read(intel_rel)
old_alias = '''      const clarificationQuestion = clarificationRequired
        ? `لقيت أكتر من نتيجة لـ ${aliasInstruction.canonicalQuery} ومينفعش أحفظ Alias على كيان غير مؤكد.\\n${candidates.map((item, index) => `${index + 1}. ${item.name} — ID: ${item.id}`).join("\\n")}\\nحدد الـID الصحيح الأول.`
        : `ملقتش كيان مؤكد باسم ${aliasInstruction.canonicalQuery}، لذلك ما حفظتش الاسم البديل.`;
      const result = {
        detectedIntent: "ALIAS_LEARN",
        entities: { project: null, assignee: null },
        activeContext: previous,
        live: { aliasLearning: { saved: false, entityType: aliasInstruction.entityType, alias: aliasInstruction.alias, canonicalQuery: aliasInstruction.canonicalQuery } },
        liveDataFetched: true,
        clarificationRequired,
        clarificationQuestion,
        clarificationCandidates: candidates.map((item) => ({ id: item.id, name: item.name })),
        metadata: { detectedIntent: "ALIAS_LEARN", aliasLearning: true, aliasSaved: false, clarificationRequired, liveDataFetched: true, systemContextItemCount: 1 },
      };'''
new_alias = '''      const publicAliasChoices = candidates.map((item, index) => {
        const details = publicChoiceDetails(aliasInstruction.entityType, item);
        return `${index + 1}. ${item.name}${details.length ? ` — ${details.join(" — ")}` : ""}`;
      }).join("\\n");
      const clarificationQuestion = clarificationRequired
        ? `لقيت أكتر من نتيجة لـ ${aliasInstruction.canonicalQuery} ومينفعش أحفظ Alias على كيان غير مؤكد.\\n${publicAliasChoices}\\nابعت الاسم بشكل أوضح أو استخدم التفاصيل الظاهرة للتمييز، بدون أي معرف تقني.`
        : `ملقتش كيان مؤكد باسم ${aliasInstruction.canonicalQuery}، لذلك ما حفظتش الاسم البديل.`;
      const result = {
        detectedIntent: "ALIAS_LEARN",
        entities: { project: null, assignee: null },
        activeContext: previous,
        live: { aliasLearning: { saved: false, entityType: aliasInstruction.entityType, alias: aliasInstruction.alias, canonicalQuery: aliasInstruction.canonicalQuery } },
        liveDataFetched: true,
        clarificationRequired,
        clarificationQuestion,
        clarificationCandidates: candidates.map((item, index) => ({
          choice: index + 1,
          name: item.name,
          ...(aliasInstruction.entityType === "PROJECT"
            ? { status: item.status || null, stage: item.stage || null }
            : { department: item.department || null, jobTitle: item.jobTitle || null }),
        })),
        metadata: { detectedIntent: "ALIAS_LEARN", aliasLearning: true, aliasSaved: false, clarificationRequired, liveDataFetched: true, systemContextItemCount: 1 },
      };'''
intel = replace_once(intel, old_alias, new_alias, "ALIAS_SAFE_CLARIFICATION")
write(intel_rel, intel)

# 2) Final bilingual UI polish, safe approval rendering, evidence scope display.
assistant_rel = "frontend/src/components/RamzyAssistant.jsx"
assistant = read(assistant_rel)
old_approval = '''const SUGGESTIONS = [
  "ما أهم مهامي اليوم؟",
  "إيه المشاريع المعرضة للتأخير؟",
  "لخص لي حالة فريقي.",
  "إيه التاسكات المتوقفة؟",
  "اقترح إعادة توزيع العمل.",
];

function approvalDetail(approval) {
  const payload = approval?.payload && typeof approval.payload === "object" ? approval.payload : {};
  if (approval?.actionType === "ADD_COMMENT") return `التعليق المقترح: ${payload.body || "-"}`;
  if (approval?.actionType === "ADD_CHECKLIST") return `عنصر الـChecklist: ${payload.title || "-"}`;
  if (approval?.actionType === "CHANGE_DUE_DATE") return payload.dueDate
    ? `الموعد الجديد: ${new Date(payload.dueDate).toLocaleString("ar-EG")}`
    : "الموعد الجديد: بدون موعد";
  if (approval?.actionType === "CHANGE_ASSIGNEE") return `المنفذ الجديد: ${payload.assigneeName || payload.assigneeId || "-"}`;
  return "";
}

function ApprovalCard({ approval, onDecision, busy }) {
  if (!approval) return null;
  const pending = approval.status === "PENDING";
  const detail = approvalDetail(approval);
  return (
    <div className="ramzy-approval-card">
      <div className="ramzy-approval-title"><Check size={16} />{approval.title}</div>
      {detail && <p className="ramzy-approval-detail">{detail}</p>}
      {approval.reason && <p>{approval.reason}</p>}
      <small>الإجراء: {approval.actionType}</small>
      {pending ? (
        <div className="ramzy-approval-actions">
          <button type="button" disabled={busy} onClick={() => onDecision(approval.id, "APPROVE")}>اعتماد</button>
          <button type="button" disabled={busy} className="danger" onClick={() => onDecision(approval.id, "REJECT")}>رفض</button>
        </div>
      ) : <span className={`ramzy-approval-status ${approval.status.toLowerCase()}`}>{approval.status}</span>}
    </div>
  );
}'''
new_approval = '''const SUGGESTIONS = {
  ar: [
    "ما أهم مهامي اليوم؟",
    "إيه المشاريع المعرضة للتأخير؟",
    "لخص لي حالة فريقي.",
    "إيه التاسكات المتوقفة؟",
    "اقترح إعادة توزيع العمل.",
  ],
  en: [
    "What are my top priorities today?",
    "Which projects are at risk of delay?",
    "Summarize my team's performance.",
    "Which tasks are blocked?",
    "Suggest how to rebalance the workload.",
  ],
};

const APPROVAL_ACTION_LABELS = {
  ADD_COMMENT: { ar: "إضافة تعليق", en: "Add comment" },
  ADD_CHECKLIST: { ar: "إضافة عنصر Checklist", en: "Add checklist item" },
  CHANGE_DUE_DATE: { ar: "تغيير موعد المهمة", en: "Change due date" },
  CHANGE_ASSIGNEE: { ar: "تغيير منفذ المهمة", en: "Change assignee" },
};

function approvalActionLabel(actionType, isEnglish) {
  const labels = APPROVAL_ACTION_LABELS[actionType];
  return labels ? labels[isEnglish ? "en" : "ar"] : String(actionType || "");
}

function approvalTitle(approval, isEnglish) {
  if (!isEnglish) return approval?.title || approvalActionLabel(approval?.actionType, false);
  const payload = approval?.payload && typeof approval.payload === "object" ? approval.payload : {};
  if (approval?.actionType === "CHANGE_ASSIGNEE") return `Change task assignee to ${payload.assigneeName || "the selected employee"}`;
  if (approval?.actionType === "CHANGE_DUE_DATE") return payload.dueDate
    ? `Change task due date to ${new Date(payload.dueDate).toLocaleString("en-US")}`
    : "Remove task due date";
  return approvalActionLabel(approval?.actionType, true);
}

function approvalDetail(approval, isEnglish) {
  const payload = approval?.payload && typeof approval.payload === "object" ? approval.payload : {};
  if (approval?.actionType === "ADD_COMMENT") return `${isEnglish ? "Suggested comment" : "التعليق المقترح"}: ${payload.body || "-"}`;
  if (approval?.actionType === "ADD_CHECKLIST") return `${isEnglish ? "Checklist item" : "عنصر الـChecklist"}: ${payload.title || "-"}`;
  if (approval?.actionType === "CHANGE_DUE_DATE") return payload.dueDate
    ? `${isEnglish ? "New due date" : "الموعد الجديد"}: ${new Date(payload.dueDate).toLocaleString(isEnglish ? "en-US" : "ar-EG")}`
    : (isEnglish ? "New due date: none" : "الموعد الجديد: بدون موعد");
  if (approval?.actionType === "CHANGE_ASSIGNEE") return `${isEnglish ? "New assignee" : "المنفذ الجديد"}: ${payload.assigneeName || (isEnglish ? "Selected employee" : "الموظف المحدد")}`;
  return "";
}

function approvalStatusLabel(status, isEnglish) {
  const normalized = String(status || "").toUpperCase();
  const labels = {
    PENDING: { ar: "بانتظار الاعتماد", en: "Pending approval" },
    EXECUTING: { ar: "جاري التنفيذ", en: "Executing" },
    EXECUTED: { ar: "تم التنفيذ", en: "Executed" },
    REJECTED: { ar: "مرفوض", en: "Rejected" },
    FAILED: { ar: "فشل التنفيذ", en: "Failed" },
    EXPIRED: { ar: "انتهت الصلاحية", en: "Expired" },
  };
  return labels[normalized]?.[isEnglish ? "en" : "ar"] || normalized;
}

function ApprovalCard({ approval, onDecision, busy, isEnglish }) {
  if (!approval) return null;
  const pending = approval.status === "PENDING";
  const detail = approvalDetail(approval, isEnglish);
  return (
    <div className="ramzy-approval-card">
      <div className="ramzy-approval-title"><Check size={16} />{approvalTitle(approval, isEnglish)}</div>
      {detail && <p className="ramzy-approval-detail">{detail}</p>}
      {approval.reason && <p>{approval.reason}</p>}
      <small>{isEnglish ? "Action" : "الإجراء"}: {approvalActionLabel(approval.actionType, isEnglish)}</small>
      {pending ? (
        <div className="ramzy-approval-actions">
          <button type="button" disabled={busy} onClick={() => onDecision(approval.id, "APPROVE")}>{isEnglish ? "Approve" : "اعتماد"}</button>
          <button type="button" disabled={busy} className="danger" onClick={() => onDecision(approval.id, "REJECT")}>{isEnglish ? "Reject" : "رفض"}</button>
        </div>
      ) : <span className={`ramzy-approval-status ${String(approval.status || "").toLowerCase()}`}>{approvalStatusLabel(approval.status, isEnglish)}</span>}
    </div>
  );
}'''
assistant = replace_once(assistant, old_approval, new_approval, "APPROVAL_I18N")

old_evidence_head = '''function EvidenceDisclosure({ evidence, isEnglish }) {
  const sources = Array.isArray(evidence?.sources) ? evidence.sources : [];
  if (!evidence || evidence.unavailable || (!sources.length && !evidence?.authorization?.enforced)) return null;
  const liveCount = Number(evidence?.summary?.liveSources || 0);
  const knowledgeCount = Number(evidence?.summary?.knowledgeSources || 0);'''
new_evidence_head = '''function evidenceScopeLabel(scope, isEnglish) {
  const labels = {
    CURRENT_USER: { ar: "نطاق المستخدم الحالي", en: "Current user scope" },
    PROJECT: { ar: "نطاق المشروع المصرح", en: "Authorized project scope" },
    WORKSPACE: { ar: "نطاق مساحة العمل المصرح", en: "Authorized workspace scope" },
    EMPLOYEE_AUTHORIZED: { ar: "نطاق الموظف المصرح", en: "Authorized employee scope" },
  };
  return labels[String(scope || "CURRENT_USER")]?.[isEnglish ? "en" : "ar"] || (isEnglish ? "Authorized scope" : "نطاق مصرح");
}

function EvidenceDisclosure({ evidence, isEnglish }) {
  const sources = Array.isArray(evidence?.sources) ? evidence.sources : [];
  if (!evidence || evidence.unavailable || (!sources.length && !evidence?.authorization?.enforced)) return null;
  const liveCount = Number(evidence?.summary?.liveSources || 0);
  const knowledgeCount = Number(evidence?.summary?.knowledgeSources || 0);'''
assistant = replace_once(assistant, old_evidence_head, new_evidence_head, "EVIDENCE_SCOPE_HELPER")

old_source_render = '''                {source.live
                  ? (isEnglish ? "Live TOS data" : "بيانات حية من TOS")
                  : (isEnglish ? "System knowledge only" : "معرفة بالنظام فقط")}
              </li>'''
new_source_render = '''                {source.live
                  ? (isEnglish ? "Live TOS data" : "بيانات حية من TOS")
                  : (isEnglish ? "System knowledge only" : "معرفة بالنظام فقط")}
                {" • "}{evidenceScopeLabel(source.scope, isEnglish)}
              </li>'''
assistant = replace_once(assistant, old_source_render, new_source_render, "EVIDENCE_SCOPE_RENDER")

old_actions = '''          <button type="button" title="نسخ" onClick={() => navigator.clipboard?.writeText(message.content)}><Copy size={13} /></button>
          {onRetry && <button type="button" title="إعادة المحاولة" onClick={onRetry}><RefreshCw size={13} /></button>}
          <button type="button" title="مفيد" onClick={() => onFeedback(message.id, 1)}><ThumbsUp size={13} /></button>
          <button type="button" title="غير مفيد" onClick={() => onFeedback(message.id, -1)}><ThumbsDown size={13} /></button>'''
new_actions = '''          <button type="button" title={isEnglish ? "Copy" : "نسخ"} aria-label={isEnglish ? "Copy response" : "نسخ الرد"} onClick={() => navigator.clipboard?.writeText(message.content)}><Copy size={13} /></button>
          {onRetry && <button type="button" title={isEnglish ? "Retry" : "إعادة المحاولة"} aria-label={isEnglish ? "Retry response" : "إعادة محاولة الرد"} onClick={onRetry}><RefreshCw size={13} /></button>}
          <button type="button" title={isEnglish ? "Helpful" : "مفيد"} aria-label={isEnglish ? "Mark response helpful" : "تقييم الرد كمفيد"} onClick={() => onFeedback(message.id, 1)}><ThumbsUp size={13} /></button>
          <button type="button" title={isEnglish ? "Not helpful" : "غير مفيد"} aria-label={isEnglish ? "Mark response not helpful" : "تقييم الرد كغير مفيد"} onClick={() => onFeedback(message.id, -1)}><ThumbsDown size={13} /></button>'''
assistant = replace_once(assistant, old_actions, new_actions, "MESSAGE_ACTION_I18N")

assistant = replace_once(
    assistant,
    '<div className="ramzy-suggestions">{SUGGESTIONS.map((text) => <button type="button" key={text} onClick={() => sendMessage(text)}>{text}</button>)}</div>',
    '<div className="ramzy-suggestions">{(isEnglish ? SUGGESTIONS.en : SUGGESTIONS.ar).map((text) => <button type="button" key={text} onClick={() => sendMessage(text)}>{text}</button>)}</div>',
    "SUGGESTIONS_LANGUAGE",
)
assistant = assistant.replace(
    '<ApprovalCard key={approval.id} approval={approval} onDecision={decideApproval} busy={loading} />',
    '<ApprovalCard key={approval.id} approval={approval} onDecision={decideApproval} busy={loading} isEnglish={isEnglish} />',
)
if assistant.count('isEnglish={isEnglish} />') < 2:
    raise SystemExit("PHASE9_PATCH_ERROR=APPROVAL_CALLS_NOT_LOCALIZED")

assistant = replace_once(
    assistant,
    'content: item.content || "تم إيقاف الرد."',
    'content: item.content || (isEnglish ? "Response stopped." : "تم إيقاف الرد.")',
    "STOPPED_RESPONSE_I18N",
)
assistant = replace_once(
    assistant,
    'setError(getErrorMessage(err, "رمزي لم يتمكن من الرد الآن."));',
    'setError(getErrorMessage(err, isEnglish ? "Ramzy could not respond right now." : "رمزي لم يتمكن من الرد الآن."));',
    "RESPONSE_ERROR_I18N",
)
assistant = replace_once(
    assistant,
    'setError(getErrorMessage(err, "تعذر تنفيذ قرار الموافقة."));',
    'setError(getErrorMessage(err, isEnglish ? "Could not process the approval decision." : "تعذر تنفيذ قرار الموافقة."));',
    "APPROVAL_ERROR_I18N",
)
assistant = replace_once(
    assistant,
    'placeholder={isEnglish ? "Ask Ramzy about tasks and projects..." : "اسأل رمزي عن المهام والمشاريع..."}',
    'placeholder={isEnglish ? "Ask Ramzy about TOS, tasks, projects, or performance..." : "اسأل رمزي عن TOS أو المهام أو المشاريع أو الأداء..."}',
    "COMPOSER_SCOPE_COPY",
)
write(assistant_rel, assistant)

# 3) Give the Phase 8 evidence disclosure a compact, theme-safe visual treatment.
css_rel = "frontend/src/index.css"
css = read(css_rel)
css_marker = "/* RAMZY_PHASE9_FINAL_POLISH_EVIDENCE */"
if css_marker in css:
    raise SystemExit("PHASE9_PATCH_ERROR=CSS_MARKER_ALREADY_PRESENT")
css += '''\n\n/* RAMZY_PHASE9_FINAL_POLISH_EVIDENCE */
.ramzy-evidence-disclosure {
  margin-top: 8px;
  border: 1px solid color-mix(in srgb, currentColor 14%, transparent);
  border-radius: 12px;
  background: color-mix(in srgb, currentColor 4%, transparent);
  overflow: hidden;
}
.ramzy-evidence-disclosure > summary {
  cursor: pointer;
  padding: 8px 10px;
  font-size: 12px;
  font-weight: 800;
  opacity: .82;
  user-select: none;
}
.ramzy-evidence-disclosure > summary:hover { opacity: 1; }
.ramzy-evidence-disclosure > summary:focus-visible {
  outline: 2px solid currentColor;
  outline-offset: -2px;
}
.ramzy-evidence-body {
  display: grid;
  gap: 7px;
  padding: 0 10px 10px;
  font-size: 12px;
  opacity: .86;
}
.ramzy-evidence-body ul {
  display: grid;
  gap: 5px;
  margin: 0;
  padding-inline-start: 18px;
}
.ramzy-evidence-body li { line-height: 1.45; }
.ramzy-approval-card small { overflow-wrap: anywhere; }
'''
write(css_rel, css)

# 4) Add a final static E2E contract test covering Phases 6-9 invariants.
test_rel = "backend/src/agency-operator/tests/ramzyFinalPolishE2E.static.test.js"
if (ROOT / test_rel).exists():
    raise SystemExit("PHASE9_PATCH_ERROR=FINAL_TEST_ALREADY_EXISTS")
test_text = r'''import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "../..");
const read = (relative) => readFile(path.join(root, relative), "utf8");

test("Phase 9 removes remaining user-visible Ramzy database ID fallbacks", async () => {
  const intelligence = await read("agency-operator/services/ramzySystemIntelligence.service.js");
  const assistant = await read("../../frontend/src/components/RamzyAssistant.jsx");
  assert.doesNotMatch(intelligence, /— ID: \$\{item\.id\}/);
  assert.doesNotMatch(intelligence, /حدد الـID الصحيح الأول/);
  assert.match(intelligence, /بدون أي معرف تقني/);
  assert.doesNotMatch(assistant, /payload\.assigneeName \|\| payload\.assigneeId/);
  assert.doesNotMatch(assistant, /المهمة: \{approval\.targetId\}/);
  assert.match(assistant, /Selected employee/);
});

test("Phase 9 finishes Arabic-English approval and evidence UI polish", async () => {
  const assistant = await read("../../frontend/src/components/RamzyAssistant.jsx");
  const css = await read("../../frontend/src/index.css");
  assert.match(assistant, /What are my top priorities today\?/);
  assert.match(assistant, /Approve/);
  assert.match(assistant, /Reject/);
  assert.match(assistant, /Copy response/);
  assert.match(assistant, /Evidence & access/);
  assert.match(assistant, /evidenceScopeLabel/);
  assert.match(assistant, /Authorized project scope/);
  assert.match(css, /RAMZY_PHASE9_FINAL_POLISH_EVIDENCE/);
  assert.match(css, /ramzy-evidence-disclosure/);
});

test("Phase 9 preserves Phase 7-8 TOS knowledge, RBAC and evidence contracts", async () => {
  const tools = await read("agency-operator/tools/createRamzyTools.js");
  const policy = await read("agency-operator/policies/agentPolicy.service.js");
  const evidence = await read("agency-operator/services/ramzyEvidence.service.js");
  const runtime = await read("agency-operator/services/ramzyRuntime.service.js");
  assert.match(tools, /get_tos_module_context/);
  assert.match(tools, /await assertRamzyToolInvocationScope/);
  assert.match(policy, /SERVER_SIDE|assertRamzyToolInvocationScope/);
  assert.match(evidence, /RAMZY_EVIDENCE_V1/);
  assert.match(evidence, /SERVER_SIDE_RBAC/);
  assert.match(runtime, /safeBuildEvidence/);
  assert.match(runtime, /metadata: \{ runId: run\.id, fallback, providerUsed, modelUsed, usage, systemIntelligence: intelligence\.metadata, evidence \}/);
});
'''
write(test_rel, test_text)

print("PHASE9_RAMZY_FINAL_POLISH_PATCH=PASS")
print("FILES_CHANGED=4")
