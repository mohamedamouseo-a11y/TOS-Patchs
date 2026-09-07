from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
PAGE = FRONTEND / "src/pages/SlaInboxPage.jsx"
V1_STYLE = FRONTEND / "src/pages/slaInboxFlagshipV1.css"
V11_STYLE = FRONTEND / "src/pages/slaInboxFlagshipV1_1DarkContrast.css"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_PAGE_SHA256 = "2d63b0b3fd91f43925caa249ca2028e2733b7fd7d32a8c6fb813e5af5d8b0a6e"
EXPECTED_V1_STYLE_SHA256 = "79e0efa7ac67d2210b9551700552ac9d01863c5c1e56b8cc247bf66428b81080"
IMPORT_ANCHOR = 'import "./slaInboxFlagshipV1.css";'
V11_IMPORT = 'import "./slaInboxFlagshipV1_1DarkContrast.css";'
RUNTIME_MARKER = "--tos-sla-inbox-v1-1-dark-contrast-runtime"

DARK_CSS = r''':root {
  --tos-sla-inbox-v1-1-dark-contrast-runtime: 1;
}

.dark .tos-sla-inbox-flagship-v1 {
  --sla-v11-text-strong: #f6f1e7;
  --sla-v11-text: #e7e0d3;
  --sla-v11-muted: #b2aa9d;
  --sla-v11-muted-soft: #958d82;
  --sla-v11-gold: #e1b955;
  --sla-v11-line: rgba(225,185,85,.18);
}

.dark .tos-sla-inbox-flagship-v1,
.dark .tos-sla-inbox-flagship-v1 .text-app {
  color: var(--sla-v11-text-strong) !important;
}

.dark .tos-sla-inbox-flagship-v1 .text-muted,
.dark .tos-sla-inbox-hero p:not(.text-amber-600),
.dark .tos-sla-inbox-kpi .text-muted,
.dark .tos-sla-inbox-row .text-muted,
.dark .tos-sla-inbox-empty,
.dark .tos-sla-inbox-loading {
  color: var(--sla-v11-muted) !important;
}

.dark .tos-sla-inbox-hero > div:first-child > p:first-child {
  color: #efc65f !important;
}

.dark .tos-sla-inbox-hero h1,
.dark .tos-sla-inbox-kpi p:last-child,
.dark .tos-sla-inbox-row-title {
  color: var(--sla-v11-text-strong) !important;
}

.dark .tos-sla-inbox-kpi p:first-child {
  color: #c9c1b4 !important;
}

.dark .tos-sla-inbox-row > div:first-child > p:not(.tos-sla-inbox-row-title) {
  color: var(--sla-v11-muted) !important;
}

.dark .tos-sla-inbox-row > div:first-child > p:last-child {
  color: var(--sla-v11-muted-soft) !important;
}

.dark .tos-sla-inbox-filter[data-active="false"] {
  color: #d8d0c4 !important;
}

.dark .tos-sla-inbox-filter[data-active="true"] {
  color: #241903 !important;
}

.dark .tos-sla-inbox-markread {
  color: var(--sla-v11-text) !important;
  border-color: var(--sla-v11-line) !important;
}

.dark .tos-sla-inbox-list > div:last-child .text-muted {
  color: #aaa295 !important;
}

.dark .tos-sla-inbox-list > div:last-child .text-app {
  color: var(--sla-v11-text-strong) !important;
}

.dark .tos-sla-inbox-list > div:last-child button {
  color: var(--sla-v11-text-strong) !important;
  border-color: var(--sla-v11-line) !important;
  background: rgba(24,24,22,.96) !important;
}

.dark .tos-sla-inbox-list > div:last-child button:disabled {
  color: #766f65 !important;
  background: rgba(19,19,17,.86) !important;
}

.dark .tos-sla-inbox-list > div:last-child span {
  color: #f0eadf !important;
}

.dark .tos-sla-inbox-row[data-type="SLA_BREACH"] span:first-child {
  color: #ff8f8f !important;
}

.dark .tos-sla-inbox-row[data-type="SLA_ESCALATION"] span:first-child {
  color: #f0bf52 !important;
}

.dark .tos-sla-inbox-row[data-type="SLA_RESOLVED"] span:first-child {
  color: #5fd6aa !important;
}
'''

PRESERVE_FILES = [
    V1_STYLE,
    FRONTEND / "src/pages/SlaCenterPage.jsx",
    FRONTEND / "src/components/RamzyAssistant.jsx",
    FRONTEND / "src/components/TcsFloatingLauncher.jsx",
    FRONTEND / "src/components/TcsDesktopWindow.jsx",
]

print("RUNNING=TOS_UXUI_SLA_INBOX_FLAGSHIP_V1_1_DARK_CONTRAST_FIX")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_count(root: Path, needle: bytes) -> int:
    if not root.exists():
        return 0
    total = 0
    for path in root.rglob("*"):
        if path.is_file():
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
    print("SLA_INBOX_FLAGSHIP_V1_1_RUNTIME=NO")
    sys.exit(1)


if ROOT.resolve() == Path("/"):
    fail("unsafe ROOT")
for path in (FRONTEND, PAGE, V1_STYLE, LIVE_PARENT, *PRESERVE_FILES):
    if not path.exists():
        fail(f"required path missing: {path}")

if sha256(PAGE) != EXPECTED_PAGE_SHA256:
    fail(f"SlaInboxPage.jsx pagination baseline mismatch: {sha256(PAGE)}")
if sha256(V1_STYLE) != EXPECTED_V1_STYLE_SHA256:
    fail(f"SLA Inbox V1 style baseline mismatch: {sha256(V1_STYLE)}")
if V11_STYLE.exists():
    fail("V1.1 dark contrast stylesheet already exists")

original = PAGE.read_text(encoding="utf-8")
if original.count(IMPORT_ANCHOR) != 1:
    fail(f"V1 import guard mismatch: {original.count(IMPORT_ANCHOR)}")
if V11_IMPORT in original:
    fail("V1.1 dark contrast import already present")

preserve_before = {str(path): sha256(path) for path in PRESERVE_FILES}

# Strict behavior anchors from V1 + pagination.
for token in (
    'request("/api/sla/inbox?limit=250")',
    'window.setInterval(() => load({ quiet: true }), 60_000)',
    'request(`/api/users/notifications/${encodeURIComponent(id)}/read`, { method: "PATCH" })',
    'request("/api/sla/inbox/mark-all-read", { method: "POST", body: "{}" })',
    'const NOTIFICATION_PAGE_SIZE = 10;',
    'data-sla-inbox-pagination="v1"',
    'const pagedNotifications = useMemo',
    'setNotificationPage(1);',
    'tos-sla-inbox-flagship-v1',
):
    if token not in original:
        fail(f"required SLA Inbox runtime anchor missing: {token}")

source = original.replace(IMPORT_ANCHOR, IMPORT_ANCHOR + "\n" + V11_IMPORT, 1)
if source.count(V11_IMPORT) != 1:
    fail("V1.1 import transform failed")

try:
    PAGE.write_text(source, encoding="utf-8")
    V11_STYLE.write_text(DARK_CSS, encoding="utf-8")
except Exception as exc:
    fail(f"source write failed: {exc}", original)

# Enforce light-mode isolation: stylesheet may only style .dark descendants plus :root marker.
for line in DARK_CSS.splitlines():
    stripped = line.strip()
    if stripped.endswith("{") and not stripped.startswith((":root", ".dark")):
        fail(f"non-dark selector detected in V1.1 CSS: {stripped}", original)

build = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, text=True, capture_output=True)
if build.returncode != 0:
    print(build.stdout[-12000:])
    print(build.stderr[-12000:])
    fail("frontend build failed", original)

if not DIST.exists() or not (DIST / "index.html").exists():
    fail("dist/index.html missing after build", original)
for marker in (
    RUNTIME_MARKER.encode(),
    b'tos-sla-inbox-flagship-v1',
    b'data-sla-inbox-pagination',
    b'Previous',
    b'Next',
):
    if tree_count(DIST, marker) < 1:
        fail(f"built output missing V1.1/pagination marker: {marker.decode(errors='ignore')}", original)

for path in PRESERVE_FILES:
    if sha256(path) != preserve_before[str(path)]:
        fail(f"out-of-scope file changed: {path}", original)

# Safe atomic deploy.
ts = int(time.time())
candidate = LIVE_PARENT / f"build.sla-inbox-v1-1-dark-contrast-candidate-{ts}"
backup = LIVE_PARENT / f"build.sla-inbox-v1-1-dark-contrast-backup-{ts}"
failed_live = LIVE_PARENT / f"build.sla-inbox-v1-1-dark-contrast-failed-{ts}"
try:
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
print("SLA_INBOX_FLAGSHIP_V1_1_RUNTIME=YES")
print("SLA_INBOX_V1_1_SCOPE=DARK_CONTRAST_ONLY")
print("SLA_INBOX_LIGHT_MODE_CHANGED=NO")
print("SLA_INBOX_DARK_KPI_TEXT=CORRECTED")
print("SLA_INBOX_DARK_NOTIFICATION_TEXT=CORRECTED")
print("SLA_INBOX_DARK_MUTED_TEXT=CORRECTED")
print("SLA_INBOX_DARK_FILTER_TEXT=CORRECTED")
print("SLA_INBOX_DARK_MARK_READ_TEXT=CORRECTED")
print("SLA_INBOX_DARK_PAGINATION_TEXT=CORRECTED")
print("SLA_INBOX_PAGINATION_V1_PRESERVED=YES")
print("SLA_INBOX_MARK_READ_CHANGED=NO")
print("SLA_INBOX_MARK_ALL_READ_CHANGED=NO")
print("SLA_INBOX_FILTER_LOGIC_CHANGED=NO")
print("SLA_INBOX_API_CHANGED=NO")
print("SLA_INBOX_POLLING_CHANGED=NO")
print("SLA_CENTER_CHANGED=NO")
print("RAMZY_CHANGED=NO")
print("TCS_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print(f"SLA_INBOX_PAGE_SHA256={sha256(PAGE)}")
print(f"SLA_INBOX_V1_STYLE_SHA256={sha256(V1_STYLE)}")
print(f"SLA_INBOX_V11_STYLE_SHA256={sha256(V11_STYLE)}")
print(f"LIVE_BACKUP={backup}")
print("STATUS=READY")