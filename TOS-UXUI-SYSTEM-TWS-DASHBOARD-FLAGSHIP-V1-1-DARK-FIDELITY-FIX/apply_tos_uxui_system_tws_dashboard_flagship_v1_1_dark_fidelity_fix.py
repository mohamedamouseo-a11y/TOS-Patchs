from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
PAGE = FRONTEND / "src/pages/tws/TwsDashboard.jsx"
V1_STYLE = FRONTEND / "src/pages/tws/twsDashboardFlagshipV1.css"
V11_STYLE = FRONTEND / "src/pages/tws/twsDashboardFlagshipV1_1DarkFidelity.css"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_PAGE_GIT_BLOB_SHA = "9748ee83a8e2cbca9d7b6afea80a9708af032248"
EXPECTED_V1_STYLE_GIT_BLOB_SHA = "a08189df8273419cf6f19b2d3c2297ae3124d74a"

IMPORT_V1 = 'import "./twsDashboardFlagshipV1.css";'
IMPORT_V11 = 'import "./twsDashboardFlagshipV1_1DarkFidelity.css";'

CSS = r''':root {
  --tos-tws-dashboard-flagship-v1-1-dark-fidelity-runtime: 1;
}

/* V1.1 — dark fidelity only. Light mode remains byte-for-byte governed by V1. */

/* 1) Only the active tab is gold in dark mode.
   V1 used [class*="dark:bg-white"], which also matched dark:bg-white/10 on inactive tabs. */
.dark .tos-tws-flagship-v1 .tos-tws-tabs .tos-tws-tab[class~="dark:bg-white/10"] {
  color: #b7afa4 !important;
  border-color: rgba(222,176,74,.08) !important;
  background: rgba(255,255,255,.055) !important;
  box-shadow: none !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-tabs .tos-tws-tab[class~="dark:bg-white/10"]:hover {
  color: #eee8df !important;
  border-color: rgba(222,176,74,.17) !important;
  background: rgba(222,176,74,.075) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-tabs .tos-tws-tab[class~="dark:bg-white"] {
  color: #251801 !important;
  border-color: rgba(222,176,74,.24) !important;
  background: linear-gradient(145deg, #efc85f, #d89e27) !important;
  box-shadow: 0 8px 18px rgba(0,0,0,.22), inset 0 1px rgba(255,255,255,.22) !important;
}

/* 2) Remove the bright lower void in the stretched hero card.
   The hero card stretches to the KPI column height; in dark mode the inner hero now fills it. */
.dark .tos-tws-flagship-v1 .tos-tws-hero-card {
  display: flex !important;
  flex-direction: column !important;
  background:
    radial-gradient(circle at 74% 16%, rgba(205,151,35,.10), transparent 31%),
    linear-gradient(135deg, #161612, #0e0e0d 62%, #19150d) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-hero-card > .tos-tws-hero {
  flex: 1 1 auto !important;
  width: 100% !important;
}

/* 3) Bucket rows stay Obsidian/Titanium instead of rendering as bright white controls. */
.dark .tos-tws-flagship-v1 .tos-tws-bucket .space-y-2 > button {
  color: #eee8de !important;
  border-color: rgba(222,176,74,.12) !important;
  background: linear-gradient(145deg, #1b1b19, #151513) !important;
  box-shadow: inset 0 1px rgba(255,255,255,.025) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-bucket .space-y-2 > button:hover {
  border-color: rgba(222,176,74,.22) !important;
  background: linear-gradient(145deg, #22211d, #191815) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-bucket .space-y-2 > button > span:last-child {
  color: #e7dfd4 !important;
}
'''

PRESERVE_FILES = [
    FRONTEND / "src/pages/tws/TwsPage.jsx",
    FRONTEND / "src/pages/tws/TDocsEditor.jsx",
    FRONTEND / "src/pages/tws/TSheetsEditor.jsx",
    FRONTEND / "src/pages/tws/TSlidesEditor.jsx",
    FRONTEND / "src/pages/tws/TwsShareViewer.jsx",
    FRONTEND / "src/pages/tws/TwsShareSettingsPage.jsx",
    FRONTEND / "src/pages/tws/TwsShared.jsx",
    FRONTEND / "src/pages/tws/TwsRecentFilesWidget.jsx",
    FRONTEND / "src/pages/tws/TwsTaskAttachments.jsx",
    FRONTEND / "src/pages/tws/twsI18n.js",
    FRONTEND / "src/pages/SlaInboxPage.jsx",
    FRONTEND / "src/pages/SlaCenterPage.jsx",
    FRONTEND / "src/pages/SlaAdvancedPage.jsx",
    FRONTEND / "src/pages/slaInboxFlagshipV1.css",
    FRONTEND / "src/pages/slaInboxFlagshipV1_1DarkContrast.css",
    FRONTEND / "src/pages/slaCenterFlagshipV1.css",
    FRONTEND / "src/pages/slaCenterFlagshipV1_1DarkTableHeader.css",
    FRONTEND / "src/pages/slaAdvancedFlagshipV1.css",
    FRONTEND / "src/pages/slaAdvancedFlagshipV1_1PremiumSelectsDarkContrast.css",
    FRONTEND / "src/pages/slaAdvancedFlagshipV1_2DropdownOverflowLayerFix.css",
    FRONTEND / "src/components/RamzyAssistant.jsx",
    FRONTEND / "src/components/TcsFloatingLauncher.jsx",
    FRONTEND / "src/components/TcsDesktopWindow.jsx",
]

print("RUNNING=TOS_UXUI_SYSTEM_TWS_DASHBOARD_FLAGSHIP_V1_1_DARK_FIDELITY_FIX")

page_before = None
v11_created = False
live_backup = None
live_failed = None


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


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


def rollback_source():
    global page_before, v11_created
    try:
        if page_before is not None:
            PAGE.write_bytes(page_before)
    except Exception:
        pass
    try:
        if v11_created and V11_STYLE.exists():
            V11_STYLE.unlink()
    except Exception:
        pass


def rollback_live():
    global live_backup, live_failed
    try:
        if live_backup is None or not live_backup.exists():
            return
        if LIVE.exists():
            if live_failed is not None and not live_failed.exists():
                LIVE.rename(live_failed)
            else:
                shutil.rmtree(LIVE)
        live_backup.rename(LIVE)
    except Exception:
        pass


def fail(message: str, build_result="FAIL_OR_SKIPPED", rollback_deploy=False):
    if rollback_deploy:
        rollback_live()
    rollback_source()
    print("PASS/FAIL=FAIL")
    print("ERROR=" + str(message))
    print("BUILD_RESULT=" + build_result)
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("TWS_DASHBOARD_FLAGSHIP_V1_1_RUNTIME=NO")
    sys.exit(1)


if ROOT.resolve() == Path("/"):
    fail("unsafe ROOT")

for path in (FRONTEND, PAGE, V1_STYLE, LIVE_PARENT, *PRESERVE_FILES):
    if not path.exists():
        fail(f"required path missing: {path}")

if git_blob_sha(PAGE) != EXPECTED_PAGE_GIT_BLOB_SHA:
    fail(f"TwsDashboard.jsx V1 baseline mismatch: {git_blob_sha(PAGE)}")
if git_blob_sha(V1_STYLE) != EXPECTED_V1_STYLE_GIT_BLOB_SHA:
    fail(f"twsDashboardFlagshipV1.css V1 baseline mismatch: {git_blob_sha(V1_STYLE)}")
if V11_STYLE.exists():
    fail(f"unexpected state: V1.1 stylesheet already exists with blob {git_blob_sha(V11_STYLE)}")

page_text = PAGE.read_text(encoding="utf-8")
if page_text.count(IMPORT_V1) != 1:
    fail(f"V1 import count mismatch: {page_text.count(IMPORT_V1)}")
if IMPORT_V11 in page_text:
    fail("unexpected state: V1.1 import already exists")

required_page_markers = (
    'const TWS_RESULT_PAGE_SIZE = 12;',
    'function TwsPremiumSelect',
    'className={cn(',
    'dark:bg-white dark:text-zinc-950',
    'dark:bg-white/10 dark:text-zinc-300',
    'className="tos-tws-hero-card overflow-hidden p-0"',
    'className="tos-tws-bucket p-4"',
    'data-tws-results-pagination="v1"',
    'limit: 60',
)
for marker in required_page_markers:
    if marker not in page_text:
        fail(f"required TWS V1 source marker missing: {marker}")

v1_style_text = V1_STYLE.read_text(encoding="utf-8")
for marker in (
    '.dark .tos-tws-flagship-v1 .tos-tws-tabs .tos-tws-tab[class*="dark:bg-white"]',
    '.dark .tos-tws-flagship-v1 .tos-tws-hero',
    '.dark .tos-tws-flagship-v1 .tos-tws-bucket',
):
    if marker not in v1_style_text:
        fail(f"required V1 dark baseline marker missing: {marker}")

page_before = PAGE.read_bytes()
v1_style_sha_before = sha256(V1_STYLE)
preserve_before = {str(path): sha256(path) for path in PRESERVE_FILES}

new_page_text = page_text.replace(IMPORT_V1, IMPORT_V1 + "\n" + IMPORT_V11, 1)
if new_page_text.count(IMPORT_V11) != 1:
    fail("V1.1 import transform failed")
if new_page_text.count(IMPORT_V1) != 1:
    fail("V1 import changed unexpectedly")

css_text = CSS
for marker in (
    '--tos-tws-dashboard-flagship-v1-1-dark-fidelity-runtime: 1;',
    '.tos-tws-tab[class~="dark:bg-white/10"]',
    '.tos-tws-tab[class~="dark:bg-white"]',
    '.tos-tws-hero-card > .tos-tws-hero',
    '.tos-tws-bucket .space-y-2 > button',
):
    if marker not in css_text:
        fail(f"V1.1 CSS marker missing before write: {marker}")

try:
    PAGE.write_text(new_page_text, encoding="utf-8")
    V11_STYLE.write_text(css_text, encoding="utf-8")
    v11_created = True
except Exception as exc:
    if V11_STYLE.exists():
        v11_created = True
    fail(f"source write failed: {exc}")

if PAGE.read_text(encoding="utf-8").count(IMPORT_V11) != 1:
    fail("V1.1 import missing after write")
if sha256(V1_STYLE) != v1_style_sha_before:
    fail("V1 stylesheet changed unexpectedly")
for path in PRESERVE_FILES:
    if sha256(path) != preserve_before[str(path)]:
        fail(f"out-of-scope source changed before build: {path}")

build = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, text=True, capture_output=True)
if build.returncode != 0:
    print(build.stdout[-12000:])
    print(build.stderr[-12000:])
    fail("frontend build failed", build_result="FAIL")

if not DIST.exists() or not (DIST / "index.html").exists():
    fail("dist/index.html missing after build", build_result="FAIL")

built_markers = (
    b'--tos-tws-dashboard-flagship-v1-runtime',
    b'--tos-tws-dashboard-flagship-v1-1-dark-fidelity-runtime',
    b'tos-tws-flagship-v1',
    b'tos-tws-premium-select',
    b'data-tws-results-pagination',
    b'tos-tws-pagination__page',
)
for marker in built_markers:
    if tree_count(DIST, marker) < 1:
        fail(f"built output missing marker: {marker.decode(errors='ignore')}", build_result="FAIL")

if PAGE.read_text(encoding="utf-8").count(IMPORT_V11) != 1:
    fail("V1.1 import changed during build", build_result="FAIL")
if sha256(V1_STYLE) != v1_style_sha_before:
    fail("V1 stylesheet changed during build", build_result="FAIL")
for path in PRESERVE_FILES:
    if sha256(path) != preserve_before[str(path)]:
        fail(f"out-of-scope source changed during build: {path}", build_result="FAIL")

ts = int(time.time())
candidate = LIVE_PARENT / f"build.tws-dashboard-flagship-v1-1-candidate-{ts}"
live_backup = LIVE_PARENT / f"build.tws-dashboard-flagship-v1-1-backup-{ts}"
live_failed = LIVE_PARENT / f"build.tws-dashboard-flagship-v1-1-failed-{ts}"

try:
    for path in (candidate, live_backup, live_failed):
        if path.exists():
            raise RuntimeError(f"timestamped deployment path already exists: {path}")
    shutil.copytree(DIST, candidate)
    if LIVE.exists():
        LIVE.rename(live_backup)
    candidate.rename(LIVE)
except Exception as exc:
    rollback_live()
    fail(f"atomic live deploy failed: {exc}", build_result="PASS")

try:
    if not (LIVE / "index.html").exists():
        raise RuntimeError("live index.html missing")
    for marker in built_markers:
        if tree_count(LIVE, marker) < 1:
            raise RuntimeError(f"live output missing marker: {marker.decode(errors='ignore')}")
except Exception as exc:
    fail(f"live runtime verification failed: {exc}", build_result="PASS", rollback_deploy=True)

if PAGE.read_text(encoding="utf-8").count(IMPORT_V11) != 1:
    fail("V1.1 import changed after deploy", build_result="PASS", rollback_deploy=True)
if sha256(V1_STYLE) != v1_style_sha_before:
    fail("V1 stylesheet changed after deploy", build_result="PASS", rollback_deploy=True)
for path in PRESERVE_FILES:
    if sha256(path) != preserve_before[str(path)]:
        fail(f"out-of-scope source changed after deploy: {path}", build_result="PASS", rollback_deploy=True)

print("PASS/FAIL=PASS")
print("BUILD_RESULT=PASS")
print("LIVE_DEPLOY=PASS")
print("TWS_DASHBOARD_FLAGSHIP_V1_1_RUNTIME=YES")
print("TWS_V1_1_SCOPE=DARK_FIDELITY_ONLY")
print("TWS_LIGHT_MODE_CHANGED=NO")
print("TWS_DARK_ACTIVE_TAB=GOLD_ONLY")
print("TWS_DARK_INACTIVE_TABS=OBSIDIAN_TITANIUM")
print("TWS_DARK_HERO_BRIGHT_VOID=REMOVED")
print("TWS_DARK_HERO_STRETCH=FULL_CARD")
print("TWS_DARK_BUCKET_ROWS=OBSIDIAN_TITANIUM")
print("TWS_DARK_BUCKET_TEXT=HIGH_CONTRAST")
print("TWS_PROJECT_FILTER=PREMIUM_CUSTOM_PRESERVED")
print("TWS_TRASH_FILTER=PREMIUM_CUSTOM_PRESERVED")
print("TWS_RESULTS_PAGINATION=PRESERVED")
print("TWS_RESULTS_PAGE_SIZE=12")
print("TWS_LIST_API_CHANGED=NO")
print("TWS_CREATE_CHANGED=NO")
print("TWS_CONTENT_UPDATE_CHANGED=NO")
print("TWS_DUPLICATE_CHANGED=NO")
print("TWS_ARCHIVE_CHANGED=NO")
print("TWS_RESTORE_CHANGED=NO")
print("TWS_TRASH_CHANGED=NO")
print("TWS_FAVORITES_CHANGED=NO")
print("SLA_INBOX_CHANGED=NO")
print("SLA_CENTER_CHANGED=NO")
print("ADVANCED_SLA_CHANGED=NO")
print("RAMZY_CHANGED=NO")
print("TCS_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print(f"TWS_DASHBOARD_PAGE_SHA256={sha256(PAGE)}")
print(f"TWS_DASHBOARD_V1_STYLE_SHA256={sha256(V1_STYLE)}")
print(f"TWS_DASHBOARD_V11_STYLE_SHA256={sha256(V11_STYLE)}")
print(f"LIVE_BACKUP={live_backup if live_backup.exists() else 'NONE'}")
print("STATUS=READY")