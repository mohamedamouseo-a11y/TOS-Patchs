from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
PAGE = FRONTEND / "src/pages/SettingsPage.jsx"
STYLE = FRONTEND / "src/pages/settingsOverviewFlagshipV1.css"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_PAGE_GIT_BLOB = "666a54257a53d971da8eb3cfce824adc24de2c65"
IMPORT_ANCHOR = 'import { DatabaseBackupAdmin } from "../components/settings/DatabaseBackupAdmin";'
IMPORT_STYLE = 'import "./settingsOverviewFlagshipV1.css";'

CSS = r'''
:root { --tos-settings-overview-flagship-v1-runtime: 1; }

.tos-settings-flagship-v1 {
  position: relative;
  isolation: isolate;
}

.tos-settings-flagship-v1 .tos-settings-flagship-header {
  position: relative;
  overflow: hidden;
  isolation: isolate;
  min-height: 180px;
  padding: 30px 34px !important;
  border: 1px solid rgba(182, 122, 21, .18) !important;
  border-radius: 32px !important;
  background:
    radial-gradient(circle at 88% 2%, rgba(241, 207, 132, .28), transparent 30%),
    radial-gradient(circle at 8% 115%, rgba(229, 188, 93, .11), transparent 38%),
    linear-gradient(135deg, #fffdf8 0%, #faf2e2 50%, #f6ead4 100%) !important;
  box-shadow: 0 24px 60px rgba(91, 58, 8, .09), inset 0 1px rgba(255,255,255,.96) !important;
}
.tos-settings-flagship-v1 .tos-settings-flagship-header::before {
  content: "";
  position: absolute;
  inset: 0;
  z-index: -2;
  background:
    linear-gradient(115deg, transparent 0 52%, rgba(171,111,14,.055) 52.2% 52.45%, transparent 52.7% 100%),
    repeating-linear-gradient(90deg, transparent 0 74px, rgba(167,112,24,.035) 75px, transparent 76px);
  opacity: .75;
}
.tos-settings-flagship-v1 .tos-settings-flagship-header::after {
  content: "";
  position: absolute;
  width: 260px;
  height: 260px;
  border-radius: 50%;
  inset-inline-end: -86px;
  top: -126px;
  z-index: -1;
  border: 1px solid rgba(181,119,17,.12);
  box-shadow: 0 0 0 28px rgba(181,119,17,.025), 0 0 0 58px rgba(181,119,17,.018);
}
.tos-settings-flagship-v1 .tos-settings-flagship-header > div { position: relative; z-index: 2; }
.tos-settings-flagship-v1 .tos-settings-flagship-header > div > div:first-child {
  border-color: rgba(174,111,13,.22) !important;
  color: #8d5f10 !important;
  background: linear-gradient(180deg, rgba(255,252,241,.96), rgba(246,226,179,.90)) !important;
  box-shadow: inset 0 1px rgba(255,255,255,.9), 0 7px 18px rgba(101,64,7,.06);
  letter-spacing: .08em;
  text-transform: uppercase;
}
.tos-settings-flagship-v1 .tos-settings-flagship-header h1 {
  font-family: Georgia, "Times New Roman", serif;
  font-size: clamp(2rem, 3vw, 3.05rem) !important;
  line-height: 1.03;
  color: #21190f !important;
  letter-spacing: -.035em;
  text-wrap: balance;
}
.tos-settings-flagship-v1 .tos-settings-flagship-header p {
  max-width: 760px !important;
  color: #756b5e !important;
  font-weight: 720;
}

.tos-settings-overview-v1 { position: relative; }
.tos-settings-overview-v1 .tos-settings-overview-hero {
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(171,111,15,.14) !important;
  border-radius: 30px !important;
  background:
    radial-gradient(circle at 100% 0%, rgba(237,199,111,.17), transparent 29%),
    linear-gradient(145deg, rgba(255,255,255,.98), rgba(253,248,237,.98)) !important;
  box-shadow: 0 18px 42px rgba(77,48,3,.065), inset 0 1px rgba(255,255,255,.98) !important;
}
.tos-settings-overview-v1 .tos-settings-overview-hero::after {
  content: "SYSTEM CONTROL";
  position: absolute;
  inset-inline-end: 28px;
  bottom: 20px;
  color: rgba(143,91,9,.055);
  font-size: clamp(34px, 5vw, 74px);
  font-weight: 950;
  letter-spacing: -.06em;
  pointer-events: none;
}
.tos-settings-overview-v1 .tos-settings-overview-hero .tos-kicker {
  color: #a06b10 !important;
  letter-spacing: .13em;
  text-transform: uppercase;
}
.tos-settings-overview-v1 .tos-settings-overview-hero h3 {
  font-family: Georgia, "Times New Roman", serif;
  font-size: clamp(1.65rem, 2.3vw, 2.35rem) !important;
  letter-spacing: -.025em;
  color: #241b10 !important;
}
.tos-settings-overview-v1 .tos-settings-overview-hero > div:first-child > div:last-child {
  border: 1px solid rgba(37,133,84,.12);
  box-shadow: inset 0 1px rgba(255,255,255,.82);
}

.tos-settings-overview-v1 .tos-settings-overview-stats > * {
  position: relative;
  overflow: hidden;
  border-color: rgba(160,104,13,.12) !important;
  background: linear-gradient(180deg, rgba(255,255,255,.94), rgba(250,245,235,.92)) !important;
  box-shadow: 0 10px 24px rgba(77,49,6,.045), inset 0 1px rgba(255,255,255,.96);
}
.tos-settings-overview-v1 .tos-settings-overview-stats > *::before {
  content: "";
  position: absolute;
  inset-block: 12px;
  inset-inline-start: 0;
  width: 3px;
  border-radius: 999px;
  background: linear-gradient(180deg,#e5bd5c,#a96d11);
}

.tos-settings-overview-v1 .tos-settings-section-grid { align-items: stretch; }
.tos-settings-overview-v1 .tos-settings-section-card {
  position: relative;
  overflow: hidden;
  min-height: 214px;
  border: 1px solid rgba(160,103,12,.12) !important;
  border-radius: 26px !important;
  background:
    radial-gradient(circle at 100% 0%, rgba(234,195,108,.11), transparent 30%),
    linear-gradient(150deg, #fffefa 0%, #fbf6ec 100%) !important;
  box-shadow: 0 14px 34px rgba(69,43,4,.055), inset 0 1px rgba(255,255,255,.98) !important;
  transition: transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease !important;
}
.tos-settings-overview-v1 .tos-settings-section-card::before {
  content: "";
  position: absolute;
  inset-inline-start: 0;
  top: 22px;
  bottom: 22px;
  width: 3px;
  border-radius: 999px;
  background: linear-gradient(180deg, rgba(224,181,80,.95), rgba(155,94,9,.8));
}
.tos-settings-overview-v1 .tos-settings-section-card:hover {
  transform: translateY(-3px);
  border-color: rgba(172,111,14,.28) !important;
  box-shadow: 0 24px 48px rgba(75,46,3,.10), inset 0 1px rgba(255,255,255,.98) !important;
}
.tos-settings-overview-v1 .tos-settings-section-card h4 {
  font-size: 1.03rem !important;
  color: #2b2115 !important;
  letter-spacing: -.012em;
}
.tos-settings-overview-v1 .tos-settings-section-card .tos-muted { color: #83786a !important; line-height: 1.65; }
.tos-settings-overview-v1 .tos-settings-section-icon {
  border: 1px solid rgba(161,104,12,.12);
  color: #9a6510 !important;
  background: linear-gradient(145deg,#fff7dc,#ecd08a) !important;
  box-shadow: 0 8px 19px rgba(116,73,5,.10), inset 0 1px rgba(255,255,255,.72);
}
.tos-settings-overview-v1 .tos-settings-section-card:nth-child(1) .tos-settings-section-icon { color:#6f55a8 !important; background:linear-gradient(145deg,#f6f0ff,#dcccf7) !important; }
.tos-settings-overview-v1 .tos-settings-section-card:nth-child(2) .tos-settings-section-icon { color:#14805d !important; background:linear-gradient(145deg,#ecfff7,#c9efdf) !important; }
.tos-settings-overview-v1 .tos-settings-section-card:nth-child(3) .tos-settings-section-icon { color:#356ca3 !important; background:linear-gradient(145deg,#eff7ff,#d5e7f8) !important; }
.tos-settings-overview-v1 .tos-settings-section-card:nth-child(4) .tos-settings-section-icon { color:#287c89 !important; background:linear-gradient(145deg,#edfbfd,#ceeef1) !important; }
.tos-settings-overview-v1 .tos-settings-section-card:nth-child(5) .tos-settings-section-icon { color:#9b5a63 !important; background:linear-gradient(145deg,#fff2f3,#f2d7da) !important; }
.tos-settings-overview-v1 .tos-settings-section-card:nth-child(6) .tos-settings-section-icon { color:#996710 !important; background:linear-gradient(145deg,#fff8e2,#efd59c) !important; }
.tos-settings-overview-v1 .tos-settings-section-card:nth-child(7) .tos-settings-section-icon { color:#4f6071 !important; background:linear-gradient(145deg,#f5f7f9,#dce2e7) !important; }
.tos-settings-overview-v1 .tos-settings-section-card:nth-child(8) .tos-settings-section-icon { color:#a25e14 !important; background:linear-gradient(145deg,#fff5e9,#f0d5b1) !important; }
.tos-settings-overview-v1 .tos-settings-section-card:nth-child(9) .tos-settings-section-icon { color:#8d5686 !important; background:linear-gradient(145deg,#fff2fb,#ecd3e8) !important; }
.tos-settings-overview-v1 .tos-settings-section-card:nth-child(10) .tos-settings-section-icon { color:#526ab5 !important; background:linear-gradient(145deg,#f1f4ff,#d7def7) !important; }

.tos-settings-overview-v1 .tos-settings-section-open {
  min-height: 42px;
  border: 1px solid rgba(161,103,11,.20) !important;
  color: #5b3b08 !important;
  background: linear-gradient(180deg,#fff8df 0%,#e9c66e 58%,#cf9b2d 100%) !important;
  box-shadow: 0 10px 20px rgba(127,77,3,.11), inset 0 1px rgba(255,255,255,.72) !important;
}
.tos-settings-overview-v1 .tos-settings-section-open:hover {
  border-color: rgba(137,84,5,.30) !important;
  background: linear-gradient(180deg,#fff3c9 0%,#e2b852 56%,#bf861a 100%) !important;
  transform: translateY(-1px);
}

.dark .tos-settings-flagship-v1 .tos-settings-flagship-header {
  border-color: rgba(222,176,74,.16) !important;
  background:
    radial-gradient(circle at 88% 0%, rgba(219,166,57,.17), transparent 30%),
    radial-gradient(circle at 10% 120%, rgba(99,119,129,.13), transparent 38%),
    linear-gradient(135deg,#121517 0%,#191d1f 52%,#111416 100%) !important;
  box-shadow: 0 28px 64px rgba(0,0,0,.32), inset 0 1px rgba(255,255,255,.035) !important;
}
.dark .tos-settings-flagship-v1 .tos-settings-flagship-header::before {
  background:
    linear-gradient(115deg, transparent 0 52%, rgba(225,177,72,.055) 52.2% 52.45%, transparent 52.7% 100%),
    repeating-linear-gradient(90deg, transparent 0 74px, rgba(229,185,87,.025) 75px, transparent 76px);
}
.dark .tos-settings-flagship-v1 .tos-settings-flagship-header > div > div:first-child {
  border-color: rgba(222,176,74,.18) !important;
  color: #e4bd60 !important;
  background: linear-gradient(180deg,rgba(42,38,28,.95),rgba(30,28,23,.95)) !important;
}
.dark .tos-settings-flagship-v1 .tos-settings-flagship-header h1 { color:#f5efe5 !important; }
.dark .tos-settings-flagship-v1 .tos-settings-flagship-header p { color:#aaa298 !important; }

.dark .tos-settings-overview-v1 .tos-settings-overview-hero {
  border-color: rgba(222,176,74,.12) !important;
  background:
    radial-gradient(circle at 100% 0%, rgba(219,165,55,.10), transparent 29%),
    linear-gradient(145deg,#171a1c 0%,#111416 100%) !important;
  box-shadow: 0 22px 50px rgba(0,0,0,.28), inset 0 1px rgba(255,255,255,.025) !important;
}
.dark .tos-settings-overview-v1 .tos-settings-overview-hero h3 { color:#f3ede4 !important; }
.dark .tos-settings-overview-v1 .tos-settings-overview-hero .tos-muted { color:#958e84 !important; }
.dark .tos-settings-overview-v1 .tos-settings-overview-hero::after { color:rgba(226,178,73,.035); }
.dark .tos-settings-overview-v1 .tos-settings-overview-stats > * {
  border-color: rgba(222,176,74,.09) !important;
  background: linear-gradient(180deg,#1c2022,#151819) !important;
  box-shadow: inset 0 1px rgba(255,255,255,.024), 0 10px 24px rgba(0,0,0,.14);
}
.dark .tos-settings-overview-v1 .tos-settings-section-card {
  border-color: rgba(222,176,74,.09) !important;
  background:
    radial-gradient(circle at 100% 0%, rgba(222,176,74,.055), transparent 30%),
    linear-gradient(150deg,#1a1d1f,#121516) !important;
  box-shadow: 0 18px 38px rgba(0,0,0,.22), inset 0 1px rgba(255,255,255,.022) !important;
}
.dark .tos-settings-overview-v1 .tos-settings-section-card:hover {
  border-color: rgba(222,176,74,.20) !important;
  box-shadow: 0 25px 50px rgba(0,0,0,.32), inset 0 1px rgba(255,255,255,.03) !important;
}
.dark .tos-settings-overview-v1 .tos-settings-section-card h4 { color:#eee7dd !important; }
.dark .tos-settings-overview-v1 .tos-settings-section-card .tos-muted { color:#8e887f !important; }
.dark .tos-settings-overview-v1 .tos-settings-section-icon {
  border-color: rgba(222,176,74,.10) !important;
  color:#dfb44f !important;
  background: linear-gradient(145deg,#28251d,#1b1b18) !important;
  box-shadow: inset 0 1px rgba(255,255,255,.035), 0 8px 18px rgba(0,0,0,.16);
}
.dark .tos-settings-overview-v1 .tos-settings-section-open {
  border-color: rgba(229,185,84,.18) !important;
  color:#241600 !important;
  background: linear-gradient(180deg,#efd275,#d5a02c 60%,#b97c12) !important;
  box-shadow: 0 10px 22px rgba(179,112,6,.16), inset 0 1px rgba(255,255,255,.32) !important;
}

@media (max-width: 760px) {
  .tos-settings-flagship-v1 .tos-settings-flagship-header {
    min-height: 0;
    padding: 22px 20px !important;
    border-radius: 26px !important;
  }
  .tos-settings-overview-v1 .tos-settings-section-card { min-height: 190px; }
  .tos-settings-overview-v1 .tos-settings-overview-hero::after { display:none; }
}
'''


def fail(message):
    print("PASS/FAIL=FAIL")
    print(f"ERROR={message}")
    print("STATUS=STOPPED")
    raise SystemExit(1)


def run(cmd, cwd=None):
    result = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    if result.stdout:
        print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
    if result.returncode != 0:
        if result.stderr:
            print(result.stderr)
        raise RuntimeError("command failed: " + " ".join(cmd))
    return result


def git_blob_sha(data):
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data).hexdigest()


print("RUNNING=TOS_UXUI_SYSTEM_SETTINGS_OVERVIEW_FLAGSHIP_V1")

if not PAGE.exists():
    fail("SettingsPage.jsx missing")
if STYLE.exists():
    fail("settingsOverviewFlagshipV1.css already exists; refusing repeated/unknown state")

page_bytes = PAGE.read_bytes()
page_blob = git_blob_sha(page_bytes)
if page_blob != EXPECTED_PAGE_GIT_BLOB:
    fail(f"SettingsPage baseline mismatch: expected={EXPECTED_PAGE_GIT_BLOB} actual={page_blob}")

source = page_bytes.decode("utf-8")
required_markers = [
    IMPORT_ANCHOR,
    "function SettingsSectionHeader({ section })",
    "function SettingsOverview({ onSelect, user })",
    'className="mt-5 grid gap-4 md:grid-cols-4"',
    'className="grid gap-4 md:grid-cols-2 xl:grid-cols-3"',
    '<Card key={section.key} hover>',
    'className={`tos-page space-y-5 ${activeSection === "github" ? ',
]
for marker in required_markers:
    if marker not in source:
        fail(f"required Settings baseline marker missing: {marker}")

page_backup = PAGE.with_suffix(PAGE.suffix + f".settings-flagship-v1-backup-{int(time.time())}")
shutil.copy2(PAGE, page_backup)

try:
    source = source.replace(IMPORT_ANCHOR, IMPORT_ANCHOR + "\n" + IMPORT_STYLE, 1)

    source = source.replace(
        '<header className="flex flex-col gap-4 rounded-[30px]',
        '<header className="tos-settings-flagship-header flex flex-col gap-4 rounded-[30px]',
        1,
    )

    overview_index = source.index("function SettingsOverview({ onSelect, user })")
    before = source[:overview_index]
    overview = source[overview_index:]
    replacements = [
        ('<div className="space-y-5">', '<div className="tos-settings-overview-v1 space-y-5">', 1),
        ('<Card>', '<Card className="tos-settings-overview-hero">', 1),
        ('className="mt-5 grid gap-4 md:grid-cols-4"', 'className="tos-settings-overview-stats mt-5 grid gap-4 md:grid-cols-4"', 1),
        ('className="grid gap-4 md:grid-cols-2 xl:grid-cols-3"', 'className="tos-settings-section-grid grid gap-4 md:grid-cols-2 xl:grid-cols-3"', 1),
        ('<Card key={section.key} hover>', '<Card key={section.key} hover className="tos-settings-section-card">', 1),
        ('className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-zinc-50 text-zinc-600 dark:bg-white/5 dark:text-zinc-300"', 'className="tos-settings-section-icon grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-zinc-50 text-zinc-600 dark:bg-white/5 dark:text-zinc-300"', 1),
        ('className="justify-center">{en ? "Open section" : "فتح القسم"}</Button>', 'className="tos-settings-section-open justify-center">{en ? "Open section" : "فتح القسم"}</Button>', 1),
    ]
    for old, new, count in replacements:
        if old not in overview:
            fail(f"overview replacement marker missing: {old[:80]}")
        overview = overview.replace(old, new, count)
    source = before + overview

    root_old = 'className={`tos-page space-y-5 ${activeSection === "github" ? '
    root_new = 'className={`tos-settings-flagship-v1 tos-page space-y-5 ${activeSection === "github" ? '
    source = source.replace(root_old, root_new, 1)

    runtime_markers = [
        IMPORT_STYLE,
        "tos-settings-flagship-v1",
        "tos-settings-flagship-header",
        "tos-settings-overview-v1",
        "tos-settings-overview-hero",
        "tos-settings-section-card",
        "tos-settings-section-open",
    ]
    for marker in runtime_markers:
        if marker not in source:
            fail(f"post-transform runtime marker missing: {marker}")

    PAGE.write_text(source)
    STYLE.write_text(CSS)

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists():
        raise RuntimeError("frontend dist missing after build")

    built_css = ""
    for css_file in DIST.rglob("*.css"):
        built_css += css_file.read_text(errors="ignore")
    if "--tos-settings-overview-flagship-v1-runtime" not in built_css:
        raise RuntimeError("Settings flagship V1 CSS runtime marker missing from build")

    LIVE_PARENT.mkdir(parents=True, exist_ok=True)
    stamp = int(time.time())
    staging = LIVE_PARENT / f"build.settings-overview-v1-staging-{stamp}"
    live_backup = LIVE_PARENT / f"build.settings-overview-v1-backup-{stamp}"
    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(DIST, staging)
    if LIVE.exists():
        LIVE.rename(live_backup)
    staging.rename(LIVE)

    live_css = ""
    for css_file in LIVE.rglob("*.css"):
        live_css += css_file.read_text(errors="ignore")
    if "--tos-settings-overview-flagship-v1-runtime" not in live_css:
        raise RuntimeError("Settings flagship V1 marker missing from live build after deploy")

    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("SETTINGS_OVERVIEW_FLAGSHIP_V1_RUNTIME=YES")
    print("SETTINGS_SCOPE=OVERVIEW_AND_SHARED_HEADER_VISUAL_ONLY")
    print("SETTINGS_LIGHT_MODE=PEARL_IVORY_CHAMPAGNE")
    print("SETTINGS_DARK_MODE=OBSIDIAN_TITANIUM_CHAMPAGNE")
    print("SETTINGS_HEADER=EXECUTIVE_SYSTEM_CONTROL_HERO")
    print("SETTINGS_OVERVIEW_KPIS=EXECUTIVE_LUXURY")
    print("SETTINGS_SECTION_CARDS=PREMIUM_COMMAND_CARDS")
    print("SETTINGS_SECTION_ICONS=JEWEL_TONED")
    print("SETTINGS_SECTION_ACTIONS=METALLIC_CHAMPAGNE")
    print("SETTINGS_NAVIGATION_LOGIC_CHANGED=NO")
    print("SETTINGS_PERMISSIONS_CHANGED=NO")
    print("SETTINGS_API_CHANGED=NO")
    print("SETTINGS_SAVE_LOGIC_CHANGED=NO")
    print("SETTINGS_INTEGRATIONS_CHANGED=NO")
    print("SETTINGS_IDENTITY_LOGIC_CHANGED=NO")
    print("SETTINGS_OPERATIONS_LOGIC_CHANGED=NO")
    print("TWS_CHANGED=NO")
    print("SLA_CHANGED=NO")
    print("RAMZY_LOGIC_CHANGED=NO")
    print("TCS_CHANGED=NO")
    print(f"SETTINGS_PAGE_BASELINE_GIT_BLOB={EXPECTED_PAGE_GIT_BLOB}")
    print(f"LIVE_BACKUP={live_backup if live_backup.exists() else 'NONE'}")
    print("STATUS=READY")
except Exception as exc:
    try:
        if page_backup.exists():
            shutil.copy2(page_backup, PAGE)
        if STYLE.exists():
            STYLE.unlink()
    except Exception:
        pass
    print("PASS/FAIL=FAIL")
    print(f"ERROR={exc}")
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("STATUS=STOPPED")
    raise SystemExit(1)
