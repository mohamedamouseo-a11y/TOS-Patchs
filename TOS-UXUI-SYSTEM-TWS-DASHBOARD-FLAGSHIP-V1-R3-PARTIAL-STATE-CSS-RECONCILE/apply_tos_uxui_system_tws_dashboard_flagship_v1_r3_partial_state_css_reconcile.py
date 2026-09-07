from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
PAGE = FRONTEND / "src/pages/tws/TwsDashboard.jsx"
STYLE = FRONTEND / "src/pages/tws/twsDashboardFlagshipV1.css"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"
PATCH_ROOT = Path(__file__).resolve().parents[1]
BASE_V1 = PATCH_ROOT / "TOS-UXUI-SYSTEM-TWS-DASHBOARD-FLAGSHIP-V1" / "apply_tos_uxui_system_tws_dashboard_flagship_v1.py"

EXPECTED_PAGE_GIT_BLOB_SHA = "9748ee83a8e2cbca9d7b6afea80a9708af032248"
EXPECTED_STYLE_GIT_BLOB_SHA = "a08189df8273419cf6f19b2d3c2297ae3124d74a"
PAGE_SIZE = 12

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

print("RUNNING=TOS_UXUI_SYSTEM_TWS_DASHBOARD_FLAGSHIP_V1_R3_PARTIAL_STATE_CSS_RECONCILE")

created_style = False


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob_sha_bytes(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def git_blob_sha(path: Path) -> str:
    return git_blob_sha_bytes(path.read_bytes())


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


def cleanup_created_style():
    global created_style
    if created_style and STYLE.exists():
        try:
            STYLE.unlink()
        except Exception:
            pass


def fail(message: str):
    cleanup_created_style()
    print("PASS/FAIL=FAIL")
    print("ERROR=" + str(message))
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("TWS_DASHBOARD_FLAGSHIP_V1_R3_RUNTIME=NO")
    sys.exit(1)


if ROOT.resolve() == Path("/"):
    fail("unsafe ROOT")

for path in (FRONTEND, PAGE, LIVE_PARENT, BASE_V1, *PRESERVE_FILES):
    if not path.exists():
        fail(f"required path missing: {path}")

# This R3 is intentionally for one exact partial state only:
# V1 JSX is already present, but its V1 stylesheet is missing.
actual_page_blob = git_blob_sha(PAGE)
if actual_page_blob != EXPECTED_PAGE_GIT_BLOB_SHA:
    fail(f"TwsDashboard.jsx partial-state baseline mismatch: {actual_page_blob}")
if STYLE.exists():
    fail(f"unexpected state: stylesheet already exists with blob {git_blob_sha(STYLE)}")

page_source = PAGE.read_text(encoding="utf-8")
required_page_markers = (
    'import "./twsDashboardFlagshipV1.css";',
    'const TWS_RESULT_PAGE_SIZE = 12;',
    'function TwsPremiumSelect',
    'tos-tws-flagship-v1',
    'tos-tws-hero',
    'tos-tws-stat',
    'tos-tws-control-card',
    'tos-tws-premium-select',
    'data-tws-results-pagination="v1"',
    'className="tos-tws-pagination"',
    '{pagedItems.map((doc) =>',
    'api.tws.list(filters)',
    'api.tws.create({ type, title:',
    'api.tws.updateContent(doc.id',
    'api.tws.duplicate(doc.id)',
    'api.tws.archive(doc.id)',
    'api.tws.restore(doc.id)',
    'api.tws.trash(doc.id)',
    'api.tws.favorites.list()',
    'api.tws.favorites.add(documentId)',
    'api.tws.favorites.remove(documentId)',
    'limit: 60',
    'window.setTimeout(load, 300)',
)
for marker in required_page_markers:
    if marker not in page_source:
        fail(f"required existing TWS V1 source marker missing: {marker}")

if '<Field as="select" value={projectFilter}' in page_source:
    fail("unexpected visible native project filter select remains")
if '<Field as="select" value={trashSubView}' in page_source:
    fail("unexpected visible native trash filter select remains")
if page_source.count('{pagedItems.map((doc) =>') != 2:
    fail(f"pagedItems render count mismatch: {page_source.count('{pagedItems.map((doc) =>')}")

# Extract the exact original V1 CSS payload from the guarded V1 installer.
base_text = BASE_V1.read_text(encoding="utf-8")
start_anchor = "CSS = r'''"
end_anchor = "\n'''\n\nprint(\"RUNNING=TOS_UXUI_SYSTEM_TWS_DASHBOARD_FLAGSHIP_V1\")"
if base_text.count(start_anchor) != 1:
    fail(f"base V1 CSS start anchor mismatch: {base_text.count(start_anchor)}")
start = base_text.index(start_anchor) + len(start_anchor)
end = base_text.find(end_anchor, start)
if end < 0:
    fail("base V1 CSS end anchor missing")
css_text = base_text[start:end]
css_bytes = css_text.encode("utf-8")
css_blob = git_blob_sha_bytes(css_bytes)
if css_blob != EXPECTED_STYLE_GIT_BLOB_SHA:
    fail(f"extracted V1 stylesheet blob mismatch: {css_blob}")

for marker in (
    '--tos-tws-dashboard-flagship-v1-runtime: 1;',
    '.tos-tws-flagship-v1',
    '.tos-tws-premium-menu',
    '.tos-tws-pagination',
):
    if marker not in css_text:
        fail(f"extracted V1 stylesheet marker missing: {marker}")

preserve_before = {str(path): sha256(path) for path in PRESERVE_FILES}
page_sha_before = sha256(PAGE)

try:
    STYLE.write_text(css_text, encoding="utf-8")
    created_style = True
except Exception as exc:
    fail(f"stylesheet creation failed: {exc}")

if git_blob_sha(STYLE) != EXPECTED_STYLE_GIT_BLOB_SHA:
    fail(f"created stylesheet blob mismatch: {git_blob_sha(STYLE)}")
if sha256(PAGE) != page_sha_before:
    fail("TwsDashboard.jsx changed while reconciling stylesheet")

build = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, text=True, capture_output=True)
if build.returncode != 0:
    print(build.stdout[-12000:])
    print(build.stderr[-12000:])
    fail("frontend build failed")

if not DIST.exists() or not (DIST / "index.html").exists():
    fail("dist/index.html missing after build")

built_markers = (
    b'--tos-tws-dashboard-flagship-v1-runtime',
    b'tos-tws-flagship-v1',
    b'tos-tws-premium-select',
    b'data-tws-results-pagination',
    b'tos-tws-pagination__page',
)
for marker in built_markers:
    if tree_count(DIST, marker) < 1:
        fail(f"built output missing TWS V1 marker: {marker.decode(errors='ignore')}")

if sha256(PAGE) != page_sha_before:
    fail("TwsDashboard.jsx changed during build")
if git_blob_sha(STYLE) != EXPECTED_STYLE_GIT_BLOB_SHA:
    fail("TWS V1 stylesheet changed during build")
for path in PRESERVE_FILES:
    if sha256(path) != preserve_before[str(path)]:
        fail(f"out-of-scope source changed: {path}")

# Atomic live deploy. No service restart. No Git in /var/www/TOS.
ts = int(time.time())
candidate = LIVE_PARENT / f"build.tws-dashboard-flagship-v1-r3-candidate-{ts}"
backup = LIVE_PARENT / f"build.tws-dashboard-flagship-v1-r3-backup-{ts}"
failed_live = LIVE_PARENT / f"build.tws-dashboard-flagship-v1-r3-failed-{ts}"

try:
    for path in (candidate, backup, failed_live):
        if path.exists():
            raise RuntimeError(f"timestamped deployment path already exists: {path}")
    shutil.copytree(DIST, candidate)
    if LIVE.exists():
        LIVE.rename(backup)
    candidate.rename(LIVE)
except Exception as exc:
    try:
        if LIVE.exists() and backup.exists():
            LIVE.rename(failed_live)
            backup.rename(LIVE)
        elif (not LIVE.exists()) and backup.exists():
            backup.rename(LIVE)
    except Exception:
        pass
    fail(f"atomic live deploy failed: {exc}")

# Verify live output; rollback live and remove newly-created source CSS on failure.
try:
    if not (LIVE / "index.html").exists():
        raise RuntimeError("live index.html missing")
    for marker in built_markers:
        if tree_count(LIVE, marker) < 1:
            raise RuntimeError(f"live output missing TWS V1 marker: {marker.decode(errors='ignore')}")
except Exception as exc:
    try:
        if LIVE.exists():
            LIVE.rename(failed_live)
        if backup.exists():
            backup.rename(LIVE)
    except Exception:
        pass
    fail(f"live runtime verification failed: {exc}")

# Successful reconciliation: stylesheet intentionally remains in source.
created_style = False

print("PASS/FAIL=PASS")
print("BUILD_RESULT=PASS")
print("LIVE_DEPLOY=PASS")
print("TWS_DASHBOARD_FLAGSHIP_V1_R3_RUNTIME=YES")
print("TWS_PARTIAL_STATE=RECONCILED")
print("TWS_EXISTING_V1_JS=VERIFIED")
print("TWS_JS_REWRITTEN=NO")
print("TWS_MISSING_V1_STYLESHEET=CREATED_FROM_ORIGINAL_PATCH")
print("TWS_STYLESHEET_BLOB_VERIFIED=YES")
print("TWS_HERO_FLAGSHIP=YES")
print("TWS_EXECUTIVE_KPI_GRID=YES")
print("TWS_NAVIGATION_RAIL=PREMIUM")
print("TWS_DOCUMENT_CARDS=FLAGSHIP")
print("TWS_BUCKETS=EXECUTIVE")
print("TWS_PROJECT_FILTER=PREMIUM_CUSTOM")
print("TWS_TRASH_FILTER=PREMIUM_CUSTOM")
print("TWS_NATIVE_VISIBLE_SELECTS_REMAINING=0")
print("TWS_RESULTS_PAGINATION=CLIENT_SIDE")
print(f"TWS_RESULTS_PAGE_SIZE={PAGE_SIZE}")
print("TWS_RESULTS_PREVIOUS_NEXT=YES")
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
print(f"TWS_DASHBOARD_STYLE_SHA256={sha256(STYLE)}")
print(f"LIVE_BACKUP={backup if backup.exists() else 'NONE'}")
print("STATUS=READY")
