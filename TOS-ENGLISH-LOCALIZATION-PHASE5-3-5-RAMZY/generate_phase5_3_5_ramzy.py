#!/usr/bin/env python3
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

EXPECTED_HEAD = "c4853875bb9376228b2376293745d23d9f72d3b6"
TARGET = "frontend/src/components/RamzySettingsAdmin.jsx"
EXPECTED_BLOB = "989fe67f260e0308e1e54be8cb198478e9626c8b"

REPLACEMENTS = [
    ('import { getErrorMessage } from "../lib/errors";\n', 'import { getErrorMessage } from "../lib/errors";\nimport { usePreferences } from "../contexts/PreferencesContext";\n'),
    ('export function RamzySettingsAdmin({ user }) {\n  const [settings, setSettings] = useState(null);', 'export function RamzySettingsAdmin({ user }) {\n  const { isAr } = usePreferences();\n  const ramzyText = (ar, en) => (isAr ? ar : en);\n  const ramzyLocale = isAr ? "ar-EG" : "en-US";\n  const [settings, setSettings] = useState(null);'),
    ('setError(getErrorMessage(err, "تعذر تحميل إعدادات رمزي."));', 'setError(getErrorMessage(err, ramzyText("تعذر تحميل إعدادات رمزي.", "Unable to load Ramzy settings.")));'),
    ('if (!window.confirm("مسح ذاكرة رمزي لهذا المستخدم؟ سيتم حذف الذاكرة الدائمة والملخصات المتراكمة لهذا الحساب فقط.")) return;', 'if (!window.confirm(ramzyText("مسح ذاكرة رمزي لهذا المستخدم؟ سيتم حذف الذاكرة الدائمة والملخصات المتراكمة لهذا الحساب فقط.", "Clear Ramzy memory for this user? Persistent memory and accumulated summaries for this account only will be deleted."))) return;'),
    ('setMessage(`تم مسح ذاكرة رمزي لهذا الحساب (${result.deletedMemoryCount || 0} عنصر ذاكرة).`);', 'setMessage(ramzyText(`تم مسح ذاكرة رمزي لهذا الحساب (${result.deletedMemoryCount || 0} عنصر ذاكرة).`, `Ramzy memory cleared for this account (${result.deletedMemoryCount || 0} memory item${Number(result.deletedMemoryCount || 0) === 1 ? "" : "s"}).`));'),
    ('setError(getErrorMessage(err, "تعذر مسح ذاكرة رمزي."));', 'setError(getErrorMessage(err, ramzyText("تعذر مسح ذاكرة رمزي.", "Unable to clear Ramzy memory.")));'),
    ('setClearAgnesKey(false); setMessage("تم حفظ إعدادات رمزي.");', 'setClearAgnesKey(false); setMessage(ramzyText("تم حفظ إعدادات رمزي.", "Ramzy settings saved."));'),
    ('setError(getErrorMessage(err, "تعذر حفظ إعدادات رمزي."));', 'setError(getErrorMessage(err, ramzyText("تعذر حفظ إعدادات رمزي.", "Unable to save Ramzy settings.")));'),
    ('if (!form) return <Card>{loading ? "جاري تحميل إعدادات رمزي..." : <Notice type="error">{error}</Notice>}</Card>;', 'if (!form) return <Card>{loading ? ramzyText("جاري تحميل إعدادات رمزي...", "Loading Ramzy settings...") : <Notice type="error">{error}</Notice>}</Card>;'),
    ('<div><p className="tos-kicker">Mastra Agency Operator</p><h3 className="mt-1 text-2xl font-black">إعدادات رمزي</h3><p className="tos-muted mt-2">Primary: Gemini | Fallback: Agnes AI</p></div>', '<div><p className="tos-kicker">Mastra Agency Operator</p><h3 className="mt-1 text-2xl font-black">{ramzyText("إعدادات رمزي", "Ramzy Settings")}</h3><p className="tos-muted mt-2">Primary: Gemini | Fallback: Agnes AI</p></div>'),
    ('<StatCard value={form.enabled ? "مفعّل" : "متوقف"} label="حالة رمزي" icon={Bot} tone={form.enabled ? "success" : "danger"} />', '<StatCard value={form.enabled ? ramzyText("مفعّل", "Enabled") : ramzyText("متوقف", "Disabled")} label={ramzyText("حالة رمزي", "Ramzy status")} icon={Bot} tone={form.enabled ? "success" : "danger"} />'),
    ('<StatCard value={form.hasGeminiKey ? "موجود" : "غير مضبوط"} label="Gemini Key" icon={ShieldCheck} tone={form.hasGeminiKey ? "success" : "danger"} />', '<StatCard value={form.hasGeminiKey ? ramzyText("موجود", "Available") : ramzyText("غير مضبوط", "Not configured")} label="Gemini Key" icon={ShieldCheck} tone={form.hasGeminiKey ? "success" : "danger"} />'),
    ('<StatCard value={form.hasAgnesKey ? "موجود" : "غير مضبوط"} label="Agnes Key" icon={ShieldCheck} tone={form.hasAgnesKey ? "success" : "danger"} />', '<StatCard value={form.hasAgnesKey ? ramzyText("موجود", "Available") : ramzyText("غير مضبوط", "Not configured")} label="Agnes Key" icon={ShieldCheck} tone={form.hasAgnesKey ? "success" : "danger"} />'),
    ('placeholder={form.hasGeminiKey ? "(محفوظ) اكتب لتغيير" : "GEMINI_API_KEY"}', 'placeholder={form.hasGeminiKey ? ramzyText("(محفوظ) اكتب لتغيير", "(Saved) type to replace") : "GEMINI_API_KEY"}'),
    ('/> مسح مفتاح Gemini</label>', '/> {ramzyText("مسح مفتاح Gemini", "Clear Gemini key")}</label>'),
    ('/> مسح مفتاح Agnes</label>', '/> {ramzyText("مسح مفتاح Agnes", "Clear Agnes key")}</label>'),
    ('<Notice type="warning" className="mt-4">حفظ المفاتيح من الواجهة يحتاج AGENT_SETTINGS_ENCRYPTION_KEY. يمكنك ضبط GEMINI_API_KEY و AGNES_API_KEY من السيرفر بدلًا من ذلك.</Notice>', '<Notice type="warning" className="mt-4">{ramzyText("حفظ المفاتيح من الواجهة يحتاج AGENT_SETTINGS_ENCRYPTION_KEY. يمكنك ضبط GEMINI_API_KEY و AGNES_API_KEY من السيرفر بدلًا من ذلك.", "Saving keys from the interface requires AGENT_SETTINGS_ENCRYPTION_KEY. You can configure GEMINI_API_KEY and AGNES_API_KEY on the server instead.")}</Notice>'),
    ('["enabled", "تفعيل رمزي"], ["readOnlyMode", "Read-only + Proposals only"], ["approvalActionsEnabled", "إتاحة الإجراءات بعد الموافقة"], ["dailySummaryEnabled", "ملخص تشغيلي يومي"], ["memoryWindowEnabled", "نافذة الذاكرة مفعّلة"], ["rollingSummaryEnabled", "تلخيص الذاكرة القديمة"], ["persistentMemoryEnabled", "ذاكرة دائمة للمستخدم"], ["systemIntelligenceEnabled", "System Intelligence: live context"], ["aliasLearningEnabled", "تعلّم الأسماء المستعارة الصريحة"],', '["enabled", ramzyText("تفعيل رمزي", "Enable Ramzy")], ["readOnlyMode", "Read-only + Proposals only"], ["approvalActionsEnabled", ramzyText("إتاحة الإجراءات بعد الموافقة", "Allow actions after approval")], ["dailySummaryEnabled", ramzyText("ملخص تشغيلي يومي", "Daily operational summary")], ["memoryWindowEnabled", ramzyText("نافذة الذاكرة مفعّلة", "Memory window enabled")], ["rollingSummaryEnabled", ramzyText("تلخيص الذاكرة القديمة", "Summarize older memory")], ["persistentMemoryEnabled", ramzyText("ذاكرة دائمة للمستخدم", "Persistent user memory")], ["systemIntelligenceEnabled", "System Intelligence: live context"], ["aliasLearningEnabled", ramzyText("تعلّم الأسماء المستعارة الصريحة", "Learn explicit aliases")],'),
    ('<span>Runs لكل مستخدم يوميًا</span>', '<span>{ramzyText("Runs لكل مستخدم يوميًا", "Runs per user per day")}</span>'),
    ('<span>Tool calls لكل Run</span>', '<span>{ramzyText("Tool calls لكل Run", "Tool calls per run")}</span>'),
    ('<span>رسائل الذاكرة القديمة (توافق)</span>', '<span>{ramzyText("رسائل الذاكرة القديمة (توافق)", "Legacy memory messages (compatibility)")}</span>'),
    ('<span>الحد العامل (حتى 40)</span>', '<span>{ramzyText("الحد العامل (حتى 40)", "Working limit (up to 40)")}</span>'),
    ('<span>الذكريات ذات الصلة لكل Run (حتى 8)</span>', '<span>{ramzyText("الذكريات ذات الصلة لكل Run (حتى 8)", "Relevant memories per run (up to 8)")}</span>'),
    ('<span>مشاريع System Intelligence (حتى 8)</span>', '<span>{ramzyText("مشاريع System Intelligence (حتى 8)", "System Intelligence projects (up to 8)")}</span>'),
    ('<span>مهام System Intelligence (حتى 20)</span>', '<span>{ramzyText("مهام System Intelligence (حتى 20)", "System Intelligence tasks (up to 20)")}</span>'),
    ('<span>مستخدمو System Intelligence (حتى 8)</span>', '<span>{ramzyText("مستخدمو System Intelligence (حتى 8)", "System Intelligence users (up to 8)")}</span>'),
    ('<div className="mt-5 grid gap-4 rounded-2xl border border-violet-200 bg-violet-50/60 p-4 text-sm"><p className="font-black">System Intelligence</p><p className="text-slate-600">يحلل نية الطلب ويقرأ بيانات TOS الحية ضمن صلاحيات المستخدم، مع حدود ثابتة وسجل آمن.</p><div className="grid gap-2 md:grid-cols-3"><span>الحالة: <b>{form.systemIntelligenceEnabled ? "مفعّل" : "متوقف"}</b></span><span>أقصى مشاريع: <b>{form.maxIntelligenceProjects}</b></span><span>أقصى مهام: <b>{form.maxIntelligenceTasks}</b></span></div></div>', '<div className="mt-5 grid gap-4 rounded-2xl border border-violet-200 bg-violet-50/60 p-4 text-sm"><p className="font-black">System Intelligence</p><p className="text-slate-600">{ramzyText("يحلل نية الطلب ويقرأ بيانات TOS الحية ضمن صلاحيات المستخدم، مع حدود ثابتة وسجل آمن.", "Analyzes request intent and reads live TOS data within the user permissions, with fixed limits and a secure audit trail.")}</p><div className="grid gap-2 md:grid-cols-3"><span>{ramzyText("الحالة:", "Status:")} <b>{form.systemIntelligenceEnabled ? ramzyText("مفعّل", "Enabled") : ramzyText("متوقف", "Disabled")}</b></span><span>{ramzyText("أقصى مشاريع:", "Max projects:")} <b>{form.maxIntelligenceProjects}</b></span><span>{ramzyText("أقصى مهام:", "Max tasks:")} <b>{form.maxIntelligenceTasks}</b></span></div></div>'),
    ('<label className="mt-5 grid gap-2 text-xs font-black"><span>Workspace IDs المسموح بها (اختياري، مفصولة بفواصل)</span><Field value={(form.allowedWorkspaceIds || []).join(", ")} onChange={(e) => patch("allowedWorkspaceIds", e.target.value.split(",").map((item) => item.trim()).filter(Boolean))} dir="ltr" placeholder="اتركها فارغة لإتاحة النطاق حسب صلاحيات المستخدم" /></label>', '<label className="mt-5 grid gap-2 text-xs font-black"><span>{ramzyText("Workspace IDs المسموح بها (اختياري، مفصولة بفواصل)", "Allowed Workspace IDs (optional, comma-separated)")}</span><Field value={(form.allowedWorkspaceIds || []).join(", ")} onChange={(e) => patch("allowedWorkspaceIds", e.target.value.split(",").map((item) => item.trim()).filter(Boolean))} dir="ltr" placeholder={ramzyText("اتركها فارغة لإتاحة النطاق حسب صلاحيات المستخدم", "Leave blank to allow scope according to user permissions")} /></label>'),
    ('<div className="mt-5"><p className="text-sm font-black">الأدوار المسموح لها</p>', '<div className="mt-5"><p className="text-sm font-black">{ramzyText("الأدوار المسموح لها", "Allowed roles")}</p>'),
    ('<div className="mt-5 flex flex-wrap gap-2"><Button onClick={save} disabled={loading || clearingMemory}><Save size={16} />{loading ? "جاري الحفظ..." : "حفظ إعدادات رمزي"}</Button><Button variant="soft" onClick={load} disabled={loading || clearingMemory}><RefreshCw size={16} /> تحديث</Button><Button variant="soft" onClick={clearMemory} disabled={loading || clearingMemory}><RefreshCw size={16} />{clearingMemory ? "جاري المسح..." : "مسح ذاكرة هذا الحساب"}</Button></div>', '<div className="mt-5 flex flex-wrap gap-2"><Button onClick={save} disabled={loading || clearingMemory}><Save size={16} />{loading ? ramzyText("جاري الحفظ...", "Saving...") : ramzyText("حفظ إعدادات رمزي", "Save Ramzy settings")}</Button><Button variant="soft" onClick={load} disabled={loading || clearingMemory}><RefreshCw size={16} /> {ramzyText("تحديث", "Refresh")}</Button><Button variant="soft" onClick={clearMemory} disabled={loading || clearingMemory}><RefreshCw size={16} />{clearingMemory ? ramzyText("جاري المسح...", "Clearing...") : ramzyText("مسح ذاكرة هذا الحساب", "Clear this account memory")}</Button></div>'),
    ('<div className="flex items-center justify-between gap-3"><div><p className="tos-kicker">Audit & Observability</p><h3 className="mt-1 text-xl font-black">سجل تشغيل رمزي</h3></div><Button variant="soft" onClick={load} disabled={loading}><RefreshCw size={16} /> تحديث</Button></div>', '<div className="flex items-center justify-between gap-3"><div><p className="tos-kicker">Audit & Observability</p><h3 className="mt-1 text-xl font-black">{ramzyText("سجل تشغيل رمزي", "Ramzy Runtime Audit")}</h3></div><Button variant="soft" onClick={load} disabled={loading}><RefreshCw size={16} /> {ramzyText("تحديث", "Refresh")}</Button></div>'),
    ('<StatCard value={audit.totals?.runs24h || 0} label="Runs آخر 24 ساعة" icon={Bot} tone="zinc" />', '<StatCard value={audit.totals?.runs24h || 0} label={ramzyText("Runs آخر 24 ساعة", "Runs in the last 24 hours")} icon={Bot} tone="zinc" />'),
    ('<StatCard value={audit.totals?.pendingApprovals || 0} label="موافقات معلقة" icon={ShieldCheck} tone="success" />', '<StatCard value={audit.totals?.pendingApprovals || 0} label={ramzyText("موافقات معلقة", "Pending approvals")} icon={ShieldCheck} tone="success" />'),
    ('<StatCard value={audit.totals?.failedRuns24h || 0} label="Runs فاشلة" icon={ShieldCheck} tone={audit.totals?.failedRuns24h ? "danger" : "success"} />', '<StatCard value={audit.totals?.failedRuns24h || 0} label={ramzyText("Runs فاشلة", "Failed runs")} icon={ShieldCheck} tone={audit.totals?.failedRuns24h ? "danger" : "success"} />'),
    ('<thead><tr className="border-b text-slate-500"><th className="p-3 text-start">الوقت</th><th className="p-3 text-start">Provider / Model</th><th className="p-3 text-start">الحالة</th><th className="p-3 text-start">User ID</th><th className="p-3 text-start">الخطأ</th></tr></thead>', '<thead><tr className="border-b text-slate-500"><th className="p-3 text-start">{ramzyText("الوقت", "Time")}</th><th className="p-3 text-start">Provider / Model</th><th className="p-3 text-start">{ramzyText("الحالة", "Status")}</th><th className="p-3 text-start">User ID</th><th className="p-3 text-start">{ramzyText("الخطأ", "Error")}</th></tr></thead>'),
    ('{new Date(run.createdAt).toLocaleString("ar-EG")}', '{new Date(run.createdAt).toLocaleString(ramzyLocale)}'),
]


def die(message, code=1):
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(code)


def run(args, cwd, check=True):
    p = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if p.stdout:
        print(p.stdout, end="")
    if p.stderr:
        print(p.stderr, end="", file=sys.stderr)
    if check and p.returncode:
        die(f"command failed rc={p.returncode}: {' '.join(args)}", 90)
    return p


def main():
    if len(sys.argv) != 3:
        die("usage: generate_phase5_3_5_ramzy.py REPO_ROOT OUTPUT_PATCH", 2)

    root = Path(sys.argv[1]).resolve()
    output = Path(sys.argv[2]).resolve()
    target = root / TARGET

    if not (root / ".git").is_dir():
        die("not a git repository", 3)
    if not target.is_file():
        die(f"missing target: {TARGET}", 4)

    head = run(["git", "rev-parse", "HEAD"], root).stdout.strip()
    print(f"HEAD={head}")
    if head != EXPECTED_HEAD:
        die(f"HEAD mismatch expected={EXPECTED_HEAD} actual={head}", 5)

    blob = run(["git", "hash-object", TARGET], root).stdout.strip()
    print(f"SOURCE_BLOB={blob}")
    if blob != EXPECTED_BLOB:
        die(f"blob mismatch expected={EXPECTED_BLOB} actual={blob}", 6)

    if run(["git", "diff", "--cached", "--", TARGET], root).stdout.strip():
        die("target has staged changes", 7)
    if run(["git", "diff", "--", TARGET], root).stdout.strip():
        die("target has tracked local changes", 8)

    raw = target.read_bytes()
    if b"\r\n" in raw:
        die("CRLF detected", 9)
    terminal_newline = raw.endswith(b"\n")
    text = raw.decode("utf-8")

    for idx, (old, new) in enumerate(REPLACEMENTS, start=1):
        count = text.count(old)
        print(f"REPLACEMENT_{idx}_MATCHES={count}")
        if count != 1:
            die(f"replacement {idx} expected exactly 1 match, found {count}", 20 + idx)
        text = text.replace(old, new, 1)

    tmp = Path(tempfile.mkdtemp(prefix="tos-phase5-3-5-ramzy-"))
    try:
        run(["git", "init", "-q"], tmp)
        run(["git", "config", "user.email", "phase5-3-5@tos.local"], tmp)
        run(["git", "config", "user.name", "TOS Phase 5.3.5 Generator"], tmp)
        tmp_target = tmp / TARGET
        tmp_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(target, tmp_target)
        run(["git", "add", "--", TARGET], tmp)
        run(["git", "commit", "-qm", "exact phase 5.3.5 baseline"], tmp)

        encoded = text.encode("utf-8")
        if terminal_newline and not encoded.endswith(b"\n"):
            encoded += b"\n"
        elif not terminal_newline and encoded.endswith(b"\n"):
            encoded = encoded[:-1]
        tmp_target.write_bytes(encoded)

        diff = subprocess.run(["git", "diff", "--binary", "--full-index", "--", TARGET], cwd=tmp, text=True, capture_output=True)
        if diff.returncode or not diff.stdout.strip():
            die("failed to generate patch", 70)
        output.write_text(diff.stdout, encoding="utf-8", newline="\n")
        print(f"GENERATED_PATCH_SHA256={hashlib.sha256(output.read_bytes()).hexdigest()}")

        numstat = run(["git", "apply", "--numstat", str(output)], root).stdout.strip().splitlines()
        paths = {row.split("\t")[-1] for row in numstat if row.strip()}
        if paths != {TARGET}:
            die(f"unexpected patch paths: {sorted(paths)}", 71)
        print("PARSER=PASS")
        run(["git", "apply", "--check", str(output)], root)
        print("APPLY_CHECK=PASS")
        print("GENERATION_MODE=RAMZY_FULL_FILE_EXACT_BLOB_LOCALIZATION")
        print("PHASE5_3_5_RAMZY_GENERATOR=PASS")
        print(f"OUTPUT={output}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
