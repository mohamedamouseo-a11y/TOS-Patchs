from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
PAGE = FRONTEND / "src/pages/SettingsPage.jsx"
STYLE = FRONTEND / "src/pages/smtpSettingsFlagshipLuxuryV1.css"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_PAGE_GIT_BLOB = "5d60d9802b5c65dfcd14690bea9240f0f2b37ab7"
IMPORT_ANCHOR = 'import "./settingsOverviewFlagshipV2_1FidelityPolish.css";'
IMPORT_STYLE = 'import "./smtpSettingsFlagshipLuxuryV1.css";'
ROOT_OLD = '''  return (\n    <Card>\n      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">'''
ROOT_NEW = '''  return (\n    <Card className="tos-smtp-settings-flagship-v1">\n      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">'''
RUNTIME_MARKER = "--tos-smtp-settings-flagship-luxury-v1-runtime"

CSS = r'''
:root { --tos-smtp-settings-flagship-luxury-v1-runtime: 1; }

/* =========================================================
   TOS Settings → SMTP Email — Flagship Luxury V1
   Light: pearl / ivory / champagne + emerald delivery signal
   Dark: obsidian / black titanium / champagne + emerald signal
   Visual only. SMTP API, save, test and permission logic untouched.
   ========================================================= */

.tos-smtp-settings-flagship-v1 {
  position: relative;
  isolation: isolate;
  overflow: hidden;
  padding: 28px !important;
  border: 1px solid rgba(177,116,18,.25) !important;
  border-radius: 30px !important;
  background:
    radial-gradient(118% 102% at 78% 135%,
      transparent 0 40%, rgba(195,127,15,.12) 40.25% 40.52%, transparent 40.8% 43.7%,
      rgba(195,127,15,.072) 43.95% 44.18%, transparent 44.48% 47.5%,
      rgba(195,127,15,.04) 47.75% 47.96%, transparent 48.25% 100%),
    radial-gradient(circle at 92% 2%, rgba(22,157,111,.09), transparent 27%),
    radial-gradient(circle at 98% 15%, rgba(244,210,130,.18), transparent 25%),
    linear-gradient(142deg,#fffefa 0%,#fffaf0 54%,#f7ead5 100%) !important;
  box-shadow:
    0 24px 52px rgba(79,48,4,.09),
    inset 0 1px rgba(255,255,255,.99) !important;
}

.tos-smtp-settings-flagship-v1::before {
  content: "";
  position: absolute;
  inset-block: 24px;
  inset-inline-start: 0;
  width: 3px;
  border-radius: 999px;
  background: linear-gradient(180deg,#f4d171 0%,#c78313 55%,#7a4603 100%);
  box-shadow: 0 0 18px rgba(216,157,39,.18);
  pointer-events: none;
}

.tos-smtp-settings-flagship-v1::after {
  content: "SMTP  •  DELIVERY CONTROL";
  position: absolute;
  top: 24px;
  inset-inline-end: 28px;
  color: rgba(111,76,34,.22);
  font-size: 9px;
  font-weight: 950;
  letter-spacing: .22em;
  text-transform: uppercase;
  pointer-events: none;
}

/* Executive header */
.tos-smtp-settings-flagship-v1 > .flex:first-child {
  position: relative;
  z-index: 1;
  padding-bottom: 22px;
  border-bottom: 1px solid rgba(169,108,13,.11);
}
.tos-smtp-settings-flagship-v1 > .flex:first-child .tos-kicker {
  color: #9a650c !important;
  letter-spacing: .17em;
  text-transform: uppercase;
}
.tos-smtp-settings-flagship-v1 > .flex:first-child h3 {
  margin-top: 6px !important;
  font-family: Georgia,"Times New Roman",serif;
  font-size: clamp(1.9rem,2.7vw,2.55rem) !important;
  letter-spacing: -.035em;
  color: #21190f !important;
}
.tos-smtp-settings-flagship-v1 > .flex:first-child .tos-muted {
  max-width: 760px;
  color: #74695e !important;
  font-weight: 700;
}
.tos-smtp-settings-flagship-v1 > .flex:first-child > div:last-child {
  width: 64px !important;
  height: 64px !important;
  border: 1px solid rgba(21,151,105,.22);
  border-radius: 22px !important;
  background: linear-gradient(145deg,#f0fff8 0%,#d8f5e8 58%,#c6eadb 100%) !important;
  color: #13865f !important;
  box-shadow: 0 12px 28px rgba(18,126,89,.14), inset 0 1px rgba(255,255,255,.92);
}

/* Status KPI hardware */
.tos-smtp-settings-flagship-v1 > div[class*="md:grid-cols-5"] {
  grid-template-columns: repeat(4,minmax(0,1fr)) !important;
  gap: 12px !important;
}
.tos-smtp-settings-flagship-v1 .tos-premium-stat {
  min-height: 126px;
  border: 1px solid rgba(167,108,14,.17) !important;
  border-radius: 20px !important;
  background:
    radial-gradient(circle at 88% 9%,rgba(24,151,108,.075),transparent 26%),
    linear-gradient(155deg,rgba(255,255,255,.98),rgba(252,247,237,.95)) !important;
  box-shadow: 0 12px 28px rgba(72,44,4,.055), inset 0 1px rgba(255,255,255,.98) !important;
  transform: none !important;
}
.tos-smtp-settings-flagship-v1 .tos-premium-stat > .flex > div:first-child > div:first-child {
  font-family: Georgia,"Times New Roman",serif;
  font-size: 1.22rem !important;
  color: #261b0f !important;
  line-height: 1.15;
}
.tos-smtp-settings-flagship-v1 .tos-premium-stat > .flex > div:first-child > div:nth-child(2) {
  color: #383027 !important;
  font-weight: 800 !important;
}
.tos-smtp-settings-flagship-v1 .tos-premium-stat > .flex > div:first-child > div:nth-child(3) {
  color: #8b8175 !important;
}
.tos-smtp-settings-flagship-v1 .tos-premium-stat > .flex > div:last-child {
  width: 43px !important;
  height: 43px !important;
  border-radius: 999px !important;
  box-shadow: 0 8px 20px rgba(69,43,5,.08), inset 0 1px rgba(255,255,255,.86);
}

/* Notices */
.tos-smtp-settings-flagship-v1 .tos-premium-notice {
  border-radius: 16px !important;
  border-color: rgba(190,128,23,.18) !important;
  box-shadow: inset 0 1px rgba(255,255,255,.60), 0 7px 18px rgba(79,48,4,.04);
}

/* Configuration vault */
.tos-smtp-settings-flagship-v1 > div[class*="md:grid-cols-2"] {
  position: relative;
  padding: 22px;
  border: 1px solid rgba(163,105,15,.14);
  border-radius: 22px;
  background:
    radial-gradient(circle at 94% 6%,rgba(22,151,108,.055),transparent 24%),
    linear-gradient(145deg,rgba(255,255,255,.92),rgba(251,246,236,.88));
  box-shadow: 0 12px 28px rgba(67,41,4,.045), inset 0 1px rgba(255,255,255,.96);
}
.tos-smtp-settings-flagship-v1 > div[class*="md:grid-cols-2"]::before {
  content: "SECURE SMTP CONFIGURATION";
  position: absolute;
  top: 8px;
  inset-inline-end: 16px;
  color: rgba(36,140,102,.26);
  font-size: 8px;
  font-weight: 950;
  letter-spacing: .16em;
  pointer-events: none;
}

.tos-smtp-settings-flagship-v1 .tos-premium-field,
.tos-smtp-settings-flagship-v1 .tos-input {
  min-height: 47px;
  border: 1px solid rgba(158,103,16,.19) !important;
  border-radius: 15px !important;
  background: linear-gradient(180deg,#fffefa,#fffaf0) !important;
  color: #2a2116 !important;
  box-shadow: inset 0 1px rgba(255,255,255,.98), 0 5px 14px rgba(71,44,4,.035);
  transition: border-color .18s ease,box-shadow .18s ease;
}
.tos-smtp-settings-flagship-v1 .tos-premium-field:focus,
.tos-smtp-settings-flagship-v1 .tos-input:focus {
  border-color: rgba(21,151,105,.58) !important;
  box-shadow: 0 0 0 3px rgba(21,151,105,.10), 0 8px 20px rgba(83,51,3,.055) !important;
}
.tos-smtp-settings-flagship-v1 input[type="checkbox"] {
  accent-color: #bd841b;
}
.tos-smtp-settings-flagship-v1 label {
  color: #4a4035;
}

/* Action hardware */
.tos-smtp-settings-flagship-v1 .tos-premium-button {
  min-height: 42px;
  border-radius: 999px !important;
  padding-inline: 18px !important;
  font-weight: 900 !important;
}
.tos-smtp-settings-flagship-v1 > .mt-5.flex .tos-premium-button:last-child {
  border: 1px solid #b9780d !important;
  color: #241603 !important;
  background: linear-gradient(180deg,#fff1b8 0%,#efca63 23%,#d9a12a 59%,#b8710b 100%) !important;
  box-shadow: 0 10px 22px rgba(115,68,2,.16), inset 0 1px rgba(255,255,255,.82) !important;
}
.tos-smtp-settings-flagship-v1 > .mt-5.flex .tos-premium-button:first-child,
.tos-smtp-settings-flagship-v1 > div[class*="lg:grid-cols"] .tos-premium-button {
  border: 1px solid rgba(22,137,99,.18) !important;
  background: linear-gradient(180deg,#f6fbf8,#e6f3ed) !important;
  color: #26785d !important;
  box-shadow: 0 8px 18px rgba(22,107,80,.07), inset 0 1px rgba(255,255,255,.90) !important;
}
.tos-smtp-settings-flagship-v1 .tos-premium-button:disabled {
  opacity: .58;
  filter: saturate(.72);
}

/* Test delivery row */
.tos-smtp-settings-flagship-v1 > div[class*="lg:grid-cols"] {
  padding: 18px;
  border: 1px solid rgba(23,145,103,.12);
  border-radius: 20px;
  background: linear-gradient(145deg,rgba(239,252,246,.75),rgba(255,252,245,.82));
}

/* =========================================================
   DARK — obsidian / titanium / champagne / emerald signal
   ========================================================= */
.dark .tos-smtp-settings-flagship-v1 {
  border-color: rgba(238,187,72,.42) !important;
  background:
    radial-gradient(118% 102% at 78% 135%,
      transparent 0 39%, rgba(255,200,73,.25) 39.28% 39.56%, transparent 39.88% 42.7%,
      rgba(255,193,55,.14) 42.98% 43.24%, transparent 43.56% 46.5%,
      rgba(255,187,41,.075) 46.78% 47.0%, transparent 47.3% 100%),
    radial-gradient(circle at 90% 3%,rgba(30,181,126,.11),transparent 27%),
    linear-gradient(140deg,#0d1418 0%,#0a1013 62%,#151006 100%) !important;
  box-shadow: 0 28px 60px rgba(0,0,0,.38),0 0 36px rgba(215,154,31,.065),inset 0 1px rgba(255,255,255,.03) !important;
}
.dark .tos-smtp-settings-flagship-v1::before {
  background: linear-gradient(180deg,#ffd56e 0%,#c98510 55%,#7b4300 100%);
  box-shadow: 0 0 19px rgba(246,184,59,.23);
}
.dark .tos-smtp-settings-flagship-v1::after {
  color: rgba(245,215,148,.50);
  text-shadow: 0 0 18px rgba(235,179,63,.10);
}
.dark .tos-smtp-settings-flagship-v1 > .flex:first-child {
  border-bottom-color: rgba(231,182,70,.14);
}
.dark .tos-smtp-settings-flagship-v1 > .flex:first-child .tos-kicker { color:#e9ba4f !important; }
.dark .tos-smtp-settings-flagship-v1 > .flex:first-child h3 { color:#fff5e6 !important; }
.dark .tos-smtp-settings-flagship-v1 > .flex:first-child .tos-muted { color:#a6b0b8 !important; }
.dark .tos-smtp-settings-flagship-v1 > .flex:first-child > div:last-child {
  border-color:rgba(62,211,154,.25);
  background:linear-gradient(145deg,#103126,#0b211a) !important;
  color:#67e4b3 !important;
  box-shadow:0 12px 28px rgba(0,0,0,.30),0 0 22px rgba(54,207,148,.10),inset 0 1px rgba(255,255,255,.045);
}

.dark .tos-smtp-settings-flagship-v1 .tos-premium-stat {
  border-color:rgba(232,182,69,.24) !important;
  background:radial-gradient(circle at 88% 10%,rgba(39,184,132,.07),transparent 26%),linear-gradient(155deg,#151c20,#0c1215) !important;
  box-shadow:0 14px 30px rgba(0,0,0,.29),inset 0 1px rgba(255,255,255,.027) !important;
}
.dark .tos-smtp-settings-flagship-v1 .tos-premium-stat > .flex > div:first-child > div:first-child { color:#fff1d5 !important; }
.dark .tos-smtp-settings-flagship-v1 .tos-premium-stat > .flex > div:first-child > div:nth-child(2) { color:#ece6dc !important; }
.dark .tos-smtp-settings-flagship-v1 .tos-premium-stat > .flex > div:first-child > div:nth-child(3) { color:#909ba4 !important; }

.dark .tos-smtp-settings-flagship-v1 > div[class*="md:grid-cols-2"] {
  border-color:rgba(232,183,72,.22);
  background:radial-gradient(circle at 94% 5%,rgba(38,184,132,.08),transparent 24%),linear-gradient(145deg,#121a1e,#0b1215);
  box-shadow:0 16px 34px rgba(0,0,0,.27),inset 0 1px rgba(255,255,255,.025);
}
.dark .tos-smtp-settings-flagship-v1 > div[class*="md:grid-cols-2"]::before { color:rgba(105,230,184,.38); }
.dark .tos-smtp-settings-flagship-v1 label { color:#e8e1d7 !important; }
.dark .tos-smtp-settings-flagship-v1 .tos-premium-field,
.dark .tos-smtp-settings-flagship-v1 .tos-input {
  border-color:rgba(231,184,77,.24) !important;
  background:linear-gradient(180deg,#151d21,#0d1418) !important;
  color:#f5efe7 !important;
  caret-color:#efc765;
  box-shadow:inset 0 1px rgba(255,255,255,.03),0 7px 18px rgba(0,0,0,.22) !important;
}
.dark .tos-smtp-settings-flagship-v1 .tos-premium-field::placeholder,
.dark .tos-smtp-settings-flagship-v1 .tos-input::placeholder { color:#89959f !important; opacity:1; }
.dark .tos-smtp-settings-flagship-v1 .tos-premium-field:focus,
.dark .tos-smtp-settings-flagship-v1 .tos-input:focus {
  border-color:rgba(74,220,164,.57) !important;
  box-shadow:0 0 0 3px rgba(48,194,141,.11),0 8px 22px rgba(0,0,0,.26) !important;
}

.dark .tos-smtp-settings-flagship-v1 .tos-premium-notice {
  border-color:rgba(234,185,74,.25) !important;
  background:linear-gradient(180deg,rgba(67,48,13,.46),rgba(42,32,15,.50)) !important;
  color:#efcc73 !important;
}

.dark .tos-smtp-settings-flagship-v1 > .mt-5.flex .tos-premium-button:last-child {
  border-color:#d69a25 !important;
  color:#160e03 !important;
  background:linear-gradient(180deg,#fff0ad 0%,#efc052 22%,#d09016 59%,#9d5600 100%) !important;
  box-shadow:0 11px 26px rgba(0,0,0,.34),0 0 18px rgba(234,172,48,.11),inset 0 1px rgba(255,255,255,.80) !important;
}
.dark .tos-smtp-settings-flagship-v1 > .mt-5.flex .tos-premium-button:first-child,
.dark .tos-smtp-settings-flagship-v1 > div[class*="lg:grid-cols"] .tos-premium-button {
  border-color:rgba(62,203,151,.19) !important;
  background:linear-gradient(180deg,#17231f,#101916) !important;
  color:#83d9b8 !important;
  box-shadow:0 8px 20px rgba(0,0,0,.23),inset 0 1px rgba(255,255,255,.025) !important;
}
.dark .tos-smtp-settings-flagship-v1 > div[class*="lg:grid-cols"] {
  border-color:rgba(54,194,143,.17);
  background:linear-gradient(145deg,rgba(11,30,24,.82),rgba(18,21,18,.88));
}

@media (max-width: 1023px) {
  .tos-smtp-settings-flagship-v1 > div[class*="md:grid-cols-5"] {
    grid-template-columns: repeat(2,minmax(0,1fr)) !important;
  }
}
@media (max-width: 767px) {
  .tos-smtp-settings-flagship-v1 { padding:20px !important; border-radius:22px !important; }
  .tos-smtp-settings-flagship-v1::after { display:none; }
  .tos-smtp-settings-flagship-v1 > div[class*="md:grid-cols-5"] { grid-template-columns:1fr !important; }
  .tos-smtp-settings-flagship-v1 > div[class*="md:grid-cols-2"] { padding:17px; border-radius:18px; }
}
'''


def fail(message):
    raise RuntimeError(message)


def git_blob_sha(path: Path):
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


if not PAGE.exists():
    fail(f"Settings page missing: {PAGE}")

page_blob = git_blob_sha(PAGE)
if page_blob != EXPECTED_PAGE_GIT_BLOB:
    fail(f"Settings page baseline mismatch: expected={EXPECTED_PAGE_GIT_BLOB} actual={page_blob}")

source = PAGE.read_text()
required_markers = [
    IMPORT_ANCHOR,
    "function EmailSettingsAdmin({ user })",
    "api.emailSettings.status()",
    "api.emailSettings.update(payload)",
    "api.emailSettings.test({ to: form.testTo.trim() || undefined })",
    "SMTP Email Settings",
    "Save email settings",
    "Test sending",
    ROOT_OLD,
]
for marker in required_markers:
    if marker not in source:
        fail(f"required SMTP Settings baseline marker missing: {marker}")

if IMPORT_STYLE in source or STYLE.exists():
    fail("SMTP Email Settings Flagship Luxury V1 already present")

stamp = int(time.time())
page_backup = PAGE.with_name(f"{PAGE.name}.smtp-settings-v1-backup-{stamp}")
shutil.copy2(PAGE, page_backup)
live_backup = None
staging = None

try:
    source = source.replace(IMPORT_ANCHOR, IMPORT_ANCHOR + "\n" + IMPORT_STYLE, 1)
    if source.count(ROOT_OLD) != 1:
        fail(f"SMTP root marker count changed unexpectedly: {source.count(ROOT_OLD)}")
    source = source.replace(ROOT_OLD, ROOT_NEW, 1)

    for marker in [IMPORT_STYLE, "tos-smtp-settings-flagship-v1", "api.emailSettings.update(payload)", "api.emailSettings.test({ to: form.testTo.trim() || undefined })"]:
        if marker not in source:
            fail(f"post-transform SMTP marker missing: {marker}")

    PAGE.write_text(source)
    STYLE.write_text(CSS)

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists():
        fail("frontend dist missing after build")

    built_css = ""
    for css_file in DIST.rglob("*.css"):
        built_css += css_file.read_text(errors="ignore")
    if RUNTIME_MARKER not in built_css:
        fail("SMTP Settings Flagship Luxury V1 runtime marker missing from built CSS")

    LIVE_PARENT.mkdir(parents=True, exist_ok=True)
    staging = LIVE_PARENT / f"build.smtp-settings-flagship-v1-staging-{stamp}"
    live_backup = LIVE_PARENT / f"build.smtp-settings-flagship-v1-backup-{stamp}"
    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(DIST, staging)

    if LIVE.exists():
        LIVE.rename(live_backup)
    staging.rename(LIVE)

    live_css = ""
    for css_file in LIVE.rglob("*.css"):
        live_css += css_file.read_text(errors="ignore")
    if RUNTIME_MARKER not in live_css:
        fail("SMTP Settings Flagship Luxury V1 runtime marker missing from live build")

    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("SMTP_SETTINGS_FLAGSHIP_LUXURY_V1_RUNTIME=YES")
    print("SMTP_SETTINGS_SCOPE=VISUAL_ONLY")
    print("SMTP_LIGHT_MODE=PEARL_IVORY_CHAMPAGNE_EMERALD")
    print("SMTP_DARK_MODE=OBSIDIAN_TITANIUM_CHAMPAGNE_EMERALD")
    print("SMTP_HEADER=EXECUTIVE_DELIVERY_CONTROL")
    print("SMTP_KPIS=LUXURY_STATUS_HARDWARE")
    print("SMTP_CONFIGURATION=SECURE_VAULT_PANEL")
    print("SMTP_FIELDS=PREMIUM_HIGH_CONTRAST")
    print("SMTP_ACTIONS=METALLIC_CHAMPAGNE_AND_EMERALD")
    print("SMTP_TEST_DELIVERY=PREMIUM_SIGNAL_PANEL")
    print("SMTP_API_CHANGED=NO")
    print("SMTP_SAVE_LOGIC_CHANGED=NO")
    print("SMTP_TEST_LOGIC_CHANGED=NO")
    print("SMTP_PERMISSIONS_CHANGED=NO")
    print("SMTP_DATA_CONTRACT_CHANGED=NO")
    print("TWS_CHANGED=NO")
    print("SLA_CHANGED=NO")
    print("RAMZY_LOGIC_CHANGED=NO")
    print("TCS_CHANGED=NO")
    print(f"SMTP_SETTINGS_PAGE_BASELINE_GIT_BLOB={EXPECTED_PAGE_GIT_BLOB}")
    print(f"LIVE_BACKUP={live_backup if live_backup and live_backup.exists() else 'NONE'}")
    print("STATUS=READY")
except Exception as exc:
    try:
        if page_backup.exists():
            shutil.copy2(page_backup, PAGE)
        if STYLE.exists():
            STYLE.unlink()
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
