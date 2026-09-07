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
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_PAGE_SHA256 = "a2890de4ea1f1f9b0f651901435bf747c27b74f15acf5af2fe48babbc40aa009"
EXPECTED_V1_STYLE_SHA256 = "79e0efa7ac67d2210b9551700552ac9d01863c5c1e56b8cc247bf66428b81080"
PAGE_SIZE = 10
RUNTIME_ATTR = 'data-sla-inbox-pagination="v1"'

PRESERVE_FILES = [
    V1_STYLE,
    FRONTEND / "src/pages/SlaCenterPage.jsx",
    FRONTEND / "src/components/RamzyAssistant.jsx",
    FRONTEND / "src/components/TcsFloatingLauncher.jsx",
    FRONTEND / "src/components/TcsDesktopWindow.jsx",
]

print("RUNNING=TOS_UXUI_SLA_INBOX_PAGINATION_V1")


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


def fail(message: str, original=None):
    if original is not None:
        try:
            PAGE.write_text(original, encoding="utf-8")
        except Exception:
            pass
    print("PASS/FAIL=FAIL")
    print("ERROR=" + str(message))
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("SLA_INBOX_PAGINATION_V1_RUNTIME=NO")
    sys.exit(1)


def require_once(source: str, token: str, label: str):
    count = source.count(token)
    if count != 1:
        fail(f"{label} guard mismatch: expected 1, found {count}")


if ROOT.resolve() == Path("/"):
    fail("unsafe ROOT")

for path in (FRONTEND, PAGE, V1_STYLE, LIVE_PARENT, *PRESERVE_FILES):
    if not path.exists():
        fail(f"required path missing: {path}")

if sha256(PAGE) != EXPECTED_PAGE_SHA256:
    fail(f"SlaInboxPage.jsx V1 baseline mismatch: {sha256(PAGE)}")
if sha256(V1_STYLE) != EXPECTED_V1_STYLE_SHA256:
    fail(f"SLA Inbox Flagship V1 style baseline mismatch: {sha256(V1_STYLE)}")

original = PAGE.read_text(encoding="utf-8")
if RUNTIME_ATTR in original or "NOTIFICATION_PAGE_SIZE" in original:
    fail("SLA Inbox pagination appears already applied")

preserve_before = {str(path): sha256(path) for path in PRESERVE_FILES}

ANCHOR_FILTERS = 'const FILTERS = ["ALL", "UNREAD", "BREACH", "ESCALATION", "RESOLVED"];'
ANCHOR_FILTER_STATE = '  const [filter, setFilter] = useState("ALL");'
ANCHOR_NOTIFICATIONS_END = '''    return rows;\n  }, [filter, payload]);'''
ANCHOR_LIST = '<div className="tos-sla-inbox-list overflow-hidden rounded-2xl border border-app bg-app-card">'
ANCHOR_MAP = '{notifications.map((item) => ('
ANCHOR_EMPTY = '{!notifications.length && <div className="tos-sla-inbox-empty p-10 text-center text-sm font-bold text-muted">{ar ? "لا توجد تنبيهات في هذا التصنيف." : "No notifications in this queue."}</div>}'

for token, label in (
    (ANCHOR_FILTERS, "filters constant"),
    (ANCHOR_FILTER_STATE, "filter state"),
    (ANCHOR_NOTIFICATIONS_END, "notifications memo end"),
    (ANCHOR_LIST, "V1 inbox list"),
    (ANCHOR_MAP, "notification map"),
    (ANCHOR_EMPTY, "empty state"),
):
    require_once(original, token, label)

source = original.replace(
    ANCHOR_FILTERS,
    ANCHOR_FILTERS + f'\nconst NOTIFICATION_PAGE_SIZE = {PAGE_SIZE};',
    1,
)
source = source.replace(
    ANCHOR_FILTER_STATE,
    ANCHOR_FILTER_STATE + '\n  const [notificationPage, setNotificationPage] = useState(1);',
    1,
)

PAGINATION_STATE = '''

  const notificationPageCount = Math.max(1, Math.ceil(notifications.length / NOTIFICATION_PAGE_SIZE));
  const safeNotificationPage = Math.min(Math.max(1, notificationPage), notificationPageCount);
  const pagedNotifications = useMemo(() => {
    const start = (safeNotificationPage - 1) * NOTIFICATION_PAGE_SIZE;
    return notifications.slice(start, start + NOTIFICATION_PAGE_SIZE);
  }, [notifications, safeNotificationPage]);

  useEffect(() => {
    setNotificationPage(1);
  }, [filter]);

  useEffect(() => {
    setNotificationPage((current) => Math.min(Math.max(1, current), notificationPageCount));
  }, [notificationPageCount]);'''
source = source.replace(ANCHOR_NOTIFICATIONS_END, ANCHOR_NOTIFICATIONS_END + PAGINATION_STATE, 1)
source = source.replace(ANCHOR_LIST, '<div data-sla-inbox-pagination="v1" className="tos-sla-inbox-list overflow-hidden rounded-2xl border border-app bg-app-card">', 1)
source = source.replace(ANCHOR_MAP, '{pagedNotifications.map((item) => (', 1)

PAGINATION_FOOTER = '''
            {notifications.length > NOTIFICATION_PAGE_SIZE && (
              <div className="flex flex-col gap-3 border-t border-app bg-app-soft/40 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
                <p className="text-xs font-bold text-muted">
                  {ar
                    ? `عرض ${(safeNotificationPage - 1) * NOTIFICATION_PAGE_SIZE + 1}–${Math.min(safeNotificationPage * NOTIFICATION_PAGE_SIZE, notifications.length)} من ${notifications.length}`
                    : `Showing ${(safeNotificationPage - 1) * NOTIFICATION_PAGE_SIZE + 1}–${Math.min(safeNotificationPage * NOTIFICATION_PAGE_SIZE, notifications.length)} of ${notifications.length}`}
                </p>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    disabled={safeNotificationPage <= 1}
                    onClick={() => setNotificationPage((current) => Math.max(1, current - 1))}
                    className="rounded-xl border border-app bg-app-card px-3 py-2 text-xs font-black text-app hover:bg-app-soft disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    {ar ? "السابق" : "Previous"}
                  </button>
                  <span className="min-w-[96px] text-center text-xs font-black text-app">
                    {ar ? `صفحة ${safeNotificationPage} من ${notificationPageCount}` : `Page ${safeNotificationPage} of ${notificationPageCount}`}
                  </span>
                  <button
                    type="button"
                    disabled={safeNotificationPage >= notificationPageCount}
                    onClick={() => setNotificationPage((current) => Math.min(notificationPageCount, current + 1))}
                    className="rounded-xl border border-app bg-app-card px-3 py-2 text-xs font-black text-app hover:bg-app-soft disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    {ar ? "التالي" : "Next"}
                  </button>
                </div>
              </div>
            )}'''
source = source.replace(ANCHOR_EMPTY, ANCHOR_EMPTY + PAGINATION_FOOTER, 1)

for token in (
    'const NOTIFICATION_PAGE_SIZE = 10;',
    'const [notificationPage, setNotificationPage] = useState(1);',
    'const pagedNotifications = useMemo',
    'data-sla-inbox-pagination="v1"',
    '{pagedNotifications.map((item) => (',
    'Page ${safeNotificationPage} of ${notificationPageCount}',
    'Showing ${(safeNotificationPage - 1) * NOTIFICATION_PAGE_SIZE + 1}',
    'setNotificationPage(1);',
):
    if token not in source:
        fail(f"transformed source missing pagination marker: {token}")

# Strict behavior preservation anchors.
for token in (
    'request("/api/sla/inbox?limit=250")',
    'window.setInterval(() => load({ quiet: true }), 60_000)',
    'request(`/api/users/notifications/${encodeURIComponent(id)}/read`, { method: "PATCH" })',
    'request("/api/sla/inbox/mark-all-read", { method: "POST", body: "{}" })',
    'if (filter === "UNREAD")',
    'if (filter === "BREACH")',
    'if (filter === "ESCALATION")',
    'if (filter === "RESOLVED")',
    'import "./slaInboxFlagshipV1.css";',
):
    if token not in source:
        fail(f"SLA Inbox behavior/V1 anchor missing after transform: {token}")

try:
    PAGE.write_text(source, encoding="utf-8")
except Exception as exc:
    fail(f"source write failed: {exc}", original)

build = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, text=True, capture_output=True)
if build.returncode != 0:
    print(build.stdout[-12000:])
    print(build.stderr[-12000:])
    fail("frontend build failed", original)

if not DIST.exists() or not (DIST / "index.html").exists():
    fail("dist/index.html missing after build", original)

for marker in (
    b'data-sla-inbox-pagination',
    b'Previous',
    b'Next',
    b'SLA Operational Inbox',
    b'tos-sla-inbox-flagship-v1',
):
    if tree_count(DIST, marker) < 1:
        fail(f"built output missing pagination/V1 marker: {marker.decode(errors='ignore')}", original)

for path in PRESERVE_FILES:
    if sha256(path) != preserve_before[str(path)]:
        fail(f"out-of-scope file changed: {path}", original)

# Safe live deployment; no service restart and no Git operation in /var/www/TOS.
ts = int(time.time())
candidate = LIVE_PARENT / f"build.sla-inbox-pagination-v1-candidate-{ts}"
backup = LIVE_PARENT / f"build.sla-inbox-pagination-v1-backup-{ts}"
failed_live = LIVE_PARENT / f"build.sla-inbox-pagination-v1-failed-{ts}"
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
print("SLA_INBOX_PAGINATION_V1_RUNTIME=YES")
print("SLA_INBOX_PAGE_SIZE=10")
print("SLA_INBOX_PAGINATION=CLIENT_SIDE")
print("SLA_INBOX_PREVIOUS_NEXT=YES")
print("SLA_INBOX_PAGE_INDICATOR=YES")
print("SLA_INBOX_RANGE_INDICATOR=YES")
print("SLA_INBOX_FILTER_CHANGE_RESETS_PAGE=YES")
print("SLA_INBOX_MARK_READ_CHANGED=NO")
print("SLA_INBOX_MARK_ALL_READ_CHANGED=NO")
print("SLA_INBOX_FILTER_LOGIC_CHANGED=NO")
print("SLA_INBOX_API_CHANGED=NO")
print("SLA_INBOX_POLLING_CHANGED=NO")
print("SLA_INBOX_FLAGSHIP_V1_PRESERVED=YES")
print("SLA_CENTER_CHANGED=NO")
print("RAMZY_CHANGED=NO")
print("TCS_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print(f"SLA_INBOX_PAGE_SHA256={sha256(PAGE)}")
print(f"SLA_INBOX_V1_STYLE_SHA256={sha256(V1_STYLE)}")
print(f"LIVE_BACKUP={backup}")
print("STATUS=READY")
