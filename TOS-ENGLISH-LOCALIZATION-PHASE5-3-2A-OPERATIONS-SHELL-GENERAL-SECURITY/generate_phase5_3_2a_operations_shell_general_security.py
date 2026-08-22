#!/usr/bin/env python3
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

EXPECTED_HEAD = "5311de3e893eeecbd46a2741f8c535836962f0fe"
TARGET = "frontend/src/pages/SettingsPage.jsx"
EXPECTED_BLOB = "fcc890c34ce4d630e75b5575fa0ad5321bcdefeb"
REGION_START = "function SettingsOperationsInfo({ user }) {"
REGION_END = "function SettingsSectionHeader({ section }) {"

REPLACEMENTS = [
    (
        '''function SettingsOperationsInfo({ user }) {\n  const [settings, setSettings] = useState(null);''',
        '''function SettingsOperationsInfo({ user }) {\n  const { isAr } = usePreferences();\n  const opsText = (ar, en) => (isAr ? ar : en);\n  const [settings, setSettings] = useState(null);''',
        1,
    ),
    (
        '''  const operationsSubSections = [\n    { key: "generalNotifications", label: "النظام العام والتنبيهات", icon: Bell },\n    { key: "security", label: "الأمان والجلسات", icon: Shield },\n    { key: "workforce", label: "سياسات الدوام والإجازات", icon: CalendarDays },\n    { key: "projectsTasks", label: "المشاريع والمهام", icon: FolderKanban },\n  ];''',
        '''  const operationsSubSections = [\n    { key: "generalNotifications", label: opsText("النظام العام والتنبيهات", "General System & Notifications"), icon: Bell },\n    { key: "security", label: opsText("الأمان والجلسات", "Security & Sessions"), icon: Shield },\n    { key: "workforce", label: opsText("سياسات الدوام والإجازات", "Workforce & Leave Policies"), icon: CalendarDays },\n    { key: "projectsTasks", label: opsText("المشاريع والمهام", "Projects & Tasks"), icon: FolderKanban },\n  ];''',
        1,
    ),
    ('''setError(getErrorMessage(err, "تعذر تحميل إعدادات التشغيل."));''', '''setError(getErrorMessage(err, opsText("تعذر تحميل إعدادات التشغيل.", "Unable to load Operations Settings.")));''', 1),
    ('''>إعدادات التشغيل</h3>''', '''>{opsText("إعدادات التشغيل", "Operations Settings")}</h3>''', 1),
    ('''>أربعة أقسام موحدة لإدارة النظام والأمان وسياسات الدوام والمشاريع دون تكرار أو تكدس.</p>''', '''>{opsText("أربعة أقسام موحدة لإدارة النظام والأمان وسياسات الدوام والمشاريع دون تكرار أو تكدس.", "Four unified sections for system, security, workforce policies, and projects without duplication or clutter.")}</p>''', 1),
    ('''{loading ? "جاري التحديث..." : "تحديث البيانات"}''', '''{loading ? opsText("جاري التحديث...", "Refreshing...") : opsText("تحديث البيانات", "Refresh data")}''', 1),
    ('''>أقسام الإعدادات</p>''', '''>{opsText("أقسام الإعدادات", "Settings sections")}</p>''', 1),
    ('''            يتم حفظ كل قسم بصورة مستقلة، لذلك لن يؤدي حفظ تبويب إلى مسح إعدادات التبويبات الأخرى.''', '''            {opsText("يتم حفظ كل قسم بصورة مستقلة، لذلك لن يؤدي حفظ تبويب إلى مسح إعدادات التبويبات الأخرى.", "Each section is saved independently, so saving one tab will not overwrite settings in other tabs.")}''', 1),
    ('''<div className="grid min-h-[420px] place-items-center text-sm font-black text-zinc-400"><RefreshCw className="mb-3 animate-spin" /> جاري تحميل إعدادات التشغيل...</div>''', '''<div className="grid min-h-[420px] place-items-center text-sm font-black text-zinc-400"><RefreshCw className="mb-3 animate-spin" /> {opsText("جاري تحميل إعدادات التشغيل...", "Loading Operations Settings...")}</div>''', 1),

    ('''>النظام العام والتنبيهات</h4>''', '''>{opsText("النظام العام والتنبيهات", "General System & Notifications")}</h4>''', 1),
    ('''>الإعدادات العامة وقنوات التحديث والتنبيه في مكان واحد.</p>''', '''>{opsText("الإعدادات العامة وقنوات التحديث والتنبيه في مكان واحد.", "General settings, update channels, and notifications in one place.")}</p>''', 1),
    ('''>إعدادات النظام العامة</h5>''', '''>{opsText("إعدادات النظام العامة", "General system settings")}</h5>''', 1),
    ('''>اللغة والمنطقة الزمنية وحالة الصيانة.</p>''', '''>{opsText("اللغة والمنطقة الزمنية وحالة الصيانة.", "Default language, timezone, and maintenance status.")}</p>''', 1),
    ('''<span>اللغة الافتراضية</span>''', '''<span>{opsText("اللغة الافتراضية", "Default language")}</span>''', 1),
    ('''<option value="ar">العربية</option>''', '''<option value="ar">{opsText("العربية", "Arabic")}</option>''', 1),
    ('''<span>المنطقة الزمنية</span>''', '''<span>{opsText("المنطقة الزمنية", "Timezone")}</span>''', 1),
    ('''>وضع الصيانة</span><span className="mt-1 block text-[11px] text-zinc-400">إيقاف وصول المستخدمين مؤقتًا</span>''', '''>{opsText("وضع الصيانة", "Maintenance mode")}</span><span className="mt-1 block text-[11px] text-zinc-400">{opsText("إيقاف وصول المستخدمين مؤقتًا", "Temporarily block user access")}</span>''', 1),
    ('''>التحديثات والتنبيهات</h5>''', '''>{opsText("التحديثات والتنبيهات", "Updates & notifications")}</h5>''', 1),
    ('''>اختر القنوات التي يسمح للنظام باستخدامها.</p>''', '''>{opsText("اختر القنوات التي يسمح للنظام باستخدامها.", "Choose which channels the system is allowed to use.")}</p>''', 1),
    (
        '''                      {[\n                        ["realtimeUpdatesEnabled", "التحديثات الفورية", "مزامنة التغييرات الجديدة مباشرة", RefreshCw],\n                        ["systemAlertsEnabled", "تنبيهات النظام", "إظهار التنبيهات داخل المنصة", Bell],\n                        ["emailNotificationsEnabled", "تنبيهات البريد الإلكتروني", "إرسال التنبيهات المهمة عبر البريد", MailPlus],\n                      ].map(([key, label, note, Icon]) => (''',
        '''                      {[\n                        ["realtimeUpdatesEnabled", opsText("التحديثات الفورية", "Realtime updates"), opsText("مزامنة التغييرات الجديدة مباشرة", "Sync new changes immediately"), RefreshCw],\n                        ["systemAlertsEnabled", opsText("تنبيهات النظام", "System alerts"), opsText("إظهار التنبيهات داخل المنصة", "Show alerts inside the platform"), Bell],\n                        ["emailNotificationsEnabled", opsText("تنبيهات البريد الإلكتروني", "Email notifications"), opsText("إرسال التنبيهات المهمة عبر البريد", "Send important alerts by email"), MailPlus],\n                      ].map(([key, label, note, Icon]) => (''',
        1,
    ),

    ('''>الأمان والجلسات</h4>''', '''>{opsText("الأمان والجلسات", "Security & Sessions")}</h4>''', 1),
    ('''>إعدادات حماية الحساب وحدود محاولات الدخول والجلسة.</p>''', '''>{opsText("إعدادات حماية الحساب وحدود محاولات الدخول والجلسة.", "Account protection, login-attempt limits, and session settings.")}</p>''', 1),
    ('''>حماية الحساب</h5>''', '''>{opsText("حماية الحساب", "Account protection")}</h5>''', 1),
    ('''>التحقق الثنائي 2FA</span><span className="mt-1 block text-[11px] font-bold text-zinc-400">طبقة حماية إضافية عند تسجيل الدخول</span>''', '''>{opsText("التحقق الثنائي 2FA", "Two-factor authentication (2FA)")}</span><span className="mt-1 block text-[11px] font-bold text-zinc-400">{opsText("طبقة حماية إضافية عند تسجيل الدخول", "Extra protection at sign-in")}</span>''', 1),
    ('''<span>الحد الأقصى لمحاولات الدخول الفاشلة</span>''', '''<span>{opsText("الحد الأقصى لمحاولات الدخول الفاشلة", "Maximum failed login attempts")}</span>''', 1),
    ('''>إدارة الجلسات</h5>''', '''>{opsText("إدارة الجلسات", "Session management")}</h5>''', 1),
    ('''<span>انتهاء جلسة الحساب عند عدم النشاط بالدقائق</span>''', '''<span>{opsText("انتهاء جلسة الحساب عند عدم النشاط بالدقائق", "Account session expires after inactivity (minutes)")}</span>''', 1),
    ('''>هذا الإعداد يخص جلسة دخول الحساب فقط، ولا يرتبط بتسجيل انصراف الموظف من الدوام.</p>''', '''>{opsText("هذا الإعداد يخص جلسة دخول الحساب فقط، ولا يرتبط بتسجيل انصراف الموظف من الدوام.", "This setting applies only to the account login session; it is unrelated to employee clock-out.")}</p>''', 1),

    ('''setMessage(`تم حفظ ${operationsSubSections.find((section) => section.key === activeOpsSection)?.label || "إعدادات التشغيل"} بنجاح.`);''', '''setMessage(opsText(`تم حفظ ${operationsSubSections.find((section) => section.key === activeOpsSection)?.label || "إعدادات التشغيل"} بنجاح.`, `${operationsSubSections.find((section) => section.key === activeOpsSection)?.label || "Operations Settings"} saved successfully.`));''', 1),
    ('''setError(getErrorMessage(err, "تعذر حفظ إعدادات القسم الحالي."));''', '''setError(getErrorMessage(err, opsText("تعذر حفظ إعدادات القسم الحالي.", "Unable to save the current section settings.")));''', 1),
    ('''>سيتم حفظ القسم الحالي فقط دون التأثير على الأقسام الأخرى.</p>''', '''>{opsText("سيتم حفظ القسم الحالي فقط دون التأثير على الأقسام الأخرى.", "Only the current section will be saved; other sections will not be affected.")}</p>''', 1),
    ('''> إعادة تعيين لآخر حفظ</Button>''', '''> {opsText("إعادة تعيين لآخر حفظ", "Reset to last saved")}</Button>''', 1),
    ('''{actionLoading ? "جاري الحفظ..." : "حفظ إعدادات القسم"}''', '''{actionLoading ? opsText("جاري الحفظ...", "Saving...") : opsText("حفظ إعدادات القسم", "Save section settings")}''', 1),
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
        die("usage: generate_phase5_3_2a_operations_shell_general_security.py REPO_ROOT OUTPUT_PATCH", 2)
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

    start = text.find(REGION_START)
    end = text.find(REGION_END, start + len(REGION_START))
    if start < 0 or end < 0:
        die("Operations region markers missing", 10)
    before, region, after = text[:start], text[start:end], text[end:]

    for idx, (old, new, expected) in enumerate(REPLACEMENTS, start=1):
        count = region.count(old)
        print(f"REPLACEMENT_{idx}_MATCHES={count}")
        if count != expected:
            die(f"replacement {idx} expected {expected} exact matches, found {count}", 20 + idx)
        region = region.replace(old, new)

    text = before + region + after
    tmp = Path(tempfile.mkdtemp(prefix="tos-phase5-3-2a-"))
    try:
        run(["git", "init", "-q"], tmp)
        run(["git", "config", "user.email", "phase5-3-2a@tos.local"], tmp)
        run(["git", "config", "user.name", "TOS Phase 5.3.2A Generator"], tmp)
        tmp_target = tmp / TARGET
        tmp_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(target, tmp_target)
        run(["git", "add", "--", TARGET], tmp)
        run(["git", "commit", "-qm", "exact phase 5.3.2a baseline"], tmp)

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
        print("GENERATION_MODE=OPERATIONS_REGION_SCOPED_FROM_EXACT_SOURCE")
        print("PHASE5_3_2A_OPERATIONS_SHELL_GENERAL_SECURITY_GENERATOR=PASS")
        print(f"OUTPUT={output}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
