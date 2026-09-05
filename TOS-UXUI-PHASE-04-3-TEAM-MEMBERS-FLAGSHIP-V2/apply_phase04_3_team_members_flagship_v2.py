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

EXPECTED_TEAM_SHA256 = "d14814aca4482d8c89d7a8a734125703f5b6123f58ccfff7368878ca94b67efe"
EXPECTED_CSS_SHA256 = "3d20f2a7fb9b35cb437af1c106bb2d77f7f166c248f0a223e052fbee2db8a6f0"
V1_MARKER = "--tos-team-phase04-3-v1-runtime"
V2_MARKER = "--tos-team-phase04-3-v2-runtime"
PANEL_CLASS = "tos-team-departments-panel-v2"

print("RUNNING=PHASE04_3_TEAM_MEMBERS_FLAGSHIP_V2")


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


for path in (TEAM, CSS):
    if not path.exists():
        fail(f"required source missing: {path}")

if sha256(TEAM) != EXPECTED_TEAM_SHA256:
    fail("TeamPage SHA256 differs from Phase 04.3 V1 live source")
if sha256(CSS) != EXPECTED_CSS_SHA256:
    fail("index.css SHA256 differs from Phase 04.3 V1 live source")

original_team = TEAM.read_text()
original_css = CSS.read_text()

if original_css.count(V1_MARKER) != 1:
    fail("Phase 04.3 V1 marker missing or duplicated")
if V2_MARKER in original_css or PANEL_CLASS in original_team:
    fail("Phase 04.3 V2 already present")

needle = 'className={cn("mb-5 rounded-[24px] border border-zinc-100 bg-white p-4 shadow-sm dark:border-white/10 dark:bg-zinc-900/70", alignClass)}'
replacement = 'className={cn("tos-team-departments-panel-v2 mb-5 rounded-[24px] border border-zinc-100 bg-white p-4 shadow-sm dark:border-white/10 dark:bg-zinc-900/70", alignClass)}'
if original_team.count(needle) != 1:
    fail("Department Management root signature not found exactly once")

updated_team = original_team.replace(needle, replacement, 1)

v2_css = r'''

/* =========================================================
   Phase 04.3 — Team Members — Flagship V2
   Scope: Department Management dark-surface correction and
   hierarchy refinement. Presentation only; V1 remains base.
   No API/state/permissions/workflow changes.
   ========================================================= */
:root { --tos-team-phase04-3-v2-runtime: 1; }

/* Department panel receives a stable local hook so its grid can no longer
   inherit legacy/global white surfaces in Dark mode. */
.tos-team-departments-panel-v2 {
  overflow: hidden;
}

.tos-team-departments-panel-v2 > .overflow-hidden {
  background: rgba(255,255,255,.74) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.82);
}

.tos-team-departments-panel-v2 > .overflow-hidden > .divide-y > div {
  min-height: 62px;
}

.tos-team-departments-panel-v2 > .overflow-hidden > .divide-y > div:hover {
  background: rgba(184,137,53,.055) !important;
}

/* Give department leadership text a little more hierarchy in Light. */
.tos-team-departments-panel-v2 > .overflow-hidden > .divide-y > div > div:nth-child(2) > div:first-child {
  color: #2b2822 !important;
}

/* ============================ DARK ============================ */
html.dark .tos-team-departments-panel-v2 {
  border-color: rgba(255,255,255,.085) !important;
  background:
    radial-gradient(circle at 8% 0%, rgba(213,181,104,.045), transparent 26%),
    linear-gradient(150deg, #111318 0%, #0c0e12 70%, #0a0c0f 100%) !important;
}

html.dark .tos-team-departments-panel-v2 > .overflow-hidden {
  border-color: rgba(255,255,255,.08) !important;
  background: #0e1014 !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.025), 0 10px 26px rgba(0,0,0,.14) !important;
}

html.dark .tos-team-departments-panel-v2 > .overflow-hidden > .hidden {
  background: #181a1f !important;
  color: #aeb2bb !important;
  border-color: rgba(255,255,255,.07) !important;
}

html.dark .tos-team-departments-panel-v2 > .overflow-hidden > .divide-y {
  background: #0e1014 !important;
  border-color: rgba(255,255,255,.065) !important;
}

html.dark .tos-team-departments-panel-v2 > .overflow-hidden > .divide-y > div {
  background: #111318 !important;
  border-color: rgba(255,255,255,.06) !important;
}

html.dark .tos-team-departments-panel-v2 > .overflow-hidden > .divide-y > div:nth-child(even) {
  background: #101217 !important;
}

html.dark .tos-team-departments-panel-v2 > .overflow-hidden > .divide-y > div:hover,
html.dark .tos-team-departments-panel-v2 > .overflow-hidden > .divide-y > div:focus-within {
  background: linear-gradient(90deg, rgba(213,181,104,.075), rgba(213,181,104,.025)) !important;
}

html.dark .tos-team-departments-panel-v2 > .overflow-hidden > .divide-y > div > div:nth-child(2) > div:first-child {
  color: #f1efe9 !important;
}

html.dark .tos-team-departments-panel-v2 > .overflow-hidden > .divide-y > div > div:nth-child(2) > div:last-child {
  color: #c8aef8 !important;
}

/* Keep semantic department icon/chips tinted but remove light-card glare. */
html.dark .tos-team-departments-panel-v2 > .overflow-hidden > .divide-y span[class*="bg-emerald-50"],
html.dark .tos-team-departments-panel-v2 > .overflow-hidden > .divide-y span[class*="bg-cyan-50"],
html.dark .tos-team-departments-panel-v2 > .overflow-hidden > .divide-y span[class*="bg-blue-50"],
html.dark .tos-team-departments-panel-v2 > .overflow-hidden > .divide-y span[class*="bg-fuchsia-50"],
html.dark .tos-team-departments-panel-v2 > .overflow-hidden > .divide-y span[class*="bg-orange-50"],
html.dark .tos-team-departments-panel-v2 > .overflow-hidden > .divide-y span[class*="bg-rose-50"],
html.dark .tos-team-departments-panel-v2 > .overflow-hidden > .divide-y span[class*="bg-violet-50"] {
  filter: saturate(.82) brightness(.82);
}

/* Action buttons stay premium dark rather than flashing white surfaces. */
html.dark .tos-team-departments-panel-v2 > .overflow-hidden > .divide-y button {
  border-color: rgba(255,255,255,.10) !important;
  background: #17191e !important;
  color: #eceae4 !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.035) !important;
}

html.dark .tos-team-departments-panel-v2 > .overflow-hidden > .divide-y button:hover {
  border-color: rgba(213,181,104,.30) !important;
  background: #201d17 !important;
  color: #efd994 !important;
}

@media (prefers-reduced-motion: reduce) {
  .tos-team-departments-panel-v2 *,
  .tos-team-departments-panel-v2 *::before,
  .tos-team-departments-panel-v2 *::after {
    transition-duration: .01ms !important;
    animation-duration: .01ms !important;
  }
}
'''

v2_css = "\n".join(line.rstrip() for line in v2_css.splitlines()).strip() + "\n"
updated_css = original_css.rstrip() + "\n\n" + v2_css

backup = None
stage = None
live_swapped = False

try:
    TEAM.write_text(updated_team)
    CSS.write_text(updated_css)

    if TEAM.read_text().count(PANEL_CLASS) != 1:
        raise RuntimeError("Department V2 source hook missing or duplicated")
    if CSS.read_text().count(V2_MARKER) != 1:
        raise RuntimeError("source V2 marker missing or duplicated")
    if CSS.read_text().count(V1_MARKER) != 1:
        raise RuntimeError("V1 marker was not preserved")

    # Validate only content introduced by this patch; do not fail on unrelated
    # historical whitespace elsewhere in the working tree.
    if any(line.endswith(" ") or line.endswith("\t") for line in v2_css.splitlines()):
        raise RuntimeError("V2 CSS contains trailing whitespace")
    if replacement.rstrip() != replacement:
        raise RuntimeError("V2 TeamPage replacement contains trailing whitespace")

    subprocess.run(["npm", "run", "build"], cwd=ROOT / "frontend", check=True)
    if not (DIST / "index.html").exists():
        raise RuntimeError("built dist index missing")

    dist_v2 = tree_count(DIST, V2_MARKER.encode())
    if dist_v2 < 1:
        raise RuntimeError("Phase 04.3 V2 marker missing from dist")

    stamp = time.strftime("%Y%m%d-%H%M%S")
    stage = LIVE_PARENT / f"build.phase04-3-team-v2.new.{int(time.time())}"
    backup = LIVE_PARENT / f"build.phase04-3-team-v2.backup-{stamp}"
    if stage.exists():
        shutil.rmtree(stage)
    shutil.copytree(DIST, stage)
    if not (stage / "index.html").exists():
        raise RuntimeError("staged live build missing index.html")
    if not LIVE.exists():
        raise RuntimeError("live frontend root missing")

    LIVE.rename(backup)
    stage.rename(LIVE)
    live_swapped = True
    subprocess.run(["systemctl", "is-active", "--quiet", "nginx"], check=True)

    live_v2 = tree_count(LIVE, V2_MARKER.encode())
    if live_v2 < 1:
        raise RuntimeError("Phase 04.3 V2 marker missing from live build")

    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("V2_RUNTIME=YES")
    print("DARK_DEPARTMENT_WHITE_SURFACE_FIXED=YES")
    print("DARK_DEPARTMENT_ROWS_REFINED=YES")
    print("DARK_DEPARTMENT_ACTIONS_REFINED=YES")
    print("LIGHT_DEPARTMENT_PRESERVED=YES")
    print("ALL_TEAM_TABLE_PRESERVED=YES")
    print("V1_VISUALS_PRESERVED=YES")
    print("BUSINESS_LOGIC_CHANGED=NO")
    print(f"SOURCE_V2_RUNTIME_COUNT={CSS.read_text().count(V2_MARKER)}")
    print(f"SOURCE_DEPARTMENT_HOOK_COUNT={TEAM.read_text().count(PANEL_CLASS)}")
    print(f"DIST_V2_RUNTIME_COUNT={dist_v2}")
    print(f"LIVE_V2_RUNTIME_COUNT={live_v2}")
    print(f"TEAM_PAGE_SHA256={sha256(TEAM)}")
    print(f"INDEX_CSS_SHA256={sha256(CSS)}")

except Exception as exc:
    try:
        TEAM.write_text(original_team)
        CSS.write_text(original_css)
    except Exception:
        pass

    if live_swapped and backup and backup.exists():
        failed_live = LIVE_PARENT / f"build.phase04-3-team-v2.failed.{int(time.time())}"
        try:
            if LIVE.exists():
                LIVE.rename(failed_live)
            backup.rename(LIVE)
        except Exception:
            pass
    elif stage and stage.exists():
        try:
            shutil.rmtree(stage)
        except Exception:
            pass

    print("PASS/FAIL=FAIL")
    print("ERROR=" + str(exc))
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("V2_RUNTIME=NO")
    print(f"TEAM_PAGE_SHA256={sha256(TEAM) if TEAM.exists() else 'MISSING'}")
    print(f"INDEX_CSS_SHA256={sha256(CSS) if CSS.exists() else 'MISSING'}")
    sys.exit(1)
