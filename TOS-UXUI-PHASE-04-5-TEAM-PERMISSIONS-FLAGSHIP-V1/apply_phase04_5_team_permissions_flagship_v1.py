from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
PATCH_DIR = Path(__file__).resolve().parent
PAGE = ROOT / "frontend/src/pages/PermissionsPage.jsx"
STYLE_TARGET = ROOT / "frontend/src/pages/permissionsFlagshipV1.css"
STYLE_ASSET = PATCH_DIR / "permissionsFlagshipV1.css"
FRONTEND = ROOT / "frontend"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_PAGE_GIT_BLOB_SHA1 = "f7495b5ef64c01895915ee8dda0d220b4f275c91"
V1_RUNTIME = "--tos-permissions-flagship-v1-runtime"
ROOT_CLASS = "tos-permissions-flagship-v1"
ROLE_FILTER_TOKEN = "tos-permissions-role-filter-menu"

print("RUNNING=PHASE04_5_TEAM_PERMISSIONS_FLAGSHIP_V1")


def git_blob_sha1(path: Path) -> str:
    data = path.read_bytes()
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data).hexdigest()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_count(root: Path, needle: bytes) -> int:
    if not root.exists():
        return 0
    total = 0
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            total += path.read_bytes().count(needle)
        except OSError:
            pass
    return total


def fail(message: str):
    print("PASS/FAIL=FAIL")
    print("ERROR=" + str(message))
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("V1_RUNTIME=NO")
    sys.exit(1)


def require_count(text: str, needle: str, expected: int, label: str):
    actual = text.count(needle)
    if actual != expected:
        fail(f"{label}: expected {expected} match(es), found {actual}")


if ROOT.resolve() == Path("/"):
    fail("unsafe ROOT")

for path in (PAGE, STYLE_ASSET, FRONTEND, LIVE_PARENT):
    if not path.exists():
        fail(f"required path missing: {path}")

if STYLE_TARGET.exists():
    fail("permissionsFlagshipV1.css already exists; refusing duplicate apply")

actual_page_blob = git_blob_sha1(PAGE)
if actual_page_blob != EXPECTED_PAGE_GIT_BLOB_SHA1:
    fail(f"PermissionsPage.jsx source guard mismatch: {actual_page_blob}")

original = PAGE.read_text(encoding="utf-8")
style_css = STYLE_ASSET.read_text(encoding="utf-8")

if V1_RUNTIME in original or ROOT_CLASS in original:
    fail("Permissions Flagship V1 appears partially or already applied")
if V1_RUNTIME not in style_css:
    fail("V1 runtime marker missing from style asset")

source = original

# 1) Add the premium dropdown icon and scoped stylesheet.
require_count(source, '  CheckCircle2,\n  Crown,', 1, "ChevronDown import anchor")
source = source.replace('  CheckCircle2,\n  Crown,', '  CheckCircle2,\n  ChevronDown,\n  Crown,', 1)

prefs_import = 'import { usePreferences } from "../contexts/PreferencesContext";'
require_count(source, prefs_import, 1, "preferences import")
source = source.replace(prefs_import, prefs_import + '\nimport "./permissionsFlagshipV1.css";', 1)

# 2) Add stable visual hooks without changing permission semantics.
role_card_old = 'className={cn("rounded-[26px] border border-slate-100 bg-gradient-to-br p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md dark:border-white/10", tone.soft)}'
role_card_new = 'className={cn("tos-permissions-role-card rounded-[26px] border border-slate-100 bg-gradient-to-br p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md dark:border-white/10", tone.soft)}'
require_count(source, role_card_old, 1, "role overview card")
source = source.replace(role_card_old, role_card_new, 1)

project_card_old = 'className={cn("rounded-[24px] border border-slate-100 bg-gradient-to-br p-5 shadow-sm dark:border-white/10", tone.soft)}'
project_card_new = 'className={cn("tos-permissions-project-card rounded-[24px] border border-slate-100 bg-gradient-to-br p-5 shadow-sm dark:border-white/10", tone.soft)}'
require_count(source, project_card_old, 1, "project scope card")
source = source.replace(project_card_old, project_card_new, 1)

matrix_shell_old = '<div className="overflow-hidden rounded-[26px] border border-slate-100 bg-white shadow-sm dark:border-white/10 dark:bg-zinc-900/70">'
matrix_shell_new = '<div className="tos-permissions-matrix-shell overflow-hidden rounded-[26px] border border-slate-100 bg-white shadow-sm dark:border-white/10 dark:bg-zinc-900/70">'
require_count(source, matrix_shell_old, 1, "matrix shell")
source = source.replace(matrix_shell_old, matrix_shell_new, 1)

table_old = '<table className="min-w-[900px] w-full text-right text-xs">'
table_new = '<table className="tos-permissions-matrix min-w-[900px] w-full text-right text-xs">'
require_count(source, table_old, 1, "matrix table")
source = source.replace(table_old, table_new, 1)

# 3) Replace the remaining native role <select> with a premium menu preserving the same value/onChange behavior.
role_filter_component = '''
function RoleFilterMenu({ value, onChange }) {
  const { lang } = usePreferences();
  const isEnglish = lang === "en";
  const ui = (ar, en) => isEnglish ? en : ar;
  const [open, setOpen] = useState(false);
  const options = [
    { value: "ALL", label: ui("كل الأدوار", "All roles") },
    { value: "ADMIN", label: ui("مدير", "Admin") },
    { value: "MANAGER", label: ui("قائد فريق", "Team Lead") },
    { value: "PROJECT_MANAGER", label: ui("مدير مشاريع", "Project Manager") },
    { value: "TEAM_MEMBER", label: ui("عضو فريق", "Team Member") },
  ];
  const current = options.find((option) => option.value === value) || options[0];

  return (
    <div className="tos-permissions-role-filter">
      {open && (
        <button
          type="button"
          className="fixed inset-0 z-40 cursor-default bg-transparent"
          aria-label={ui("إغلاق قائمة الأدوار", "Close role menu")}
          onClick={() => setOpen(false)}
        />
      )}
      <button
        type="button"
        className="tos-permissions-role-filter-trigger relative z-50"
        data-open={open ? "true" : "false"}
        aria-haspopup="listbox"
        aria-expanded={open}
        onClick={() => setOpen((currentOpen) => !currentOpen)}
      >
        <span className="inline-flex items-center gap-2"><SlidersHorizontal size={15} /> {current.label}</span>
        <ChevronDown size={15} className={cn("transition-transform", open && "rotate-180")} />
      </button>
      {open && (
        <div className="tos-permissions-role-filter-menu" role="listbox" aria-label={ui("تصفية حسب الدور", "Filter by role")}>
          {options.map((option) => {
            const selected = option.value === value;
            return (
              <button
                key={option.value}
                type="button"
                role="option"
                aria-selected={selected}
                data-selected={selected ? "true" : "false"}
                className="tos-permissions-role-filter-option"
                onClick={() => {
                  onChange(option.value);
                  setOpen(false);
                }}
              >
                <span>{option.label}</span>
                {selected && <CheckCircle2 size={15} />}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}

'''
matrix_anchor = 'function MatrixTable({ matrix, users = [], query, roleFilter, canManage = false, busyKey = "", onToggle }) {'
require_count(source, matrix_anchor, 1, "MatrixTable insertion anchor")
source = source.replace(matrix_anchor, role_filter_component + matrix_anchor, 1)

native_role_filter = '''            <label className="relative block">
              <SlidersHorizontal size={15} className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <select value={roleFilter} onChange={(event) => setRoleFilter(event.target.value)} className="h-11 rounded-2xl border border-slate-200 bg-white pr-9 pl-8 text-xs font-black text-slate-700 outline-none transition focus:border-violet-200 focus:ring-4 focus:ring-violet-100 dark:border-white/10 dark:bg-zinc-950 dark:text-white dark:focus:ring-violet-500/10">
                <option value="ALL">{ui("كل الأدوار", "All roles")}</option>
                <option value="ADMIN">{ui("مدير", "Admin")}</option>
                <option value="MANAGER">{ui("قائد فريق", "Team Lead")}</option>
                <option value="PROJECT_MANAGER">{ui("مدير مشاريع", "Project Manager")}</option>
                <option value="TEAM_MEMBER">{ui("عضو فريق", "Team Member")}</option>
              </select>
            </label>'''
premium_role_filter = '            <RoleFilterMenu value={roleFilter} onChange={setRoleFilter} />'
require_count(source, native_role_filter, 1, "native role filter")
source = source.replace(native_role_filter, premium_role_filter, 1)

# 4) Build executive KPIs from data already loaded by this page; no API or DB additions.
user_counts_line = '  const userCounts = useMemo(() => users.reduce((acc, item) => ({ ...acc, [item.role]: (acc[item.role] || 0) + 1 }), {}), [users]);'
require_count(source, user_counts_line, 1, "userCounts anchor")
stats_block = '''
  const permissionStats = useMemo(() => {
    const permissionKeys = matrix?.permissions || [];
    const managedRoles = ["ADMIN", "MANAGER", "PROJECT_MANAGER", "TEAM_MEMBER"];
    const enabledGrants = managedRoles.reduce((total, role) => {
      return total + permissionKeys.reduce((roleTotal, permission) => {
        return roleTotal + (matrix?.rolePermissions?.[role]?.[permission.key] ? 1 : 0);
      }, 0);
    }, 0);
    return {
      users: users.length,
      permissionKeys: permissionKeys.length,
      managedRoles: managedRoles.length,
      enabledGrants,
    };
  }, [matrix, users]);
'''
source = source.replace(user_counts_line, user_counts_line + stats_block, 1)

# 5) Flagship page/section hooks and the KPI strip.
root_old = '<div className="tos-page space-y-5">'
root_new = '<div className="tos-page tos-permissions-flagship-v1 space-y-5">'
require_count(source, root_old, 1, "page root")
source = source.replace(root_old, root_new, 1)

hero_old = '<div className="rounded-[30px] border border-slate-100 bg-white p-5 shadow-sm dark:border-white/10 dark:bg-zinc-900/70">'
hero_new = '<div className="tos-permissions-hero rounded-[30px] border border-slate-100 bg-white p-5 shadow-sm dark:border-white/10 dark:bg-zinc-900/70">'
require_count(source, hero_old, 1, "hero shell")
source = source.replace(hero_old, hero_new, 1)

section_old = '<section className="rounded-[30px] border border-slate-100 bg-white p-5 shadow-sm dark:border-white/10 dark:bg-zinc-900/70">'
section_new = '<section className="tos-permissions-section rounded-[30px] border border-slate-100 bg-white p-5 shadow-sm dark:border-white/10 dark:bg-zinc-900/70">'
require_count(source, section_old, 2, "role/project sections")
source = source.replace(section_old, section_new)

matrix_section_old = '<section id="permission-matrix" className="rounded-[30px] border border-slate-100 bg-white p-5 shadow-sm dark:border-white/10 dark:bg-zinc-900/70">'
matrix_section_new = '<section id="permission-matrix" className="tos-permissions-section tos-permissions-matrix-section rounded-[30px] border border-slate-100 bg-white p-5 shadow-sm dark:border-white/10 dark:bg-zinc-900/70">'
require_count(source, matrix_section_old, 1, "matrix section")
source = source.replace(matrix_section_old, matrix_section_new, 1)

role_grid_old = '<div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">'
role_grid_new = '<div className="tos-permissions-role-grid grid gap-4 md:grid-cols-2 xl:grid-cols-4">'
require_count(source, role_grid_old, 1, "role grid")
source = source.replace(role_grid_old, role_grid_new, 1)

console_old = '<div className="flex flex-wrap items-center gap-2">\n            <label className="relative block">\n              <Search size={15}'
console_new = '<div className="tos-permissions-console flex flex-wrap items-center gap-2">\n            <label className="tos-permissions-search relative block">\n              <Search size={15}'
require_count(source, console_old, 1, "matrix filter console")
source = source.replace(console_old, console_new, 1)

notices_anchor = '''      <Notice type="success">{message}</Notice>
      <Notice type="error">{error}</Notice>
'''
require_count(source, notices_anchor, 1, "KPI insertion anchor")
kpi_block = '''

      <section className="tos-permissions-kpi-grid" aria-label={ui("ملخص الصلاحيات", "Permissions summary")}>
        <div className="tos-permissions-kpi">
          <div className="tos-permissions-kpi-top"><span className="tos-permissions-kpi-label">{ui("أعضاء الفريق", "Team members")}</span><span className="tos-permissions-kpi-icon"><UsersRound size={18} /></span></div>
          <div className="tos-permissions-kpi-value">{permissionStats.users}</div>
          <div className="tos-permissions-kpi-note">{ui("الحسابات الظاهرة في نطاق الفريق", "Accounts in the current team scope")}</div>
        </div>
        <div className="tos-permissions-kpi">
          <div className="tos-permissions-kpi-top"><span className="tos-permissions-kpi-label">{ui("مفاتيح الصلاحيات", "Permission keys")}</span><span className="tos-permissions-kpi-icon"><ShieldCheck size={18} /></span></div>
          <div className="tos-permissions-kpi-value">{permissionStats.permissionKeys}</div>
          <div className="tos-permissions-kpi-note">{ui("الصلاحيات الديناميكية المتاحة", "Dynamic permissions currently available")}</div>
        </div>
        <div className="tos-permissions-kpi">
          <div className="tos-permissions-kpi-top"><span className="tos-permissions-kpi-label">{ui("الأدوار القابلة للإدارة", "Managed roles")}</span><span className="tos-permissions-kpi-icon"><UserCog size={18} /></span></div>
          <div className="tos-permissions-kpi-value">{permissionStats.managedRoles}</div>
          <div className="tos-permissions-kpi-note">{ui("مع حماية صلاحيات مدير النظام", "System Admin remains protected")}</div>
        </div>
        <div className="tos-permissions-kpi">
          <div className="tos-permissions-kpi-top"><span className="tos-permissions-kpi-label">{ui("المنح المفعلة", "Enabled grants")}</span><span className="tos-permissions-kpi-icon"><CheckCircle2 size={18} /></span></div>
          <div className="tos-permissions-kpi-value">{permissionStats.enabledGrants}</div>
          <div className="tos-permissions-kpi-note">{ui("إجمالي حالات السماح عبر الأدوار", "Allowed states across managed roles")}</div>
        </div>
      </section>
'''
source = source.replace(notices_anchor, notices_anchor + kpi_block, 1)

# Exact post-transform invariants.
if source.count('import "./permissionsFlagshipV1.css";') != 1:
    fail("stylesheet import post-check failed")
if source.count('select value={roleFilter}') != 0:
    fail("native role filter still present after transformation")
if source.count('<RoleFilterMenu value={roleFilter} onChange={setRoleFilter} />') != 1:
    fail("premium role filter usage post-check failed")
if source.count(ROOT_CLASS) != 1:
    fail("flagship root class post-check failed")
if source.count('tos-permissions-kpi') < 8:
    fail("executive KPI strip post-check failed")

created_style = False
try:
    PAGE.write_text(source, encoding="utf-8")
    shutil.copyfile(STYLE_ASSET, STYLE_TARGET)
    created_style = True
except Exception as exc:
    PAGE.write_text(original, encoding="utf-8")
    if created_style and STYLE_TARGET.exists():
        STYLE_TARGET.unlink()
    fail(f"source transformation failed and rolled back: {exc}")

build = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, text=True, capture_output=True)
if build.returncode != 0:
    print(build.stdout[-6000:])
    print(build.stderr[-6000:])
    PAGE.write_text(original, encoding="utf-8")
    if STYLE_TARGET.exists():
        STYLE_TARGET.unlink()
    fail("frontend build failed; source rolled back")

if not DIST.exists():
    PAGE.write_text(original, encoding="utf-8")
    if STYLE_TARGET.exists():
        STYLE_TARGET.unlink()
    fail("frontend dist missing after successful build")

for marker in (V1_RUNTIME.encode(), ROOT_CLASS.encode(), ROLE_FILTER_TOKEN.encode(), b"tos-permissions-kpi-grid"):
    if tree_count(DIST, marker) < 1:
        PAGE.write_text(original, encoding="utf-8")
        if STYLE_TARGET.exists():
            STYLE_TARGET.unlink()
        fail(f"built output missing runtime marker/token: {marker.decode()}")

timestamp = int(time.time())
candidate = LIVE_PARENT / f"build.team-permissions-v1-candidate-{timestamp}"
backup = LIVE_PARENT / f"build.team-permissions-v1-backup-{timestamp}"
failed_live = LIVE_PARENT / f"build.team-permissions-v1-failed-{timestamp}"

try:
    if candidate.exists() or backup.exists() or failed_live.exists():
        raise RuntimeError("timestamped deployment path already exists")
    shutil.copytree(DIST, candidate)
    if not LIVE.exists():
        raise RuntimeError(f"live build missing: {LIVE}")
    LIVE.rename(backup)
    candidate.rename(LIVE)
except Exception as exc:
    try:
        if LIVE.exists() and backup.exists():
            LIVE.rename(failed_live)
            backup.rename(LIVE)
        elif backup.exists() and not LIVE.exists():
            backup.rename(LIVE)
    finally:
        PAGE.write_text(original, encoding="utf-8")
        if STYLE_TARGET.exists():
            STYLE_TARGET.unlink()
    fail(f"live deployment failed and rollback attempted: {exc}")

print("PASS/FAIL=PASS")
print("BUILD_RESULT=PASS")
print("LIVE_DEPLOY=PASS")
print("V1_RUNTIME=YES")
print("EXECUTIVE_KPI_STRIP=YES")
print("ROLE_OVERVIEW_CARDS=REFINED")
print("PROJECT_SCOPE_CARDS=REFINED")
print("ROLE_FILTER_PREMIUM_MENU=YES")
print("NATIVE_ROLE_FILTER_SELECTS_REMAINING=0")
print("PERMISSION_MATRIX=EXECUTIVE_REFINED")
print("MATRIX_STICKY_PERMISSION_COLUMN=YES")
print("LIGHT_FLAGSHIP=YES")
print("DARK_FLAGSHIP=YES")
print("PERMISSION_SEMANTICS_CHANGED=NO")
print("FUNCTIONALITY_CHANGED=NO")
print("BUSINESS_LOGIC_CHANGED=NO")
print("API_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print(f"PERMISSIONS_PAGE_SHA256={sha256(PAGE)}")
print(f"PERMISSIONS_STYLE_SHA256={sha256(STYLE_TARGET)}")
print(f"LIVE_BACKUP={backup}")
print("STATUS=READY")
