from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
PAGE = FRONTEND / "src/pages/SlaCenterPage.jsx"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_PAGE_BLOB_SHA = "236e857d741985b8820cc48ddaa4cc961fd53ecf"
PAGE_SIZE = 6
RUNTIME_ATTR = 'data-sla-breach-pagination="v1"'

PRESERVE_FILES = [
    FRONTEND / "src/pages/SlaInboxPage.jsx",
    FRONTEND / "src/components/RamzyAssistant.jsx",
    FRONTEND / "src/components/TcsFloatingLauncher.jsx",
    FRONTEND / "src/components/TcsDesktopWindow.jsx",
]

print("RUNNING=TOS_UXUI_SLA_CENTER_BREACH_PAGINATION_V1")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


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
    print("SLA_CENTER_BREACH_PAGINATION_V1_RUNTIME=NO")
    sys.exit(1)


def require_once(source: str, token: str, label: str):
    count = source.count(token)
    if count != 1:
        fail(f"{label} guard mismatch: expected 1, found {count}")


if ROOT.resolve() == Path("/"):
    fail("unsafe ROOT")

for path in (FRONTEND, PAGE, LIVE_PARENT, *PRESERVE_FILES):
    if not path.exists():
        fail(f"required path missing: {path}")

actual_blob = git_blob_sha(PAGE)
if actual_blob != EXPECTED_PAGE_BLOB_SHA:
    fail(f"SlaCenterPage.jsx baseline mismatch: {actual_blob}")

original = PAGE.read_text(encoding="utf-8")
if RUNTIME_ATTR in original or "BREACH_PAGE_SIZE" in original:
    fail("SLA Center breach pagination appears already applied")

preserve_before = {str(path): sha256(path) for path in PRESERVE_FILES}

ANCHOR_DIMENSIONS = 'const DIMENSIONS = ["departments", "employees", "clients"];'
ANCHOR_DIMENSION_STATE = '  const [dimension, setDimension] = useState("departments");'
ANCHOR_ROWS = '  const rows = useMemo(() => data?.drilldowns?.[dimension] || [], [data, dimension]);'
ANCHOR_BREACH_CARD = '            <div className="rounded-2xl border border-app bg-app-card">\n              <div className="flex items-center justify-between border-b border-app p-4">\n                <div>\n                  <h2 className="font-black text-app">{ar ? "أقدم الاختراقات النشطة" : "Breach Aging"}</h2>'
ANCHOR_MAP = '                {(data?.topBreaches || []).map((item) => ('
ANCHOR_EMPTY = '                {!(data?.topBreaches || []).length && ('
ANCHOR_LIST_CLOSE = '''                )}\n              </div>\n            </div>\n          </>'''

for token, label in (
    (ANCHOR_DIMENSIONS, "dimensions anchor"),
    (ANCHOR_DIMENSION_STATE, "dimension state anchor"),
    (ANCHOR_ROWS, "rows anchor"),
    (ANCHOR_BREACH_CARD, "breach card anchor"),
    (ANCHOR_MAP, "breach map anchor"),
    (ANCHOR_EMPTY, "breach empty anchor"),
    (ANCHOR_LIST_CLOSE, "breach list close anchor"),
):
    require_once(original, token, label)

source = original.replace(
    ANCHOR_DIMENSIONS,
    ANCHOR_DIMENSIONS + f'\nconst BREACH_PAGE_SIZE = {PAGE_SIZE};',
    1,
)
source = source.replace(
    ANCHOR_DIMENSION_STATE,
    ANCHOR_DIMENSION_STATE + '\n  const [breachPage, setBreachPage] = useState(1);',
    1,
)

PAGINATION_STATE = '''  const topBreaches = useMemo(() => Array.isArray(data?.topBreaches) ? data.topBreaches : [], [data]);
  const breachPageCount = Math.max(1, Math.ceil(topBreaches.length / BREACH_PAGE_SIZE));
  const safeBreachPage = Math.min(Math.max(1, breachPage), breachPageCount);
  const pagedBreaches = useMemo(() => {
    const start = (safeBreachPage - 1) * BREACH_PAGE_SIZE;
    return topBreaches.slice(start, start + BREACH_PAGE_SIZE);
  }, [topBreaches, safeBreachPage]);

  useEffect(() => {
    setBreachPage((current) => Math.min(Math.max(1, current), breachPageCount));
  }, [breachPageCount]);'''
source = source.replace(ANCHOR_ROWS, ANCHOR_ROWS + "\n" + PAGINATION_STATE, 1)

source = source.replace(
    ANCHOR_BREACH_CARD,
    '            <div data-sla-breach-pagination="v1" className="rounded-2xl border border-app bg-app-card">\n              <div className="flex items-center justify-between border-b border-app p-4">\n                <div>\n                  <h2 className="font-black text-app">{ar ? "أقدم الاختراقات النشطة" : "Breach Aging"}</h2>',
    1,
)
source = source.replace(ANCHOR_MAP, '                {pagedBreaches.map((item) => (', 1)
source = source.replace(ANCHOR_EMPTY, '                {!topBreaches.length && (', 1)

PAGINATION_FOOTER = '''                )}
              </div>
              {topBreaches.length > BREACH_PAGE_SIZE && (
                <div className="flex flex-col gap-3 border-t border-app px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
                  <p className="text-xs font-bold text-muted">
                    {ar
                      ? `عرض ${(safeBreachPage - 1) * BREACH_PAGE_SIZE + 1}–${Math.min(safeBreachPage * BREACH_PAGE_SIZE, topBreaches.length)} من ${topBreaches.length}`
                      : `Showing ${(safeBreachPage - 1) * BREACH_PAGE_SIZE + 1}–${Math.min(safeBreachPage * BREACH_PAGE_SIZE, topBreaches.length)} of ${topBreaches.length}`}
                  </p>
                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      disabled={safeBreachPage <= 1}
                      onClick={() => setBreachPage((current) => Math.max(1, current - 1))}
                      className="rounded-xl border border-app px-3 py-2 text-xs font-black hover:bg-app-soft disabled:cursor-not-allowed disabled:opacity-40"
                    >
                      {ar ? "السابق" : "Previous"}
                    </button>
                    <span className="min-w-[92px] text-center text-xs font-black text-app">
                      {ar ? `صفحة ${safeBreachPage} من ${breachPageCount}` : `Page ${safeBreachPage} of ${breachPageCount}`}
                    </span>
                    <button
                      type="button"
                      disabled={safeBreachPage >= breachPageCount}
                      onClick={() => setBreachPage((current) => Math.min(breachPageCount, current + 1))}
                      className="rounded-xl border border-app px-3 py-2 text-xs font-black hover:bg-app-soft disabled:cursor-not-allowed disabled:opacity-40"
                    >
                      {ar ? "التالي" : "Next"}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </>'''
source = source.replace(ANCHOR_LIST_CLOSE, PAGINATION_FOOTER, 1)

for token in (
    'const BREACH_PAGE_SIZE = 6;',
    'const [breachPage, setBreachPage] = useState(1);',
    'const pagedBreaches = useMemo',
    'data-sla-breach-pagination="v1"',
    '{pagedBreaches.map((item) => (',
    'Page ${safeBreachPage} of ${breachPageCount}',
    'Showing ${(safeBreachPage - 1) * BREACH_PAGE_SIZE + 1}',
):
    if token not in source:
        fail(f"transformed source missing marker: {token}")

# Strict logic-preservation anchors.
for token in (
    'request("/api/sla/dashboard")',
    'window.setInterval(() => load({ quiet: true }), 60_000)',
    'const [dimension, setDimension] = useState("departments")',
    'data?.drilldowns?.[dimension] || []',
    'href="/sla-inbox"',
):
    if token not in source:
        fail(f"SLA logic anchor missing after transform: {token}")

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
    b'data-sla-breach-pagination',
    b'v1',
    b'Previous',
    b'Next',
    b'Breach Aging',
):
    if tree_count(DIST, marker) < 1:
        fail(f"built output missing pagination marker: {marker.decode(errors='ignore')}", original)

for path in PRESERVE_FILES:
    if sha256(path) != preserve_before[str(path)]:
        fail(f"out-of-scope file changed: {path}", original)

# Safe live deployment; no service restart and no Git operation in /var/www/TOS.
ts = int(time.time())
candidate = LIVE_PARENT / f"build.sla-center-breach-pagination-v1-candidate-{ts}"
backup = LIVE_PARENT / f"build.sla-center-breach-pagination-v1-backup-{ts}"
failed_live = LIVE_PARENT / f"build.sla-center-breach-pagination-v1-failed-{ts}"
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
print("SLA_CENTER_BREACH_PAGINATION_V1_RUNTIME=YES")
print("SLA_CENTER_BREACH_PAGE_SIZE=6")
print("SLA_CENTER_BREACH_PAGINATION=CLIENT_SIDE")
print("SLA_CENTER_BREACH_PREVIOUS_NEXT=YES")
print("SLA_CENTER_BREACH_PAGE_INDICATOR=YES")
print("SLA_CENTER_BREACH_RANGE_INDICATOR=YES")
print("SLA_CENTER_DRILLDOWN_CHANGED=NO")
print("SLA_CENTER_KPIS_CHANGED=NO")
print("SLA_CENTER_API_CHANGED=NO")
print("SLA_CENTER_POLLING_CHANGED=NO")
print("SLA_CENTER_DATA_CALCULATIONS_CHANGED=NO")
print("SLA_INBOX_CHANGED=NO")
print("RAMZY_CHANGED=NO")
print("TCS_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print(f"SLA_CENTER_PAGE_SHA256={sha256(PAGE)}")
print(f"LIVE_BACKUP={backup}")
print("STATUS=READY")
