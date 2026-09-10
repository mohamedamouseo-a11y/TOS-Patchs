from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
PAGE = FRONTEND / "src/pages/SettingsPage.jsx"
V2_STYLE = FRONTEND / "src/pages/settingsOverviewFlagshipV2Reference.css"
V21_STYLE = FRONTEND / "src/pages/settingsOverviewFlagshipV2_1FidelityPolish.css"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

V2_IMPORT = 'import "./settingsOverviewFlagshipV2Reference.css";'
V21_IMPORT = 'import "./settingsOverviewFlagshipV2_1FidelityPolish.css";'
V2_RUNTIME = "--tos-settings-overview-flagship-v2-reference-runtime"
V21_RUNTIME = "--tos-settings-overview-flagship-v2-1-fidelity-polish-runtime"

CSS = r'''
:root { --tos-settings-overview-flagship-v2-1-fidelity-polish-runtime: 1; }

/* =========================================================
   TOS Settings Overview — V2.1 Fidelity Polish
   Approved reference fidelity pass only.
   No settings behavior or data flow changes.
   ========================================================= */

/* LIGHT — richer pearl field and more visible flowing champagne linework */
.tos-settings-flagship-v1.tos-page {
  background:
    radial-gradient(circle at 8% 4%, rgba(225,174,62,.11), transparent 26%),
    radial-gradient(circle at 94% 92%, rgba(213,162,54,.075), transparent 30%),
    linear-gradient(180deg, rgba(255,253,248,.94), rgba(255,255,255,.76)) !important;
}

.tos-settings-flagship-v1 .tos-settings-flagship-header {
  border-color: rgba(184,121,17,.40) !important;
  background:
    radial-gradient(125% 108% at 73% 144%,
      transparent 0 36.5%, rgba(196,126,14,.18) 36.8% 37.06%, transparent 37.34% 40.2%,
      rgba(196,126,14,.125) 40.48% 40.72%, transparent 41.0% 43.9%,
      rgba(196,126,14,.082) 44.16% 44.38%, transparent 44.65% 47.6%,
      rgba(196,126,14,.048) 47.86% 48.05%, transparent 48.3% 100%),
    radial-gradient(circle at 88% -12%, rgba(249,217,147,.53), transparent 34%),
    linear-gradient(132deg,#fffefa 0%,#fffaf0 43%,#f6e6c8 100%) !important;
  box-shadow:
    0 20px 48px rgba(90,56,4,.095),
    0 1px 0 rgba(255,255,255,.98) inset,
    0 -1px 0 rgba(153,93,4,.08) inset !important;
}

.tos-settings-overview-v1 .tos-settings-overview-hero {
  border-color: rgba(183,121,17,.26) !important;
  background:
    radial-gradient(118% 92% at 92% 118%,
      transparent 0 42.5%, rgba(198,130,16,.12) 42.72% 42.98%, transparent 43.24% 46.25%,
      rgba(198,130,16,.075) 46.48% 46.72%, transparent 46.98% 50%,
      rgba(198,130,16,.045) 50.22% 50.42%, transparent 50.7% 100%),
    radial-gradient(circle at 92% 8%, rgba(244,208,127,.12), transparent 26%),
    linear-gradient(145deg,#fff 0%,#fffefa 62%,#faf0dc 100%) !important;
  box-shadow: 0 18px 42px rgba(67,43,8,.085), inset 0 1px rgba(255,255,255,.99) !important;
}

/* KPI: clearer hierarchy and premium hardware depth */
.tos-settings-overview-v1 .tos-settings-overview-stats > .tos-premium-stat {
  min-height: 122px !important;
  border-color: rgba(173,111,12,.23) !important;
  background:
    radial-gradient(circle at 88% 10%, rgba(235,195,102,.16), transparent 27%),
    linear-gradient(156deg,#ffffff 0%,#fffdf8 100%) !important;
  box-shadow:
    0 13px 30px rgba(68,42,5,.07),
    inset 0 1px rgba(255,255,255,.99),
    inset 0 -1px rgba(139,84,4,.035) !important;
}
.tos-settings-overview-v1 .tos-settings-overview-stats > .tos-premium-stat > .flex > div:first-child > div:first-child {
  font-size: 1.48rem !important;
  font-weight: 900 !important;
  color: #1d160d !important;
}
.tos-settings-overview-v1 .tos-settings-overview-stats > .tos-premium-stat > .flex > div:first-child > div:nth-child(2) {
  color: #2f2a22 !important;
  font-weight: 800 !important;
}
.tos-settings-overview-v1 .tos-settings-overview-stats > .tos-premium-stat > .flex > div:first-child > div:nth-child(3) {
  color: #8c8173 !important;
}
.tos-settings-overview-v1 .tos-settings-overview-stats > .tos-premium-stat > .flex > div:last-child {
  border-color: rgba(177,114,12,.18) !important;
  box-shadow:
    0 10px 24px rgba(78,48,4,.10),
    0 0 0 1px rgba(255,255,255,.72) inset,
    0 0 22px rgba(214,160,50,.06) !important;
}

/* Cards: stronger wave layer, edge hardware and depth */
.tos-settings-overview-v1 .tos-settings-section-card {
  border-color: rgba(183,119,15,.34) !important;
  background:
    radial-gradient(122% 88% at 88% 124%,
      transparent 0 40.8%, rgba(200,130,16,.16) 41.05% 41.30%, transparent 41.58% 44.1%,
      rgba(200,130,16,.10) 44.35% 44.58%, transparent 44.85% 47.45%,
      rgba(200,130,16,.060) 47.68% 47.89%, transparent 48.15% 100%),
    radial-gradient(circle at 87% 9%, rgba(239,202,118,.14), transparent 26%),
    linear-gradient(145deg,#fff 0%,#fffdf8 57%,#f9edd7 100%) !important;
  box-shadow:
    0 17px 35px rgba(75,47,3,.085),
    0 2px 0 rgba(255,255,255,.99) inset,
    0 -1px 0 rgba(143,87,4,.05) inset !important;
}
.tos-settings-overview-v1 .tos-settings-section-card::before {
  width: 2px !important;
  background: linear-gradient(180deg,#ffd979 0%,#d4941c 46%,#a95f00 100%) !important;
  box-shadow: 0 0 18px rgba(217,158,40,.22) !important;
}
.tos-settings-overview-v1 .tos-settings-section-card::after {
  border-color: rgba(177,113,13,.20) !important;
  background: linear-gradient(180deg,rgba(255,255,255,.96),rgba(248,235,203,.92)) !important;
  box-shadow: 0 7px 17px rgba(83,51,2,.075), inset 0 1px rgba(255,255,255,.96) !important;
}
.tos-settings-overview-v1 .tos-settings-section-card:hover {
  border-color: rgba(192,127,17,.50) !important;
  box-shadow:
    0 24px 46px rgba(83,51,3,.12),
    0 0 24px rgba(216,158,39,.045),
    inset 0 1px rgba(255,255,255,.99) !important;
}

/* Jewel orb icons: tighter, brighter rings */
.tos-settings-overview-v1 .tos-settings-section-icon {
  border-color: rgba(255,255,255,.72) !important;
  box-shadow:
    0 10px 22px rgba(68,42,5,.10),
    0 0 0 1px rgba(148,93,8,.10),
    inset 0 1px rgba(255,255,255,.94) !important;
}

/* Metallic action: reference is satin metal, not mirror chrome */
.tos-settings-overview-v1 .tos-settings-section-open {
  min-height: 42px !important;
  border-color: #b9780d !important;
  background:
    linear-gradient(180deg,#fff1ba 0%,#f0cd69 24%,#dda72e 58%,#bd7810 100%) !important;
  box-shadow:
    0 9px 18px rgba(119,71,3,.17),
    inset 0 1px rgba(255,255,255,.82),
    inset 0 -2px rgba(92,51,0,.13),
    0 0 0 1px rgba(255,232,151,.28) !important;
}
.tos-settings-overview-v1 .tos-settings-section-open::before {
  inset: 2px 9% auto !important;
  height: 24% !important;
  opacity: .56 !important;
  background: linear-gradient(180deg,rgba(255,255,255,.50),rgba(255,255,255,0)) !important;
}
.tos-settings-overview-v1 .tos-settings-section-open:hover {
  background: linear-gradient(180deg,#ffefb1 0%,#ebc45a 24%,#d39721 59%,#ad6906 100%) !important;
  box-shadow: 0 12px 24px rgba(121,72,3,.22), inset 0 1px rgba(255,255,255,.78) !important;
}

/* =========================================================
   DARK — stronger luminous-gold wave, deeper black titanium
   ========================================================= */
.dark .tos-settings-flagship-v1.tos-page {
  background:
    radial-gradient(circle at 9% -1%, rgba(232,177,62,.085), transparent 29%),
    radial-gradient(circle at 91% 100%, rgba(225,163,43,.06), transparent 31%),
    linear-gradient(180deg,#07090b 0%,#030506 100%) !important;
}

.dark .tos-settings-flagship-v1 .tos-settings-flagship-header {
  border-color: rgba(239,188,73,.56) !important;
  background:
    radial-gradient(123% 108% at 73% 137%,
      transparent 0 35.8%, rgba(255,205,87,.44) 36.08% 36.34%, transparent 36.62% 39.20%,
      rgba(255,197,62,.30) 39.48% 39.72%, transparent 40.0% 42.7%,
      rgba(255,191,48,.18) 42.98% 43.21%, transparent 43.48% 46.2%,
      rgba(255,185,38,.095) 46.47% 46.67%, transparent 46.95% 100%),
    radial-gradient(circle at 77% 55%, rgba(237,172,38,.18), transparent 27%),
    linear-gradient(132deg,#091014 0%,#0f1519 51%,#120d05 100%) !important;
  box-shadow:
    0 30px 62px rgba(0,0,0,.42),
    0 0 42px rgba(222,157,24,.10),
    inset 0 1px rgba(255,255,255,.045) !important;
}

.dark .tos-settings-overview-v1 .tos-settings-overview-hero {
  border-color: rgba(237,186,72,.38) !important;
  background:
    radial-gradient(112% 90% at 92% 112%,
      transparent 0 41.5%, rgba(250,190,61,.20) 41.78% 42.04%, transparent 42.34% 45.05%,
      rgba(250,190,61,.12) 45.31% 45.56%, transparent 45.84% 48.65%,
      rgba(250,190,61,.065) 48.90% 49.11%, transparent 49.38% 100%),
    radial-gradient(circle at 90% 17%, rgba(228,164,35,.09), transparent 27%),
    linear-gradient(145deg,#0d1519 0%,#080d10 70%,#130d05 100%) !important;
  box-shadow:
    0 26px 54px rgba(0,0,0,.38),
    0 0 30px rgba(221,158,31,.055),
    inset 0 1px rgba(255,255,255,.03) !important;
}

.dark .tos-settings-overview-v1 .tos-settings-overview-stats > .tos-premium-stat {
  border-color: rgba(235,183,68,.34) !important;
  background:
    radial-gradient(circle at 87% 10%,rgba(234,177,59,.105),transparent 26%),
    linear-gradient(155deg,#12191d 0%,#090f12 100%) !important;
  box-shadow:
    0 16px 32px rgba(0,0,0,.34),
    0 0 22px rgba(226,163,35,.04),
    inset 0 1px rgba(255,255,255,.03) !important;
}
.dark .tos-settings-overview-v1 .tos-settings-overview-stats > .tos-premium-stat > .flex > div:first-child > div:first-child {
  color:#fff3d7 !important;
  text-shadow: 0 0 18px rgba(239,188,76,.10);
}

.dark .tos-settings-overview-v1 .tos-settings-section-card {
  border-color: rgba(239,185,67,.48) !important;
  background:
    radial-gradient(122% 89% at 89% 124%,
      transparent 0 39.7%, rgba(255,195,59,.28) 40.0% 40.27%, transparent 40.57% 43.0%,
      rgba(255,191,49,.17) 43.27% 43.52%, transparent 43.82% 46.35%,
      rgba(255,187,43,.095) 46.60% 46.82%, transparent 47.10% 100%),
    radial-gradient(circle at 86% 12%,rgba(233,175,55,.085),transparent 27%),
    linear-gradient(145deg,#10181c 0%,#080e11 63%,#130d05 100%) !important;
  box-shadow:
    0 21px 42px rgba(0,0,0,.38),
    0 0 34px rgba(224,160,28,.065),
    inset 0 1px rgba(255,255,255,.03),
    inset 0 -1px rgba(255,198,74,.035) !important;
}
.dark .tos-settings-overview-v1 .tos-settings-section-card::before {
  background: linear-gradient(180deg,#ffe08b 0%,#f0b13a 43%,#a95f00 100%) !important;
  box-shadow: 0 0 22px rgba(255,190,54,.34) !important;
}
.dark .tos-settings-overview-v1 .tos-settings-section-card::after {
  border-color: rgba(239,187,71,.32) !important;
  background: linear-gradient(180deg,rgba(53,45,25,.90),rgba(25,23,19,.92)) !important;
  color: #f0c55e !important;
  box-shadow: 0 8px 20px rgba(0,0,0,.30), inset 0 1px rgba(255,238,187,.055) !important;
}
.dark .tos-settings-overview-v1 .tos-settings-section-card:hover {
  border-color: rgba(249,201,86,.72) !important;
  box-shadow:
    0 27px 54px rgba(0,0,0,.45),
    0 0 38px rgba(231,169,38,.11),
    inset 0 1px rgba(255,255,255,.035) !important;
}
.dark .tos-settings-overview-v1 .tos-settings-section-icon {
  border-color: rgba(255,235,186,.20) !important;
  box-shadow:
    0 10px 25px rgba(0,0,0,.34),
    0 0 26px currentColor,
    inset 0 1px rgba(255,255,255,.07) !important;
}

.dark .tos-settings-overview-v1 .tos-settings-section-open {
  border-color: #d7971f !important;
  background:
    linear-gradient(180deg,#ffec9c 0%,#edbd4d 23%,#d19013 58%,#9e5500 100%) !important;
  box-shadow:
    0 11px 24px rgba(0,0,0,.34),
    0 0 18px rgba(237,173,45,.12),
    inset 0 1px rgba(255,255,255,.74),
    inset 0 -2px rgba(64,33,0,.22) !important;
}
.dark .tos-settings-overview-v1 .tos-settings-section-open::before {
  height: 22% !important;
  opacity: .44 !important;
}
.dark .tos-settings-overview-v1 .tos-settings-section-open:hover {
  background: linear-gradient(180deg,#ffe88c 0%,#eab63d 24%,#c67f09 60%,#864300 100%) !important;
  box-shadow: 0 14px 28px rgba(0,0,0,.41),0 0 24px rgba(238,177,49,.17),inset 0 1px rgba(255,255,255,.72) !important;
}

@media (max-width: 767px) {
  .tos-settings-overview-v1 .tos-settings-overview-stats > .tos-premium-stat { min-height: 112px !important; }
  .tos-settings-overview-v1 .tos-settings-section-card { min-height: 178px !important; }
}
'''


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


if not PAGE.exists():
    fail(f"Settings page missing: {PAGE}")
if not V2_STYLE.exists():
    fail(f"Settings Overview V2 Reference style missing: {V2_STYLE}")
if V21_STYLE.exists():
    fail("Settings Overview V2.1 Fidelity Polish style already exists")

page_text = PAGE.read_text()
v2_text = V2_STYLE.read_text()

required_page_markers = [
    V2_IMPORT,
    "tos-settings-flagship-v1",
    "tos-settings-overview-v1",
    "tos-settings-overview-stats",
    "tos-settings-section-card",
    "tos-settings-section-open",
]
for marker in required_page_markers:
    if marker not in page_text:
        fail(f"required V2 page marker missing: {marker}")

if V2_RUNTIME not in v2_text:
    fail("required V2 reference runtime marker missing")
if V21_IMPORT in page_text:
    fail("Settings Overview V2.1 Fidelity Polish import already present")

stamp = int(time.time())
page_backup = PAGE.with_name(f"{PAGE.name}.v2-1-fidelity-backup-{stamp}")
shutil.copy2(PAGE, page_backup)
live_backup = None
staging = None

try:
    page_text = page_text.replace(V2_IMPORT, V2_IMPORT + "\n" + V21_IMPORT, 1)
    if V21_IMPORT not in page_text:
        fail("V2.1 import injection failed")

    PAGE.write_text(page_text)
    V21_STYLE.write_text(CSS)

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists():
        fail("frontend dist missing after build")

    built_css = ""
    for css_file in DIST.rglob("*.css"):
        built_css += css_file.read_text(errors="ignore")
    if V21_RUNTIME not in built_css:
        fail("V2.1 runtime marker missing from built CSS")

    LIVE_PARENT.mkdir(parents=True, exist_ok=True)
    staging = LIVE_PARENT / f"build.settings-overview-v2-1-fidelity-staging-{stamp}"
    live_backup = LIVE_PARENT / f"build.settings-overview-v2-1-fidelity-backup-{stamp}"
    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(DIST, staging)

    if LIVE.exists():
        LIVE.rename(live_backup)
    staging.rename(LIVE)

    live_css = ""
    for css_file in LIVE.rglob("*.css"):
        live_css += css_file.read_text(errors="ignore")
    if V21_RUNTIME not in live_css:
        fail("V2.1 runtime marker missing from live build")

    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("SETTINGS_OVERVIEW_FLAGSHIP_V2_1_RUNTIME=YES")
    print("SETTINGS_V2_REFERENCE_BASELINE=PRESERVED")
    print("SETTINGS_V21_SCOPE=REFERENCE_FIDELITY_POLISH_ONLY")
    print("SETTINGS_LIGHT_WAVES=STRONGER_CHAMPAGNE_FLOW")
    print("SETTINGS_DARK_WAVES=LUMINOUS_GOLD_HIGHER_FIDELITY")
    print("SETTINGS_CARD_DEPTH=ENHANCED")
    print("SETTINGS_GOLD_EDGES=ENHANCED")
    print("SETTINGS_KPI_HIERARCHY=ENHANCED")
    print("SETTINGS_ACTION_BUTTONS=SATIN_METALLIC_GOLD")
    print("SETTINGS_JEWEL_ICONS=ENHANCED")
    print("SETTINGS_LOGIC_CHANGED=NO")
    print("SETTINGS_API_CHANGED=NO")
    print("SETTINGS_PERMISSIONS_CHANGED=NO")
    print("SETTINGS_NAVIGATION_CHANGED=NO")
    print("SETTINGS_SAVE_LOGIC_CHANGED=NO")
    print("SETTINGS_INTEGRATIONS_CHANGED=NO")
    print("TWS_CHANGED=NO")
    print("SLA_CHANGED=NO")
    print("RAMZY_LOGIC_CHANGED=NO")
    print("TCS_CHANGED=NO")
    print(f"LIVE_BACKUP={live_backup if live_backup and live_backup.exists() else 'NONE'}")
    print("STATUS=READY")
except Exception as exc:
    try:
        if page_backup.exists():
            shutil.copy2(page_backup, PAGE)
        if V21_STYLE.exists():
            V21_STYLE.unlink()
        if LIVE.exists() and live_backup and live_backup.exists():
            shutil.rmtree(LIVE)
            live_backup.rename(LIVE)
        elif live_backup and live_backup.exists() and not LIVE.exists():
            live_backup.rename(LIVE)
        if staging and staging.exists():
            shutil.rmtree(staging)
    except Exception:
        pass
    print("PASS/FAIL=FAIL")
    print(f"ERROR={exc}")
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("STATUS=STOPPED")
    raise SystemExit(1)
