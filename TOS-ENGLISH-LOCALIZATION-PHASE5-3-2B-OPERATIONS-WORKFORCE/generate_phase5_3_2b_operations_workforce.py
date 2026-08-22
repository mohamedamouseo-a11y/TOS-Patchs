#!/usr/bin/env python3
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

EXPECTED_HEAD = "5311de3e893eeecbd46a2741f8c535836962f0fe"
TARGET = "frontend/src/pages/SettingsPage.jsx"
EXPECTED_BLOB = "d3b450daab982c9ab24dcf7f82b373087b3bbc6b"
REGION_START = "function SettingsOperationsInfo({ user }) {"
REGION_END = "function SettingsSectionHeader({ section }) {"

REPLACEMENTS = [
    (
        '  const opsText = (ar, en) => (isAr ? ar : en);\n',
        '  const opsText = (ar, en) => (isAr ? ar : en);\n  const workforceDayLabel = { SUN: opsText("الأحد", "Sunday"), MON: opsText("الاثنين", "Monday"), TUE: opsText("الثلاثاء", "Tuesday"), WED: opsText("الأربعاء", "Wednesday"), THU: opsText("الخميس", "Thursday"), FRI: opsText("الجمعة", "Friday"), SAT: opsText("السبت", "Saturday") };\n',
        1,
    ),
    (
        '{ key: "workforce", label: "سياسات الدوام والإجازات", icon: CalendarDays },',
        '{ key: "workforce", label: opsText("سياسات الدوام والإجازات", "Workforce & Leave Policies"), icon: CalendarDays },',
        1,
    ),
    (
        'throw new Error("تم إرسال الإعدادات لكن القيم العائدة من السيرفر لا تطابق القيم المطلوبة.");',
        'throw new Error(opsText("تم إرسال الإعدادات لكن القيم العائدة من السيرفر لا تطابق القيم المطلوبة.", "Settings were sent, but the values returned by the server do not match the requested values."));',
        1,
    ),
    ('>سياسات الدوام والإجازات</h4>', '>{opsText("سياسات الدوام والإجازات", "Workforce & Leave Policies")}</h4>', 1),
    ('>الحضور والاستراحة وShadowing وأنواع الإجازات في تبويب موحد.</p>', '>{opsText("الحضور والاستراحة وShadowing وأنواع الإجازات في تبويب موحد.", "Attendance, breaks, Shadowing, and leave types in one unified section.")}</p>', 1),
    (
        '''                    {[\n                      ["attendance", "الحضور والانصراف", SlidersHorizontal],\n                      ["break", "إعدادات الاستراحة", Coffee],\n                      ["shadowing", "Shadowing والتغطيات", UserRound],\n                      ["leaves", "أنواع الإجازات", CalendarDays],\n                    ].map(([key, label, Icon]) =>''',
        '''                    {[\n                      ["attendance", opsText("الحضور والانصراف", "Attendance & Clock-out"), SlidersHorizontal],\n                      ["break", opsText("إعدادات الاستراحة", "Break Settings"), Coffee],\n                      ["shadowing", opsText("Shadowing والتغطيات", "Shadowing & Coverage"), UserRound],\n                      ["leaves", opsText("أنواع الإجازات", "Leave Types"), CalendarDays],\n                    ].map(([key, label, Icon]) =>''',
        1,
    ),
    ('>الحضور والانصراف</h5><p className="mt-1 text-xs font-bold text-zinc-400">ضبط مدة الانصراف التلقائي عند توقف اتصال Heartbeat.</p>', '>{opsText("الحضور والانصراف", "Attendance & Clock-out")}</h5><p className="mt-1 text-xs font-bold text-zinc-400">{opsText("ضبط مدة الانصراف التلقائي عند توقف اتصال Heartbeat.", "Configure automatic clock-out when the Heartbeat connection stops.")}</p>', 1),
    ('<span>مدة الانصراف التلقائي عند توقف الاتصال بالدقائق</span>', '<span>{opsText("مدة الانصراف التلقائي عند توقف الاتصال بالدقائق", "Automatic clock-out after connection loss (minutes)")}</span>', 1),
    ('>القيمة المسموحة للـ Auto Logout من {heartbeatMin} إلى {heartbeatMax} دقيقة.</Notice>', '>{opsText(`القيمة المسموحة للـ Auto Logout من ${heartbeatMin} إلى ${heartbeatMax} دقيقة.`, `Allowed Auto Logout value is ${heartbeatMin} to ${heartbeatMax} minutes.`)}</Notice>', 1),
    ('>يسجل النظام الانصراف عند انقطاع الاتصال لمدة تتجاوز القيمة المحددة، ولا يخص تسجيل الخروج من حساب النظام.</p>', '>{opsText("يسجل النظام الانصراف عند انقطاع الاتصال لمدة تتجاوز القيمة المحددة، ولا يخص تسجيل الخروج من حساب النظام.", "The system records clock-out when the connection is lost beyond the configured duration; this does not sign the user out of their account.")}</p>', 1),
    ('>إعدادات الاستراحة</h5><p className="mt-1 text-xs font-bold text-zinc-400">تحديد أيام ووقت الاستراحة التي تظهر في THRS.</p>', '>{opsText("إعدادات الاستراحة", "Break Settings")}</h5><p className="mt-1 text-xs font-bold text-zinc-400">{opsText("تحديد أيام ووقت الاستراحة التي تظهر في THRS.", "Choose the break days and time shown in THRS.")}</p>', 1),
    ('>{form.breakEnabled ? "الاستراحة مفعلة" : "الاستراحة متوقفة"}</button>', '>{form.breakEnabled ? opsText("الاستراحة مفعلة", "Break enabled") : opsText("الاستراحة متوقفة", "Break disabled")}</button>', 1),
    ('>أيام تطبيق الاستراحة</p>', '>{opsText("أيام تطبيق الاستراحة", "Break days")}</p>', 1),
    ('>{day.label}</button>', '>{workforceDayLabel[day.key] || day.label}</button>', 1),
    ('<span>من</span>', '<span>{opsText("من", "From")}</span>', 1),
    ('<span>إلى</span>', '<span>{opsText("إلى", "To")}</span>', 1),
    ('>Shadowing والتغطيات</h5><p className="mt-1 text-xs font-bold text-zinc-400">تفعيل مرحلة التغطية وضبط قاعدة الاستئذانات بالساعات.</p>', '>{opsText("Shadowing والتغطيات", "Shadowing & Coverage")}</h5><p className="mt-1 text-xs font-bold text-zinc-400">{opsText("تفعيل مرحلة التغطية وضبط قاعدة الاستئذانات بالساعات.", "Enable coverage and configure hourly-permission rules.")}</p>', 1),
    ('>تفعيل نظام Shadowing بالكامل</span><span className="mt-1 block text-[11px] font-bold opacity-70">عند إيقافه لن تُطلب تغطية لأي إجازة أو استئذان مهما كانت القواعد المحددة.</span>', '>{opsText("تفعيل نظام Shadowing بالكامل", "Enable the full Shadowing system")}</span><span className="mt-1 block text-[11px] font-bold opacity-70">{opsText("عند إيقافه لن تُطلب تغطية لأي إجازة أو استئذان مهما كانت القواعد المحددة.", "When disabled, no leave or permission request will require coverage regardless of the configured rules.")}</span>', 1),
    ('<span>تطبيق Shadowing على الاستئذانات</span>', '<span>{opsText("تطبيق Shadowing على الاستئذانات", "Apply Shadowing to hourly permissions")}</span>', 1),
    ('<span>الحد الأدنى بالساعات</span>', '<span>{opsText("الحد الأدنى بالساعات", "Minimum duration (hours)")}</span>', 1),
    (
        '<span>الحالة عند بلوغ الحد</span><select value={form.generalSettings?.shadowingSettings?.hourlyPermissionMode || "REQUIRED"} onChange={(event) => updateShadowingSettings({ hourlyPermissionMode: event.target.value })} className="h-12 rounded-2xl border border-zinc-200 bg-white px-4 text-sm font-bold dark:border-white/10 dark:bg-zinc-950"><option value="REQUIRED">إجباري</option><option value="OPTIONAL">اختياري</option><option value="OFF">غير مطلوب</option></select>',
        '<span>{opsText("الحالة عند بلوغ الحد", "Rule at threshold")}</span><select value={form.generalSettings?.shadowingSettings?.hourlyPermissionMode || "REQUIRED"} onChange={(event) => updateShadowingSettings({ hourlyPermissionMode: event.target.value })} className="h-12 rounded-2xl border border-zinc-200 bg-white px-4 text-sm font-bold dark:border-white/10 dark:bg-zinc-950"><option value="REQUIRED">{opsText("إجباري", "Required")}</option><option value="OPTIONAL">{opsText("اختياري", "Optional")}</option><option value="OFF">{opsText("غير مطلوب", "Not required")}</option></select>',
        1,
    ),
    ('>أنواع الإجازات القادمة من THRS</h5><p className="mt-1 text-xs font-bold text-zinc-400">حدد ما إذا كانت التغطية إجبارية أو اختيارية أو غير مطلوبة لكل نوع.</p>', '>{opsText("أنواع الإجازات القادمة من THRS", "Leave Types from THRS")}</h5><p className="mt-1 text-xs font-bold text-zinc-400">{opsText("حدد ما إذا كانت التغطية إجبارية أو اختيارية أو غير مطلوبة لكل نوع.", "Choose whether coverage is required, optional, or not required for each type.")}</p>', 1),
    ('>{isHourly ? "محسوبة بالساعات — تُدار من قاعدة الاستئذانات" : "محسوبة بالأيام"}</p>', '>{isHourly ? opsText("محسوبة بالساعات — تُدار من قاعدة الاستئذانات", "Calculated in hours — managed by the hourly-permission rule") : opsText("محسوبة بالأيام", "Calculated in days")}</p>', 1),
    (
        '<option value="REQUIRED">إجباري</option><option value="OPTIONAL">اختياري</option><option value="OFF">غير مطلوب</option></select></div>; }) : <p className="px-4 py-8 text-center text-xs font-bold text-zinc-400">تعذر تحميل أنواع الإجازات من THRS حاليًا.</p>',
        '<option value="REQUIRED">{opsText("إجباري", "Required")}</option><option value="OPTIONAL">{opsText("اختياري", "Optional")}</option><option value="OFF">{opsText("غير مطلوب", "Not required")}</option></select></div>; }) : <p className="px-4 py-8 text-center text-xs font-bold text-zinc-400">{opsText("تعذر تحميل أنواع الإجازات من THRS حاليًا.", "Unable to load leave types from THRS right now.")}</p>',
        1,
    ),
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
        die("usage: generate_phase5_3_2b_operations_workforce.py REPO_ROOT OUTPUT_PATCH", 2)
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

    raw = target.read_bytes()
    if b"\r\n" in raw:
        die("CRLF detected", 8)
    terminal_newline = raw.endswith(b"\n")
    text = raw.decode("utf-8")
    start = text.find(REGION_START)
    end = text.find(REGION_END, start + len(REGION_START))
    if start < 0 or end < 0:
        die("Operations region markers missing", 9)
    before, region, after = text[:start], text[start:end], text[end:]

    for idx, (old, new, expected) in enumerate(REPLACEMENTS, start=1):
        count = region.count(old)
        print(f"REPLACEMENT_{idx}_MATCHES={count}")
        if count != expected:
            die(f"replacement {idx} expected {expected} exact matches, found {count}", 20 + idx)
        region = region.replace(old, new, expected)

    text = before + region + after
    tmp = Path(tempfile.mkdtemp(prefix="tos-phase5-3-2b-"))
    try:
        run(["git", "init", "-q"], tmp)
        run(["git", "config", "user.email", "phase5-3-2b@tos.local"], tmp)
        run(["git", "config", "user.name", "TOS Phase 5.3.2B Generator"], tmp)
        tmp_target = tmp / TARGET
        tmp_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(target, tmp_target)
        run(["git", "add", "--", TARGET], tmp)
        run(["git", "commit", "-qm", "exact post-5.3.2a baseline"], tmp)
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
        print("GENERATION_MODE=WORKFORCE_REGION_SCOPED_FROM_EXACT_POST_5_3_2A_SOURCE")
        print("PHASE5_3_2B_OPERATIONS_WORKFORCE_GENERATOR=PASS")
        print(f"OUTPUT={output}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
