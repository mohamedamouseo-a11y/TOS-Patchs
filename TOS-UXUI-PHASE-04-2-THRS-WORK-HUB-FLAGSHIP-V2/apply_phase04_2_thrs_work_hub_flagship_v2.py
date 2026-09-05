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
EXPECTED_CSS_SHA = "9134e3bccfa5240aa86f3477f1c84d0ce7244edf9f922ce61725cc5a616442a5"
V1_MARKER = "--tos-workhub-phase04-2-v1-runtime"
V2_MARKER = "--tos-workhub-phase04-2-v2-runtime"
V1_SECTION_MARKER = "Phase 04.2 — THRS / Employee Work Hub — Flagship V1"

print("RUNNING=PHASE04_2_THRS_WORK_HUB_FLAGSHIP_V2")


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
    print("BUILD_RESULT=SKIPPED")
    print("LIVE_DEPLOY=SKIPPED")
    print("V2_RUNTIME=NO")
    sys.exit(1)


for path in (HUB, CSS):
    if not path.exists():
        fail(f"required source missing: {path}")
if sha256(HUB) != EXPECTED_HUB_SHA:
    fail("EmployeeWorkHub differs from verified Phase 04.2 V1 state")
if sha256(CSS) != EXPECTED_CSS_SHA:
    fail("index.css differs from verified Phase 04.2 V1 state")

original_css = CSS.read_text()
if original_css.count(V1_MARKER) != 1:
    fail("verified V1 runtime marker not found exactly once")
if V2_MARKER in original_css:
    fail("Phase 04.2 V2 already present")

section_anchor = "/* =========================================================\n   Phase 04.2 — THRS / Employee Work Hub — Flagship V1"
section_index = original_css.find(section_anchor)
if section_index < 0:
    fail("V1 consolidated section anchor not found")

v2_css = r'''
/* =========================================================
   Phase 04.2 — THRS / Employee Work Hub — Flagship V2
   Consolidates V1 and refines visual hierarchy after Light/Dark review.
   Scope: THRS Work Hub only. No business logic changes.
   ========================================================= */
:root {
  --tos-workhub-phase04-2-v1-runtime: 1;
  --tos-workhub-phase04-2-v2-runtime: 1;
}

.tos-core-workhub-premium {
  --wh-gold: #b9872e;
  --wh-gold-hi: #d5b56a;
  --wh-gold-soft: rgba(185,135,46,.11);
  --wh-border: rgba(98,83,57,.18);
  --wh-border-strong: rgba(185,135,46,.28);
  --wh-text: #1b1a17;
  --wh-muted: #6f6b62;
  display: grid;
  gap: .9rem !important;
  padding-bottom: 1.15rem;
}

.tos-core-workhub-premium > section.grid.gap-5 {
  gap: .9rem !important;
}

.tos-core-workhub-premium > section.grid.gap-5 > div,
.tos-core-workhub-premium > section#thrs-requests-management,
.tos-core-workhub-premium > section.overflow-hidden {
  position: relative;
  isolation: isolate;
  overflow: hidden;
  border-color: var(--wh-border) !important;
  background:
    radial-gradient(circle at 7% 0%, rgba(214,184,120,.11), transparent 24%),
    linear-gradient(145deg, #fffefa 0%, #faf7f0 48%, #f7f4ec 100%) !important;
  box-shadow:
    0 18px 48px rgba(55,44,25,.085),
    0 3px 10px rgba(55,44,25,.035),
    inset 0 1px 0 rgba(255,255,255,.98) !important;
}

.tos-core-workhub-premium > section.grid.gap-5 > div::before,
.tos-core-workhub-premium > section#thrs-requests-management::before,
.tos-core-workhub-premium > section.overflow-hidden::before {
  content: "";
  position: absolute;
  inset-inline: 16px;
  top: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(185,135,46,.72), transparent);
  pointer-events: none;
  z-index: 2;
}

.tos-core-workhub-premium h2 {
  color: var(--wh-text) !important;
  letter-spacing: -.028em;
}

.tos-core-workhub-premium h3 {
  letter-spacing: -.02em;
}

.tos-core-workhub-premium > section.grid.gap-5 > div > div:first-child h2,
.tos-core-workhub-premium > section#thrs-requests-management > div:first-child h2,
.tos-core-workhub-premium > section.overflow-hidden > div:first-child h2 {
  font-size: 1.22rem !important;
  line-height: 1.28 !important;
}

/* Executive metric surfaces */
.tos-core-workhub-premium .xl\:grid-cols-6 > div,
.tos-core-workhub-premium .md\:grid-cols-5 > div,
.tos-core-workhub-premium .grid.w-full.max-w-2xl.grid-cols-3 > div {
  border-color: rgba(102,88,61,.15) !important;
  background: linear-gradient(150deg, rgba(255,255,255,.99), rgba(248,244,235,.94)) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.96), 0 7px 18px rgba(50,39,20,.045) !important;
}

/* Forms: stronger legibility, same dimensions/workflow */
.tos-core-workhub-premium input:not([type="checkbox"]):not([type="radio"]):not([type="file"]),
.tos-core-workhub-premium select,
.tos-core-workhub-premium textarea {
  border-color: rgba(98,86,65,.22) !important;
  background-color: rgba(255,255,255,.985) !important;
  color: #24221d !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.96), 0 1px 0 rgba(73,58,31,.02);
}

.tos-core-workhub-premium input:not([type="checkbox"]):not([type="radio"]):not([type="file"]):focus,
.tos-core-workhub-premium select:focus,
.tos-core-workhub-premium textarea:focus {
  border-color: rgba(185,135,46,.68) !important;
  box-shadow: 0 0 0 3px rgba(185,135,46,.105) !important;
  outline: none !important;
}

.tos-core-workhub-premium select option {
  background: #fffefb;
  color: #25231e;
}

/* Request management table */
.tos-core-workhub-premium table {
  border-collapse: separate;
  border-spacing: 0;
}

.tos-core-workhub-premium table thead,
.tos-core-workhub-premium table thead tr,
.tos-core-workhub-premium table thead th {
  background: linear-gradient(180deg, #f7f3e9, #f0eadc) !important;
}

.tos-core-workhub-premium table thead th {
  color: #625d52 !important;
  letter-spacing: .035em;
  border-bottom-color: rgba(105,89,58,.14) !important;
}

.tos-core-workhub-premium table tbody tr {
  transition: background-color .16s ease, box-shadow .16s ease;
}

.tos-core-workhub-premium table tbody tr:nth-child(even) {
  background: rgba(248,245,238,.54);
}

.tos-core-workhub-premium table tbody tr:hover {
  background: rgba(185,135,46,.06) !important;
}

.tos-core-workhub-premium table tbody td {
  border-bottom-color: rgba(100,86,60,.08) !important;
}

/* Composer tabs and workflow strip */
.tos-core-workhub-premium > section.grid.gap-5 > div:nth-child(2) .grid.grid-cols-2 > button {
  border: 1px solid rgba(103,89,64,.13);
}

.tos-core-workhub-premium > section.grid.gap-5 > div:nth-child(2) .grid.grid-cols-2 > button[class*="bg-black"] {
  background: linear-gradient(135deg, #191815, #0c0d0f) !important;
  box-shadow: 0 6px 16px rgba(30,24,14,.16) !important;
}

/* Focus treatment */
.tos-core-workhub-premium button {
  -webkit-tap-highlight-color: transparent;
}

.tos-core-workhub-premium button:focus-visible {
  outline: 2px solid rgba(185,135,46,.62);
  outline-offset: 2px;
}

.tos-core-workhub-premium [class*="bg-slate-50"] {
  border-color: rgba(110,94,67,.12);
}

/* ============================ DARK ============================ */
html.dark .tos-core-workhub-premium {
  --wh-gold: #d3ac55;
  --wh-gold-hi: #efd58d;
  --wh-gold-soft: rgba(211,172,85,.12);
  --wh-border: rgba(255,255,255,.085);
  --wh-border-strong: rgba(211,172,85,.24);
  --wh-text: #f5f3ee;
  --wh-muted: #a8abb1;
}

html.dark .tos-core-workhub-premium > section.grid.gap-5 > div,
html.dark .tos-core-workhub-premium > section#thrs-requests-management,
html.dark .tos-core-workhub-premium > section.overflow-hidden {
  border-color: rgba(255,255,255,.085) !important;
  background:
    radial-gradient(circle at 7% 0%, rgba(211,172,85,.055), transparent 24%),
    linear-gradient(150deg, #121419 0%, #0d0f13 58%, #090b0e 100%) !important;
  box-shadow:
    0 22px 58px rgba(0,0,0,.36),
    inset 0 1px 0 rgba(255,255,255,.025) !important;
}

html.dark .tos-core-workhub-premium h2,
html.dark .tos-core-workhub-premium h3 {
  color: #f7f4ed !important;
}

html.dark .tos-core-workhub-premium .xl\:grid-cols-6 > div,
html.dark .tos-core-workhub-premium .md\:grid-cols-5 > div,
html.dark .tos-core-workhub-premium .grid.w-full.max-w-2xl.grid-cols-3 > div {
  border-color: rgba(255,255,255,.07) !important;
  background: linear-gradient(150deg, #191b20 0%, #111318 100%) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.025), 0 9px 22px rgba(0,0,0,.18) !important;
}

html.dark .tos-core-workhub-premium input:not([type="checkbox"]):not([type="radio"]):not([type="file"]),
html.dark .tos-core-workhub-premium select,
html.dark .tos-core-workhub-premium textarea {
  border-color: rgba(255,255,255,.11) !important;
  background-color: #15171b !important;
  color: #f3f1ec !important;
  -webkit-text-fill-color: #f3f1ec;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.02) !important;
  color-scheme: dark;
}

html.dark .tos-core-workhub-premium input:not([type="checkbox"]):not([type="radio"]):not([type="file"]):focus,
html.dark .tos-core-workhub-premium select:focus,
html.dark .tos-core-workhub-premium textarea:focus {
  border-color: rgba(211,172,85,.60) !important;
  box-shadow: 0 0 0 3px rgba(211,172,85,.10) !important;
}

html.dark .tos-core-workhub-premium select option {
  background: #15171b;
  color: #f2f0eb;
}

/* Remove bright table strip in Dark */
html.dark .tos-core-workhub-premium table thead,
html.dark .tos-core-workhub-premium table thead tr,
html.dark .tos-core-workhub-premium table thead th {
  background: #111318 !important;
  color: #aeb1b8 !important;
  border-color: rgba(255,255,255,.075) !important;
}

html.dark .tos-core-workhub-premium table tbody tr,
html.dark .tos-core-workhub-premium table tbody tr:nth-child(even) {
  background: rgba(17,19,24,.78) !important;
}

html.dark .tos-core-workhub-premium table tbody tr:hover {
  background: rgba(211,172,85,.055) !important;
}

html.dark .tos-core-workhub-premium table tbody td {
  border-color: rgba(255,255,255,.055) !important;
}

/* Remove stark white artifacts from dark mode while keeping clear hierarchy */
html.dark .tos-core-workhub-premium [class*="dark:bg-white"][class*="dark:text-zinc-950"] {
  background: linear-gradient(135deg, #e7cf91, #cda959) !important;
  color: #17150f !important;
  border-color: rgba(239,213,141,.44) !important;
  box-shadow: 0 7px 18px rgba(0,0,0,.20), inset 0 1px 0 rgba(255,255,255,.34) !important;
}

html.dark .tos-core-workhub-premium > section.grid.gap-5 > div:nth-child(2) .grid.grid-cols-2 > button:not([class*="bg-black"]) {
  background: #15171b !important;
  color: #aeb1b7 !important;
  border-color: rgba(255,255,255,.085) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.02) !important;
}

html.dark .tos-core-workhub-premium > section.grid.gap-5 > div:nth-child(2) .grid.grid-cols-2 > button[class*="bg-black"] {
  background: linear-gradient(135deg, #24211a, #121316) !important;
  color: #f5e7bc !important;
  border-color: rgba(211,172,85,.30) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.025), 0 8px 20px rgba(0,0,0,.24) !important;
}

/* Toolbar/icon buttons that remained bright in the request editor */
html.dark .tos-core-workhub-premium button[class*="bg-white"]:not([class*="dark:bg-white"]) {
  background: #191b20 !important;
  color: #d8d9dd !important;
  border-color: rgba(255,255,255,.10) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.02) !important;
}

html.dark .tos-core-workhub-premium button[class*="bg-white"]:not([class*="dark:bg-white"]):hover {
  background: #202329 !important;
  color: #ffffff !important;
}

/* Scope pills (All team / attendance tabs) should be champagne, not pure white */
html.dark .tos-core-workhub-premium button[class*="dark:bg-white"][class*="shadow"] {
  background: linear-gradient(135deg, #dfc57f, #bd9747) !important;
  color: #17150f !important;
}

html.dark .tos-core-workhub-premium [class*="bg-slate-50"] {
  border-color: rgba(255,255,255,.065);
}

@media (max-width: 1023px) {
  .tos-core-workhub-premium,
  .tos-core-workhub-premium > section.grid.gap-5 {
    gap: .78rem !important;
  }
}

@media (prefers-reduced-motion: reduce) {
  .tos-core-workhub-premium *,
  .tos-core-workhub-premium *::before,
  .tos-core-workhub-premium *::after {
    scroll-behavior: auto !important;
    transition-duration: .01ms !important;
    animation-duration: .01ms !important;
  }
}
'''

updated_css = original_css[:section_index].rstrip() + "\n\n" + v2_css.strip() + "\n"
updated_css = "\n".join(line.rstrip() for line in updated_css.splitlines()) + "\n"

backup = None
stage = None
live_swapped = False

try:
    CSS.write_text(updated_css)
    current = CSS.read_text()
    if current.count(V2_MARKER) != 1:
        raise RuntimeError("source V2 marker missing or duplicated")
    if current.count(V1_MARKER) != 1:
        raise RuntimeError("consolidated V1 compatibility marker missing or duplicated")
    if V1_SECTION_MARKER in current:
        raise RuntimeError("old V1 CSS block was not consolidated")
    if sha256(HUB) != EXPECTED_HUB_SHA:
        raise RuntimeError("EmployeeWorkHub changed unexpectedly")

    subprocess.run([
        "git", "-C", str(ROOT), "diff", "--check", "--", "frontend/src/index.css"
    ], check=True)

    subprocess.run(["npm", "run", "build"], cwd=ROOT / "frontend", check=True)
    if not (DIST / "index.html").exists():
        raise RuntimeError("built dist index missing")

    dist_count = tree_count(DIST, V2_MARKER.encode())
    if dist_count < 1:
        raise RuntimeError("Phase 04.2 V2 marker missing from dist")

    stamp = time.strftime("%Y%m%d-%H%M%S")
    stage = LIVE_PARENT / f"build.phase04-2-workhub-v2.new.{int(time.time())}"
    backup = LIVE_PARENT / f"build.phase04-2-workhub-v2.backup-{stamp}"
    if stage.exists():
        shutil.rmtree(stage)
    shutil.copytree(DIST, stage)
    if not (stage / "index.html").exists():
        raise RuntimeError("staged index missing")
    if not LIVE.exists():
        raise RuntimeError("live frontend root missing")

    LIVE.rename(backup)
    stage.rename(LIVE)
    live_swapped = True
    subprocess.run(["systemctl", "is-active", "--quiet", "nginx"], check=True)

    live_count = tree_count(LIVE, V2_MARKER.encode())
    if live_count < 1:
        raise RuntimeError("Phase 04.2 V2 marker missing from live build")

except Exception as exc:
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
print("V2_RUNTIME=YES")
print("V1_BLOCK_CONSOLIDATED=YES")
print("LIGHT_DEPTH_REFINED=YES")
print("DARK_WHITE_ARTIFACTS_REDUCED=YES")
print("DARK_TABLE_HEADER_FIXED=YES")
print("COMPOSER_TABS_REFINED=YES")
print("FORM_CONTROLS_REFINED=YES")
print("REQUEST_TABLE_REFINED=YES")
print("BUSINESS_LOGIC_CHANGED=NO")
print("SOURCE_V2_RUNTIME_COUNT=" + str(CSS.read_text().count(V2_MARKER)))
print("DIST_V2_RUNTIME_COUNT=" + str(tree_count(DIST, V2_MARKER.encode())))
print("LIVE_V2_RUNTIME_COUNT=" + str(tree_count(LIVE, V2_MARKER.encode())))
print("EMPLOYEE_WORK_HUB_SHA256=" + sha256(HUB))
print("INDEX_CSS_SHA256=" + sha256(CSS))
