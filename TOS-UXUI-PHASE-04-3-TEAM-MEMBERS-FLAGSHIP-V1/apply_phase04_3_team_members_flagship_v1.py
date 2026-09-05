from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
TEAM = ROOT / "frontend/src/pages/TeamPage.jsx"
CSS = ROOT / "frontend/src/index.css"
DIST = ROOT / "frontend/dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_TEAM_GIT_BLOB = "84e8ab7cfe4bf01246f39f295c2aebee9db647f9"
EXPECTED_CSS_GIT_BLOB = "2bb605b906eceda15ef799eb766224be6f0ddb85"
MARKER = "--tos-team-phase04-3-v1-runtime"

print("RUNNING=PHASE04_3_TEAM_MEMBERS_FLAGSHIP_V1")


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
    print("ERROR=" + str(message))
    print("BUILD_RESULT=SKIPPED")
    print("LIVE_DEPLOY=SKIPPED")
    print("V1_RUNTIME=NO")
    sys.exit(1)


for path in (TEAM, CSS):
    if not path.exists():
        fail(f"required source missing: {path}")

if git_blob(TEAM) != EXPECTED_TEAM_GIT_BLOB:
    fail("TeamPage differs from latest approved TOS source")
if git_blob(CSS) != EXPECTED_CSS_GIT_BLOB:
    fail("index.css differs from latest approved TOS source")

team_source = TEAM.read_text()
if 'className="tos-page tos-core-team-premium"' not in team_source:
    fail("Team premium root class missing")

original_css = CSS.read_text()
if MARKER in original_css:
    fail("Phase 04.3 V1 already present")

v1_css = r'''

/* =========================================================
   Phase 04.3 — Team Members — Flagship V1
   Scope: Team > Team Members (/team) presentation only.
   Executive hierarchy, premium Light/Dark surfaces, KPI deck,
   department/member panels, filters, tables and modal polish.
   No state/API/permission/workflow changes.
   ========================================================= */
:root { --tos-team-phase04-3-v1-runtime: 1; }

.tos-core-team-premium {
  --tm-gold: #b88935;
  --tm-gold-hi: #d9bb72;
  --tm-gold-soft: rgba(184,137,53,.11);
  --tm-line: rgba(103,86,55,.16);
  --tm-line-strong: rgba(184,137,53,.30);
  --tm-surface: #fffefa;
  --tm-surface-soft: #f8f4eb;
  --tm-text: #1d1b17;
  --tm-muted: #716c62;
  gap: .95rem !important;
  padding-bottom: 1.15rem;
}

/* KPI deck */
.tos-core-team-premium > .grid:first-of-type {
  gap: .72rem !important;
  margin-bottom: .1rem !important;
}

.tos-core-team-premium > .grid:first-of-type > div {
  position: relative;
  overflow: hidden;
  min-height: 132px;
  border: 1px solid var(--tm-line) !important;
  border-radius: 24px !important;
  background:
    radial-gradient(circle at 15% 0%, rgba(216,184,113,.12), transparent 34%),
    linear-gradient(145deg, rgba(255,255,255,.995), rgba(248,244,235,.96)) !important;
  box-shadow: 0 12px 30px rgba(51,39,20,.06), inset 0 1px 0 rgba(255,255,255,.98) !important;
}

.tos-core-team-premium > .grid:first-of-type > div::before {
  content: "";
  position: absolute;
  inset-inline: 18px;
  top: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(184,137,53,.62), transparent);
  pointer-events: none;
}

/* Main operational panels */
.tos-core-team-premium > div:not(.fixed)[class*="rounded"],
.tos-core-team-premium > section:not(.fixed),
.tos-core-team-premium > div:not(.fixed) > section {
  border-color: var(--tm-line) !important;
}

.tos-core-team-premium > div:not(.fixed)[class*="rounded"] {
  background:
    radial-gradient(circle at 8% 0%, rgba(214,181,112,.075), transparent 25%),
    linear-gradient(150deg, rgba(255,255,255,.99), rgba(249,246,239,.97)) !important;
  box-shadow: 0 16px 42px rgba(51,39,20,.065), inset 0 1px 0 rgba(255,255,255,.96) !important;
}

.tos-core-team-premium h2 {
  color: var(--tm-text) !important;
  letter-spacing: -.026em;
}

.tos-core-team-premium h3 {
  letter-spacing: -.018em;
}

/* Filters and form controls */
.tos-core-team-premium input:not([type="checkbox"]):not([type="radio"]):not([type="file"]),
.tos-core-team-premium select,
.tos-core-team-premium textarea {
  border: 1px solid rgba(101,87,64,.19) !important;
  background-color: rgba(255,255,255,.97) !important;
  color: #28251f !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.96), 0 1px 2px rgba(43,34,18,.025);
}

.tos-core-team-premium input:not([type="checkbox"]):not([type="radio"]):not([type="file"]):focus,
.tos-core-team-premium select:focus,
.tos-core-team-premium textarea:focus {
  border-color: rgba(184,137,53,.64) !important;
  box-shadow: 0 0 0 3px rgba(184,137,53,.105) !important;
  outline: none !important;
}

.tos-core-team-premium select option {
  background: #fffefa;
  color: #27241e;
}

/* Team / department tables */
.tos-core-team-premium table {
  border-collapse: separate;
  border-spacing: 0;
  background: rgba(255,255,255,.78) !important;
}

.tos-core-team-premium table thead,
.tos-core-team-premium table thead tr,
.tos-core-team-premium table thead th {
  background: linear-gradient(180deg, #f7f2e7, #f1eadb) !important;
  color: #625c50 !important;
  border-color: rgba(107,89,57,.12) !important;
}

.tos-core-team-premium table thead th {
  letter-spacing: .03em;
}

.tos-core-team-premium table tbody tr {
  background: rgba(255,255,255,.76) !important;
}

.tos-core-team-premium table tbody tr:nth-child(even) {
  background: rgba(249,246,239,.66) !important;
}

.tos-core-team-premium table tbody tr:hover,
.tos-core-team-premium table tbody tr:focus-within {
  background: rgba(184,137,53,.065) !important;
}

.tos-core-team-premium table tbody td {
  border-color: rgba(99,84,57,.075) !important;
}

/* Member avatars/cards and compact surfaces */
.tos-core-team-premium article,
.tos-core-team-premium [class*="rounded-[24px]"][class*="border"],
.tos-core-team-premium [class*="rounded-[26px]"][class*="border"] {
  border-color: rgba(102,86,58,.14) !important;
}

.tos-core-team-premium article:hover {
  border-color: var(--tm-line-strong) !important;
  box-shadow: 0 14px 34px rgba(48,36,17,.075) !important;
}

/* Modals / drawers belong to the same visual system */
.tos-core-team-premium > .fixed form,
.tos-core-team-premium > .fixed > div:not([class*="backdrop"]) {
  border-color: rgba(105,88,57,.16) !important;
  background:
    radial-gradient(circle at 10% 0%, rgba(214,181,112,.09), transparent 28%),
    linear-gradient(150deg, #fffefa, #f8f4eb) !important;
  box-shadow: 0 28px 72px rgba(42,32,16,.22), inset 0 1px 0 rgba(255,255,255,.96) !important;
}

.tos-core-team-premium button {
  -webkit-tap-highlight-color: transparent;
}

.tos-core-team-premium button:focus-visible {
  outline: 2px solid rgba(184,137,53,.68);
  outline-offset: 2px;
}

/* ============================ DARK ============================ */
html.dark .tos-core-team-premium {
  --tm-gold: #d5b568;
  --tm-gold-hi: #efd994;
  --tm-gold-soft: rgba(213,181,104,.11);
  --tm-line: rgba(255,255,255,.085);
  --tm-line-strong: rgba(213,181,104,.26);
  --tm-surface: #101216;
  --tm-surface-soft: #15171c;
  --tm-text: #f4f2ec;
  --tm-muted: #a6a9b0;
}

html.dark .tos-core-team-premium > .grid:first-of-type > div {
  border-color: rgba(255,255,255,.08) !important;
  background:
    radial-gradient(circle at 14% 0%, rgba(213,181,104,.06), transparent 34%),
    linear-gradient(150deg, #181a1f 0%, #111318 100%) !important;
  box-shadow: 0 15px 34px rgba(0,0,0,.22), inset 0 1px 0 rgba(255,255,255,.025) !important;
}

html.dark .tos-core-team-premium > div:not(.fixed)[class*="rounded"] {
  border-color: rgba(255,255,255,.08) !important;
  background:
    radial-gradient(circle at 8% 0%, rgba(213,181,104,.045), transparent 25%),
    linear-gradient(150deg, #111318 0%, #0c0e12 66%, #0a0c0f 100%) !important;
  box-shadow: 0 20px 50px rgba(0,0,0,.28), inset 0 1px 0 rgba(255,255,255,.02) !important;
}

html.dark .tos-core-team-premium h2,
html.dark .tos-core-team-premium h3 {
  color: #f6f3eb !important;
}

html.dark .tos-core-team-premium input:not([type="checkbox"]):not([type="radio"]):not([type="file"]),
html.dark .tos-core-team-premium select,
html.dark .tos-core-team-premium textarea {
  border-color: rgba(255,255,255,.105) !important;
  background-color: #15171c !important;
  color: #f2f0eb !important;
  -webkit-text-fill-color: #f2f0eb;
  color-scheme: dark;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.02) !important;
}

html.dark .tos-core-team-premium select option {
  background: #15171c;
  color: #f2f0eb;
}

html.dark .tos-core-team-premium table,
html.dark .tos-core-team-premium table tbody {
  background: #0e1014 !important;
}

html.dark .tos-core-team-premium table thead,
html.dark .tos-core-team-premium table thead tr,
html.dark .tos-core-team-premium table thead th {
  background: #181a1f !important;
  color: #b5b8bf !important;
  border-color: rgba(255,255,255,.075) !important;
}

html.dark .tos-core-team-premium table tbody tr,
html.dark .tos-core-team-premium table tbody tr:nth-child(even) {
  background: #111318 !important;
}

html.dark .tos-core-team-premium table tbody tr:hover,
html.dark .tos-core-team-premium table tbody tr:focus-within {
  background: #1a1813 !important;
}

html.dark .tos-core-team-premium table tbody td {
  background: transparent !important;
  border-color: rgba(255,255,255,.055) !important;
}

html.dark .tos-core-team-premium article {
  border-color: rgba(255,255,255,.075) !important;
  background: linear-gradient(145deg, rgba(24,26,31,.96), rgba(15,17,21,.96)) !important;
}

html.dark .tos-core-team-premium article:hover {
  border-color: rgba(213,181,104,.24) !important;
  box-shadow: 0 16px 38px rgba(0,0,0,.24) !important;
}

html.dark .tos-core-team-premium > .fixed form,
html.dark .tos-core-team-premium > .fixed > div:not([class*="backdrop"]) {
  border-color: rgba(255,255,255,.09) !important;
  background:
    radial-gradient(circle at 10% 0%, rgba(213,181,104,.055), transparent 28%),
    linear-gradient(150deg, #15171c, #0d0f13) !important;
  box-shadow: 0 30px 80px rgba(0,0,0,.48), inset 0 1px 0 rgba(255,255,255,.025) !important;
}

/* Avoid stark white active buttons in Dark; use champagne titanium instead. */
html.dark .tos-core-team-premium button[class*="dark:bg-white"][class*="dark:text-zinc-950"] {
  background: linear-gradient(135deg, #e4cc8d, #c4a254) !important;
  color: #17150f !important;
  border-color: rgba(239,217,148,.38) !important;
  box-shadow: 0 7px 18px rgba(0,0,0,.18), inset 0 1px 0 rgba(255,255,255,.28) !important;
}

@media (max-width: 1023px) {
  .tos-core-team-premium { gap: .78rem !important; }
  .tos-core-team-premium > .grid:first-of-type > div { min-height: 118px; }
}

@media (prefers-reduced-motion: reduce) {
  .tos-core-team-premium *,
  .tos-core-team-premium *::before,
  .tos-core-team-premium *::after {
    transition-duration: .01ms !important;
    animation-duration: .01ms !important;
    scroll-behavior: auto !important;
  }
}
'''

# Normalize only the added block so diff-check cannot fail on trailing whitespace.
v1_css = "\n".join(line.rstrip() for line in v1_css.splitlines()).strip() + "\n"
updated_css = original_css.rstrip() + "\n\n" + v1_css

backup = None
stage = None
live_swapped = False

try:
    CSS.write_text(updated_css)
    if CSS.read_text().count(MARKER) != 1:
        raise RuntimeError("source V1 marker missing or duplicated")
    if git_blob(TEAM) != EXPECTED_TEAM_GIT_BLOB:
        raise RuntimeError("TeamPage changed unexpectedly")

    subprocess.run([
        "git", "-C", str(ROOT), "diff", "--check", "--", "frontend/src/index.css"
    ], check=True)

    subprocess.run(["npm", "run", "build"], cwd=ROOT / "frontend", check=True)
    if not (DIST / "index.html").exists():
        raise RuntimeError("built dist index missing")

    dist_count = tree_count(DIST, MARKER.encode())
    if dist_count < 1:
        raise RuntimeError("Phase 04.3 V1 marker missing from dist")

    stamp = time.strftime("%Y%m%d-%H%M%S")
    stage = LIVE_PARENT / f"build.phase04-3-team-v1.new.{int(time.time())}"
    backup = LIVE_PARENT / f"build.phase04-3-team-v1.backup-{stamp}"
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
        raise RuntimeError("Phase 04.3 V1 marker missing from live build")

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
print("SCREEN=TEAM_MEMBERS_ONLY")
print("V1_RUNTIME=YES")
print("LIGHT_FLAGSHIP_SURFACES=YES")
print("DARK_FLAGSHIP_SURFACES=YES")
print("KPI_DECK_REFINED=YES")
print("DEPARTMENT_PANEL_REFINED=YES")
print("TEAM_TABLE_REFINED=YES")
print("MODALS_REFINED=YES")
print("BUSINESS_LOGIC_CHANGED=NO")
print("SOURCE_V1_RUNTIME_COUNT=" + str(CSS.read_text().count(MARKER)))
print("DIST_V1_RUNTIME_COUNT=" + str(tree_count(DIST, MARKER.encode())))
print("LIVE_V1_RUNTIME_COUNT=" + str(tree_count(LIVE, MARKER.encode())))
print("TEAM_PAGE_SHA256=" + sha256(TEAM))
print("INDEX_CSS_SHA256=" + sha256(CSS))
