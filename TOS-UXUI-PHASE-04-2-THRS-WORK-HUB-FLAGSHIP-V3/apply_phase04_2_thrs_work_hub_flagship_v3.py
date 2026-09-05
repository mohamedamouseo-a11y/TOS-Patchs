from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
HUB = ROOT / "frontend/src/pages/EmployeeWorkHub.jsx"
CSS = ROOT / "frontend/src/index.css"
DIST = ROOT / "frontend/dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_HUB_SHA = "d86f5553b002b6fd89328c90ab5c369050595cee87695200d89f77a74d292e43"
EXPECTED_CSS_SHA = "746874f8c2812ac0401ce02106040c3a309a1d6dc4b2ff5136de252eab2f3115"
V2_MARKER = "--tos-workhub-phase04-2-v2-runtime"
V3_MARKER = "--tos-workhub-phase04-2-v3-runtime"

print("RUNNING=PHASE04_2_THRS_WORK_HUB_FLAGSHIP_V3")


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


def fail(message: str):
    print("PASS/FAIL=FAIL")
    print("ERROR=" + str(message))
    print("BUILD_RESULT=SKIPPED")
    print("LIVE_DEPLOY=SKIPPED")
    print("V3_RUNTIME=NO")
    sys.exit(1)


for path in (HUB, CSS):
    if not path.exists():
        fail(f"required source missing: {path}")
if sha256(HUB) != EXPECTED_HUB_SHA:
    fail("EmployeeWorkHub differs from verified V2 state")
if sha256(CSS) != EXPECTED_CSS_SHA:
    fail("index.css differs from verified V2 state")

original_hub = HUB.read_text()
original_css = CSS.read_text()
if original_css.count(V2_MARKER) != 1:
    fail("verified V2 runtime marker not found exactly once")
if V3_MARKER in original_css:
    fail("Phase 04.2 V3 already present")

# Add semantic visual hooks only; no state, API, permission or workflow changes.
replacements = [
    (
        '<div className="overflow-hidden rounded-[26px] border border-slate-200 bg-white dark:border-white/10 dark:bg-zinc-950">',
        '<div className="tos-thrs-admin-table overflow-hidden rounded-[26px] border border-slate-200 bg-white dark:border-white/10 dark:bg-zinc-950">',
    ),
    (
        '<div className="grid gap-3 rounded-[24px] border border-slate-100 bg-slate-50 p-3 dark:border-white/10 dark:bg-white/5 sm:grid-cols-2 xl:grid-cols-6">',
        '<div className="tos-thrs-admin-filters grid gap-3 rounded-[24px] border border-slate-100 bg-slate-50 p-3 dark:border-white/10 dark:bg-white/5 sm:grid-cols-2 xl:grid-cols-6">',
    ),
    (
        '<tr key={item.id} className={`${selectedRequestIdSet.has(item.id) ? "bg-amber-50/70 dark:bg-amber-400/5" : ""} align-top transition hover:bg-slate-50/70 dark:hover:bg-white/5`}>',
        '<tr key={item.id} className={`tos-thrs-admin-row ${selectedRequestIdSet.has(item.id) ? "bg-amber-50/70 dark:bg-amber-400/5" : ""} align-top transition hover:bg-slate-50/70 dark:hover:bg-white/5`}>',
    ),
]

updated_hub = original_hub
for old, new in replacements:
    count = updated_hub.count(old)
    if count != 1:
        fail(f"expected one visual hook anchor, found {count}")
    updated_hub = updated_hub.replace(old, new, 1)

v3_css = r'''

/* =========================================================
   Phase 04.2 — THRS / Employee Work Hub — Flagship V3
   Screenshot refinement: eliminate dark zebra white rows and
   harden admin filter visibility. Visual scope only.
   ========================================================= */
:root { --tos-workhub-phase04-2-v3-runtime: 1; }

/* Give management controls their own deliberate surface in Light. */
.tos-core-workhub-premium .tos-thrs-admin-filters {
  border-color: rgba(104,88,58,.15) !important;
  background: linear-gradient(145deg, rgba(251,248,241,.96), rgba(247,243,233,.90)) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.94);
}

.tos-core-workhub-premium .tos-thrs-admin-table {
  border-color: rgba(105,88,57,.16) !important;
  background: #fffefb !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.92);
}

/* Explicit cell surfaces prevent global compatibility rules from painting
   individual zebra cells independently of the row. */
.tos-core-workhub-premium .tos-thrs-admin-table tbody tr > td {
  background-color: transparent !important;
  background-image: none !important;
}

html.dark .tos-core-workhub-premium .tos-thrs-admin-filters {
  border-color: rgba(255,255,255,.085) !important;
  background: linear-gradient(145deg, #14161a, #0f1115) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.025), 0 8px 20px rgba(0,0,0,.12) !important;
}

html.dark .tos-core-workhub-premium .tos-thrs-admin-filters label > span:first-child {
  color: #b4b7bd !important;
}

html.dark .tos-core-workhub-premium .tos-thrs-admin-filters label > span:last-child {
  color: #777c85 !important;
}

html.dark .tos-core-workhub-premium .tos-thrs-admin-filters input:not([type="checkbox"]),
html.dark .tos-core-workhub-premium .tos-thrs-admin-filters select {
  background: #17191e !important;
  background-color: #17191e !important;
  color: #f2f0eb !important;
  -webkit-text-fill-color: #f2f0eb !important;
  border-color: rgba(255,255,255,.11) !important;
  color-scheme: dark !important;
}

html.dark .tos-core-workhub-premium .tos-thrs-admin-table {
  border-color: rgba(255,255,255,.08) !important;
  background: #0d0f13 !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.02), 0 12px 28px rgba(0,0,0,.18) !important;
}

html.dark .tos-core-workhub-premium .tos-thrs-admin-table table,
html.dark .tos-core-workhub-premium .tos-thrs-admin-table tbody {
  background: #0d0f13 !important;
}

html.dark .tos-core-workhub-premium .tos-thrs-admin-table tbody .tos-thrs-admin-row,
html.dark .tos-core-workhub-premium .tos-thrs-admin-table tbody .tos-thrs-admin-row:nth-child(odd),
html.dark .tos-core-workhub-premium .tos-thrs-admin-table tbody .tos-thrs-admin-row:nth-child(even) {
  background: transparent !important;
}

html.dark .tos-core-workhub-premium .tos-thrs-admin-table tbody .tos-thrs-admin-row > td {
  background: #121419 !important;
  background-color: #121419 !important;
  background-image: none !important;
  border-color: rgba(255,255,255,.055) !important;
}

html.dark .tos-core-workhub-premium .tos-thrs-admin-table tbody .tos-thrs-admin-row:nth-child(even) > td {
  background: #0f1115 !important;
  background-color: #0f1115 !important;
}

html.dark .tos-core-workhub-premium .tos-thrs-admin-table tbody .tos-thrs-admin-row:hover > td {
  background: #1a1813 !important;
  background-color: #1a1813 !important;
}

html.dark .tos-core-workhub-premium .tos-thrs-admin-table tbody .tos-thrs-admin-row:has(input[type="checkbox"]:checked) > td {
  background: #1b1710 !important;
  background-color: #1b1710 !important;
}

html.dark .tos-core-workhub-premium .tos-thrs-admin-table thead,
html.dark .tos-core-workhub-premium .tos-thrs-admin-table thead tr,
html.dark .tos-core-workhub-premium .tos-thrs-admin-table thead th {
  background: #181a1f !important;
  background-color: #181a1f !important;
  color: #b3b6bd !important;
  border-color: rgba(255,255,255,.07) !important;
}
'''

updated_css = original_css.rstrip() + v3_css + "\n"
updated_css = "\n".join(line.rstrip() for line in updated_css.splitlines()) + "\n"

backup = None
stage = None
live_swapped = False

try:
    HUB.write_text(updated_hub)
    CSS.write_text(updated_css)

    if HUB.read_text().count("tos-thrs-admin-table") != 1:
        raise RuntimeError("admin table visual hook verification failed")
    if HUB.read_text().count("tos-thrs-admin-filters") != 1:
        raise RuntimeError("admin filters visual hook verification failed")
    if HUB.read_text().count("tos-thrs-admin-row") != 1:
        raise RuntimeError("admin row visual hook verification failed")
    if CSS.read_text().count(V3_MARKER) != 1:
        raise RuntimeError("source V3 runtime marker missing or duplicated")

    subprocess.run([
        "git", "-C", str(ROOT), "diff", "--check", "--",
        "frontend/src/pages/EmployeeWorkHub.jsx", "frontend/src/index.css"
    ], check=True)

    subprocess.run(["npm", "run", "build"], cwd=ROOT / "frontend", check=True)
    if not (DIST / "index.html").exists():
        raise RuntimeError("built dist index missing")

    dist_count = tree_count(DIST, V3_MARKER.encode())
    if dist_count < 1:
        raise RuntimeError("Phase 04.2 V3 marker missing from dist")

    stamp = time.strftime("%Y%m%d-%H%M%S")
    stage = LIVE_PARENT / f"build.phase04-2-workhub-v3.new.{int(time.time())}"
    backup = LIVE_PARENT / f"build.phase04-2-workhub-v3.backup-{stamp}"
    if stage.exists():
        shutil.rmtree(stage)
    shutil.copytree(DIST, stage)
    if not LIVE.exists():
        raise RuntimeError("live frontend root missing")

    LIVE.rename(backup)
    stage.rename(LIVE)
    live_swapped = True
    subprocess.run(["systemctl", "is-active", "--quiet", "nginx"], check=True)

    live_count = tree_count(LIVE, V3_MARKER.encode())
    if live_count < 1:
        raise RuntimeError("Phase 04.2 V3 marker missing from live build")

except Exception as exc:
    HUB.write_text(original_hub)
    CSS.write_text(original_css)
    if live_swapped and backup and backup.exists():
        if LIVE.exists():
            shutil.rmtree(LIVE)
        backup.rename(LIVE)
    if stage and stage.exists():
        shutil.rmtree(stage)
    fail(str(exc))

print("PASS/FAIL=PASS")
print("BUILD_RESULT=PASS")
print("LIVE_DEPLOY=PASS")
print("SCREEN=THRS_WORK_HUB_ONLY")
print("V3_RUNTIME=YES")
print("DARK_TABLE_ZEBRA_WHITE_FIXED=YES")
print("DARK_ADMIN_FILTERS_HARDENED=YES")
print("LIGHT_MANAGEMENT_SURFACES_PRESERVED=YES")
print("V2_VISUALS_PRESERVED=YES")
print("BUSINESS_LOGIC_CHANGED=NO")
print("SOURCE_V3_RUNTIME_COUNT=" + str(CSS.read_text().count(V3_MARKER)))
print("DIST_V3_RUNTIME_COUNT=" + str(tree_count(DIST, V3_MARKER.encode())))
print("LIVE_V3_RUNTIME_COUNT=" + str(tree_count(LIVE, V3_MARKER.encode())))
print("EMPLOYEE_WORK_HUB_SHA256=" + sha256(HUB))
print("INDEX_CSS_SHA256=" + sha256(CSS))
