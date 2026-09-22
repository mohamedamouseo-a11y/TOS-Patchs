#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
TARGET = ROOT / "frontend/src/components/ProfessionalTaskBoard.jsx"
MARKER = "TOS_TASK_WAITING_CLIENT_PREMIUM_MODAL_V1"

def fail(message, original=None):
    if original is not None and TARGET.exists():
        TARGET.write_text(original, encoding="utf-8")
    print("PATCH=FAIL")
    print(f"ERROR={message}")
    raise SystemExit(1)

if not (ROOT / ".git").is_dir():
    fail(f"TOS git repository not found: {ROOT}")
if not TARGET.is_file():
    fail(f"Missing target: {TARGET.relative_to(ROOT)}")

original = TARGET.read_text(encoding="utf-8")

if MARKER in original:
    required = [
        'data-tos-waiting-client-modal-v1="true"',
        "waitingClientStatusDraft",
        "confirmWaitingClientStatusChange",
        "waitingClientQuickReasons",
        "حدد سبب انتظار العميل ليظهر في سجل المهمة",
    ]
    missing = [item for item in required if item not in original]
    if missing:
        fail(f"Marker exists but implementation is incomplete: {missing}")
    print("PATCH=PASS")
    print("ACTION=ALREADY_APPLIED")
    print("WAITING_CLIENT_PROMPT=REMOVED")
    print("PREMIUM_MODAL=ACTIVE")
    print("QUICK_REASONS=ACTIVE")
    print("INLINE_VALIDATION=ACTIVE")
    print("BACKEND_LOGIC=PRESERVED")
    print("FILES_CHANGED=0")
    raise SystemExit(0)

text = original

state_anchor = '''  const [waitingClientReply, setWaitingClientReply] = useState("");
  const [waitingClientReplyError, setWaitingClientReplyError] = useState("");'''
state_replacement = '''  const [waitingClientReply, setWaitingClientReply] = useState("");
  const [waitingClientReplyError, setWaitingClientReplyError] = useState("");
  // TOS_TASK_WAITING_CLIENT_PREMIUM_MODAL_V1
  const [waitingClientStatusDraft, setWaitingClientStatusDraft] = useState(null);'''
if text.count(state_anchor) != 1:
    fail(f"state anchor expected once, found {text.count(state_anchor)}")
text = text.replace(state_anchor, state_replacement, 1)

reset_anchor = '''    setWaitingClientReply("");
    setWaitingClientReplyError("");
    setDependencyTaskId("");'''
reset_replacement = '''    setWaitingClientReply("");
    setWaitingClientReplyError("");
    setWaitingClientStatusDraft(null);
    setDependencyTaskId("");'''
if text.count(reset_anchor) != 1:
    fail(f"reset anchor expected once, found {text.count(reset_anchor)}")
text = text.replace(reset_anchor, reset_replacement, 1)

old_status_handler = '''  async function handleTaskStatusChange(nextStatus) {
    const normalizedStatus = String(nextStatus || "").toUpperCase();
    const currentStatus = effectiveTaskStatusForUi(draftRef.current || draft);
    if (normalizedStatus === "WAITING_CLIENT" && currentStatus !== "WAITING_CLIENT" && !String((draftRef.current || draft)?.blockedReason || "").trim()) {
      const reason = window.prompt(isAr ? "اكتب سبب انتظار العميل قبل نقل المهمة:" : "Enter the reason for waiting on the client:", "");
      if (reason === null) return null;
      const safeReason = String(reason || "").trim();
      if (!safeReason) {
        window.alert(isAr ? "لازم تكتب سبب انتظار العميل قبل نقل المهمة." : "Waiting Client requires a clear client blocker reason.");
        return null;
      }
      return savePatch({ status: normalizedStatus, blockedReason: safeReason });
    }
    return savePatch({ status: normalizedStatus });
  }'''

new_status_handler = '''  const waitingClientQuickReasons = isAr
    ? ["في انتظار رد العميل", "في انتظار اعتماد العميل", "في انتظار ملفات من العميل", "في انتظار معلومات من العميل"]
    : ["Waiting for client reply", "Waiting for client approval", "Waiting for client files", "Waiting for client information"];

  async function confirmWaitingClientStatusChange() {
    const safeReason = String(waitingClientStatusDraft?.reason || "").trim();
    if (!safeReason) {
      setWaitingClientStatusDraft((current) => current ? {
        ...current,
        error: isAr ? "يرجى كتابة سبب انتظار العميل." : "Please enter the reason for waiting on the client.",
      } : current);
      return null;
    }

    try {
      const updated = await savePatch({ status: "WAITING_CLIENT", blockedReason: safeReason });
      if (updated) setWaitingClientStatusDraft(null);
      return updated;
    } catch (error) {
      setWaitingClientStatusDraft((current) => current ? {
        ...current,
        error: error?.message || (isAr ? "تعذر نقل المهمة إلى بانتظار العميل." : "Could not move the task to Waiting Client."),
      } : current);
      return null;
    }
  }

  async function handleTaskStatusChange(nextStatus) {
    const normalizedStatus = String(nextStatus || "").toUpperCase();
    const currentStatus = effectiveTaskStatusForUi(draftRef.current || draft);
    if (normalizedStatus === "WAITING_CLIENT" && currentStatus !== "WAITING_CLIENT" && !String((draftRef.current || draft)?.blockedReason || "").trim()) {
      setWaitingClientStatusDraft({ reason: "", error: "" });
      return null;
    }
    return savePatch({ status: normalizedStatus });
  }'''
if text.count(old_status_handler) != 1:
    fail(f"status handler anchor expected once, found {text.count(old_status_handler)}")
text = text.replace(old_status_handler, new_status_handler, 1)

modal_anchor = '''      ) : null}
      <motion.div'''
modal_replacement = '''      ) : null}

      {waitingClientStatusDraft && (
        <div
          className="absolute inset-0 z-[120] grid place-items-center bg-slate-950/45 p-4 backdrop-blur-[2px]"
          data-tos-waiting-client-modal-v1="true"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget && !saving) setWaitingClientStatusDraft(null);
          }}
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="tos-waiting-client-modal-title"
            className="w-full max-w-[560px] overflow-hidden rounded-[30px] border border-white/80 bg-white shadow-2xl shadow-slate-950/25 dark:border-white/10 dark:bg-zinc-950"
            dir={modalDirection}
            onMouseDown={(event) => event.stopPropagation()}
          >
            <div className="border-b border-slate-100 bg-gradient-to-b from-amber-50/80 to-white px-6 py-5 dark:border-white/10 dark:from-amber-500/10 dark:to-zinc-950">
              <div className="flex items-start justify-between gap-4">
                <div className="flex min-w-0 items-start gap-3">
                  <span className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-amber-100 text-amber-700 ring-1 ring-amber-200 dark:bg-amber-500/15 dark:text-amber-200 dark:ring-amber-400/20">
                    <Clock3 size={21} />
                  </span>
                  <div className="min-w-0">
                    <h3 id="tos-waiting-client-modal-title" className="text-lg font-black text-slate-950 dark:text-white">
                      {isAr ? "نقل المهمة إلى «بانتظار العميل»" : "Move task to Waiting Client"}
                    </h3>
                    <p className="mt-1 text-xs font-semibold leading-6 text-slate-500 dark:text-zinc-400">
                      {isAr ? "حدد سبب انتظار العميل ليظهر في سجل المهمة." : "Add the client-waiting reason so it is recorded with the task."}
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  disabled={saving}
                  onClick={() => setWaitingClientStatusDraft(null)}
                  className="grid h-10 w-10 shrink-0 place-items-center rounded-full border border-slate-200 bg-white text-slate-500 transition hover:bg-slate-50 disabled:opacity-50 dark:border-white/10 dark:bg-zinc-900 dark:text-zinc-300"
                  aria-label={isAr ? "إلغاء" : "Cancel"}
                >
                  <X size={17} />
                </button>
              </div>

              <div className="mt-4 flex flex-wrap items-center gap-2 rounded-2xl border border-amber-100 bg-white/80 px-3 py-2.5 text-xs font-black dark:border-amber-400/20 dark:bg-zinc-900/80">
                <span className="rounded-full bg-slate-100 px-3 py-1.5 text-slate-600 dark:bg-white/10 dark:text-zinc-300">
                  {displayTaskSystemName(effectiveTaskStatusForUi(draftRef.current || draft), modalUi)}
                </span>
                <span className="text-amber-500" aria-hidden="true">→</span>
                <span className="rounded-full bg-amber-100 px-3 py-1.5 text-amber-800 dark:bg-amber-500/15 dark:text-amber-200">
                  {displayTaskSystemName("WAITING_CLIENT", modalUi)}
                </span>
              </div>
            </div>

            <div className="px-6 py-5">
              <label className="block">
                <span className="text-sm font-black text-slate-800 dark:text-zinc-100">
                  {isAr ? "سبب انتظار العميل *" : "Waiting Client reason *"}
                </span>
                <textarea
                  autoFocus
                  maxLength={600}
                  rows={4}
                  value={waitingClientStatusDraft.reason}
                  onChange={(event) => setWaitingClientStatusDraft((current) => current ? { ...current, reason: event.target.value, error: "" } : current)}
                  onKeyDown={(event) => {
                    if (event.key === "Escape" && !saving) setWaitingClientStatusDraft(null);
                    if ((event.ctrlKey || event.metaKey) && event.key === "Enter" && !saving) confirmWaitingClientStatusChange();
                  }}
                  placeholder={isAr ? "مثال: في انتظار اعتماد التصميم النهائي من العميل..." : "Example: Waiting for the client's final design approval..."}
                  className="mt-2 min-h-[118px] w-full resize-y rounded-[20px] border border-slate-200 bg-slate-50 px-4 py-3 text-sm font-semibold leading-7 text-slate-800 outline-none transition placeholder:text-slate-400 focus:border-amber-300 focus:bg-white focus:ring-4 focus:ring-amber-100/70 dark:border-white/10 dark:bg-zinc-900 dark:text-zinc-100 dark:focus:border-amber-400/40 dark:focus:bg-zinc-950 dark:focus:ring-amber-500/10"
                />
              </label>

              <div className="mt-3">
                <p className="mb-2 text-[11px] font-black text-slate-400 dark:text-zinc-500">
                  {isAr ? "اختيارات سريعة" : "Quick reasons"}
                </p>
                <div className="flex flex-wrap gap-2">
                  {waitingClientQuickReasons.map((reason) => (
                    <button
                      key={reason}
                      type="button"
                      disabled={saving}
                      onClick={() => setWaitingClientStatusDraft((current) => current ? { ...current, reason, error: "" } : current)}
                      className="rounded-full border border-amber-100 bg-amber-50 px-3 py-1.5 text-[11px] font-black text-amber-700 transition hover:border-amber-200 hover:bg-amber-100 disabled:opacity-50 dark:border-amber-400/20 dark:bg-amber-500/10 dark:text-amber-200"
                    >
                      {reason}
                    </button>
                  ))}
                </div>
              </div>

              <div className="mt-3 flex items-center justify-between gap-3 text-[11px] font-bold">
                <span className={waitingClientStatusDraft.error ? "text-red-600 dark:text-red-300" : "text-slate-400 dark:text-zinc-500"}>
                  {waitingClientStatusDraft.error || (isAr ? "اكتب سببًا واضحًا ومختصرًا يمكن الرجوع إليه لاحقًا." : "Use a clear, concise reason that can be referenced later.")}
                </span>
                <span className="shrink-0 text-slate-400 dark:text-zinc-500">{String(waitingClientStatusDraft.reason || "").length}/600</span>
              </div>
            </div>

            <div className="flex flex-wrap items-center justify-end gap-2 border-t border-slate-100 bg-slate-50/70 px-6 py-4 dark:border-white/10 dark:bg-zinc-900/60">
              <button
                type="button"
                disabled={saving}
                onClick={() => setWaitingClientStatusDraft(null)}
                className="rounded-2xl border border-slate-200 bg-white px-5 py-3 text-xs font-black text-slate-600 transition hover:bg-slate-50 disabled:opacity-50 dark:border-white/10 dark:bg-zinc-950 dark:text-zinc-200"
              >
                {isAr ? "إلغاء" : "Cancel"}
              </button>
              <button
                type="button"
                disabled={saving || !String(waitingClientStatusDraft.reason || "").trim()}
                onClick={confirmWaitingClientStatusChange}
                className="inline-flex items-center gap-2 rounded-2xl bg-amber-500 px-5 py-3 text-xs font-black text-white shadow-sm shadow-amber-200 transition hover:bg-amber-600 focus:outline-none focus:ring-4 focus:ring-amber-100 disabled:cursor-not-allowed disabled:opacity-50 dark:shadow-black/20"
              >
                <Clock3 size={15} />
                {saving ? (isAr ? "جاري النقل..." : "Moving...") : (isAr ? "تأكيد النقل" : "Confirm move")}
              </button>
            </div>
          </div>
        </div>
      )}

      <motion.div'''
if text.count(modal_anchor) != 1:
    fail(f"modal insertion anchor expected once, found {text.count(modal_anchor)}")
text = text.replace(modal_anchor, modal_replacement, 1)

TARGET.write_text(text, encoding="utf-8")

try:
    subprocess.run(
        ["git", "-C", str(ROOT), "diff", "--check", "--", "frontend/src/components/ProfessionalTaskBoard.jsx"],
        check=True,
    )
except Exception:
    fail("git diff --check failed; original restored", original)

patched = TARGET.read_text(encoding="utf-8")
required_after = [
    MARKER,
    'data-tos-waiting-client-modal-v1="true"',
    "const [waitingClientStatusDraft, setWaitingClientStatusDraft] = useState(null);",
    "const waitingClientQuickReasons = isAr",
    "async function confirmWaitingClientStatusChange()",
    'setWaitingClientStatusDraft({ reason: "", error: "" });',
    "حدد سبب انتظار العميل ليظهر في سجل المهمة",
    "اختيارات سريعة",
    "تأكيد النقل",
]
missing = [item for item in required_after if item not in patched]
if missing:
    fail(f"Post-patch validation failed: {missing}", original)

legacy = [
    'window.prompt(isAr ? "اكتب سبب انتظار العميل قبل نقل المهمة:"',
    'window.alert(isAr ? "لازم تكتب سبب انتظار العميل قبل نقل المهمة."',
]
leftovers = [item for item in legacy if item in patched]
if leftovers:
    fail(f"Legacy browser dialog still present: {leftovers}", original)

print("PATCH=PASS")
print("ACTION=APPLIED")
print("WAITING_CLIENT_PROMPT=REMOVED")
print("PREMIUM_MODAL=ACTIVE")
print("QUICK_REASONS=4")
print("INLINE_VALIDATION=ACTIVE")
print("KEYBOARD=ESC_CANCEL_CTRL_ENTER_CONFIRM")
print("STATUS_LOGIC=PRESERVED")
print("BLOCKED_REASON_FIELD=PRESERVED")
print("BACKEND_CHANGES=NONE")
print("DB_CHANGES=NONE")
print("FILES_CHANGED=frontend/src/components/ProfessionalTaskBoard.jsx")
print("BUILD=NOT_RUN")
print("DEPLOY=NOT_RUN")
