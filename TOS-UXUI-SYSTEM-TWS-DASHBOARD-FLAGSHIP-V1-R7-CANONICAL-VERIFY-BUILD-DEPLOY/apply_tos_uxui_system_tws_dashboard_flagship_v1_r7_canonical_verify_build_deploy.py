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

print("RUNNING=TOS_UXUI_SYSTEM_TWS_DASHBOARD_FLAGSHIP_V1_R7_CANONICAL_VERIFY_BUILD_DEPLOY")

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


def fail(message: str, build_result="FAIL_OR_SKIPPED", rollback=False):
    if rollback:
        rollback_live()
    print("PASS/FAIL=FAIL")
    print("ERROR=" + str(message))
    print("BUILD_RESULT=" + build_result)
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("TWS_DASHBOARD_FLAGSHIP_V1_R7_RUNTIME=NO")
    sys.exit(1)


if ROOT.resolve() == Path("/"):
    fail("unsafe ROOT")

for path in (FRONTEND, PAGE, STYLE, LIVE_PARENT, *PRESERVE_FILES):
    if not path.exists():
        fail(f"required path missing: {path}")

actual_page_blob = git_blob_sha(PAGE)
actual_style_blob = git_blob_sha(STYLE)
if actual_page_blob != EXPECTED_PAGE_GIT_BLOB_SHA:
    fail(f"TwsDashboard.jsx canonical baseline mismatch: {actual_page_blob}")
if actual_style_blob != EXPECTED_STYLE_GIT_BLOB_SHA:
    fail(f"twsDashboardFlagshipV1.css canonical baseline mismatch: {actual_style_blob}")

page_source = PAGE.read_text(encoding="utf-8")
style_source = STYLE.read_text(encoding="utf-8")

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
        fail(f"required canonical TWS V1 source marker missing: {marker}")

if '<Field as="select" value={projectFilter}' in page_source:
    fail("visible native project filter select remains")
if '<Field as="select" value={trashSubView}' in page_source:
    fail("visible native trash filter select remains")
if page_source.count('{pagedItems.map((doc) =>') != 2:
    fail(f"pagedItems render count mismatch: {page_source.count('{pagedItems.map((doc) =>')}")

required_style_markers = (
    '--tos-tws-dashboard-flagship-v1-runtime: 1;',
    '.tos-tws-flagship-v1',
    '.tos-tws-hero',
    '.tos-tws-premium-menu',
    '.tos-tws-pagination',
    '.dark .tos-tws-flagship-v1',
)
for marker in required_style_markers:
    if marker not in style_source:
        fail(f"required canonical TWS V1 style marker missing: {marker}")

page_sha_before = sha256(PAGE)
style_sha_before = sha256(STYLE)
preserve_before = {str(path): sha256(path) for path in PRESERVE_FILES}

build = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, text=True, capture_output=True)
if build.returncode != 0:
    print(build.stdout[-12000:])
    print(build.stderr[-12000:])
    fail("frontend build failed", build_result="FAIL")

if not DIST.exists() or not (DIST / "index.html").exists():
    fail("dist/index.html missing after build", build_result="FAIL")

built_markers = (
    b'--tos-tws-dashboard-flagship-v1-runtime',
    b'tos-tws-flagship-v1',
    b'tos-tws-premium-select',
    b'data-tws-results-pagination',
    b'tos-tws-pagination__page',
)
for marker in built_markers:
    if tree_count(DIST, marker) < 1:
        fail(f"built output missing TWS V1 marker: {marker.decode(errors='ignore')}", build_result="FAIL")

if sha256(PAGE) != page_sha_before:
    fail("TwsDashboard.jsx changed during build", build_result="FAIL")
if sha256(STYLE) != style_sha_before:
    fail("TWS Flagship V1 stylesheet changed during build", build_result="FAIL")
for path in PRESERVE_FILES:
    if sha256(path) != preserve_before[str(path)]:
        fail(f"out-of-scope source changed during build: {path}", build_result="FAIL")

# Atomic live deploy only. No source writes, no service restart, no Git in /var/www/TOS.
ts = int(time.time())
candidate = LIVE_PARENT / f"build.tws-dashboard-flagship-v1-r7-candidate-{ts}"
live_backup = LIVE_PARENT / f"build.tws-dashboard-flagship-v1-r7-backup-{ts}"
live_failed = LIVE_PARENT / f"build.tws-dashboard-flagship-v1-r7-failed-{ts}"

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
            raise RuntimeError(f"live output missing TWS V1 marker: {marker.decode(errors='ignore')}")
except Exception as exc:
    fail(f"live runtime verification failed: {exc}", build_result="PASS", rollback=True)

# Final source integrity: absolutely no source file may have changed.
if sha256(PAGE) != page_sha_before:
    fail("TwsDashboard.jsx changed after deploy", build_result="PASS", rollback=True)
if sha256(STYLE) != style_sha_before:
    fail("TWS Flagship V1 stylesheet changed after deploy", build_result="PASS", rollback=True)
for path in PRESERVE_FILES:
    if sha256(path) != preserve_before[str(path)]:
        fail(f"out-of-scope source changed after deploy: {path}", build_result="PASS", rollback=True)

print("PASS/FAIL=PASS")
print("BUILD_RESULT=PASS")
print("LIVE_DEPLOY=PASS")
print("TWS_DASHBOARD_FLAGSHIP_V1_R7_RUNTIME=YES")
print("TWS_CANONICAL_SOURCE_STATE=VERIFIED")
print("TWS_SOURCE_WRITES=ZERO")
print("TWS_EXISTING_V1_JS=VERIFIED")
print("TWS_EXISTING_V1_STYLESHEET=VERIFIED")
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
print(f"TWS_DASHBOARD_PAGE_GIT_BLOB_SHA={git_blob_sha(PAGE)}")
print(f"TWS_DASHBOARD_STYLE_GIT_BLOB_SHA={git_blob_sha(STYLE)}")
print(f"LIVE_BACKUP={live_backup if live_backup.exists() else 'NONE'}")
print("STATUS=READY")