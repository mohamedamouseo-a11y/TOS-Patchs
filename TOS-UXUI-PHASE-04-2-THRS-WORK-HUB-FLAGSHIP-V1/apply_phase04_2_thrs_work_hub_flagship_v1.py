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

EXPECTED_HUB_GIT_BLOB = "9d6d7423165ec43022676aac771780a087a64cab"
EXPECTED_CSS_GIT_BLOB = "e6a197fd88e618a8b36c1fc57bd536eee4499b41"
MARKER = "--tos-workhub-phase04-2-v1-runtime"

print("RUNNING=PHASE04_2_THRS_WORK_HUB_FLAGSHIP_V1")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob(path: Path) -> str:
    rel = path.relative_to(ROOT)
    return subprocess.check_output(["git", "-C", str(ROOT), "hash-object", str(rel)], text=True).strip()


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
    print("BUILD_RESULT=SKIPPED")
    print("LIVE_DEPLOY=SKIPPED")
    print("V1_RUNTIME=NO")
    print(f"ERROR={message}")
    sys.exit(1)


for path in (HUB, CSS):
    if not path.exists():
        fail(f"required source missing: {path}")

if git_blob(HUB) != EXPECTED_HUB_GIT_BLOB:
    fail("EmployeeWorkHub differs from the latest approved TOS source")
if git_blob(CSS) != EXPECTED_CSS_GIT_BLOB:
    fail("index.css differs from the latest approved TOS source")
if "tos-core-workhub-premium" not in HUB.read_text():
    fail("Work Hub premium root class missing")

original_css = CSS.read_text()
if MARKER in original_css:
    fail("Phase 04.2 V1 already present")

v1_css = r'''

/* =========================================================
   Phase 04.2 — THRS / Employee Work Hub — Flagship V1
   Scope: visual hierarchy, premium surfaces, typography,
   controls, tables and Light/Dark consistency only.
   No business logic or workflow changes.
   ========================================================= */
:root { --tos-workhub-phase04-2-v1-runtime: 1; }

.tos-core-workhub-premium {
  --wh-gold: #c49a45;
  --wh-gold-soft: rgba(196,154,69,.14);
  --wh-border: rgba(120,104,76,.15);
  --wh-text: #1d1c18;
  --wh-muted: #78746b;
  display: grid;
  gap: 1rem !important;
  padding-bottom: 1.15rem;
}

.tos-core-workhub-premium > section.grid.gap-5 {
  gap: 1rem !important;
}

.tos-core-workhub-premium > section.grid.gap-5 > div,
.tos-core-workhub-premium > section#thrs-requests-management,
.tos-core-workhub-premium > section.overflow-hidden {
  position: relative;
  isolation: isolate;
  overflow: hidden;
  border-color: var(--wh-border) !important;
  background:
    radial-gradient(circle at 8% 0%, rgba(210,181,119,.10), transparent 25%),
    linear-gradient(145deg, rgba(255,255,255,.99), rgba(250,248,243,.97)) !important;
  box-shadow:
    0 18px 50px rgba(49,39,22,.075),
    0 2px 8px rgba(49,39,22,.035),
    inset 0 1px 0 rgba(255,255,255,.96) !important;
}

.tos-core-workhub-premium > section.grid.gap-5 > div::before,
.tos-core-workhub-premium > section#thrs-requests-management::before,
.tos-core-workhub-premium > section.overflow-hidden::before {
  content: "";
  position: absolute;
  inset-inline: 18px;
  top: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(196,154,69,.72), transparent);
  pointer-events: none;
  z-index: 2;
}

.tos-core-workhub-premium h2 {
  color: var(--wh-text) !important;
  letter-spacing: -.025em;
}

.tos-core-workhub-premium h3 {
  letter-spacing: -.018em;
}

.tos-core-workhub-premium > section.grid.gap-5 > div > div:first-child h2,
.tos-core-workhub-premium > section#thrs-requests-management > div:first-child h2,
.tos-core-workhub-premium > section.overflow-hidden > div:first-child h2 {
  font-size: 1.16rem !important;
  line-height: 1.35 !important;
}

.tos-core-workhub-premium .xl\:grid-cols-6 > div,
.tos-core-workhub-premium .md\:grid-cols-5 > div {
  border-color: rgba(119,106,79,.13) !important;
  background: linear-gradient(145deg, rgba(255,255,255,.98), rgba(249,247,241,.90)) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.9), 0 6px 16px rgba(44,36,23,.035);
}

.tos-core-workhub-premium input:not([type="checkbox"]):not([type="radio"]):not([type="file"]),
.tos-core-workhub-premium select,
.tos-core-workhub-premium textarea {
  border-color: rgba(112,101,79,.18) !important;
  background-color: rgba(255,255,255,.96) !important;
  color: #292720 !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.88);
}

.tos-core-workhub-premium input:not([type="checkbox"]):not([type="radio"]):not([type="file"]):focus,
.tos-core-workhub-premium select:focus,
.tos-core-workhub-premium textarea:focus {
  border-color: rgba(196,154,69,.62) !important;
  box-shadow: 0 0 0 3px rgba(196,154,69,.105) !important;
  outline: none !important;
}

.tos-core-workhub-premium select option {
  background: #fffefb;
  color: #27251f;
}

.tos-core-workhub-premium table {
  border-collapse: separate;
  border-spacing: 0;
}

.tos-core-workhub-premium table thead {
  background: linear-gradient(180deg, #f8f6f0, #f3f0e8) !important;
}

.tos-core-workhub-premium table thead th {
  color: #716c61 !important;
  letter-spacing: .025em;
}

.tos-core-workhub-premium table tbody tr {
  transition: background-color .16s ease, box-shadow .16s ease;
}

.tos-core-workhub-premium table tbody tr:hover {
  background: rgba(196,154,69,.045) !important;
}

.tos-core-workhub-premium button {
  -webkit-tap-highlight-color: transparent;
}

.tos-core-workhub-premium button:focus-visible {
  outline: 2px solid rgba(196,154,69,.58);
  outline-offset: 2px;
}

.tos-core-workhub-premium [class*="bg-slate-50"] {
  border-color: rgba(120,107,82,.11);
}

html.dark .tos-core-workhub-premium {
  --wh-gold: #d5b56a;
  --wh-gold-soft: rgba(213,181,106,.12);
  --wh-border: rgba(255,255,255,.085);
  --wh-text: #f5f3ee;
  --wh-muted: #a5a7ad;
}

html.dark .tos-core-workhub-premium > section.grid.gap-5 > div,
html.dark .tos-core-workhub-premium > section#thrs-requests-management,
html.dark .tos-core-workhub-premium > section.overflow-hidden {
  border-color: rgba(255,255,255,.08) !important;
  background:
    radial-gradient(circle at 8% 0%, rgba(213,181,106,.055), transparent 26%),
    linear-gradient(150deg, #111318 0%, #0c0e12 62%, #0a0c0f 100%) !important;
  box-shadow:
    0 22px 56px rgba(0,0,0,.34),
    inset 0 1px 0 rgba(255,255,255,.025) !important;
}

html.dark .tos-core-workhub-premium h2 {
  color: #f7f5ef !important;
}

html.dark .tos-core-workhub-premium .xl\:grid-cols-6 > div,
html.dark .tos-core-workhub-premium .md\:grid-cols-5 > div {
  border-color: rgba(255,255,255,.07) !important;
  background: linear-gradient(145deg, rgba(25,27,32,.96), rgba(15,17,21,.96)) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.025), 0 8px 20px rgba(0,0,0,.16);
}

html.dark .tos-core-workhub-premium input:not([type="checkbox"]):not([type="radio"]):not([type="file"]),
html.dark .tos-core-workhub-premium select,
html.dark .tos-core-workhub-premium textarea {
  border-color: rgba(255,255,255,.10) !important;
  background-color: #15171b !important;
  color: #f2f0eb !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.02);
}

html.dark .tos-core-workhub-premium input:not([type="checkbox"]):not([type="radio"]):not([type="file"]):focus,
html.dark .tos-core-workhub-premium select:focus,
html.dark .tos-core-workhub-premium textarea:focus {
  border-color: rgba(213,181,106,.56) !important;
  box-shadow: 0 0 0 3px rgba(213,181,106,.10) !important;
}

html.dark .tos-core-workhub-premium select option {
  background: #15171b;
  color: #f2f0eb;
}

html.dark .tos-core-workhub-premium table thead {
  background: linear-gradient(180deg, #15171b, #111318) !important;
}

html.dark .tos-core-workhub-premium table thead th {
  color: #a8abb2 !important;
}

html.dark .tos-core-workhub-premium table tbody tr:hover {
  background: rgba(213,181,106,.045) !important;
}

html.dark .tos-core-workhub-premium [class*="bg-slate-50"] {
  border-color: rgba(255,255,255,.065);
}

@media (max-width: 1023px) {
  .tos-core-workhub-premium {
    gap: .8rem !important;
  }
  .tos-core-workhub-premium > section.grid.gap-5 {
    gap: .8rem !important;
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

updated_css = original_css.rstrip() + "\n" + v1_css.strip() + "\n"
backup = None
stage = None
live_swapped = False

try:
    CSS.write_text(updated_css)
    if CSS.read_text().count(MARKER) != 1:
        raise RuntimeError("source V1 marker missing or duplicated")
    if git_blob(HUB) != EXPECTED_HUB_GIT_BLOB:
        raise RuntimeError("EmployeeWorkHub changed unexpectedly")

    subprocess.run([
        "git", "-C", str(ROOT), "diff", "--check", "--", "frontend/src/index.css"
    ], check=True)

    subprocess.run(["npm", "run", "build"], cwd=ROOT / "frontend", check=True)
    if not (DIST / "index.html").exists():
        raise RuntimeError("built dist index missing")

    dist_count = tree_count(DIST, MARKER.encode())
    if dist_count < 1:
        raise RuntimeError("Phase 04.2 V1 marker missing from dist")

    stamp = time.strftime("%Y%m%d-%H%M%S")
    stage = LIVE_PARENT / f"build.phase04-2-workhub-v1.new.{int(time.time())}"
    backup = LIVE_PARENT / f"build.phase04-2-workhub-v1.backup-{stamp}"
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

    live_count = tree_count(LIVE, MARKER.encode())
    if live_count < 1:
        raise RuntimeError("Phase 04.2 V1 marker missing from live build")

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
print("V1_RUNTIME=YES")
print("LIGHT_FLAGSHIP_SURFACES=YES")
print("DARK_FLAGSHIP_SURFACES=YES")
print("FORM_CONTROLS_REFINED=YES")
print("REQUEST_TABLE_REFINED=YES")
print("BUSINESS_LOGIC_CHANGED=NO")
print("SOURCE_V1_RUNTIME_COUNT=" + str(CSS.read_text().count(MARKER)))
print("DIST_V1_RUNTIME_COUNT=" + str(tree_count(DIST, MARKER.encode())))
print("LIVE_V1_RUNTIME_COUNT=" + str(tree_count(LIVE, MARKER.encode())))
print("EMPLOYEE_WORK_HUB_SHA256=" + sha256(HUB))
print("INDEX_CSS_SHA256=" + sha256(CSS))
