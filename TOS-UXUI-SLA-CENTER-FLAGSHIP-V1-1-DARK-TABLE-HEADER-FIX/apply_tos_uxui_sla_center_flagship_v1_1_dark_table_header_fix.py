from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
PAGE = FRONTEND / "src/pages/SlaCenterPage.jsx"
V1_STYLE = FRONTEND / "src/pages/slaCenterFlagshipV1.css"
V11_STYLE = FRONTEND / "src/pages/slaCenterFlagshipV1_1DarkTableHeader.css"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_PAGE_SHA256 = "dffdb2cda7e72b2b726a71885c4e11fd1e6b13c152d3e649074cc6061efd0685"
EXPECTED_V1_STYLE_SHA256 = "358e2086740f8997b93a2a16505948007bd43e810d9e4f3c955133171a56be82"
IMPORT_ANCHOR = 'import "./slaCenterFlagshipV1.css";'
V11_IMPORT = 'import "./slaCenterFlagshipV1_1DarkTableHeader.css";'
RUNTIME_MARKER = "--tos-sla-center-v1-1-dark-table-header-runtime"

DARK_CSS = r''':root {
  --tos-sla-center-v1-1-dark-table-header-runtime: 1;
}

/*
 * V1.1 scope: dark-mode SLA Drill-down table header only.
 * Explicitly paint thead + tr + th because the legacy bg-app-soft surface can
 * otherwise keep a light cell background even when the thead itself is dark.
 */
.dark .tos-sla-center-flagship-v1 .tos-sla-center-table thead,
.dark .tos-sla-center-flagship-v1 .tos-sla-center-table thead tr,
.dark .tos-sla-center-flagship-v1 .tos-sla-center-table thead th {
  background: #181816 !important;
  background-color: #181816 !important;
  background-image: none !important;
}

.dark .tos-sla-center-flagship-v1 .tos-sla-center-table thead {
  color: #bdb3a5 !important;
  box-shadow: inset 0 -1px 0 rgba(222,179,82,.10);
}

.dark .tos-sla-center-flagship-v1 .tos-sla-center-table thead th {
  color: #bdb3a5 !important;
  border-color: rgba(255,255,255,.055) !important;
  text-shadow: none !important;
}

.dark .tos-sla-center-flagship-v1 .tos-sla-center-table thead th:first-child {
  color: #cec5b7 !important;
}
'''

PRESERVE_FILES = [
    V1_STYLE,
    FRONTEND / "src/pages/SlaInboxPage.jsx",
    FRONTEND / "src/pages/slaInboxFlagshipV1.css",
    FRONTEND / "src/pages/slaInboxFlagshipV1_1DarkContrast.css",
    FRONTEND / "src/components/RamzyAssistant.jsx",
    FRONTEND / "src/components/TcsFloatingLauncher.jsx",
    FRONTEND / "src/components/TcsDesktopWindow.jsx",
]

print("RUNNING=TOS_UXUI_SLA_CENTER_FLAGSHIP_V1_1_DARK_TABLE_HEADER_FIX")


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


def fail(message: str, original_page=None):
    if original_page is not None:
        try:
            PAGE.write_text(original_page, encoding="utf-8")
        except Exception:
            pass
    if V11_STYLE.exists():
        try:
            V11_STYLE.unlink()
        except Exception:
            pass
    print("PASS/FAIL=FAIL")
    print("ERROR=" + str(message))
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("SLA_CENTER_FLAGSHIP_V1_1_RUNTIME=NO")
    sys.exit(1)


if ROOT.resolve() == Path("/"):
    fail("unsafe ROOT")

for path in (FRONTEND, PAGE, V1_STYLE, LIVE_PARENT, *PRESERVE_FILES):
    if not path.exists():
        fail(f"required path missing: {path}")

actual_page_sha = sha256(PAGE)
actual_style_sha = sha256(V1_STYLE)
if actual_page_sha != EXPECTED_PAGE_SHA256:
    fail(f"SlaCenterPage.jsx V1 baseline mismatch: {actual_page_sha}")
if actual_style_sha != EXPECTED_V1_STYLE_SHA256:
    fail(f"SLA Center Flagship V1 style baseline mismatch: {actual_style_sha}")
if V11_STYLE.exists():
    fail("V1.1 dark table header stylesheet already exists")

original = PAGE.read_text(encoding="utf-8")
if original.count(IMPORT_ANCHOR) != 1:
    fail(f"V1 style import guard mismatch: {original.count(IMPORT_ANCHOR)}")
if V11_IMPORT in original:
    fail("V1.1 import already present")

# Confirm the exact Flagship + pagination baseline and all behavior anchors before touching source.
for token in (
    'request("/api/sla/dashboard")',
    'window.setInterval(() => load({ quiet: true }), 60_000)',
    'const BREACH_PAGE_SIZE = 6;',
    'data-sla-breach-pagination="v1"',
    'const pagedBreaches = useMemo',
    'tos-sla-center-flagship-v1',
    'tos-sla-center-table',
    'tos-sla-center-pagination',
    'href="/sla-inbox"',
):
    if token not in original:
        fail(f"required SLA Center V1/pagination/behavior anchor missing: {token}")

preserve_before = {str(path): sha256(path) for path in PRESERVE_FILES}

source = original.replace(IMPORT_ANCHOR, IMPORT_ANCHOR + "\n" + V11_IMPORT, 1)
if source.count(V11_IMPORT) != 1:
    fail("V1.1 import transform failed")

# Scope guard: every actual style selector in V1.1 must be dark-scoped, except the root runtime marker.
for selector in (
    '.dark .tos-sla-center-flagship-v1 .tos-sla-center-table thead',
    '.dark .tos-sla-center-flagship-v1 .tos-sla-center-table thead tr',
    '.dark .tos-sla-center-flagship-v1 .tos-sla-center-table thead th',
):
    if selector not in DARK_CSS:
        fail(f"dark selector missing from V1.1 stylesheet: {selector}")

try:
    PAGE.write_text(source, encoding="utf-8")
    V11_STYLE.write_text(DARK_CSS, encoding="utf-8")
except Exception as exc:
    fail(f"source/style write failed: {exc}", original)

build = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, text=True, capture_output=True)
if build.returncode != 0:
    print(build.stdout[-12000:])
    print(build.stderr[-12000:])
    fail("frontend build failed", original)

if not DIST.exists() or not (DIST / "index.html").exists():
    fail("dist/index.html missing after build", original)

for marker in (
    RUNTIME_MARKER.encode(),
    b'tos-sla-center-flagship-v1',
    b'tos-sla-center-table',
    b'data-sla-breach-pagination',
    b'Breach Aging',
    b'SLA Drill-down',
):
    if tree_count(DIST, marker) < 1:
        fail(f"built output missing V1.1/V1/pagination marker: {marker.decode(errors='ignore')}", original)

# The only source changes allowed are SlaCenterPage.jsx import + new V1.1 CSS file.
for path in PRESERVE_FILES:
    if sha256(path) != preserve_before[str(path)]:
        fail(f"out-of-scope file changed: {path}", original)

# Reconfirm behavior after transformation.
transformed = PAGE.read_text(encoding="utf-8")
for token in (
    'request("/api/sla/dashboard")',
    'window.setInterval(() => load({ quiet: true }), 60_000)',
    'const BREACH_PAGE_SIZE = 6;',
    'const pagedBreaches = useMemo',
    'data-sla-breach-pagination="v1"',
):
    if token not in transformed:
        fail(f"SLA Center behavior/pagination changed unexpectedly: {token}", original)

# Safe atomic live deploy; no service restart and no Git operation in /var/www/TOS.
ts = int(time.time())
candidate = LIVE_PARENT / f"build.sla-center-v1-1-dark-table-header-candidate-{ts}"
backup = LIVE_PARENT / f"build.sla-center-v1-1-dark-table-header-backup-{ts}"
failed_live = LIVE_PARENT / f"build.sla-center-v1-1-dark-table-header-failed-{ts}"
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
        fail(f"live deployment failed and rollback attempted: {exc}", original)

print("PASS/FAIL=PASS")
print("BUILD_RESULT=PASS")
print("LIVE_DEPLOY=PASS")
print("SLA_CENTER_FLAGSHIP_V1_1_RUNTIME=YES")
print("SLA_CENTER_V1_1_SCOPE=DARK_TABLE_HEADER_ONLY")
print("SLA_CENTER_LIGHT_MODE_CHANGED=NO")
print("SLA_CENTER_DARK_THEAD_BACKGROUND=OBSIDIAN_TITANIUM")
print("SLA_CENTER_DARK_THEAD_ROW_BACKGROUND=OBSIDIAN_TITANIUM")
print("SLA_CENTER_DARK_TH_BACKGROUND=OBSIDIAN_TITANIUM")
print("SLA_CENTER_DARK_TH_TEXT_CONTRAST=CORRECTED")
print("SLA_CENTER_PAGINATION_V1_PRESERVED=YES")
print("SLA_CENTER_DRILLDOWN_LOGIC_CHANGED=NO")
print("SLA_CENTER_API_CHANGED=NO")
print("SLA_CENTER_POLLING_CHANGED=NO")
print("SLA_CENTER_DATA_CALCULATIONS_CHANGED=NO")
print("SLA_INBOX_CHANGED=NO")
print("RAMZY_CHANGED=NO")
print("TCS_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print(f"SLA_CENTER_PAGE_SHA256={sha256(PAGE)}")
print(f"SLA_CENTER_V1_STYLE_SHA256={sha256(V1_STYLE)}")
print(f"SLA_CENTER_V11_STYLE_SHA256={sha256(V11_STYLE)}")
print(f"LIVE_BACKUP={backup}")
print("STATUS=READY")
