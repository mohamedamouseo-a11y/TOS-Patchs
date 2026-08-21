#!/usr/bin/env python3
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

EXPECTED_HEAD = "fe18c6b47aac108a099297376c4a83f0add079fd"
TARGET = "frontend/src/pages/TeamPage.jsx"
EXPECTED_BLOB = "e1839f0ae08d639bae43ea88a49dc5f18dcdd0fc"

CORE_OLD = '''const PROJECT_ROLE_LABELS = {
  OWNER: "مالك",
  MANAGER: "مدير مشروع",
  MEMBER: "عضو",
};

const PROJECT_ROLE_HINTS = {
  OWNER: "تحكم كامل داخل المشروع والبوردات.",
  MANAGER: "مدير مشروع داخل هذا المشروع المحدد فقط، ولا يغيّر دوره الإداري داخل القسم.",
  MEMBER: "تنفيذ المهام والتعليق ورفع الملفات.",
};

const SYSTEM_ROLE_HINTS = {
  SUPER_ADMIN: ["تحكم كامل في النظام", "إدارة كل المستخدمين", "وصول لكل المشاريع"],
  ADMIN: ["إدارة الفريق والعملاء", "إنشاء وتعديل المشاريع", "وصول إداري عام"],
  MANAGER: ["صلاحية إدارة داخلية", "يمكن تعيينه كقائد Department من لوحة الأقسام", "لا يصبح قائد فريق إلا عند اختياره كمسؤول قسم"],
  PROJECT_MANAGER: ["صلاحية متابعة مشاريع عامة", "مدير المشروع الحقيقي يظهر من دوره داخل المشروع", "لا يساوي قائد فريق أو مدير قسم"],
  TEAM_MEMBER: ["تنفيذ المهام", "تعليقات وملفات داخل المشاريع المرتبط بها", "بدون إدارة مستخدمين"],
};

function getProjectIds(userItem) {
  return (userItem.projects || []).map((project) => project.id);
}

function dateLabel(value) {
  if (!value) return "—";
  try {
    return new Intl.DateTimeFormat("ar-EG", { dateStyle: "medium" }).format(new Date(value));
  } catch {
    return "—";
  }
}

function dateTimeLabel(value) {
  if (!value) return "—";
  try {
    return new Intl.DateTimeFormat("ar-EG", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
  } catch {
    return "—";
  }
}

function passwordStrengthDetails(value = "") {
  const password = String(value || "");
  if (!password) return { score: 0, label: "لم تُكتب كلمة مرور", tone: "bg-zinc-200 dark:bg-white/10", text: "text-zinc-400" };
  let score = 0;
  if (password.length >= 12) score += 1;
  if (/[a-z]/.test(password) && /[A-Z]/.test(password)) score += 1;
  if (/\\d/.test(password)) score += 1;
  if (/[^A-Za-z0-9]/.test(password)) score += 1;
  if (score <= 1) return { score, label: "ضعيفة", tone: "bg-red-500", text: "text-red-600 dark:text-red-300" };
  if (score === 2) return { score, label: "متوسطة", tone: "bg-amber-500", text: "text-amber-600 dark:text-amber-300" };
  if (score === 3) return { score, label: "جيدة", tone: "bg-blue-500", text: "text-blue-600 dark:text-blue-300" };
  return { score, label: "قوية", tone: "bg-emerald-500", text: "text-emerald-600 dark:text-emerald-300" };
}'''

CORE_NEW = '''const PROJECT_ROLE_LABELS_AR = {
  OWNER: "مالك",
  MANAGER: "مدير مشروع",
  MEMBER: "عضو",
};
const PROJECT_ROLE_LABELS_EN = {
  OWNER: "Owner",
  MANAGER: "Project Manager",
  MEMBER: "Member",
};
const PROJECT_ROLE_LABELS = PROJECT_ROLE_LABELS_AR;

const PROJECT_ROLE_HINTS_AR = {
  OWNER: "تحكم كامل داخل المشروع والبوردات.",
  MANAGER: "مدير مشروع داخل هذا المشروع المحدد فقط، ولا يغيّر دوره الإداري داخل القسم.",
  MEMBER: "تنفيذ المهام والتعليق ورفع الملفات.",
};
const PROJECT_ROLE_HINTS_EN = {
  OWNER: "Full control inside the project and its boards.",
  MANAGER: "Project Manager in this project only; the administrative department role does not change.",
  MEMBER: "Execute tasks, comment, and upload files.",
};
const PROJECT_ROLE_HINTS = PROJECT_ROLE_HINTS_AR;

const SYSTEM_ROLE_HINTS_AR = {
  SUPER_ADMIN: ["تحكم كامل في النظام", "إدارة كل المستخدمين", "وصول لكل المشاريع"],
  ADMIN: ["إدارة الفريق والعملاء", "إنشاء وتعديل المشاريع", "وصول إداري عام"],
  MANAGER: ["صلاحية إدارة داخلية", "يمكن تعيينه كقائد Department من لوحة الأقسام", "لا يصبح قائد فريق إلا عند اختياره كمسؤول قسم"],
  PROJECT_MANAGER: ["صلاحية متابعة مشاريع عامة", "مدير المشروع الحقيقي يظهر من دوره داخل المشروع", "لا يساوي قائد فريق أو مدير قسم"],
  TEAM_MEMBER: ["تنفيذ المهام", "تعليقات وملفات داخل المشاريع المرتبط بها", "بدون إدارة مستخدمين"],
};
const SYSTEM_ROLE_HINTS_EN = {
  SUPER_ADMIN: ["Full system control", "Manage all users", "Access all projects"],
  ADMIN: ["Manage team and clients", "Create and edit projects", "General administrative access"],
  MANAGER: ["Internal management permissions", "Can be assigned as a Department Lead from Department Management", "Becomes a Team Lead only when assigned as a department manager"],
  PROJECT_MANAGER: ["General project follow-up permissions", "The actual project manager is defined by the role inside each project", "Does not equal Team Lead or Department Manager"],
  TEAM_MEMBER: ["Execute tasks", "Comments and files in assigned projects", "No user management"],
};
const SYSTEM_ROLE_HINTS = SYSTEM_ROLE_HINTS_AR;

function currentTeamLang() {
  if (typeof document !== "undefined" && document.documentElement?.lang === "en") return "en";
  try { return window.localStorage.getItem("tamiyouz-language") === "en" ? "en" : "ar"; } catch { return "ar"; }
}

function teamText(ar, en, lang = currentTeamLang()) {
  return lang === "en" ? en : ar;
}

function projectRoleLabel(role, lang = currentTeamLang()) {
  const labels = lang === "en" ? PROJECT_ROLE_LABELS_EN : PROJECT_ROLE_LABELS_AR;
  return labels[role] || role || teamText("عضو", "Member", lang);
}

function projectRoleHint(role, lang = currentTeamLang()) {
  const hints = lang === "en" ? PROJECT_ROLE_HINTS_EN : PROJECT_ROLE_HINTS_AR;
  return hints[role] || "";
}

function systemRoleHints(role, lang = currentTeamLang()) {
  const hints = lang === "en" ? SYSTEM_ROLE_HINTS_EN : SYSTEM_ROLE_HINTS_AR;
  return hints[role] || [];
}

function getProjectIds(userItem) {
  return (userItem.projects || []).map((project) => project.id);
}

function dateLabel(value, lang = currentTeamLang()) {
  if (!value) return "—";
  try {
    return new Intl.DateTimeFormat(lang === "en" ? "en-GB" : "ar-EG", { dateStyle: "medium" }).format(new Date(value));
  } catch {
    return "—";
  }
}

function dateTimeLabel(value, lang = currentTeamLang()) {
  if (!value) return "—";
  try {
    return new Intl.DateTimeFormat(lang === "en" ? "en-GB" : "ar-EG", { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
  } catch {
    return "—";
  }
}

function passwordStrengthDetails(value = "", lang = currentTeamLang()) {
  const password = String(value || "");
  if (!password) return { score: 0, label: teamText("لم تُكتب كلمة مرور", "No password entered", lang), tone: "bg-zinc-200 dark:bg-white/10", text: "text-zinc-400" };
  let score = 0;
  if (password.length >= 12) score += 1;
  if (/[a-z]/.test(password) && /[A-Z]/.test(password)) score += 1;
  if (/\\d/.test(password)) score += 1;
  if (/[^A-Za-z0-9]/.test(password)) score += 1;
  if (score <= 1) return { score, label: teamText("ضعيفة", "Weak", lang), tone: "bg-red-500", text: "text-red-600 dark:text-red-300" };
  if (score === 2) return { score, label: teamText("متوسطة", "Medium", lang), tone: "bg-amber-500", text: "text-amber-600 dark:text-amber-300" };
  if (score === 3) return { score, label: teamText("جيدة", "Good", lang), tone: "bg-blue-500", text: "text-blue-600 dark:text-blue-300" };
  return { score, label: teamText("قوية", "Strong", lang), tone: "bg-emerald-500", text: "text-emerald-600 dark:text-emerald-300" };
}'''

REPLACEMENTS = [
    (CORE_OLD, CORE_NEW, 1),
    ('const passwordStrength = passwordStrengthDetails(editing?.newPassword || "");', 'const passwordStrength = passwordStrengthDetails(editing?.newPassword || "", lang);', 1),
    ('const selectedRoleHints = SYSTEM_ROLE_HINTS[selectedRole] || [];', 'const selectedRoleHints = systemRoleHints(selectedRole, lang);', 1),
    ('>عرض التفاصيل</button>', '>{teamText("عرض التفاصيل", "View details", lang)}</button>', 1),
    ('>عرض المزيد</button>', '>{teamText("عرض المزيد", "View more", lang)}</button>', 1),
    ('<span>الفريق</span><span>‹</span><span>أعضاء الفريق</span><span>‹</span><span className="text-amber-700 dark:text-amber-300">تفاصيل العضو</span>', '<span>{teamText("الفريق", "Team", lang)}</span><span>‹</span><span>{teamText("أعضاء الفريق", "Team members", lang)}</span><span>‹</span><span className="text-amber-700 dark:text-amber-300">{teamText("تفاصيل العضو", "Member details", lang)}</span>', 1),
    ('<h2 className="text-xl font-black text-zinc-950 dark:text-white">تفاصيل العضو</h2>', '<h2 className="text-xl font-black text-zinc-950 dark:text-white">{teamText("تفاصيل العضو", "Member details", lang)}</h2>', 1),
    ('<p className="mt-1 text-xs font-bold text-zinc-500">استعراض وإدارة بيانات العضو وصلاحياته وإجراءاته دون حذف أي وظيفة قائمة.</p>', '<p className="mt-1 text-xs font-bold text-zinc-500">{teamText("استعراض وإدارة بيانات العضو وصلاحياته وإجراءاته دون حذف أي وظيفة قائمة.", "Review and manage member data, permissions, and actions without removing existing functionality.", lang)}</p>', 1),
    ('aria-label="إغلاق تفاصيل العضو"', 'aria-label={teamText("إغلاق تفاصيل العضو", "Close member details", lang)}', 1),
    ('>حالة الحساب</div>', '>{teamText("حالة الحساب", "Account status", lang)}</div>', 1),
    ('>القسم</div>', '>{teamText("القسم", "Department", lang)}</div>', 2),
    ('>نوع الحساب</div>', '>{teamText("نوع الحساب", "Account type", lang)}</div>', 2),
    ('>حساب داخلي</div>', '>{teamText("حساب داخلي", "Internal account", lang)}</div>', 2),
    ('>آخر تسجيل دخول</div>', '>{teamText("آخر تسجيل دخول", "Last login", lang)}</div>', 1),
    ('>تاريخ الانضمام</div>', '>{teamText("تاريخ الانضمام", "Joined at", lang)}</div>', 1),
    ('? "جاري الإرسال..." : "إعادة الدعوة"', '? teamText("جاري الإرسال...", "Sending...", lang) : teamText("إعادة الدعوة", "Resend invite", lang)', 1),
    ('>إلغاء الدعوة</button>', '>{teamText("إلغاء الدعوة", "Cancel invite", lang)}</button>', 1),
    ('>تعطيل الحساب</button>', '>{teamText("تعطيل الحساب", "Disable account", lang)}</button>', 1),
    ('<UserCheck size={14} /> تفعيل الحساب', '<UserCheck size={14} /> {teamText("تفعيل الحساب", "Activate account", lang)}', 1),
    ('? "جاري الفصل..." : "فصل من الفريق"', '? teamText("جاري الفصل...", "Separating...", lang) : teamText("فصل من الفريق", "Separate from team", lang)', 1),
    ('>غير قابل للإدارة من هذا الحساب</span>', '>{teamText("غير قابل للإدارة من هذا الحساب", "Not manageable from this account", lang)}</span>', 1),
    ('>المشاريع المرتبطة</h4>', '>{teamText("المشاريع المرتبطة", "Linked projects", lang)}</h4>', 1),
    ('>المشاريع التي يعمل عليها العضو وإدارة الربط الحالي.</p>', '>{teamText("المشاريع التي يعمل عليها العضو وإدارة الربط الحالي.", "Projects assigned to this member and the current assignment management.", lang)}</p>', 1),
    ('>الكل</div>', '>{teamText("الكل", "All", lang)}</div>', 1),
    ('>نشطة</div>', '>{teamText("نشطة", "Active", lang)}</div>', 1),
    ('>مكتملة</div>', '>{teamText("مكتملة", "Completed", lang)}</div>', 1),
    ('{PROJECT_ROLE_LABELS[project.role] || project.role || "عضو"}', '{projectRoleLabel(project.role, lang)}', 1),
    ('{removeBusy ? "جاري..." : "إلغاء"}', '{removeBusy ? teamText("جاري...", "Working...", lang) : teamText("إلغاء", "Remove", lang)}', 1),
    ('>غير مرتبط بمشاريع محددة</div>', '>{teamText("غير مرتبط بمشاريع محددة", "Not linked to specific projects", lang)}</div>', 1),
    ('>تعديل المشاريع المخصصة</div>', '>{teamText("تعديل المشاريع المخصصة", "Edit assigned projects", lang)}</div>', 1),
    ('<UserPlus size={14} /> إدارة المشاريع', '<UserPlus size={14} /> {teamText("إدارة المشاريع", "Manage projects", lang)}', 1),
    ('>البيانات الأساسية</h4>', '>{teamText("البيانات الأساسية", "Basic information", lang)}</h4>', 1),
    ('>تحديث المعلومات الأساسية للعضو.</p>', '>{teamText("تحديث المعلومات الأساسية للعضو.", "Update the member basic information.", lang)}</p>', 1),
    ('>الاسم الكامل</span>', '>{teamText("الاسم الكامل", "Full name", lang)}</span>', 1),
    ('>البريد الإلكتروني</span>', '>{teamText("البريد الإلكتروني", "Email", lang)}</span>', 1),
    ('>الدور الوظيفي</span>', '>{teamText("الدور الوظيفي", "System role", lang)}</span>', 1),
    ('>الحالة</div>', '>{teamText("الحالة", "Status", lang)}</div>', 1),
    ("{[['الاسم الكامل', item.name || '—'], ['البريد الإلكتروني', item.email || '—'], ['القسم', departmentLabel(item.department, lang)], ['الدور الوظيفي', roleLabel(item.role, lang)], ['الحالة', statusLabel(status, lang)], ['نوع الحساب', 'حساب داخلي']].map", "{[[teamText('الاسم الكامل', 'Full name', lang), item.name || '—'], [teamText('البريد الإلكتروني', 'Email', lang), item.email || '—'], [teamText('القسم', 'Department', lang), departmentLabel(item.department, lang)], [teamText('الدور الوظيفي', 'System role', lang), roleLabel(item.role, lang)], [teamText('الحالة', 'Status', lang), statusLabel(status, lang)], [teamText('نوع الحساب', 'Account type', lang), teamText('حساب داخلي', 'Internal account', lang)]].map", 1),
    ('? "جاري الحفظ..." : "حفظ التغييرات"', '? teamText("جاري الحفظ...", "Saving...", lang) : teamText("حفظ التغييرات", "Save changes", lang)', 1),
    ('>الأدوار والصلاحيات</h4>', '>{teamText("الأدوار والصلاحيات", "Roles and permissions", lang)}</h4>', 1),
    ('>الدور الحالي وما يتيحه من صلاحيات أساسية.</p>', '>{teamText("الدور الحالي وما يتيحه من صلاحيات أساسية.", "Current role and its core permissions.", lang)}</p>', 1),
    ('>قائد فريق — {department}</div>', '>{teamText("قائد فريق", "Team Lead", lang)} — {department}</div>', 1),
    ('>مدير مشروع — {project.name}</div>', '>{teamText("مدير مشروع", "Project Manager", lang)} — {project.name}</div>', 1),
    ('>ملاحظات</h4>', '>{teamText("ملاحظات", "Notes", lang)}</h4>', 1),
    ('>ملاحظات إدارية متاحة حول العضو.</p>', '>{teamText("ملاحظات إدارية متاحة حول العضو.", "Administrative notes available for this member.", lang)}</p>', 1),
    ('{item.profileNotes || item.workNotes || "لا توجد ملاحظات مسجلة حاليًا."}', '{item.profileNotes || item.workNotes || teamText("لا توجد ملاحظات مسجلة حاليًا.", "No notes are currently recorded.", lang)}', 1),
    ('>الأمان وتغيير كلمة المرور</h4>', '>{teamText("الأمان وتغيير كلمة المرور", "Security and password", lang)}</h4>', 1),
    ('>تغيير مباشر وآمن لكلمة مرور العضو.</p>', '>{teamText("تغيير مباشر وآمن لكلمة مرور العضو.", "Safely change the member password directly.", lang)}</p>', 1),
    ('>كلمة المرور الجديدة</span>', '>{teamText("كلمة المرور الجديدة", "New password", lang)}</span>', 1),
    ('placeholder="اكتب كلمة المرور الجديدة"', 'placeholder={teamText("اكتب كلمة المرور الجديدة", "Enter the new password", lang)}', 1),
    ('aria-label={showEditNewPassword ? "إخفاء كلمة المرور" : "إظهار كلمة المرور"}', 'aria-label={showEditNewPassword ? teamText("إخفاء كلمة المرور", "Hide password", lang) : teamText("إظهار كلمة المرور", "Show password", lang)}', 1),
    ('>تأكيد كلمة المرور</span>', '>{teamText("تأكيد كلمة المرور", "Confirm password", lang)}</span>', 1),
    ('placeholder="أعد كتابة كلمة المرور الجديدة"', 'placeholder={teamText("أعد كتابة كلمة المرور الجديدة", "Re-enter the new password", lang)}', 1),
    ('aria-label={showEditConfirmPassword ? "إخفاء تأكيد كلمة المرور" : "إظهار تأكيد كلمة المرور"}', 'aria-label={showEditConfirmPassword ? teamText("إخفاء تأكيد كلمة المرور", "Hide password confirmation", lang) : teamText("إظهار تأكيد كلمة المرور", "Show password confirmation", lang)}', 1),
    ('>قوة كلمة المرور</span>', '>{teamText("قوة كلمة المرور", "Password strength", lang)}</span>', 1),
    ('<div>• 12 حرفًا على الأقل.</div><div>• يفضّل الجمع بين حروف كبيرة وصغيرة وأرقام ورمز خاص.</div><div>• اترك الحقلين فارغين للاحتفاظ بكلمة المرور الحالية.</div>', '<div>• {teamText("12 حرفًا على الأقل.", "At least 12 characters.", lang)}</div><div>• {teamText("يفضّل الجمع بين حروف كبيرة وصغيرة وأرقام ورمز خاص.", "Use upper- and lowercase letters, numbers, and a special character.", lang)}</div><div>• {teamText("اترك الحقلين فارغين للاحتفاظ بكلمة المرور الحالية.", "Leave both fields empty to keep the current password.", lang)}</div>', 1),
    ('? "جاري الحفظ..." : "حفظ وتحديث كلمة المرور"', '? teamText("جاري الحفظ...", "Saving...", lang) : teamText("حفظ وتحديث كلمة المرور", "Save and update password", lang)', 1),
    ('{status !== "ACTIVE" ? "التغيير المباشر متاح للحسابات النشطة فقط. يمكنك استخدام إجراءات الدعوة أو إعادة التفعيل حسب حالة الحساب." : "لا تملك صلاحية تغيير كلمة مرور هذا العضو."}', '{status !== "ACTIVE" ? teamText("التغيير المباشر متاح للحسابات النشطة فقط. يمكنك استخدام إجراءات الدعوة أو إعادة التفعيل حسب حالة الحساب.", "Direct password changes are available only for active accounts. Use invitation or reactivation actions according to account status.", lang) : teamText("لا تملك صلاحية تغيير كلمة مرور هذا العضو.", "You do not have permission to change this member password.", lang)}', 1),
    ('<RefreshCw size={14} /> إرسال رابط إعادة تعيين بدلًا من التغيير المباشر', '<RefreshCw size={14} /> {teamText("إرسال رابط إعادة تعيين بدلًا من التغيير المباشر", "Send a reset link instead", lang)}', 1),
    ('>سجل النشاط</h4>', '>{teamText("سجل النشاط", "Activity log", lang)}</h4>', 1),
    ('>آخر المؤشرات المتاحة المتعلقة بالعضو.</p>', '>{teamText("آخر المؤشرات المتاحة المتعلقة بالعضو.", "Latest available activity indicators for this member.", lang)}</p>', 1),
    ('{[{ label: "حالة الحساب الحالية", value: statusLabel(status, lang), tone: "bg-emerald-500" }, { label: "آخر تسجيل دخول", value: dateTimeLabel(item.lastLoginAt), tone: "bg-blue-500" }, { label: "آخر ظهور", value: dateTimeLabel(item.lastSeenAt || item.lastActivityAt), tone: "bg-amber-500" }, { label: "تاريخ إنشاء الحساب", value: dateTimeLabel(item.createdAt), tone: "bg-zinc-400" }].map', '{[{ label: teamText("حالة الحساب الحالية", "Current account status", lang), value: statusLabel(status, lang), tone: "bg-emerald-500" }, { label: teamText("آخر تسجيل دخول", "Last login", lang), value: dateTimeLabel(item.lastLoginAt, lang), tone: "bg-blue-500" }, { label: teamText("آخر ظهور", "Last seen", lang), value: dateTimeLabel(item.lastSeenAt || item.lastActivityAt, lang), tone: "bg-amber-500" }, { label: teamText("تاريخ إنشاء الحساب", "Account created", lang), value: dateTimeLabel(item.createdAt, lang), tone: "bg-zinc-400" }].map', 1),
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
        die("usage: generate_batch4_3_1_team.py REPO_ROOT OUTPUT_PATCH", 2)

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

    tmp = Path(tempfile.mkdtemp(prefix="tos-batch4-3-1-team-"))
    try:
        run(["git", "init", "-q"], tmp)
        run(["git", "config", "user.email", "batch4-3-1@tos.local"], tmp)
        run(["git", "config", "user.name", "TOS Batch 4.3.1 Generator"], tmp)
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
            die(f"git diff failed rc={proc.returncode}", 50)
        if not proc.stdout.strip():
            die("generated patch is empty", 51)
        output.write_text(proc.stdout, encoding="utf-8", newline="\n")
        print(f"GENERATED_PATCH_SHA256={sha256(output)}")

        numstat = run(["git", "apply", "--numstat", str(output)], root).stdout.strip().splitlines()
        parsed_paths = {row.split("\t")[-1] for row in numstat if row.strip()}
        if parsed_paths != {TARGET}:
            die(f"unexpected patch paths: {sorted(parsed_paths)}", 52)
        print("PARSER=PASS")
        run(["git", "apply", "--check", str(output)], root)
        print("APPLY_CHECK=PASS")
        print("GENERATION_MODE=GIT_DIFF_FROM_EXACT_LIVE_SOURCE")
        print("BATCH4_3_1_TEAM_GENERATOR=PASS")
        print(f"OUTPUT={output}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
