#!/usr/bin/env python3
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

EXPECTED_HEAD = "77dbd47013cf3706634e28b913719664560ffbc6"
TARGET_SETTINGS = "frontend/src/pages/SettingsPage.jsx"
TARGET_DATABASE = "frontend/src/components/settings/DatabaseBackupAdmin.jsx"
EXPECTED_SETTINGS_BLOB = "c7719283696e1d93a34b9a08e40bad15db50291d"
EXPECTED_DATABASE_BLOB = "872a767af3b6186563c078a6490a6af29b439ed9"

SETTINGS_REPLACEMENTS = [('function formatBackupDate(value) {\n  if (!value) return "—";\n  try { return new Date(value).toLocaleString(); } catch { return "—"; }\n}', 'function formatBackupDate(value, locale) {\n  if (!value) return "—";\n  try { return new Date(value).toLocaleString(locale); } catch { return "—"; }\n}'), ('function SystemBackupAdmin({ user }) {\n  const [status, setStatus] = useState(null);', 'function SystemBackupAdmin({ user }) {\n  const { isAr } = usePreferences();\n  const systemBackupText = (ar, en) => (isAr ? ar : en);\n  const systemBackupLocale = isAr ? "ar-EG" : "en-US";\n  const [status, setStatus] = useState(null);'), ('setError(getErrorMessage(err, "تعذر تحميل إعدادات النسخ الاحتياطي."));', 'setError(getErrorMessage(err, systemBackupText("تعذر تحميل إعدادات النسخ الاحتياطي.", "Unable to load backup settings.")));'), ('await runAction("save", "تم حفظ إعدادات النسخ الاحتياطي.", () => api.systemBackups.updateSettings({', 'await runAction("save", systemBackupText("تم حفظ إعدادات النسخ الاحتياطي.", "Backup settings saved."), () => api.systemBackups.updateSettings({'), ('const result = await runAction("run", "تم تنفيذ Backup ورفعه على Google Drive.", () => api.systemBackups.runNow());', 'const result = await runAction("run", systemBackupText("تم تنفيذ Backup ورفعه على Google Drive.", "Backup completed and uploaded to Google Drive."), () => api.systemBackups.runNow());'), ('<p className="tos-muted mt-2">إعدادات النسخ الاحتياطي تظهر لمدير النظام فقط.</p>', '<p className="tos-muted mt-2">{systemBackupText("إعدادات النسخ الاحتياطي تظهر لمدير النظام فقط.", "Backup settings are available to the System Admin only.")}</p>'), ('<h3 className="mt-1 text-2xl font-black text-zinc-950 dark:text-white">نسخ احتياطي للكود على Google Drive</h3>', '<h3 className="mt-1 text-2xl font-black text-zinc-950 dark:text-white">{systemBackupText("نسخ احتياطي للكود على Google Drive", "Code backup to Google Drive")}</h3>'), ('<p className="tos-muted mt-2">ينشئ ملف tar.gz نظيف للكود، يستثني الملفات الثقيلة والحساسة، ويرفع Latest مع الاحتفاظ بالنسخة السابقة اختياريًا.</p>', '<p className="tos-muted mt-2">{systemBackupText("ينشئ ملف tar.gz نظيف للكود، يستثني الملفات الثقيلة والحساسة، ويرفع Latest مع الاحتفاظ بالنسخة السابقة اختياريًا.", "Creates a clean tar.gz code archive, excludes heavy and sensitive files, uploads Latest, and can optionally retain the previous backup.")}</p>'), ('<StatCard value={settings.enabled ? "مفعّل" : "متوقف"} label="Auto Backup" note={`${settings.frequencyHours || 24} ساعة`} icon={RefreshCw} tone={settings.enabled ? "success" : "zinc"} />', '<StatCard value={settings.enabled ? systemBackupText("مفعّل", "Enabled") : systemBackupText("متوقف", "Stopped")} label="Auto Backup" note={systemBackupText(`${settings.frequencyHours || 24} ساعة`, `${settings.frequencyHours || 24} hours`)} icon={RefreshCw} tone={settings.enabled ? "success" : "zinc"} />'), ('<StatCard value={status?.running ? "يعمل" : latestRun?.status || "—"} label="آخر عملية" note={formatBackupDate(latestRun?.startedAt)} icon={Shield} tone={latestRun?.status === "SUCCESS" ? "success" : latestRun?.status === "FAILED" ? "danger" : "zinc"} />', '<StatCard value={status?.running ? systemBackupText("يعمل", "Running") : latestRun?.status || "—"} label={systemBackupText("آخر عملية", "Last run")} note={formatBackupDate(latestRun?.startedAt, systemBackupLocale)} icon={Shield} tone={latestRun?.status === "SUCCESS" ? "success" : latestRun?.status === "FAILED" ? "danger" : "zinc"} />'), ('<StatCard value={formatBackupBytes(latestRun?.archiveBytes)} label="حجم النسخة" note={`${latestRun?.fileCount || 0} ملف`} icon={Package} tone="zinc" />', '<StatCard value={formatBackupBytes(latestRun?.archiveBytes)} label={systemBackupText("حجم النسخة", "Backup size")} note={systemBackupText(`${latestRun?.fileCount || 0} ملف`, `${latestRun?.fileCount || 0} files`)} icon={Package} tone="zinc" />'), ('<StatCard value={formatBackupDate(settings.nextRunAt)} label="النسخة القادمة" note="حسب الجدولة" icon={HardDrive} tone={settings.enabled ? "success" : "zinc"} />', '<StatCard value={formatBackupDate(settings.nextRunAt, systemBackupLocale)} label={systemBackupText("النسخة القادمة", "Next backup")} note={systemBackupText("حسب الجدولة", "According to schedule")} icon={HardDrive} tone={settings.enabled ? "success" : "zinc"} />'), ('<p className="text-xs font-black text-zinc-500 dark:text-zinc-400">جاهزية المصدر</p>', '<p className="text-xs font-black text-zinc-500 dark:text-zinc-400">{systemBackupText("جاهزية المصدر", "Source readiness")}</p>'), ('<div className="mt-2 flex items-center gap-2"><Badge tone={form.sourcePath.trim() ? "success" : "danger"}>{form.sourcePath.trim() ? "محدد" : "ناقص"}</Badge><span className="truncate text-xs font-bold text-zinc-500" dir="ltr">{form.sourcePath || "Source Path"}</span></div>', '<div className="mt-2 flex items-center gap-2"><Badge tone={form.sourcePath.trim() ? "success" : "danger"}>{form.sourcePath.trim() ? systemBackupText("محدد", "Set") : systemBackupText("ناقص", "Missing")}</Badge><span className="truncate text-xs font-bold text-zinc-500" dir="ltr">{form.sourcePath || "Source Path"}</span></div>'), ('<p className="text-xs font-black text-zinc-500 dark:text-zinc-400">وجهة Google Drive</p>', '<p className="text-xs font-black text-zinc-500 dark:text-zinc-400">{systemBackupText("وجهة Google Drive", "Google Drive destination")}</p>'), ('<div className="mt-2 flex items-center gap-2"><Badge tone={form.backupFolderName.trim() ? "success" : "warning"}>{form.backupFolderName.trim() ? "جاهزة" : "تحتاج اسم"}</Badge><span className="truncate text-xs font-bold text-zinc-500" dir="ltr">{form.backupFolderName || "TOS Backups"}</span></div>', '<div className="mt-2 flex items-center gap-2"><Badge tone={form.backupFolderName.trim() ? "success" : "warning"}>{form.backupFolderName.trim() ? systemBackupText("جاهزة", "Ready") : systemBackupText("تحتاج اسم", "Name required")}</Badge><span className="truncate text-xs font-bold text-zinc-500" dir="ltr">{form.backupFolderName || "TOS Backups"}</span></div>'), ('<p className="text-xs font-black text-zinc-500 dark:text-zinc-400">سياسة الاحتفاظ</p>', '<p className="text-xs font-black text-zinc-500 dark:text-zinc-400">{systemBackupText("سياسة الاحتفاظ", "Retention policy")}</p>'), ('<div className="mt-2 flex items-center gap-2"><Badge tone={form.keepPrevious ? "success" : "zinc"}>{form.keepPrevious ? "Latest + Previous" : "Latest فقط"}</Badge><span className="text-xs font-bold text-zinc-500">بدون حفظ ملفات حساسة</span></div>', '<div className="mt-2 flex items-center gap-2"><Badge tone={form.keepPrevious ? "success" : "zinc"}>{form.keepPrevious ? "Latest + Previous" : systemBackupText("Latest فقط", "Latest only")}</Badge><span className="text-xs font-bold text-zinc-500">{systemBackupText("بدون حفظ ملفات حساسة", "No sensitive files stored")}</span></div>'), ('<Field value={form.sourcePath} onChange={(e) => setField("sourcePath", e.target.value)} placeholder="Source Path على السيرفر" dir="ltr" className="md:col-span-2" />', '<Field value={form.sourcePath} onChange={(e) => setField("sourcePath", e.target.value)} placeholder={systemBackupText("Source Path على السيرفر", "Source Path on server")} dir="ltr" className="md:col-span-2" />'), ('<option value="1">كل ساعة</option>\n          <option value="6">كل 6 ساعات</option>\n          <option value="12">كل 12 ساعة</option>\n          <option value="24">يوميًا</option>\n          <option value="168">أسبوعيًا</option>', '<option value="1">{systemBackupText("كل ساعة", "Every hour")}</option>\n          <option value="6">{systemBackupText("كل 6 ساعات", "Every 6 hours")}</option>\n          <option value="12">{systemBackupText("كل 12 ساعة", "Every 12 hours")}</option>\n          <option value="24">{systemBackupText("يوميًا", "Daily")}</option>\n          <option value="168">{systemBackupText("أسبوعيًا", "Weekly")}</option>'), ('<Field value={form.runAtHour} onChange={(e) => setField("runAtHour", e.target.value)} placeholder="ساعة التنفيذ 0-23 اختياري" dir="ltr" />', '<Field value={form.runAtHour} onChange={(e) => setField("runAtHour", e.target.value)} placeholder={systemBackupText("ساعة التنفيذ 0-23 اختياري", "Run hour 0–23 (optional)")} dir="ltr" />'), ('          تشغيل النسخ التلقائي\n', '          {systemBackupText("تشغيل النسخ التلقائي", "Enable automatic backup")}\n'), ('          الاحتفاظ بنسخة Previous قبل استبدال Latest\n', '          {systemBackupText("الاحتفاظ بنسخة Previous قبل استبدال Latest", "Keep Previous before replacing Latest")}\n'), ('<Notice type="warning" className="mt-4">لا يتم حفظ .env أو node_modules أو dist أو build أو .git داخل النسخة.</Notice>', '<Notice type="warning" className="mt-4">{systemBackupText("لا يتم حفظ .env أو node_modules أو dist أو build أو .git داخل النسخة.", ".env, node_modules, dist, build, and .git are not included in the backup.")}</Notice>'), ('<Button type="button" variant="soft" onClick={loadStatus} disabled={loading || Boolean(actionLoading)}><RefreshCw size={17} className={loading ? "animate-spin" : ""} />{loading ? "جاري التحديث..." : "تحديث الحالة"}</Button>', '<Button type="button" variant="soft" onClick={loadStatus} disabled={loading || Boolean(actionLoading)}><RefreshCw size={17} className={loading ? "animate-spin" : ""} />{loading ? systemBackupText("جاري التحديث...", "Refreshing...") : systemBackupText("تحديث الحالة", "Refresh status")}</Button>'), ('<Button type="button" variant="soft" onClick={saveSettings} disabled={Boolean(actionLoading)}>{actionLoading === "save" ? "جاري الحفظ..." : "حفظ الإعدادات"}</Button>', '<Button type="button" variant="soft" onClick={saveSettings} disabled={Boolean(actionLoading)}>{actionLoading === "save" ? systemBackupText("جاري الحفظ...", "Saving...") : systemBackupText("حفظ الإعدادات", "Save settings")}</Button>'), ('<Button type="button" onClick={runNow} disabled={Boolean(actionLoading) || !form.sourcePath.trim()}>{actionLoading === "run" ? "جاري النسخ..." : "Run Backup Now"}</Button>', '<Button type="button" onClick={runNow} disabled={Boolean(actionLoading) || !form.sourcePath.trim()}>{actionLoading === "run" ? systemBackupText("جاري النسخ...", "Backing up...") : "Run Backup Now"}</Button>'), ('<h4 className="font-black text-zinc-950 dark:text-white">آخر العمليات</h4>', '<h4 className="font-black text-zinc-950 dark:text-white">{systemBackupText("آخر العمليات", "Recent runs")}</h4>'), ('{loading && <p className="tos-muted">جاري التحميل...</p>}', '{loading && <p className="tos-muted">{systemBackupText("جاري التحميل...", "Loading...")}</p>}'), ('{!loading && (!status?.runs || status.runs.length === 0) && <p className="tos-muted">لا توجد عمليات Backup بعد.</p>}', '{!loading && (!status?.runs || status.runs.length === 0) && <p className="tos-muted">{systemBackupText("لا توجد عمليات Backup بعد.", "No backup runs yet.")}</p>}'), ('{formatBackupDate(run.startedAt)}', '{formatBackupDate(run.startedAt, systemBackupLocale)}')]
DATABASE_REPLACEMENTS = [('import { getErrorMessage } from "../../lib/errors";', 'import { getErrorMessage } from "../../lib/errors";\nimport { usePreferences } from "../../contexts/PreferencesContext";'), ('export function DatabaseBackupAdmin({ user }) {\n  const [status, setStatus] = useState(null);', 'export function DatabaseBackupAdmin({ user }) {\n  const { isAr } = usePreferences();\n  const dbBackupText = (ar, en) => (isAr ? ar : en);\n  const dbBackupLocale = isAr ? "ar-EG" : "en-US";\n  const [status, setStatus] = useState(null);'), ('setMessage("تم ربط Google Drive وتفعيل النسخ التلقائي اليومي.");', 'setMessage(dbBackupText("تم ربط Google Drive وتفعيل النسخ التلقائي اليومي.", "Google Drive connected and automatic daily backup enabled."));'), ('setError(params.get("reason") || "فشل ربط Google Drive.");', 'setError(params.get("reason") || dbBackupText("فشل ربط Google Drive.", "Failed to connect Google Drive."));'), ('setMessage("تم ربط Google Drive بنجاح.");', 'setMessage(dbBackupText("تم ربط Google Drive بنجاح.", "Google Drive connected successfully."));'), ('loadStatus().catch((err) => setError(getErrorMessage(err, "تعذر تحميل حالة Database Backup.")));', 'loadStatus().catch((err) => setError(getErrorMessage(err, dbBackupText("تعذر تحميل حالة Database Backup.", "Unable to load Database Backup status."))));'), ('setMessage("تم حفظ إعدادات النسخ التلقائي.");', 'setMessage(dbBackupText("تم حفظ إعدادات النسخ التلقائي.", "Automatic backup settings saved."));'), ('if (!config?.googleDrive?.hasClientSecret && !liveSecret) throw new Error("Google Client Secret مطلوب قبل الربط.");', 'if (!config?.googleDrive?.hasClientSecret && !liveSecret) throw new Error(dbBackupText("Google Client Secret مطلوب قبل الربط.", "Google Client Secret is required before connecting."));'), ('throw new Error("Google Client Secret لم يتم حفظه بشكل صحيح.");', 'throw new Error(dbBackupText("Google Client Secret لم يتم حفظه بشكل صحيح.", "Google Client Secret was not saved correctly."));'), ('if (!auth?.url) throw new Error("لم يتم استلام Google OAuth URL.");', 'if (!auth?.url) throw new Error(dbBackupText("لم يتم استلام Google OAuth URL.", "Google OAuth URL was not received."));'), ('if (!window.confirm("فصل Google Drive المخصص للـ Database Backup؟ الملفات الموجودة لن تُحذف.")) return;', 'if (!window.confirm(dbBackupText("فصل Google Drive المخصص للـ Database Backup؟ الملفات الموجودة لن تُحذف.", "Disconnect the dedicated Google Drive for Database Backup? Existing files will not be deleted."))) return;'), ('setMessage("تم فصل Google Drive وإيقاف النسخ التلقائي.");', 'setMessage(dbBackupText("تم فصل Google Drive وإيقاف النسخ التلقائي.", "Google Drive disconnected and automatic backup disabled."));'), ('setMessage("تم إنشاء Database Backup مشفّر ورفعه والتحقق منه.");', 'setMessage(dbBackupText("تم إنشاء Database Backup مشفّر ورفعه والتحقق منه.", "Encrypted Database Backup created, uploaded, and verified."));'), ('if (!window.confirm(`فحص ${backup.name} داخل قاعدة مؤقتة معزولة قبل الاسترجاع؟`)) return;', 'if (!window.confirm(dbBackupText(`فحص ${backup.name} داخل قاعدة مؤقتة معزولة قبل الاسترجاع؟`, `Validate ${backup.name} in an isolated temporary database before restore?`))) return;'), ('setMessage("نجح فحص النسخة. اكتب RESTORE للتأكيد النهائي.");', 'setMessage(dbBackupText("نجح فحص النسخة. اكتب RESTORE للتأكيد النهائي.", "Backup validation passed. Type RESTORE for final confirmation."));'), ('if (!window.confirm("سيتم استبدال قاعدة بيانات TOS الحالية بهذه النسخة. استمرار؟")) return;', 'if (!window.confirm(dbBackupText("سيتم استبدال قاعدة بيانات TOS الحالية بهذه النسخة. استمرار؟", "The current TOS database will be replaced with this backup. Continue?"))) return;'), ('setMessage("تم Restore لقاعدة البيانات بنجاح.");', 'setMessage(dbBackupText("تم Restore لقاعدة البيانات بنجاح.", "Database restored successfully."));'), ('<h3 className="mt-1 text-2xl font-black text-zinc-950 dark:text-white">نسخ قاعدة البيانات إلى Google Drive</h3>', '<h3 className="mt-1 text-2xl font-black text-zinc-950 dark:text-white">{dbBackupText("نسخ قاعدة البيانات إلى Google Drive", "Database backups to Google Drive")}</h3>'), ('<p className="tos-muted mt-2">PostgreSQL فقط — مشفّر AES-256-GCM — آخر 3 نسخ — Restore محمي بخطوتين.</p>', '<p className="tos-muted mt-2">{dbBackupText("PostgreSQL فقط — مشفّر AES-256-GCM — آخر 3 نسخ — Restore محمي بخطوتين.", "PostgreSQL only — AES-256-GCM encrypted — latest 3 backups — two-step protected restore.")}</p>'), ('{busy === "save" ? "جاري الحفظ..." : "حفظ Auto Backup"}', '{busy === "save" ? dbBackupText("جاري الحفظ...", "Saving...") : dbBackupText("حفظ Auto Backup", "Save Auto Backup")}'), ('placeholder={config?.googleDrive?.hasClientSecret ? "Client Secret محفوظ — اتركه فارغًا للإبقاء عليه" : "Google Client Secret"}', 'placeholder={config?.googleDrive?.hasClientSecret ? dbBackupText("Client Secret محفوظ — اتركه فارغًا للإبقاء عليه", "Client Secret saved — leave blank to keep it unchanged") : "Google Client Secret"}'), ('{backups.length === 0 && <p className="tos-muted text-sm">لا توجد نسخ متاحة بعد.</p>}', '{backups.length === 0 && <p className="tos-muted text-sm">{dbBackupText("لا توجد نسخ متاحة بعد.", "No backups are available yet.")}</p>}'), ('{backup.createdTime ? new Date(backup.createdTime).toLocaleString() : ""}', '{backup.createdTime ? new Date(backup.createdTime).toLocaleString(dbBackupLocale) : ""}'), ('{!config?.encryptionReady && <Notice type="warning" className="mt-4">أضف TOS_DB_BACKUP_ENCRYPTION_KEY على السيرفر قبل تفعيل أو تشغيل Database Backup. احتفظ بنسخة خارجية من المفتاح.</Notice>}', '{!config?.encryptionReady && <Notice type="warning" className="mt-4">{dbBackupText("أضف TOS_DB_BACKUP_ENCRYPTION_KEY على السيرفر قبل تفعيل أو تشغيل Database Backup. احتفظ بنسخة خارجية من المفتاح.", "Add TOS_DB_BACKUP_ENCRYPTION_KEY on the server before enabling or running Database Backup. Keep an external copy of the key.")}</Notice>}')]

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

def transform(text, replacements, label):
    for idx, (old, new) in enumerate(replacements, start=1):
        count = text.count(old)
        print(f"{label}_REPLACEMENT_{idx}_MATCHES={count}")
        if count != 1:
            die(f"{label} replacement {idx} expected exactly 1 match, found {count}", 20 + idx)
        text = text.replace(old, new, 1)
    return text

def main():
    if len(sys.argv) != 3:
        die("usage: generate_phase5_3_3b_backups.py REPO_ROOT OUTPUT_PATCH", 2)

    root = Path(sys.argv[1]).resolve()
    output = Path(sys.argv[2]).resolve()
    settings_path = root / TARGET_SETTINGS
    database_path = root / TARGET_DATABASE

    if not (root / ".git").is_dir():
        die("not a git repository", 3)
    if not settings_path.is_file() or not database_path.is_file():
        die("required target missing", 4)

    head = run(["git", "rev-parse", "HEAD"], root).stdout.strip()
    print(f"HEAD={head}")
    if head != EXPECTED_HEAD:
        die(f"HEAD mismatch expected={EXPECTED_HEAD} actual={head}", 5)

    settings_blob = run(["git", "hash-object", TARGET_SETTINGS], root).stdout.strip()
    database_blob = run(["git", "hash-object", TARGET_DATABASE], root).stdout.strip()
    print(f"SETTINGS_SOURCE_BLOB={settings_blob}")
    print(f"DATABASE_SOURCE_BLOB={database_blob}")
    if settings_blob != EXPECTED_SETTINGS_BLOB:
        die(f"SettingsPage blob mismatch expected={EXPECTED_SETTINGS_BLOB} actual={settings_blob}", 6)
    if database_blob != EXPECTED_DATABASE_BLOB:
        die(f"DatabaseBackupAdmin blob mismatch expected={EXPECTED_DATABASE_BLOB} actual={database_blob}", 7)

    staged = run(["git", "diff", "--cached", "--name-only"], root).stdout.strip().splitlines()
    if staged:
        die(f"staged tracked files present: {staged}", 8)

    tracked = run(["git", "diff", "--name-only"], root).stdout.strip().splitlines()
    if tracked != [TARGET_SETTINGS]:
        die(f"expected existing unstaged Identity diff only in SettingsPage, found: {tracked}", 9)

    settings_raw = settings_path.read_bytes()
    database_raw = database_path.read_bytes()
    if b"\r\n" in settings_raw or b"\r\n" in database_raw:
        die("CRLF detected", 10)

    settings_text = transform(settings_raw.decode("utf-8"), SETTINGS_REPLACEMENTS, "SETTINGS")
    database_text = transform(database_raw.decode("utf-8"), DATABASE_REPLACEMENTS, "DATABASE")

    tmp = Path(tempfile.mkdtemp(prefix="tos-phase5-3-3b-"))
    try:
        run(["git", "init", "-q"], tmp)
        run(["git", "config", "user.email", "phase5-3-3b@tos.local"], tmp)
        run(["git", "config", "user.name", "TOS Phase 5.3.3B Generator"], tmp)

        for rel, source in [(TARGET_SETTINGS, settings_path), (TARGET_DATABASE, database_path)]:
            dst = tmp / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, dst)

        run(["git", "add", "--", TARGET_SETTINGS, TARGET_DATABASE], tmp)
        run(["git", "commit", "-qm", "exact phase 5.3.3b baseline"], tmp)

        (tmp / TARGET_SETTINGS).write_text(settings_text, encoding="utf-8", newline="\n")
        (tmp / TARGET_DATABASE).write_text(database_text, encoding="utf-8", newline="\n")

        diff = subprocess.run(
            ["git", "diff", "--binary", "--full-index", "--", TARGET_SETTINGS, TARGET_DATABASE],
            cwd=tmp, text=True, capture_output=True
        )
        if diff.returncode or not diff.stdout.strip():
            die("failed to generate patch", 70)

        output.write_text(diff.stdout, encoding="utf-8", newline="\n")
        print(f"GENERATED_PATCH_SHA256={hashlib.sha256(output.read_bytes()).hexdigest()}")

        numstat = run(["git", "apply", "--numstat", str(output)], root).stdout.strip().splitlines()
        paths = {row.split("\t")[-1] for row in numstat if row.strip()}
        expected = {TARGET_SETTINGS, TARGET_DATABASE}
        if paths != expected:
            die(f"unexpected patch paths: {sorted(paths)}", 71)

        print("PARSER=PASS")
        run(["git", "apply", "--check", str(output)], root)
        print("APPLY_CHECK=PASS")
        print("GENERATION_MODE=TWO_FILE_EXACT_BLOB_BACKUPS_LOCALIZATION")
        print("PHASE5_3_3B_BACKUPS_GENERATOR=PASS")
        print(f"OUTPUT={output}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

if __name__ == "__main__":
    main()
