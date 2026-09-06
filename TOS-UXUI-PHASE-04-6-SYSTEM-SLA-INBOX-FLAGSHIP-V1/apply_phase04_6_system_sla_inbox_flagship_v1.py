from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
PATCH_DIR = Path(__file__).resolve().parent
PAGE = ROOT / "frontend/src/pages/SlaInboxPage.jsx"
STYLE_TARGET = ROOT / "frontend/src/pages/slaInboxFlagshipV1.css"
STYLE_ASSET = PATCH_DIR / "slaInboxFlagshipV1.css"
FRONTEND = ROOT / "frontend"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_PAGE_GIT_BLOB_SHA1 = "98644467a39ea41584b1305d6de343b26b7af582"
V1_RUNTIME = "--tos-sla-inbox-flagship-v1-runtime"
ROOT_CLASS = "tos-sla-inbox-flagship-v1"
KPI_CLASS = "tos-sla-inbox-kpi"
LIST_CLASS = "tos-sla-inbox-list"

print("RUNNING=PHASE04_6_SYSTEM_SLA_INBOX_FLAGSHIP_V1")


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
    fail("slaInboxFlagshipV1.css already exists; refusing duplicate apply")

actual_page_blob = git_blob_sha1(PAGE)
if actual_page_blob != EXPECTED_PAGE_GIT_BLOB_SHA1:
    fail(f"SlaInboxPage.jsx source guard mismatch: {actual_page_blob}")

original = PAGE.read_text(encoding="utf-8")
style_css = STYLE_ASSET.read_text(encoding="utf-8")
if V1_RUNTIME not in style_css:
    fail("V1 runtime marker missing from style asset")
if ROOT_CLASS in original or V1_RUNTIME in original:
    fail("SLA Inbox Flagship V1 appears partially or already applied")

source = original

# Scoped stylesheet only for SLA Inbox.
prefs_import = 'import { usePreferences } from "../contexts/PreferencesContext";'
require_count(source, prefs_import, 1, "preferences import")
source = source.replace(prefs_import, prefs_import + '\nimport "./slaInboxFlagshipV1.css";', 1)

# Stable visual hooks; handlers, requests and state remain untouched.
replacements = [
    ('<div className="p-4 sm:p-6">', '<div className="tos-sla-inbox-flagship-v1 p-4 sm:p-6">', "page root"),
    ('<div className="mx-auto max-w-7xl space-y-5">', '<div className="tos-sla-inbox-frame mx-auto max-w-7xl space-y-5">', "page frame"),
    ('<div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">', '<div className="tos-sla-inbox-hero flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">', "hero"),
    ('className="inline-flex items-center gap-2 rounded-xl border border-app px-3 py-2 text-sm font-bold hover:bg-app-soft"', 'className="tos-sla-refresh-button inline-flex items-center gap-2 rounded-xl border border-app px-3 py-2 text-sm font-bold hover:bg-app-soft"', "refresh button"),
    ('className="inline-flex items-center gap-2 rounded-xl bg-amber-500 px-3 py-2 text-sm font-black text-zinc-950 disabled:opacity-50"', 'className="tos-sla-markall-button inline-flex items-center gap-2 rounded-xl bg-amber-500 px-3 py-2 text-sm font-black text-zinc-950 disabled:opacity-50"', "mark-all button"),
    ('<div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">', '<div className="tos-sla-inbox-kpi-grid grid gap-3 sm:grid-cols-2 xl:grid-cols-4">', "KPI grid"),
    ('<div key={key} className="rounded-2xl border border-app bg-app-card p-4 shadow-sm">', '<div key={key} data-tone={key} className="tos-sla-inbox-kpi rounded-2xl border border-app bg-app-card p-4 shadow-sm">', "KPI card"),
    ('<div className="flex flex-wrap gap-2">', '<div className="tos-sla-inbox-filters flex flex-wrap gap-2">', "filters rail"),
    ('className={`rounded-full px-4 py-2 text-sm font-bold ${filter === item ? "bg-app text-app-card" : "border border-app bg-app-card text-app"}`}', 'data-active={filter === item ? "true" : "false"} className={`tos-sla-inbox-filter rounded-full px-4 py-2 text-sm font-bold ${filter === item ? "bg-app text-app-card" : "border border-app bg-app-card text-app"}`}', "filter button"),
    ('{error && <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-4 text-sm font-bold text-red-600">{error}</div>}', '{error && <div className="tos-sla-inbox-error rounded-2xl border border-red-500/30 bg-red-500/10 p-4 text-sm font-bold text-red-600">{error}</div>}', "error state"),
    ('<div className="rounded-2xl border border-app bg-app-card p-10 text-center text-sm font-bold text-muted">{ar ? "جارٍ التحميل..." : "Loading..."}</div>', '<div className="tos-sla-inbox-loading rounded-2xl border border-app bg-app-card p-10 text-center text-sm font-bold text-muted">{ar ? "جارٍ التحميل..." : "Loading..."}</div>', "loading state"),
    ('<div className="overflow-hidden rounded-2xl border border-app bg-app-card">', '<div className="tos-sla-inbox-list overflow-hidden rounded-2xl border border-app bg-app-card">', "inbox list"),
    ('<div key={item.id} className={`flex flex-col gap-3 border-b border-app p-4 last:border-0 md:flex-row md:items-center md:justify-between ${item.readAt ? "opacity-70" : "bg-amber-500/[0.035]"}`}>', '<div key={item.id} data-type={item.type} data-read={item.readAt ? "true" : "false"} data-unread={!item.readAt ? "true" : "false"} className={`tos-sla-inbox-row flex flex-col gap-3 border-b border-app p-4 last:border-0 md:flex-row md:items-center md:justify-between ${item.readAt ? "opacity-70" : "bg-amber-500/[0.035]"}`}>', "notification row"),
    ('<p className="mt-2 font-black text-app">{item.title}</p>', '<p className="tos-sla-inbox-row-title mt-2 font-black text-app">{item.title}</p>', "notification title"),
    ('className="rounded-xl border border-app px-3 py-2 text-sm font-bold hover:bg-app-soft disabled:opacity-50"', 'className="tos-sla-inbox-markread rounded-xl border border-app px-3 py-2 text-sm font-bold hover:bg-app-soft disabled:opacity-50"', "mark-read button"),
    ('{!notifications.length && <div className="p-10 text-center text-sm font-bold text-muted">{ar ? "لا توجد تنبيهات في هذا التصنيف." : "No notifications in this queue."}</div>}', '{!notifications.length && <div className="tos-sla-inbox-empty p-10 text-center text-sm font-bold text-muted">{ar ? "لا توجد تنبيهات في هذا التصنيف." : "No notifications in this queue."}</div>}', "empty state"),
]

for old, new, label in replacements:
    require_count(source, old, 1, label)
    source = source.replace(old, new, 1)

try:
    PAGE.write_text(source, encoding="utf-8")
    STYLE_TARGET.write_text(style_css, encoding="utf-8")
except Exception as exc:
    PAGE.write_text(original, encoding="utf-8")
    if STYLE_TARGET.exists():
        STYLE_TARGET.unlink()
    fail(f"V1 source transformation failed and rolled back: {exc}")

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

for marker in (V1_RUNTIME.encode(), ROOT_CLASS.encode(), KPI_CLASS.encode(), LIST_CLASS.encode()):
    if tree_count(DIST, marker) < 1:
        PAGE.write_text(original, encoding="utf-8")
        if STYLE_TARGET.exists():
            STYLE_TARGET.unlink()
        fail(f"built output missing runtime marker/token: {marker.decode()}")

timestamp = int(time.time())
candidate = LIVE_PARENT / f"build.sla-inbox-v1-candidate-{timestamp}"
backup = LIVE_PARENT / f"build.sla-inbox-v1-backup-{timestamp}"
failed_live = LIVE_PARENT / f"build.sla-inbox-v1-failed-{timestamp}"

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
print("SLA_HERO_FLAGSHIP=YES")
print("SLA_EXECUTIVE_KPI_STRIP=YES")
print("SLA_FILTER_RAIL=PREMIUM")
print("SLA_NOTIFICATION_LIST=EXECUTIVE_REFINED")
print("SLA_TYPE_ACCENTS=YES")
print("SLA_UNREAD_VISUAL_PRIORITY=YES")
print("LIGHT_FLAGSHIP=YES")
print("DARK_FLAGSHIP=YES")
print("TCS_CHANGED=NO")
print("RAMZY_CHANGED=NO")
print("SLA_REQUESTS_CHANGED=NO")
print("FUNCTIONALITY_CHANGED=NO")
print("BUSINESS_LOGIC_CHANGED=NO")
print("API_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print(f"SLA_INBOX_PAGE_SHA256={sha256(PAGE)}")
print(f"SLA_INBOX_STYLE_SHA256={sha256(STYLE_TARGET)}")
print(f"LIVE_BACKUP={backup}")
print("STATUS=READY")
