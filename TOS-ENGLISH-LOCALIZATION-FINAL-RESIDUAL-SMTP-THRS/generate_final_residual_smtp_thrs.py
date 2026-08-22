#!/usr/bin/env python3
from __future__ import annotations

import difflib
import hashlib
import subprocess
import sys
from pathlib import Path

EXPECTED_HEAD = "665d1fd5d2a5f043a1649c88ce6f737c1d46c2d4"
TARGET = "frontend/src/pages/SettingsPage.jsx"
EXPECTED_BLOB = "4247bc629bfa6a44842b3cacc770aa782c999dff"
MODE = "FINAL_SMTP_THRS_EXACT_BLOB_LOCALIZATION"


def run(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def blob_sha(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: generate_final_residual_smtp_thrs.py <repo> <patch-output>", file=sys.stderr)
        return 2

    repo = Path(sys.argv[1]).resolve()
    patch_out = Path(sys.argv[2]).resolve()
    target = repo / TARGET

    head = run(repo, "rev-parse", "HEAD")
    print(f"HEAD={head}")
    if head != EXPECTED_HEAD:
        raise SystemExit(f"HEAD_MISMATCH expected={EXPECTED_HEAD} actual={head}")

    staged = run(repo, "diff", "--cached", "--name-only")
    tracked = run(repo, "diff", "--name-only")
    print(f"STAGED_TRACKED={staged or 'NONE'}")
    print(f"UNSTAGED_TRACKED={tracked or 'NONE'}")
    if staged or tracked:
        raise SystemExit("TRACKED_WORKTREE_NOT_CLEAN")

    current_blob = run(repo, "hash-object", TARGET)
    print(f"SOURCE_BLOB_BEFORE={current_blob}")
    if current_blob != EXPECTED_BLOB:
        raise SystemExit(f"SOURCE_BLOB_MISMATCH expected={EXPECTED_BLOB} actual={current_blob}")

    original = target.read_text(encoding="utf-8")

    replacements = [
        (
            'function EmailSettingsAdmin({ user }) {\n  const [status, setStatus] = useState(null);',
            'function EmailSettingsAdmin({ user }) {\n  const { isAr } = usePreferences();\n  const smtpText = (ar, en) => (isAr ? ar : en);\n  const [status, setStatus] = useState(null);',
        ),
        (
            '      setError(getErrorMessage(err, "تعذر تحميل إعدادات البريد."));',
            '      setError(getErrorMessage(err, smtpText("تعذر تحميل إعدادات البريد.", "Unable to load email settings.")));',
        ),
        (
            '      setMessage("تم حفظ إعدادات البريد SMTP.");\n    } catch (err) {\n      setError(getErrorMessage(err, "تعذر حفظ إعدادات البريد."));',
            '      setMessage(smtpText("تم حفظ إعدادات البريد SMTP.", "SMTP email settings saved."));\n    } catch (err) {\n      setError(getErrorMessage(err, smtpText("تعذر حفظ إعدادات البريد.", "Unable to save email settings.")));',
        ),
        (
            '    const parts = [result?.message || "تعذر إرسال رسالة الاختبار."];\n    const detailParts = [];\n    if (result?.stage) detailParts.push(`المرحلة: ${result.stage === "verify" ? "فحص الاتصال" : "إرسال الرسالة"}`);\n    if (result?.reason) detailParts.push(`السبب: ${result.reason}`);\n    if (result?.details?.code) detailParts.push(`الكود: ${result.details.code}`);\n    if (result?.details?.responseCode) detailParts.push(`SMTP: ${result.details.responseCode}`);\n    if (result?.details?.response) detailParts.push(`رد الخادم: ${result.details.response}`);',
            '    const parts = [result?.message || smtpText("تعذر إرسال رسالة الاختبار.", "Unable to send the test email.")];\n    const detailParts = [];\n    if (result?.stage) detailParts.push(smtpText(`المرحلة: ${result.stage === "verify" ? "فحص الاتصال" : "إرسال الرسالة"}`, `Stage: ${result.stage === "verify" ? "Connection verification" : "Message delivery"}`));\n    if (result?.reason) detailParts.push(smtpText(`السبب: ${result.reason}`, `Reason: ${result.reason}`));\n    if (result?.details?.code) detailParts.push(smtpText(`الكود: ${result.details.code}`, `Code: ${result.details.code}`));\n    if (result?.details?.responseCode) detailParts.push(`SMTP: ${result.details.responseCode}`);\n    if (result?.details?.response) detailParts.push(smtpText(`رد الخادم: ${result.details.response}`, `Server response: ${result.details.response}`));',
        ),
        (
            '      setMessage(`تم إرسال رسالة اختبار إلى ${result.to || form.testTo || form.from}.`);\n    } catch (err) {\n      setError(getErrorMessage(err, "تعذر إرسال رسالة الاختبار."));',
            '      setMessage(smtpText(`تم إرسال رسالة اختبار إلى ${result.to || form.testTo || form.from}.`, `Test email sent to ${result.to || form.testTo || form.from}.`));\n    } catch (err) {\n      setError(getErrorMessage(err, smtpText("تعذر إرسال رسالة الاختبار.", "Unable to send the test email.")));',
        ),
        (
            '  const testDisabledReason = !status?.configured\n    ? "احفظ إعدادات SMTP المكتملة قبل اختبار الإرسال."\n    : !smtpFieldsReady\n      ? "أكمل بيانات SMTP الأساسية وكلمة المرور قبل الاختبار."\n      : "";',
            '  const testDisabledReason = !status?.configured\n    ? smtpText("احفظ إعدادات SMTP المكتملة قبل اختبار الإرسال.", "Save complete SMTP settings before testing delivery.")\n    : !smtpFieldsReady\n      ? smtpText("أكمل بيانات SMTP الأساسية وكلمة المرور قبل الاختبار.", "Complete the required SMTP fields and password before testing.")\n      : "";',
        ),
        (
            '          <h3 className="mt-1 text-2xl font-black text-zinc-950 dark:text-white">إعدادات البريد SMTP</h3>\n          <p className="tos-muted mt-2">تستخدم هذه الإعدادات في دعوات الفريق واستعادة كلمة المرور وإرسال روابط التعيين.</p>',
            '          <h3 className="mt-1 text-2xl font-black text-zinc-950 dark:text-white">{smtpText("إعدادات البريد SMTP", "SMTP Email Settings")}</h3>\n          <p className="tos-muted mt-2">{smtpText("تستخدم هذه الإعدادات في دعوات الفريق واستعادة كلمة المرور وإرسال روابط التعيين.", "These settings are used for team invitations, password recovery, and setup links.")}</p>',
        ),
        (
            '        <StatCard value={loading ? "..." : status?.configured ? "مفعّل" : "غير مفعّل"} label="حالة البريد" note={status?.source === "DATABASE" ? "من لوحة التحكم" : status?.source === "ENV" ? "من السيرفر" : "SMTP"} icon={MailPlus} tone={status?.configured ? "success" : "danger"} />\n        <StatCard value={status?.hasPassword ? "محفوظة" : "ناقصة"} label="كلمة المرور" note="مخفية للأمان" icon={Shield} tone={status?.hasPassword ? "success" : "zinc"} />\n        <StatCard value={status?.host ? "موجود" : "ناقص"} label="SMTP Host" note="Server" icon={Terminal} tone={status?.host ? "success" : "zinc"} />\n        <StatCard value={status?.from ? "موجود" : "ناقص"} label="From Email" note="Sender" icon={MailPlus} tone={status?.from ? "success" : "zinc"} />',
            '        <StatCard value={loading ? "..." : status?.configured ? smtpText("مفعّل", "Enabled") : smtpText("غير مفعّل", "Disabled")} label={smtpText("حالة البريد", "Email status")} note={status?.source === "DATABASE" ? smtpText("من لوحة التحكم", "From control panel") : status?.source === "ENV" ? smtpText("من السيرفر", "From server") : "SMTP"} icon={MailPlus} tone={status?.configured ? "success" : "danger"} />\n        <StatCard value={status?.hasPassword ? smtpText("محفوظة", "Saved") : smtpText("ناقصة", "Missing")} label={smtpText("كلمة المرور", "Password")} note={smtpText("مخفية للأمان", "Hidden for security")} icon={Shield} tone={status?.hasPassword ? "success" : "zinc"} />\n        <StatCard value={status?.host ? smtpText("موجود", "Available") : smtpText("ناقص", "Missing")} label="SMTP Host" note="Server" icon={Terminal} tone={status?.host ? "success" : "zinc"} />\n        <StatCard value={status?.from ? smtpText("موجود", "Available") : smtpText("ناقص", "Missing")} label="From Email" note="Sender" icon={MailPlus} tone={status?.from ? "success" : "zinc"} />',
        ),
        (
            '        <Notice type="warning" className="mt-4">إرسال الدعوات وروابط استعادة كلمة المرور لن يعمل تلقائيًا إلا بعد ضبط SMTP أو تفعيل إعداداته من السيرفر. سيظل إنشاء ونسخ الروابط اليدوية متاحًا من صفحة الفريق.</Notice>',
            '        <Notice type="warning" className="mt-4">{smtpText("إرسال الدعوات وروابط استعادة كلمة المرور لن يعمل تلقائيًا إلا بعد ضبط SMTP أو تفعيل إعداداته من السيرفر. سيظل إنشاء ونسخ الروابط اليدوية متاحًا من صفحة الفريق.", "Invitations and password-recovery emails will not be sent automatically until SMTP is configured here or enabled on the server. Manual link creation and copying will remain available from the Team page.")}</Notice>',
        ),
        (
            '          <Field type="password" value={form.pass} onChange={(e) => setField("pass", e.target.value)} disabled={clearPassword} placeholder={status?.hasPassword ? "SMTP Password محفوظة — اتركها فارغة بدون تغيير" : "SMTP Password"} autoComplete="new-password" dir="ltr" />',
            '          <Field type="password" value={form.pass} onChange={(e) => setField("pass", e.target.value)} disabled={clearPassword} placeholder={status?.hasPassword ? smtpText("SMTP Password محفوظة — اتركها فارغة بدون تغيير", "SMTP Password saved — leave blank to keep it unchanged") : "SMTP Password"} autoComplete="new-password" dir="ltr" />',
        ),
        (
            '              استخدام SSL / Secure SMTP',
            '              {smtpText("استخدام SSL / Secure SMTP", "Use SSL / Secure SMTP")}',
        ),
        (
            '                مسح كلمة المرور الحالية عند الحفظ',
            '                {smtpText("مسح كلمة المرور الحالية عند الحفظ", "Clear current password when saving")}',
        ),
        (
            '        <Button type="button" variant="soft" onClick={loadStatus} disabled={loading}><RefreshCw size={17} className={loading ? "animate-spin" : ""} />{loading ? "جاري التحديث..." : "تحديث الحالة"}</Button>\n        <Button type="button" onClick={saveSettings} disabled={Boolean(actionLoading)}>{actionLoading === "save" ? "جاري الحفظ..." : "حفظ إعدادات البريد"}</Button>',
            '        <Button type="button" variant="soft" onClick={loadStatus} disabled={loading}><RefreshCw size={17} className={loading ? "animate-spin" : ""} />{loading ? smtpText("جاري التحديث...", "Refreshing...") : smtpText("تحديث الحالة", "Refresh status")}</Button>\n        <Button type="button" onClick={saveSettings} disabled={Boolean(actionLoading)}>{actionLoading === "save" ? smtpText("جاري الحفظ...", "Saving...") : smtpText("حفظ إعدادات البريد", "Save email settings")}</Button>',
        ),
        (
            '        <Field value={form.testTo} onChange={(e) => setField("testTo", e.target.value)} placeholder="بريد اختبار اختياري" dir="ltr" />\n        <Button type="button" variant="soft" onClick={testEmail} disabled={!canTestSmtp} title={testDisabledReason}>{actionLoading === "test" ? "جاري الاختبار..." : "اختبار الإرسال"}</Button>',
            '        <Field value={form.testTo} onChange={(e) => setField("testTo", e.target.value)} placeholder={smtpText("بريد اختبار اختياري", "Optional test email")} dir="ltr" />\n        <Button type="button" variant="soft" onClick={testEmail} disabled={!canTestSmtp} title={testDisabledReason}>{actionLoading === "test" ? smtpText("جاري الاختبار...", "Testing...") : smtpText("اختبار الإرسال", "Test sending")}</Button>',
        ),
        (
            '          تم ربط {employeeMapping.matchedCount} موظف تلقائيًا بين TOS و THRS اعتمادًا على الإيميل الرسمي. {employeeMapping.unmatchedCount ? `عدد غير مطابق: ${employeeMapping.unmatchedCount}.` : ""}',
            '          {thrsText(`تم ربط ${employeeMapping.matchedCount} موظف تلقائيًا بين TOS و THRS اعتمادًا على الإيميل الرسمي.${employeeMapping.unmatchedCount ? ` عدد غير مطابق: ${employeeMapping.unmatchedCount}.` : ""}`, `${employeeMapping.matchedCount} employees were automatically mapped between TOS and THRS using their official email addresses.${employeeMapping.unmatchedCount ? ` Unmatched: ${employeeMapping.unmatchedCount}.` : ""}`)}',
        ),
    ]

    updated = original
    for index, (old, new) in enumerate(replacements, start=1):
        count = updated.count(old)
        print(f"REPLACEMENT_{index}_MATCHES={count}")
        if count != 1:
            raise SystemExit(f"REPLACEMENT_{index}_COUNT_MISMATCH expected=1 actual={count}")
        updated = updated.replace(old, new, 1)

    if updated == original:
        raise SystemExit("NO_CHANGES_GENERATED")

    patch = "\n".join(
        difflib.unified_diff(
            original.splitlines(),
            updated.splitlines(),
            fromfile=f"a/{TARGET}",
            tofile=f"b/{TARGET}",
            lineterm="",
        )
    ) + "\n"
    patch_out.parent.mkdir(parents=True, exist_ok=True)
    patch_out.write_text(patch, encoding="utf-8")

    after_blob = blob_sha(updated.encode("utf-8"))
    print(f"SOURCE_BLOB_AFTER_EXPECTED={after_blob}")
    print(f"PATCH_SHA256={hashlib.sha256(patch.encode('utf-8')).hexdigest()}")

    check = subprocess.run(["git", "-C", str(repo), "apply", "--check", str(patch_out)], text=True, capture_output=True)
    if check.returncode != 0:
        print(check.stdout, end="")
        print(check.stderr, end="", file=sys.stderr)
        raise SystemExit("APPLY_CHECK=FAIL")

    print("PARSER=PASS")
    print("APPLY_CHECK=PASS")
    print(f"GENERATION_MODE={MODE}")
    print("FINAL_SMTP_THRS_GENERATOR=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
