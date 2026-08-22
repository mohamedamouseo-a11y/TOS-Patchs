#!/usr/bin/env python3
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

EXPECTED_HEAD = "a9be3b4b5daabbcd2505720c4df6eaf97a8fe82d"
TARGET = "frontend/src/pages/SettingsPage.jsx"
EXPECTED_BLOB = "e6e87e7489c76693f5ab46b3c61caeb2d5e6d4d0"

REPLACEMENTS = [
    ('''function GoogleDriveAdmin({ user }) {
  const [status, setStatus] = useState(null);''',
     '''function GoogleDriveAdmin({ user }) {
  const { isAr } = usePreferences();
  const driveText = (ar, en) => (isAr ? ar : en);
  const [status, setStatus] = useState(null);''', 1),
    ('''setError(getErrorMessage(err, "تعذر تحميل حالة التخزين السحابي."));''',
     '''setError(getErrorMessage(err, driveText("تعذر تحميل حالة التخزين السحابي.", "Unable to load cloud storage status.")));''', 1),
    ('''await runAction("auth", "تم فتح نافذة ربط Google Drive.", async () => {''',
     '''await runAction("auth", driveText("تم فتح نافذة ربط Google Drive.", "Google Drive connection window opened."), async () => {''', 1),
    ('''if (!data?.url) throw new Error("لم يتم استلام رابط الربط من السيرفر.");''',
     '''if (!data?.url) throw new Error(driveText("لم يتم استلام رابط الربط من السيرفر.", "The server did not return a connection URL."));''', 1),
    ('''await runAction("save", "تم حفظ إعدادات Google Drive.", async () => {''',
     '''await runAction("save", driveText("تم حفظ إعدادات Google Drive.", "Google Drive settings saved."), async () => {''', 1),
    ('''throw new Error("Client Secret لم يتم حفظه. حاول مرة أخرى أو راجع السيرفر.");''',
     '''throw new Error(driveText("Client Secret لم يتم حفظه. حاول مرة أخرى أو راجع السيرفر.", "Client Secret was not saved. Try again or check the server."));''', 1),
    ('''await runAction("disconnect", "تم فصل Google Drive.", async () => {''',
     '''await runAction("disconnect", driveText("تم فصل Google Drive.", "Google Drive disconnected."), async () => {''', 1),
    ('''<p className="tos-muted mt-2">إعدادات الربط تظهر لمدير النظام فقط.</p>''',
     '''<p className="tos-muted mt-2">{driveText("إعدادات الربط تظهر لمدير النظام فقط.", "Connection settings are available to the System Admin only.")}</p>''', 1),
    ('''<h3 className="mt-1 text-2xl font-black text-zinc-950 dark:text-white">إعدادات التخزين على Google Drive</h3>''',
     '''<h3 className="mt-1 text-2xl font-black text-zinc-950 dark:text-white">{driveText("إعدادات التخزين على Google Drive", "Google Drive Storage Settings")}</h3>''', 1),
    ('''<p className="tos-muted mt-2">ارفع الملفات داخل السيستم، ويتم حفظها في Drive بدون إظهار روابط Drive للفريق.</p>''',
     '''<p className="tos-muted mt-2">{driveText("ارفع الملفات داخل السيستم، ويتم حفظها في Drive بدون إظهار روابط Drive للفريق.", "Upload files inside TOS and store them in Drive without exposing Drive links to the team.")}</p>''', 1),
    ('''<StatCard value={loading ? "..." : status?.connected ? "متصل" : "غير متصل"} label="حالة الربط" note="OAuth" icon={HardDrive} tone={status?.connected ? "success" : "zinc"} />''',
     '''<StatCard value={loading ? "..." : status?.connected ? driveText("متصل", "Connected") : driveText("غير متصل", "Disconnected")} label={driveText("حالة الربط", "Connection status")} note="OAuth" icon={HardDrive} tone={status?.connected ? "success" : "zinc"} />''', 1),
    ('''<StatCard value={status?.hasCredentials ? "جاهزة" : "ناقصة"} label="بيانات OAuth" note="Client ID / Secret / Redirect" icon={Shield} tone={status?.hasCredentials ? "success" : "zinc"} />''',
     '''<StatCard value={status?.hasCredentials ? driveText("جاهزة", "Ready") : driveText("ناقصة", "Incomplete")} label={driveText("بيانات OAuth", "OAuth credentials")} note="Client ID / Secret / Redirect" icon={Shield} tone={status?.hasCredentials ? "success" : "zinc"} />''', 1),
    ('''<StatCard value={status?.storageReady ? "جاهز" : "متوقف"} label="التخزين" note="Upload Ready" icon={Shield} tone={status?.storageReady ? "success" : "zinc"} />''',
     '''<StatCard value={status?.storageReady ? driveText("جاهز", "Ready") : driveText("متوقف", "Unavailable")} label={driveText("التخزين", "Storage")} note="Upload Ready" icon={Shield} tone={status?.storageReady ? "success" : "zinc"} />''', 1),
    ('''<StatCard value={status?.rootFolderStatus === "app_folder" ? "مجلد النظام" : status?.rootFolderStatus === "valid" ? "سليم" : status?.rootFolderStatus === "invalid" ? "خطأ" : status?.rootFolderId ? "ينتظر فحص" : "اختياري"} label="Root Folder" note="Google Drive" icon={HardDrive} tone={status?.rootFolderStatus === "valid" || status?.rootFolderStatus === "app_folder" ? "success" : "zinc"} />''',
     '''<StatCard value={status?.rootFolderStatus === "app_folder" ? driveText("مجلد النظام", "System folder") : status?.rootFolderStatus === "valid" ? driveText("سليم", "Valid") : status?.rootFolderStatus === "invalid" ? driveText("خطأ", "Invalid") : status?.rootFolderId ? driveText("ينتظر فحص", "Pending check") : driveText("اختياري", "Optional")} label="Root Folder" note="Google Drive" icon={HardDrive} tone={status?.rootFolderStatus === "valid" || status?.rootFolderStatus === "app_folder" ? "success" : "zinc"} />''', 1),
    ('''placeholder={status?.hasClientSecret ? "Client Secret محفوظ — اتركه فارغًا بدون تغيير" : "Google Client Secret"}''',
     '''placeholder={status?.hasClientSecret ? driveText("Client Secret محفوظ — اتركه فارغًا بدون تغيير", "Client Secret saved — leave blank to keep it unchanged") : "Google Client Secret"}''', 1),
    ('''              مسح Client Secret الحالي عند الحفظ''',
     '''              {driveText("مسح Client Secret الحالي عند الحفظ", "Clear the current Client Secret when saving")}''', 1),
    ('''<p className="text-xs font-bold text-zinc-400 dark:text-zinc-500">بعد الحفظ سيتم تفريغ الخانة للأمان، لكن الحالة يجب أن تظهر جاهزة.</p>''',
     '''<p className="text-xs font-bold text-zinc-400 dark:text-zinc-500">{driveText("بعد الحفظ سيتم تفريغ الخانة للأمان، لكن الحالة يجب أن تظهر جاهزة.", "After saving, the field is cleared for security while the status should remain Ready.")}</p>''', 1),
    ('''placeholder="Root Folder ID اختياري"''',
     '''placeholder={driveText("Root Folder ID اختياري", "Root Folder ID (optional)")}''', 1),
    ('''        لازم Redirect URI في Google Console يكون نفس القيمة المكتوبة هنا بالضبط.''',
     '''        {driveText("لازم Redirect URI في Google Console يكون نفس القيمة المكتوبة هنا بالضبط.", "The Redirect URI in Google Console must exactly match the value shown here.")}''', 1),
    ('''        مع Scope drive.file الأفضل تترك Root Folder فارغًا؛ النظام سيُنشئ مجلد Tamiyouz System بنفسه ويتجنب مشكلة صلاحيات المجلدات القديمة.''',
     '''        {driveText("مع Scope drive.file الأفضل تترك Root Folder فارغًا؛ النظام سيُنشئ مجلد Tamiyouz System بنفسه ويتجنب مشكلة صلاحيات المجلدات القديمة.", "With the drive.file scope, leave Root Folder blank. TOS will create its own Tamiyouz System folder and avoid inherited permission issues.")}''', 1),
    ('''{loading ? "جاري التحديث..." : "تحديث الحالة"}''',
     '''{loading ? driveText("جاري التحديث...", "Refreshing...") : driveText("تحديث الحالة", "Refresh status")}''', 1),
    ('''{actionLoading === "save" ? "جاري الحفظ..." : "حفظ الإعدادات"}''',
     '''{actionLoading === "save" ? driveText("جاري الحفظ...", "Saving...") : driveText("حفظ الإعدادات", "Save settings")}''', 1),
    ('''{actionLoading === "auth" ? "جاري الفتح..." : "ربط Google Drive"}''',
     '''{actionLoading === "auth" ? driveText("جاري الفتح...", "Opening...") : driveText("ربط Google Drive", "Connect Google Drive")}''', 1),
    ('''{actionLoading === "disconnect" ? "جاري الفصل..." : "فصل الربط"}''',
     '''{actionLoading === "disconnect" ? driveText("جاري الفصل...", "Disconnecting...") : driveText("فصل الربط", "Disconnect")}''', 1),

    ('''function ThrsIntegrationAdmin({ user }) {
  const [settings, setSettings] = useState(null);''',
     '''function ThrsIntegrationAdmin({ user }) {
  const { isAr } = usePreferences();
  const thrsText = (ar, en) => (isAr ? ar : en);
  const [settings, setSettings] = useState(null);''', 1),
    ('''<h3 className="mt-1 text-2xl font-black text-zinc-950 dark:text-white">ربط THRS مع TOS</h3>''',
     '''<h3 className="mt-1 text-2xl font-black text-zinc-950 dark:text-white">{thrsText("ربط THRS مع TOS", "Connect THRS with TOS")}</h3>''', 1),
    ('''<p className="tos-muted mt-2">اضبط رابط THRS والتوكن من هنا بدل الاعتماد على Replit Secrets فقط، ثم استخدمها في طلبات شؤون الموظفين.</p>''',
     '''<p className="tos-muted mt-2">{thrsText("اضبط رابط THRS والتوكن من هنا بدل الاعتماد على Replit Secrets فقط، ثم استخدمها في طلبات شؤون الموظفين.", "Configure the THRS URL and tokens here, then use them for employee-work requests.")}</p>''', 1),
    ('''<StatCard value={ready ? "جاهز" : configured ? "مكتمل غير مفعّل" : "غير مكتمل"} label="حالة الربط" note={settings?.settingsSource || "Settings"} icon={Unplug} tone={ready ? "success" : configured ? "warning" : "danger"} />''',
     '''<StatCard value={ready ? thrsText("جاهز", "Ready") : configured ? thrsText("مكتمل غير مفعّل", "Configured, disabled") : thrsText("غير مكتمل", "Incomplete")} label={thrsText("حالة الربط", "Connection status")} note={settings?.settingsSource || "Settings"} icon={Unplug} tone={ready ? "success" : configured ? "warning" : "danger"} />''', 1),
    ('''<StatCard value={settings?.hasToken ? "محفوظ" : "ناقص"} label="API Token" note="مخفي ومشفّر" icon={Shield} tone={settings?.hasToken ? "success" : "zinc"} />''',
     '''<StatCard value={settings?.hasToken ? thrsText("محفوظ", "Saved") : thrsText("ناقص", "Missing")} label="API Token" note={thrsText("مخفي ومشفّر", "Hidden and encrypted")} icon={Shield} tone={settings?.hasToken ? "success" : "zinc"} />''', 1),
    ('''<StatCard value={settings?.hasCallbackToken ? "محفوظ" : "ناقص"} label="Callback Token" note="لرجوع قرار THRS" icon={Shield} tone={settings?.hasCallbackToken ? "success" : "zinc"} />''',
     '''<StatCard value={settings?.hasCallbackToken ? thrsText("محفوظ", "Saved") : thrsText("ناقص", "Missing")} label="Callback Token" note={thrsText("لرجوع قرار THRS", "Receives the THRS decision")} icon={Shield} tone={settings?.hasCallbackToken ? "success" : "zinc"} />''', 1),
    ('''<StatCard value={leaveTypes.length || 0} label="أنواع الإجازات" note="للقوائم داخل TOS" icon={SlidersHorizontal} tone={leaveTypes.length ? "success" : "warning"} />''',
     '''<StatCard value={leaveTypes.length || 0} label={thrsText("أنواع الإجازات", "Leave types")} note={thrsText("للقوائم داخل TOS", "Used in TOS lists")} icon={SlidersHorizontal} tone={leaveTypes.length ? "success" : "warning"} />''', 1),
    ('''<StatCard value={employeeMapping?.matchedCount || 0} label="مطابقة الموظفين" note="TOS ↔ THRS بالإيميل" icon={Shield} tone={employeeMapping?.matchedCount ? "success" : "warning"} />''',
     '''<StatCard value={employeeMapping?.matchedCount || 0} label={thrsText("مطابقة الموظفين", "Employee mapping")} note={thrsText("TOS ↔ THRS بالإيميل", "TOS ↔ THRS by email")} icon={Shield} tone={employeeMapping?.matchedCount ? "success" : "warning"} />''', 1),
    ('''<Notice type="warning" className="mt-4">ربط THRS غير جاهز. أكمل الرابط والتوكن وفعل الربط حتى يمكن إرسال الطلبات إلى THRS. يمكن استخدام أنواع إجازات احتياطية بالـ IDs الحقيقية مؤقتًا.</Notice>''',
     '''<Notice type="warning" className="mt-4">{thrsText("ربط THRS غير جاهز. أكمل الرابط والتوكن وفعل الربط حتى يمكن إرسال الطلبات إلى THRS. يمكن استخدام أنواع إجازات احتياطية بالـ IDs الحقيقية مؤقتًا.", "THRS is not ready. Complete the URL and tokens and enable the integration before sending requests. Real THRS leave-type IDs can be used as a temporary fallback.")}</Notice>''', 1),
    ('''          تفعيل مزامنة طلبات شؤون الموظفين إلى THRS''',
     '''          {thrsText("تفعيل مزامنة طلبات شؤون الموظفين إلى THRS", "Enable employee-work request sync to THRS")}''', 1),
    ('''<option value="MANUAL">MANUAL — يدوي / عند الضغط أو الموافقة</option>''',
     '''<option value="MANUAL">{thrsText("MANUAL — يدوي / عند الضغط أو الموافقة", "MANUAL — on demand or approval")}</option>''', 1),
    ('''<option value="AUTO">AUTO — تلقائي بعد موافقة TOS</option>''',
     '''<option value="AUTO">{thrsText("AUTO — تلقائي بعد موافقة TOS", "AUTO — automatically after TOS approval")}</option>''', 1),
    ('''<option value="DISABLED">DISABLED — إيقاف</option>''',
     '''<option value="DISABLED">{thrsText("DISABLED — إيقاف", "DISABLED — off")}</option>''', 1),
    ('''placeholder="THRS API URL مثال: https://hr.tamiyouz.com"''',
     '''placeholder={thrsText("THRS API URL مثال: https://hr.tamiyouz.com", "THRS API URL, e.g. https://hr.tamiyouz.com")}''', 1),
    ('''placeholder={settings?.hasToken ? "THRS API Token محفوظ — اتركه فارغًا بدون تغيير" : "THRS API Token"}''',
     '''placeholder={settings?.hasToken ? thrsText("THRS API Token محفوظ — اتركه فارغًا بدون تغيير", "THRS API Token saved — leave blank to keep it unchanged") : "THRS API Token"}''', 1),
    (''' /> مسح API Token عند الحفظ</label>''',
     ''' /> {thrsText("مسح API Token عند الحفظ", "Clear API Token when saving")}</label>''', 1),
    ('''placeholder={settings?.hasCallbackToken ? "Callback Token محفوظ — اتركه فارغًا بدون تغيير" : "Callback Token"}''',
     '''placeholder={settings?.hasCallbackToken ? thrsText("Callback Token محفوظ — اتركه فارغًا بدون تغيير", "Callback Token saved — leave blank to keep it unchanged") : "Callback Token"}''', 1),
    (''' /> مسح Callback Token عند الحفظ</label>''',
     ''' /> {thrsText("مسح Callback Token عند الحفظ", "Clear Callback Token when saving")}</label>''', 1),
    ('''placeholder={'أنواع إجازات احتياطية عند عدم توفر THRS\nمثال:\nleave_type_id_1|إجازة سنوية|ANNUAL\nleave_type_id_2|إجازة مرضية|SICK'}''',
     '''placeholder={thrsText('أنواع إجازات احتياطية عند عدم توفر THRS\nمثال:\nleave_type_id_1|إجازة سنوية|ANNUAL\nleave_type_id_2|إجازة مرضية|SICK', 'Fallback leave types when THRS is unavailable\nExample:\nleave_type_id_1|Annual Leave|ANNUAL\nleave_type_id_2|Sick Leave|SICK')}''', 1),
    ('''<p className="mt-2 text-xs font-bold text-zinc-400">استخدم IDs الحقيقية من THRS فقط حتى تظهر قائمة نوع الإجازة بشكل صحيح.</p>''',
     '''<p className="mt-2 text-xs font-bold text-zinc-400">{thrsText("استخدم IDs الحقيقية من THRS فقط حتى تظهر قائمة نوع الإجازة بشكل صحيح.", "Use real THRS IDs only so the leave-type list renders correctly.")}</p>''', 1),
    ('''{actionLoading === "save" ? "جاري الحفظ..." : "حفظ ربط THRS"}''',
     '''{actionLoading === "save" ? thrsText("جاري الحفظ...", "Saving...") : thrsText("حفظ ربط THRS", "Save THRS integration")}''', 1),
    ('''{actionLoading === "test" ? "جاري الاختبار..." : "اختبار الاتصال"}''',
     '''{actionLoading === "test" ? thrsText("جاري الاختبار...", "Testing...") : thrsText("اختبار الاتصال", "Test connection")}''', 1),
    ('''{actionLoading === "leaveTypes" ? "جاري الجلب..." : "جلب أنواع الإجازات"}''',
     '''{actionLoading === "leaveTypes" ? thrsText("جاري الجلب...", "Loading...") : thrsText("جلب أنواع الإجازات", "Load leave types")}''', 1),
    ('''{actionLoading === "employeeMappings" ? "جاري المطابقة..." : "مطابقة موظفي THRS"}''',
     '''{actionLoading === "employeeMappings" ? thrsText("جاري المطابقة...", "Mapping...") : thrsText("مطابقة موظفي THRS", "Map THRS employees")}''', 1),
    ('''<h4 className="text-sm font-black text-zinc-950 dark:text-white">أنواع الإجازات المتاحة للقوائم</h4>''',
     '''<h4 className="text-sm font-black text-zinc-950 dark:text-white">{thrsText("أنواع الإجازات المتاحة للقوائم", "Leave types available to lists")}</h4>''', 1),

    ('''<Button type="button" variant="soft" onClick={loadSettings} disabled={busy}><RefreshCw size={16} className={loading ? "animate-spin" : ""} /> تحديث</Button>''',
     '''<Button type="button" variant="soft" onClick={loadSettings} disabled={busy}><RefreshCw size={16} className={loading ? "animate-spin" : ""} /> {identityCopy.refresh}</Button>''', 1),
    ('''<h4 className="text-base font-black text-zinc-950 dark:text-white">الشعار والأيقونة</h4>''',
     '''<h4 className="text-base font-black text-zinc-950 dark:text-white">{identityLang === "en" ? "Logo & icon" : "الشعار والأيقونة"}</h4>''', 1),
    ('''{actionLoading === "logo" ? `رفع ${Math.round(uploadProgress.logo || 0)}%` : "رفع شعار"}''',
     '''{actionLoading === "logo" ? (identityLang === "en" ? `Uploading ${Math.round(uploadProgress.logo || 0)}%` : `رفع ${Math.round(uploadProgress.logo || 0)}%`) : (identityLang === "en" ? "Upload logo" : "رفع شعار")}''', 1),
    ('''placeholder="رابط الشعار"''',
     '''placeholder={identityLang === "en" ? "Logo URL" : "رابط الشعار"}''', 1),
    ('''{actionLoading === "favicon" ? `رفع ${Math.round(uploadProgress.favicon || 0)}%` : "رفع أيقونة"}''',
     '''{actionLoading === "favicon" ? (identityLang === "en" ? `Uploading ${Math.round(uploadProgress.favicon || 0)}%` : `رفع ${Math.round(uploadProgress.favicon || 0)}%`) : (identityLang === "en" ? "Upload icon" : "رفع أيقونة")}''', 1),
    ('''placeholder="رابط الأيقونة"''',
     '''placeholder={identityLang === "en" ? "Icon URL" : "رابط الأيقونة"}''', 1),
    ('''<h4 className="text-base font-black text-zinc-950 dark:text-white">بيانات النظام والوضع</h4>''',
     '''<h4 className="text-base font-black text-zinc-950 dark:text-white">{identityLang === "en" ? "System identity & mode" : "بيانات النظام والوضع"}</h4>''', 1),
    ('''placeholder="اسم النظام"''',
     '''placeholder={identityLang === "en" ? "System name" : "اسم النظام"}''', 1),
    ('''placeholder="وصف مختصر"''',
     '''placeholder={identityLang === "en" ? "Short description" : "وصف مختصر"}''', 1),
    ('''<p className="mt-3 text-sm font-black text-zinc-950 dark:text-white">{option.label}</p><p className="mt-1 text-[11px] font-bold text-zinc-500">{option.description}</p>''',
     '''<p className="mt-3 text-sm font-black text-zinc-950 dark:text-white">{identityLang === "en" ? (option.key === "dark" ? "Dark Mode" : "Light Mode") : option.label}</p><p className="mt-1 text-[11px] font-bold text-zinc-500">{identityLang === "en" ? (option.key === "dark" ? "Comfortable dark interface for long sessions." : "Calm light interface for everyday use.") : option.description}</p>''', 1),
]

def die(message, code=1):
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(code)

def run(args, cwd, check=True):
    proc = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)
    if check and proc.returncode:
        die(f"command failed rc={proc.returncode}: {' '.join(args)}", 90)
    return proc

def sha256(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    if len(sys.argv) != 3:
        die("usage: generate_phase5_3_1_settings_core.py REPO_ROOT OUTPUT_PATCH", 2)
    root = Path(sys.argv[1]).resolve()
    output = Path(sys.argv[2]).resolve()
    target = root / TARGET
    if not (root / ".git").is_dir():
        die(f"not a git repository: {root}", 3)
    if not target.is_file():
        die(f"target missing: {TARGET}", 4)
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
    print("TARGET_CLEAN=YES")
    raw = target.read_bytes()
    if b"\r\n" in raw:
        die("CRLF source detected", 9)
    terminal_newline = raw.endswith(b"\n")
    text = raw.decode("utf-8")
    for index, (old, new, expected_count) in enumerate(REPLACEMENTS, start=1):
        count = text.count(old)
        print(f"REPLACEMENT_{index}_MATCHES={count}")
        if count != expected_count:
            die(f"replacement {index} expected {expected_count} exact matches, found {count}", 20 + index)
        text = text.replace(old, new)
    tmp = Path(tempfile.mkdtemp(prefix="tos-phase5-3-1-settings-core-"))
    try:
        run(["git", "init", "-q"], tmp)
        run(["git", "config", "user.email", "phase5-3-1@tos.local"], tmp)
        run(["git", "config", "user.name", "TOS Phase 5.3.1 Generator"], tmp)
        tmp_target = tmp / TARGET
        tmp_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(target, tmp_target)
        run(["git", "add", "--", TARGET], tmp)
        run(["git", "commit", "-qm", "exact live baseline"], tmp)
        encoded = text.encode("utf-8")
        if terminal_newline and not encoded.endswith(b"\n"):
            encoded += b"\n"
        elif not terminal_newline and encoded.endswith(b"\n"):
            encoded = encoded[:-1]
        tmp_target.write_bytes(encoded)
        proc = subprocess.run(["git", "diff", "--binary", "--full-index", "--", TARGET], cwd=tmp, text=True, capture_output=True)
        if proc.returncode:
            die(f"git diff failed rc={proc.returncode}", 80)
        if not proc.stdout.strip():
            die("generated patch is empty", 81)
        output.write_text(proc.stdout, encoding="utf-8", newline="\n")
        print(f"GENERATED_PATCH_SHA256={sha256(output)}")
        numstat = run(["git", "apply", "--numstat", str(output)], root).stdout.strip().splitlines()
        paths = {row.split("\t")[-1] for row in numstat if row.strip()}
        if paths != {TARGET}:
            die(f"unexpected patch paths: {sorted(paths)}", 82)
        print("PARSER=PASS")
        run(["git", "apply", "--check", str(output)], root)
        print("APPLY_CHECK=PASS")
        print("GENERATION_MODE=GIT_DIFF_FROM_EXACT_LIVE_SOURCE")
        print("PHASE5_3_1_SETTINGS_CORE_GENERATOR=PASS")
        print(f"OUTPUT={output}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

if __name__ == "__main__":
    main()
