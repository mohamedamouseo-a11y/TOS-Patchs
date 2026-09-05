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

EXPECTED_TEAM_SHA256 = "12f719a374a580f73678f97a809f3345e267d91aae46728875873546a4823d19"
EXPECTED_CSS_SHA256 = "d339cf90d1678abd198ed71253acf01b5e3160ac7ff4bac1bee70e328402cbfd"
V1_MARKER = "--tos-team-phase04-3-v1-runtime"
V2_MARKER = "--tos-team-phase04-3-v2-runtime"
V3_MARKER = "--tos-team-phase04-3-v3-runtime"
DEPARTMENT_HOOK = "tos-team-departments-panel-v2"
KPI_HOOK = "tos-team-kpi-card-v3"
ALL_TEAM_HOOK = "tos-team-all-team-panel-v3"

print("RUNNING=PHASE04_3_TEAM_MEMBERS_FLAGSHIP_V3")


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
    print("V3_RUNTIME=NO")
    sys.exit(1)


for path in (TEAM, CSS):
    if not path.exists():
        fail(f"required source missing: {path}")

if sha256(TEAM) != EXPECTED_TEAM_SHA256:
    fail("TeamPage SHA256 differs from approved Phase 04.3 V2 live source")
if sha256(CSS) != EXPECTED_CSS_SHA256:
    fail("index.css SHA256 differs from approved Phase 04.3 V2 live source")

original_team = TEAM.read_text()
original_css = CSS.read_text()

if original_css.count(V1_MARKER) != 1 or original_css.count(V2_MARKER) != 1:
    fail("Phase 04.3 V1/V2 markers missing or duplicated")
if original_team.count(DEPARTMENT_HOOK) != 1:
    fail("Phase 04.3 V2 department hook missing or duplicated")
if V3_MARKER in original_css or KPI_HOOK in original_team or ALL_TEAM_HOOK in original_team:
    fail("Phase 04.3 V3 already present")

old_mini_block = r'''  const ringStyle = { background: `conic-gradient(${current.ring} ${percent}%, ${current.soft} 0)` };

  return (
    <div className="grid justify-items-center text-center">
      <div className="relative grid h-18 w-18 shrink-0 place-items-center rounded-full" style={ringStyle}>
        <div className="grid h-[52px] w-[52px] place-items-center rounded-full bg-white shadow-inner dark:bg-zinc-900">
          <span className={cn("text-xl font-black", current.text)}>{numericValue}</span>
        </div>
      </div>
      <div className="mt-2 text-xs font-black text-zinc-950 dark:text-white">{label}</div>
      <div className={cn("mt-0.5 text-[10px] font-black", current.badge)}>{percent}% {lang === "en" ? "of total" : "من الإجمالي"}</div>
    </div>
  );'''

new_mini_block = r'''  const ringStyle = { "--tm-kpi-progress": `${percent}%` };

  return (
    <div className="tos-team-kpi-card-v3 grid justify-items-center text-center" data-tone={tone} style={ringStyle}>
      <div className="tos-team-kpi-ring-v3 relative grid h-18 w-18 shrink-0 place-items-center rounded-full">
        <div className="tos-team-kpi-core-v3 grid h-[52px] w-[52px] place-items-center rounded-full bg-white shadow-inner dark:bg-zinc-900">
          <span className={cn("tos-team-kpi-value-v3 text-xl font-black", current.text)}>{numericValue}</span>
        </div>
      </div>
      <div className="tos-team-kpi-copy-v3">
        <div className="tos-team-kpi-label-v3 mt-2 text-xs font-black text-zinc-950 dark:text-white">{label}</div>
        <div className={cn("tos-team-kpi-share-v3 mt-0.5 text-[10px] font-black", current.badge)}>{percent}% {lang === "en" ? "of total" : "من الإجمالي"}</div>
      </div>
    </div>
  );'''

if original_team.count(old_mini_block) != 1:
    fail("MiniStat V2 source signature not found exactly once")
updated_team = original_team.replace(old_mini_block, new_mini_block, 1)

old_all_team = '''      <div className="mb-5 rounded-[24px] border border-zinc-100 bg-white p-3.5 shadow-sm dark:border-white/10 dark:bg-zinc-900/70">\n        <div className="mb-3 flex flex-wrap items-center justify-between gap-2.5">\n          <div>\n            <h2 className="text-lg font-black text-zinc-950 dark:text-white">{lang === "en" ? "All Team" : "كل الفريق"}</h2>'''
new_all_team = '''      <div className="tos-team-all-team-panel-v3 mb-5 rounded-[24px] border border-zinc-100 bg-white p-3.5 shadow-sm dark:border-white/10 dark:bg-zinc-900/70">\n        <div className="mb-3 flex flex-wrap items-center justify-between gap-2.5">\n          <div>\n            <h2 className="text-lg font-black text-zinc-950 dark:text-white">{lang === "en" ? "All Team" : "كل الفريق"}</h2>'''
if updated_team.count(old_all_team) != 1:
    fail("All Team panel source signature not found exactly once")
updated_team = updated_team.replace(old_all_team, new_all_team, 1)

v3_css = r'''

/* =========================================================
   Phase 04.3 — Team Members — Flagship V3
   Executive KPI Deck + luxury section refinement.
   Presentation only. V1/V2 mechanics and all business logic remain intact.
   ========================================================= */
:root { --tos-team-phase04-3-v3-runtime: 1; }

/* ---------- Executive KPI instrumentation ---------- */
.tos-team-kpi-card-v3 {
  --tm-kpi-accent: #23252b;
  --tm-kpi-accent-rgb: 35,37,43;
  position: relative;
  isolation: isolate;
  display: grid !important;
  grid-template-columns: 86px minmax(0,1fr);
  grid-template-rows: auto auto;
  column-gap: 15px;
  row-gap: 2px;
  align-items: center;
  justify-items: stretch !important;
  min-height: 136px !important;
  padding: 20px 20px 23px !important;
  text-align: start !important;
  overflow: hidden;
}

.tos-team-kpi-card-v3[data-tone="emerald"] { --tm-kpi-accent: #0aa678; --tm-kpi-accent-rgb: 10,166,120; }
.tos-team-kpi-card-v3[data-tone="amber"] { --tm-kpi-accent: #c99022; --tm-kpi-accent-rgb: 201,144,34; }
.tos-team-kpi-card-v3[data-tone="red"] { --tm-kpi-accent: #df5458; --tm-kpi-accent-rgb: 223,84,88; }
.tos-team-kpi-card-v3[data-tone="blue"] { --tm-kpi-accent: #387de8; --tm-kpi-accent-rgb: 56,125,232; }
.tos-team-kpi-card-v3[data-tone="zinc"] { --tm-kpi-accent: #25272d; --tm-kpi-accent-rgb: 37,39,45; }

.tos-team-kpi-card-v3::before {
  content: "";
  position: absolute;
  width: 150px;
  height: 150px;
  inset-inline-end: -48px;
  top: -70px;
  border-radius: 999px;
  background: radial-gradient(circle, rgba(var(--tm-kpi-accent-rgb),.13), rgba(var(--tm-kpi-accent-rgb),0) 68%);
  pointer-events: none;
  z-index: -1;
}

.tos-team-kpi-card-v3::after {
  content: "";
  position: absolute;
  inset-inline: 20px;
  bottom: 12px;
  height: 2px;
  border-radius: 999px;
  background: linear-gradient(90deg,
    rgba(var(--tm-kpi-accent-rgb),.96) 0 var(--tm-kpi-progress),
    rgba(104,96,82,.13) var(--tm-kpi-progress) 100%);
  box-shadow: 0 0 14px rgba(var(--tm-kpi-accent-rgb),.10);
  opacity: .9;
}

.tos-team-kpi-ring-v3 {
  grid-row: 1 / span 2;
  width: 82px !important;
  height: 82px !important;
  padding: 7px;
  background:
    conic-gradient(from -90deg,
      var(--tm-kpi-accent) 0 var(--tm-kpi-progress),
      color-mix(in srgb, var(--tm-kpi-accent) 12%, #e8e4dc) var(--tm-kpi-progress) 100%) !important;
  box-shadow:
    0 0 0 1px rgba(var(--tm-kpi-accent-rgb),.12),
    0 10px 24px rgba(var(--tm-kpi-accent-rgb),.11),
    inset 0 0 0 1px rgba(255,255,255,.50);
}

.tos-team-kpi-ring-v3::before {
  content: "";
  position: absolute;
  inset: -5px;
  border: 1px solid rgba(var(--tm-kpi-accent-rgb),.16);
  border-radius: inherit;
  box-shadow: inset 0 0 16px rgba(var(--tm-kpi-accent-rgb),.06);
  pointer-events: none;
}

.tos-team-kpi-ring-v3::after {
  content: "";
  position: absolute;
  width: 7px;
  height: 7px;
  top: 3px;
  left: 50%;
  transform: translateX(-50%);
  border-radius: 999px;
  background: #fffdf7;
  border: 1px solid rgba(var(--tm-kpi-accent-rgb),.24);
  box-shadow: 0 0 0 3px rgba(var(--tm-kpi-accent-rgb),.08), 0 2px 5px rgba(35,29,17,.12);
}

.tos-team-kpi-core-v3 {
  position: relative;
  width: 62px !important;
  height: 62px !important;
  border: 1px solid rgba(83,72,54,.12);
  background:
    radial-gradient(circle at 34% 24%, rgba(255,255,255,1), rgba(255,254,250,.96) 46%, rgba(244,240,232,.94) 100%) !important;
  box-shadow:
    inset 0 1px 0 rgba(255,255,255,.95),
    inset 0 -6px 16px rgba(76,62,39,.045),
    0 4px 12px rgba(46,37,22,.07) !important;
}

.tos-team-kpi-value-v3 {
  color: var(--tm-kpi-accent) !important;
  font-size: 1.62rem !important;
  line-height: 1;
  letter-spacing: -.045em;
  text-shadow: 0 1px 0 rgba(255,255,255,.65);
}

.tos-team-kpi-copy-v3 {
  min-width: 0;
  align-self: center;
}

.tos-team-kpi-label-v3 {
  margin-top: 0 !important;
  color: #25221d !important;
  font-size: .82rem !important;
  line-height: 1.25;
  letter-spacing: -.018em;
}

.tos-team-kpi-share-v3 {
  display: inline-flex;
  align-items: center;
  width: fit-content;
  margin-top: 8px !important;
  padding: 5px 8px;
  border: 1px solid rgba(var(--tm-kpi-accent-rgb),.14);
  border-radius: 999px;
  background: rgba(var(--tm-kpi-accent-rgb),.065);
  color: color-mix(in srgb, var(--tm-kpi-accent) 82%, #4d463a) !important;
  font-size: .64rem !important;
  letter-spacing: .01em;
}

@media (hover:hover) {
  .tos-team-kpi-card-v3 {
    transition: transform .18s ease, border-color .18s ease, box-shadow .18s ease, background .18s ease;
  }
  .tos-team-kpi-card-v3:hover {
    transform: translateY(-2px);
    border-color: rgba(var(--tm-kpi-accent-rgb),.28) !important;
    box-shadow: 0 18px 38px rgba(49,38,20,.09), inset 0 1px 0 rgba(255,255,255,.98) !important;
  }
}

/* ---------- Executive section chrome ---------- */
.tos-team-departments-panel-v2,
.tos-team-all-team-panel-v3 {
  position: relative;
  overflow: hidden;
  border-color: rgba(104,86,57,.18) !important;
  background:
    radial-gradient(circle at 8% -8%, rgba(208,170,92,.105), transparent 23%),
    linear-gradient(148deg, rgba(255,255,255,.995), rgba(248,244,235,.975)) !important;
  box-shadow: 0 20px 48px rgba(53,40,19,.075), inset 0 1px 0 rgba(255,255,255,.98) !important;
}

.tos-team-departments-panel-v2::before,
.tos-team-all-team-panel-v3::before {
  content: "";
  position: absolute;
  top: 0;
  inset-inline: 24px;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(184,137,53,.62), transparent);
  pointer-events: none;
}

.tos-team-departments-panel-v2 > .mb-3\.5,
.tos-team-all-team-panel-v3 > .mb-3 {
  padding-bottom: 11px;
  border-bottom: 1px solid rgba(98,81,53,.09);
}

.tos-team-departments-panel-v2 h2,
.tos-team-all-team-panel-v3 h2 {
  font-size: 1.02rem !important;
  letter-spacing: -.025em;
}

/* All Team filter band becomes a deliberate command surface. */
.tos-team-all-team-panel-v3 > .mb-3.grid {
  padding: 8px;
  border: 1px solid rgba(101,83,53,.12);
  border-radius: 17px;
  background: rgba(248,244,235,.66);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.74);
}

.tos-team-all-team-panel-v3 table thead th {
  padding-top: 11px !important;
  padding-bottom: 11px !important;
}

.tos-team-all-team-panel-v3 table tbody tr {
  transition: background-color .16s ease, box-shadow .16s ease;
}

.tos-team-all-team-panel-v3 table tbody tr:hover {
  box-shadow: inset 3px 0 0 rgba(184,137,53,.45);
}

/* ============================ DARK ============================ */
html.dark .tos-team-kpi-card-v3[data-tone="zinc"] {
  --tm-kpi-accent: #d8c48f;
  --tm-kpi-accent-rgb: 216,196,143;
}

html.dark .tos-team-kpi-card-v3 {
  border-color: rgba(255,255,255,.085) !important;
  background:
    radial-gradient(circle at 84% 0%, rgba(var(--tm-kpi-accent-rgb),.055), transparent 35%),
    linear-gradient(145deg, #17191e 0%, #101216 74%, #0d0f13 100%) !important;
  box-shadow: 0 16px 38px rgba(0,0,0,.29), inset 0 1px 0 rgba(255,255,255,.025) !important;
}

html.dark .tos-team-kpi-card-v3::after {
  background: linear-gradient(90deg,
    rgba(var(--tm-kpi-accent-rgb),.88) 0 var(--tm-kpi-progress),
    rgba(255,255,255,.075) var(--tm-kpi-progress) 100%);
  box-shadow: 0 0 16px rgba(var(--tm-kpi-accent-rgb),.12);
}

html.dark .tos-team-kpi-ring-v3 {
  background:
    conic-gradient(from -90deg,
      var(--tm-kpi-accent) 0 var(--tm-kpi-progress),
      color-mix(in srgb, var(--tm-kpi-accent) 10%, #2c2f35) var(--tm-kpi-progress) 100%) !important;
  box-shadow:
    0 0 0 1px rgba(var(--tm-kpi-accent-rgb),.12),
    0 12px 28px rgba(0,0,0,.26),
    0 0 24px rgba(var(--tm-kpi-accent-rgb),.055),
    inset 0 0 0 1px rgba(255,255,255,.045) !important;
}

html.dark .tos-team-kpi-ring-v3::after {
  background: #f6ecd0;
  border-color: rgba(var(--tm-kpi-accent-rgb),.36);
  box-shadow: 0 0 0 3px rgba(var(--tm-kpi-accent-rgb),.08), 0 0 12px rgba(var(--tm-kpi-accent-rgb),.24);
}

html.dark .tos-team-kpi-core-v3 {
  border-color: rgba(255,255,255,.08);
  background:
    radial-gradient(circle at 34% 24%, #202329 0%, #16181d 50%, #101216 100%) !important;
  box-shadow:
    inset 0 1px 0 rgba(255,255,255,.04),
    inset 0 -8px 18px rgba(0,0,0,.20),
    0 4px 12px rgba(0,0,0,.24) !important;
}

html.dark .tos-team-kpi-value-v3 {
  color: var(--tm-kpi-accent) !important;
  text-shadow: 0 0 16px rgba(var(--tm-kpi-accent-rgb),.10);
}

html.dark .tos-team-kpi-label-v3 {
  color: #f1efe9 !important;
}

html.dark .tos-team-kpi-share-v3 {
  border-color: rgba(var(--tm-kpi-accent-rgb),.16);
  background: rgba(var(--tm-kpi-accent-rgb),.075);
  color: color-mix(in srgb, var(--tm-kpi-accent) 86%, #f4f2ed) !important;
}

html.dark .tos-team-departments-panel-v2,
html.dark .tos-team-all-team-panel-v3 {
  border-color: rgba(255,255,255,.085) !important;
  background:
    radial-gradient(circle at 8% -8%, rgba(213,181,104,.055), transparent 25%),
    linear-gradient(150deg, #111318 0%, #0c0e12 70%, #090b0e 100%) !important;
  box-shadow: 0 22px 54px rgba(0,0,0,.32), inset 0 1px 0 rgba(255,255,255,.022) !important;
}

html.dark .tos-team-departments-panel-v2 > .mb-3\.5,
html.dark .tos-team-all-team-panel-v3 > .mb-3 {
  border-bottom-color: rgba(255,255,255,.07);
}

html.dark .tos-team-all-team-panel-v3 > .mb-3.grid {
  border-color: rgba(255,255,255,.075);
  background: rgba(255,255,255,.025);
  box-shadow: inset 0 1px 0 rgba(255,255,255,.018);
}

html.dark .tos-team-all-team-panel-v3 table tbody tr:hover {
  background: linear-gradient(90deg, rgba(213,181,104,.07), rgba(213,181,104,.018)) !important;
  box-shadow: inset 3px 0 0 rgba(213,181,104,.48);
}

@media (max-width: 1280px) {
  .tos-team-kpi-card-v3 {
    grid-template-columns: 74px minmax(0,1fr);
    column-gap: 12px;
    padding-inline: 15px !important;
  }
  .tos-team-kpi-ring-v3 { width: 72px !important; height: 72px !important; }
  .tos-team-kpi-core-v3 { width: 54px !important; height: 54px !important; }
  .tos-team-kpi-value-v3 { font-size: 1.4rem !important; }
}

@media (max-width: 767px) {
  .tos-team-kpi-card-v3 {
    grid-template-columns: 70px minmax(0,1fr);
    min-height: 112px !important;
    padding-block: 15px 20px !important;
  }
  .tos-team-kpi-ring-v3 { width: 68px !important; height: 68px !important; }
  .tos-team-kpi-core-v3 { width: 51px !important; height: 51px !important; }
}

@media (prefers-reduced-motion: reduce) {
  .tos-team-kpi-card-v3,
  .tos-team-kpi-card-v3 *,
  .tos-team-all-team-panel-v3 * {
    transition-duration: .01ms !important;
    animation-duration: .01ms !important;
  }
}
'''

v3_css = "\n".join(line.rstrip() for line in v3_css.splitlines()).strip() + "\n"
updated_css = original_css.rstrip() + "\n\n" + v3_css

backup = None
stage = None
live_swapped = False

try:
    TEAM.write_text(updated_team)
    CSS.write_text(updated_css)

    if TEAM.read_text().count(KPI_HOOK) != 1:
        raise RuntimeError("V3 KPI source hook missing or duplicated")
    if TEAM.read_text().count(ALL_TEAM_HOOK) != 1:
        raise RuntimeError("V3 All Team source hook missing or duplicated")
    if TEAM.read_text().count(DEPARTMENT_HOOK) != 1:
        raise RuntimeError("V2 department hook was not preserved")
    if CSS.read_text().count(V3_MARKER) != 1:
        raise RuntimeError("source V3 marker missing or duplicated")
    if CSS.read_text().count(V1_MARKER) != 1 or CSS.read_text().count(V2_MARKER) != 1:
        raise RuntimeError("V1/V2 markers were not preserved")

    # Validate only material introduced by V3 so historical whitespace elsewhere
    # cannot fail the patch. This phase intentionally changes presentation only.
    introduced = new_mini_block + "\n" + new_all_team + "\n" + v3_css
    if any(line.endswith(" ") or line.endswith("\t") for line in introduced.splitlines()):
        raise RuntimeError("V3 introduced trailing whitespace")

    subprocess.run(["npm", "run", "build"], cwd=ROOT / "frontend", check=True)
    if not (DIST / "index.html").exists():
        raise RuntimeError("built dist index missing")

    dist_v3 = tree_count(DIST, V3_MARKER.encode())
    dist_kpi = tree_count(DIST, KPI_HOOK.encode())
    if dist_v3 < 1 or dist_kpi < 1:
        raise RuntimeError(f"Phase 04.3 V3 marker/hook missing from dist: marker={dist_v3}, kpi={dist_kpi}")

    stamp = time.strftime("%Y%m%d-%H%M%S")
    stage = LIVE_PARENT / f"build.phase04-3-team-v3.new.{int(time.time())}"
    backup = LIVE_PARENT / f"build.phase04-3-team-v3.backup-{stamp}"
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

    live_v3 = tree_count(LIVE, V3_MARKER.encode())
    live_kpi = tree_count(LIVE, KPI_HOOK.encode())
    if live_v3 < 1 or live_kpi < 1:
        raise RuntimeError(f"Phase 04.3 V3 marker/hook missing from live build: marker={live_v3}, kpi={live_kpi}")

    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("V3_RUNTIME=YES")
    print("EXECUTIVE_KPI_DECK=YES")
    print("LUXURY_RADIAL_GAUGES=YES")
    print("KPI_MICRO_INSIGHTS_REFINED=YES")
    print("DEPARTMENT_SECTION_REFINED=YES")
    print("ALL_TEAM_COMMAND_SURFACE_REFINED=YES")
    print("LIGHT_FLAGSHIP_REFINED=YES")
    print("DARK_FLAGSHIP_REFINED=YES")
    print("V2_DEPARTMENT_FIX_PRESERVED=YES")
    print("BUSINESS_LOGIC_CHANGED=NO")
    print(f"SOURCE_V3_RUNTIME_COUNT={CSS.read_text().count(V3_MARKER)}")
    print(f"SOURCE_KPI_HOOK_COUNT={TEAM.read_text().count(KPI_HOOK)}")
    print(f"SOURCE_ALL_TEAM_HOOK_COUNT={TEAM.read_text().count(ALL_TEAM_HOOK)}")
    print(f"DIST_V3_RUNTIME_COUNT={dist_v3}")
    print(f"LIVE_V3_RUNTIME_COUNT={live_v3}")
    print(f"TEAM_PAGE_SHA256={sha256(TEAM)}")
    print(f"INDEX_CSS_SHA256={sha256(CSS)}")

except Exception as exc:
    try:
        TEAM.write_text(original_team)
        CSS.write_text(original_css)
    except Exception:
        pass

    if live_swapped and backup and backup.exists():
        failed_live = LIVE_PARENT / f"build.phase04-3-team-v3.failed.{int(time.time())}"
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
    print("V3_RUNTIME=NO")
    print(f"TEAM_PAGE_SHA256={sha256(TEAM) if TEAM.exists() else 'MISSING'}")
    print(f"INDEX_CSS_SHA256={sha256(CSS) if CSS.exists() else 'MISSING'}")
    sys.exit(1)
