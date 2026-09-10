from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
PAGE = FRONTEND / "src/pages/SettingsPage.jsx"
STYLE = FRONTEND / "src/pages/googleDriveSettingsFlagshipLuxuryV1.css"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_PAGE_GIT_BLOB = "a5afad7936370db1c03a1c7c9e4a8a396d019fd7"
IMPORT_ANCHOR = 'import "./smtpSettingsFlagshipLuxuryV1_2DarkFieldValueContrastFix.css";'
IMPORT_STYLE = 'import "./googleDriveSettingsFlagshipLuxuryV1.css";'
DRIVE_START = "function GoogleDriveAdmin({ user })"
DRIVE_END = "\n\n\n\nfunction formatBackupBytes"
ROOT_OLD = '''  return (\n    <Card>\n      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">'''
ROOT_NEW = '''  return (\n    <Card className="tos-gdrive-settings-flagship-v1">\n      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">'''
RUNTIME_MARKER = "--tos-gdrive-settings-flagship-luxury-v1-runtime"

CSS = r'''
:root { --tos-gdrive-settings-flagship-luxury-v1-runtime: 1; }

/* =========================================================
   TOS Settings → Google Drive — Flagship Luxury V1
   Light: pearl / ivory / champagne + cloud blue / cyan
   Dark: obsidian / titanium / champagne + electric cloud blue
   Visual only. OAuth/API/save/connect/disconnect logic untouched.
   ========================================================= */

.tos-gdrive-settings-flagship-v1 {
  position: relative;
  isolation: isolate;
  overflow: hidden;
  padding: 28px !important;
  border: 1px solid rgba(178,118,21,.24) !important;
  border-radius: 30px !important;
  background:
    radial-gradient(120% 100% at 78% 135%, transparent 0 40%, rgba(190,128,24,.11) 40.25% 40.50%, transparent 40.82% 44%, rgba(190,128,24,.055) 44.22% 44.45%, transparent 44.75% 100%),
    radial-gradient(circle at 92% 2%, rgba(46,144,218,.11), transparent 27%),
    radial-gradient(circle at 98% 13%, rgba(104,211,225,.10), transparent 24%),
    linear-gradient(142deg,#fffefa 0%,#fffaf1 55%,#f6ead7 100%) !important;
  box-shadow: 0 24px 52px rgba(78,48,4,.085), inset 0 1px rgba(255,255,255,.98) !important;
}

.tos-gdrive-settings-flagship-v1::before {
  content: "";
  position: absolute;
  inset-block: 24px;
  inset-inline-start: 0;
  width: 3px;
  border-radius: 999px;
  background: linear-gradient(180deg,#f4d272 0%,#c88613 55%,#744100 100%);
  box-shadow: 0 0 18px rgba(216,157,39,.18);
  pointer-events: none;
}

.tos-gdrive-settings-flagship-v1::after {
  content: "CLOUD  •  STORAGE CONTROL";
  position: absolute;
  top: 24px;
  inset-inline-end: 28px;
  color: rgba(61,100,132,.23);
  font-size: 9px;
  font-weight: 950;
  letter-spacing: .20em;
  text-transform: uppercase;
  pointer-events: none;
}

/* Executive header */
.tos-gdrive-settings-flagship-v1 > .flex:first-child {
  position: relative;
  z-index: 1;
  padding-bottom: 22px;
  border-bottom: 1px solid rgba(172,112,18,.11);
}
.tos-gdrive-settings-flagship-v1 > .flex:first-child .tos-kicker {
  color: #98630b !important;
  letter-spacing: .17em;
  text-transform: uppercase;
}
.tos-gdrive-settings-flagship-v1 > .flex:first-child h3 {
  margin-top: 6px !important;
  font-family: Georgia,"Times New Roman",serif;
  font-size: clamp(1.9rem,2.7vw,2.55rem) !important;
  letter-spacing: -.035em;
  color: #20180e !important;
}
.tos-gdrive-settings-flagship-v1 > .flex:first-child .tos-muted {
  max-width: 820px;
  color: #6f665e !important;
  font-weight: 700;
}
.tos-gdrive-settings-flagship-v1 > .flex:first-child > div:last-child {
  width: 66px !important;
  height: 66px !important;
  border: 1px solid rgba(48,135,201,.23);
  border-radius: 22px !important;
  background: linear-gradient(145deg,#f1f9ff 0%,#dbeefc 55%,#c9e5f6 100%) !important;
  color: #2d78ac !important;
  box-shadow: 0 13px 29px rgba(38,113,168,.14), inset 0 1px rgba(255,255,255,.92);
}

/* Cloud status KPI hardware */
.tos-gdrive-settings-flagship-v1 > div[class*="md:grid-cols-4"] {
  gap: 12px !important;
}
.tos-gdrive-settings-flagship-v1 .tos-premium-stat {
  min-height: 126px;
  border: 1px solid rgba(168,109,15,.17) !important;
  border-radius: 20px !important;
  background:
    radial-gradient(circle at 88% 9%,rgba(54,145,211,.075),transparent 27%),
    linear-gradient(155deg,rgba(255,255,255,.98),rgba(252,247,238,.95)) !important;
  box-shadow: 0 12px 28px rgba(73,45,4,.055), inset 0 1px rgba(255,255,255,.98) !important;
  transform: none !important;
}
.tos-gdrive-settings-flagship-v1 .tos-premium-stat > .flex > div:first-child > div:first-child {
  font-family: Georgia,"Times New Roman",serif;
  font-size: 1.18rem !important;
  line-height: 1.15;
  color: #251a0f !important;
}
.tos-gdrive-settings-flagship-v1 .tos-premium-stat > .flex > div:first-child > div:nth-child(2) {
  color: #3a3229 !important;
  font-weight: 800 !important;
}
.tos-gdrive-settings-flagship-v1 .tos-premium-stat > .flex > div:first-child > div:nth-child(3) {
  color: #8c8176 !important;
}
.tos-gdrive-settings-flagship-v1 .tos-premium-stat > .flex > div:last-child {
  width: 44px !important;
  height: 44px !important;
  border-radius: 999px !important;
  box-shadow: 0 8px 20px rgba(56,84,102,.09), inset 0 1px rgba(255,255,255,.88);
}

/* OAuth credentials vault */
.tos-gdrive-settings-flagship-v1 > div[class*="md:grid-cols-2"] {
  position: relative;
  padding: 22px;
  border: 1px solid rgba(71,142,192,.16);
  border-radius: 22px;
  background:
    radial-gradient(circle at 94% 6%,rgba(47,143,210,.075),transparent 25%),
    linear-gradient(145deg,rgba(255,255,255,.93),rgba(246,250,252,.88));
  box-shadow: 0 12px 28px rgba(49,78,96,.055), inset 0 1px rgba(255,255,255,.96);
}
.tos-gdrive-settings-flagship-v1 > div[class*="md:grid-cols-2"]::before {
  content: "SECURE OAUTH CREDENTIALS";
  position: absolute;
  top: 8px;
  inset-inline-end: 16px;
  color: rgba(39,118,172,.31);
  font-size: 8px;
  font-weight: 950;
  letter-spacing: .16em;
  pointer-events: none;
}

.tos-gdrive-settings-flagship-v1 .tos-premium-field,
.tos-gdrive-settings-flagship-v1 .tos-input {
  min-height: 47px;
  border: 1px solid rgba(84,137,173,.20) !important;
  border-radius: 15px !important;
  background: linear-gradient(180deg,#fff,#f8fbfd) !important;
  color: #26333d !important;
  box-shadow: inset 0 1px rgba(255,255,255,.98), 0 5px 14px rgba(54,88,109,.035);
}
.tos-gdrive-settings-flagship-v1 .tos-premium-field:focus,
.tos-gdrive-settings-flagship-v1 .tos-input:focus {
  border-color: rgba(45,137,201,.58) !important;
  box-shadow: 0 0 0 3px rgba(45,137,201,.10),0 8px 20px rgba(42,87,117,.06) !important;
}
.tos-gdrive-settings-flagship-v1 input[type="checkbox"] { accent-color:#be861b; }
.tos-gdrive-settings-flagship-v1 label { color:#4b4540; }
.tos-gdrive-settings-flagship-v1 p.text-xs { line-height:1.55; }

/* Notices */
.tos-gdrive-settings-flagship-v1 .tos-premium-notice {
  border-radius: 16px !important;
  box-shadow: inset 0 1px rgba(255,255,255,.55),0 7px 18px rgba(55,70,79,.035);
}

/* Command action rail */
.tos-gdrive-settings-flagship-v1 > .mt-5.flex {
  padding: 18px;
  border: 1px solid rgba(62,132,180,.12);
  border-radius: 20px;
  background: linear-gradient(145deg,rgba(239,249,255,.75),rgba(255,251,242,.82));
}
.tos-gdrive-settings-flagship-v1 .tos-premium-button {
  min-height: 42px;
  border-radius: 999px !important;
  padding-inline: 18px !important;
  font-weight: 900 !important;
}
.tos-gdrive-settings-flagship-v1 > .mt-5.flex .tos-premium-button:nth-child(3) {
  border: 1px solid #b97a0d !important;
  color: #201404 !important;
  background: linear-gradient(180deg,#fff1b9 0%,#efcb64 23%,#d9a22b 59%,#b8710b 100%) !important;
  box-shadow: 0 10px 22px rgba(111,66,3,.17), inset 0 1px rgba(255,255,255,.82) !important;
}
.tos-gdrive-settings-flagship-v1 > .mt-5.flex .tos-premium-button:nth-child(1),
.tos-gdrive-settings-flagship-v1 > .mt-5.flex .tos-premium-button:nth-child(2) {
  border: 1px solid rgba(44,131,191,.17) !important;
  background: linear-gradient(180deg,#f4faff,#e7f3fa) !important;
  color: #2c719d !important;
  box-shadow: 0 8px 18px rgba(44,107,150,.07), inset 0 1px rgba(255,255,255,.90) !important;
}
.tos-gdrive-settings-flagship-v1 > .mt-5.flex .tos-premium-button:nth-child(4) {
  box-shadow: 0 8px 18px rgba(170,55,55,.08), inset 0 1px rgba(255,255,255,.72) !important;
}

/* =========================================================
   DARK — obsidian / titanium / champagne / cloud blue
   ========================================================= */
.dark .tos-gdrive-settings-flagship-v1 {
  color: #eee9e2 !important;
  border-color: rgba(238,188,72,.42) !important;
  background:
    radial-gradient(120% 100% at 78% 135%,transparent 0 39%,rgba(255,199,70,.22) 39.25% 39.52%,transparent 39.82% 43%,rgba(255,191,50,.115) 43.25% 43.5%,transparent 43.8% 100%),
    radial-gradient(circle at 91% 2%,rgba(47,155,229,.14),transparent 28%),
    radial-gradient(circle at 99% 13%,rgba(56,205,218,.08),transparent 25%),
    linear-gradient(142deg,#0b1318 0%,#0a1014 60%,#110d07 100%) !important;
  box-shadow: 0 29px 62px rgba(0,0,0,.40),0 0 36px rgba(215,154,31,.06),inset 0 1px rgba(255,255,255,.03) !important;
}
.dark .tos-gdrive-settings-flagship-v1::before {
  background: linear-gradient(180deg,#ffd66f 0%,#ca8611 55%,#754000 100%);
  box-shadow: 0 0 20px rgba(246,184,59,.24);
}
.dark .tos-gdrive-settings-flagship-v1::after {
  color: rgba(177,221,249,.46);
  text-shadow: 0 0 18px rgba(61,168,236,.10);
}
.dark .tos-gdrive-settings-flagship-v1 > .flex:first-child { border-bottom-color:rgba(232,184,73,.16); }
.dark .tos-gdrive-settings-flagship-v1 > .flex:first-child .tos-kicker { color:#ecbd51 !important; }
.dark .tos-gdrive-settings-flagship-v1 > .flex:first-child h3 { color:#fff2dd !important; text-shadow:0 1px rgba(0,0,0,.35); }
.dark .tos-gdrive-settings-flagship-v1 > .flex:first-child .tos-muted { color:#aeb7bd !important; }
.dark .tos-gdrive-settings-flagship-v1 > .flex:first-child > div:last-child {
  border-color:rgba(74,174,237,.30) !important;
  background:linear-gradient(145deg,#11314a 0%,#0c2334 58%,#091821 100%) !important;
  color:#8fd4ff !important;
  box-shadow:0 12px 30px rgba(0,0,0,.30),0 0 23px rgba(57,162,229,.13),inset 0 1px rgba(255,255,255,.04) !important;
}

.dark .tos-gdrive-settings-flagship-v1 .tos-premium-stat {
  border-color:rgba(232,183,73,.23) !important;
  background:radial-gradient(circle at 88% 9%,rgba(52,164,236,.10),transparent 27%),linear-gradient(155deg,#151d22 0%,#0b1318 100%) !important;
  box-shadow:0 14px 31px rgba(0,0,0,.30),inset 0 1px rgba(255,255,255,.028) !important;
}
.dark .tos-gdrive-settings-flagship-v1 .tos-premium-stat > .flex > div:first-child > div:first-child { color:#fff0d8 !important; }
.dark .tos-gdrive-settings-flagship-v1 .tos-premium-stat > .flex > div:first-child > div:nth-child(2) { color:#eee8de !important; }
.dark .tos-gdrive-settings-flagship-v1 .tos-premium-stat > .flex > div:first-child > div:nth-child(3) { color:#99a6ae !important; }

.dark .tos-gdrive-settings-flagship-v1 > div[class*="md:grid-cols-2"] {
  border-color:rgba(69,167,229,.22) !important;
  background:radial-gradient(circle at 94% 5%,rgba(51,169,238,.11),transparent 24%),linear-gradient(145deg,#111b20 0%,#0a1419 100%) !important;
  box-shadow:0 16px 34px rgba(0,0,0,.29),inset 0 1px rgba(255,255,255,.026) !important;
}
.dark .tos-gdrive-settings-flagship-v1 > div[class*="md:grid-cols-2"]::before {
  color:rgba(129,207,255,.60) !important;
  text-shadow:0 0 16px rgba(55,168,237,.10);
}
.dark .tos-gdrive-settings-flagship-v1 .tos-premium-field,
.dark .tos-gdrive-settings-flagship-v1 .tos-input {
  border-color:rgba(79,156,207,.27) !important;
  background:linear-gradient(180deg,#151e23 0%,#0d161b 100%) !important;
  color:#f3f1ed !important;
  -webkit-text-fill-color:#f3f1ed !important;
  caret-color:#99d7ff;
  box-shadow:inset 0 1px rgba(255,255,255,.028),0 7px 18px rgba(0,0,0,.20) !important;
}
.dark .tos-gdrive-settings-flagship-v1 .tos-premium-field::placeholder,
.dark .tos-gdrive-settings-flagship-v1 .tos-input::placeholder {
  color:#9faab2 !important;
  -webkit-text-fill-color:#9faab2 !important;
  opacity:1 !important;
}
.dark .tos-gdrive-settings-flagship-v1 .tos-premium-field:focus,
.dark .tos-gdrive-settings-flagship-v1 .tos-input:focus {
  border-color:rgba(86,185,247,.62) !important;
  box-shadow:0 0 0 3px rgba(72,170,232,.11),0 9px 23px rgba(0,0,0,.26) !important;
}
.dark .tos-gdrive-settings-flagship-v1 .text-zinc-400,
.dark .tos-gdrive-settings-flagship-v1 .text-zinc-500,
.dark .tos-gdrive-settings-flagship-v1 .dark\:text-zinc-400,
.dark .tos-gdrive-settings-flagship-v1 .dark\:text-zinc-500,
.dark .tos-gdrive-settings-flagship-v1 label { color:#cbd3d8 !important; }
.dark .tos-gdrive-settings-flagship-v1 input[type="checkbox"] { accent-color:#d19a25 !important; }

.dark .tos-gdrive-settings-flagship-v1 .tos-premium-notice { box-shadow:inset 0 1px rgba(255,255,255,.025),0 8px 20px rgba(0,0,0,.20) !important; }
.dark .tos-gdrive-settings-flagship-v1 > .mt-5.flex {
  border-color:rgba(71,164,224,.20) !important;
  background:radial-gradient(circle at 90% 10%,rgba(47,159,229,.08),transparent 26%),linear-gradient(145deg,#101d24 0%,#0b151a 100%) !important;
  box-shadow:0 14px 30px rgba(0,0,0,.25),inset 0 1px rgba(255,255,255,.025) !important;
}
.dark .tos-gdrive-settings-flagship-v1 > .mt-5.flex .tos-premium-button:nth-child(1),
.dark .tos-gdrive-settings-flagship-v1 > .mt-5.flex .tos-premium-button:nth-child(2) {
  border-color:rgba(82,177,237,.28) !important;
  background:linear-gradient(180deg,#132735,#0c1b24) !important;
  color:#9ad8ff !important;
}
.dark .tos-gdrive-settings-flagship-v1 > .mt-5.flex .tos-premium-button:nth-child(3) {
  border-color:#d59a22 !important;
  color:#160e02 !important;
  background:linear-gradient(180deg,#fff0ae 0%,#efc356 24%,#d4921b 61%,#a95d03 100%) !important;
  box-shadow:0 12px 26px rgba(0,0,0,.34),0 0 17px rgba(231,170,47,.12),inset 0 1px rgba(255,255,255,.80) !important;
}

@media (max-width: 767px) {
  .tos-gdrive-settings-flagship-v1 { padding:20px !important; border-radius:23px !important; }
  .tos-gdrive-settings-flagship-v1::after { display:none; }
  .tos-gdrive-settings-flagship-v1 > div[class*="md:grid-cols-2"] { padding:18px; }
  .tos-gdrive-settings-flagship-v1 > .mt-5.flex { padding:14px; }
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
for marker in [
    IMPORT_ANCHOR,
    DRIVE_START,
    DRIVE_END,
    "api.googleDrive.status()",
    "api.googleDrive.authUrl()",
    "api.googleDrive.updateSettings(payload)",
    "api.googleDrive.disconnect()",
    'Google Drive Storage Settings',
]:
    if marker not in source:
        fail(f"required Google Drive baseline marker missing: {marker}")

if IMPORT_STYLE in source or STYLE.exists():
    fail("Google Drive Settings Flagship Luxury V1 already present")

drive_start = source.index(DRIVE_START)
drive_end = source.index(DRIVE_END, drive_start)
drive_segment = source[drive_start:drive_end]
if drive_segment.count(ROOT_OLD) != 1:
    fail(f"Google Drive scoped root marker count unexpected: {drive_segment.count(ROOT_OLD)}")
for marker in [
    "api.googleDrive.status()",
    "api.googleDrive.authUrl()",
    "api.googleDrive.updateSettings(payload)",
    "api.googleDrive.disconnect()",
    "window.open(data.url",
]:
    if marker not in drive_segment:
        fail(f"Google Drive scoped baseline marker missing: {marker}")

stamp = int(time.time())
page_backup = PAGE.with_name(f"{PAGE.name}.google-drive-v1-backup-{stamp}")
shutil.copy2(PAGE, page_backup)
live_backup = None
staging = None

try:
    source = source.replace(IMPORT_ANCHOR, IMPORT_ANCHOR + "\n" + IMPORT_STYLE, 1)
    drive_start = source.index(DRIVE_START)
    drive_end = source.index(DRIVE_END, drive_start)
    drive_segment = source[drive_start:drive_end]
    drive_segment = drive_segment.replace(ROOT_OLD, ROOT_NEW, 1)
    source = source[:drive_start] + drive_segment + source[drive_end:]

    post_start = source.index(DRIVE_START)
    post_end = source.index(DRIVE_END, post_start)
    post_segment = source[post_start:post_end]
    for marker in [
        'className="tos-gdrive-settings-flagship-v1"',
        "api.googleDrive.status()",
        "api.googleDrive.authUrl()",
        "api.googleDrive.updateSettings(payload)",
        "api.googleDrive.disconnect()",
    ]:
        if marker not in post_segment:
            fail(f"post-transform Google Drive marker missing: {marker}")
    if IMPORT_STYLE not in source:
        fail("Google Drive V1 style import injection failed")

    PAGE.write_text(source)
    STYLE.write_text(CSS)
    if RUNTIME_MARKER not in STYLE.read_text():
        fail("Google Drive V1 runtime marker missing after style write")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists():
        fail("frontend dist missing after build")

    built_css = "".join(p.read_text(errors="ignore") for p in DIST.rglob("*.css"))
    if RUNTIME_MARKER not in built_css:
        fail("Google Drive V1 runtime marker missing from built CSS")
    if ".tos-gdrive-settings-flagship-v1" not in built_css:
        fail("Google Drive V1 scope marker missing from built CSS")

    LIVE_PARENT.mkdir(parents=True, exist_ok=True)
    staging = LIVE_PARENT / f"build.google-drive-settings-v1-staging-{stamp}"
    live_backup = LIVE_PARENT / f"build.google-drive-settings-v1-backup-{stamp}"
    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(DIST, staging)
    if LIVE.exists():
        LIVE.rename(live_backup)
    staging.rename(LIVE)

    live_css = "".join(p.read_text(errors="ignore") for p in LIVE.rglob("*.css"))
    if RUNTIME_MARKER not in live_css:
        fail("Google Drive V1 runtime marker missing from live build")

    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("GOOGLE_DRIVE_SETTINGS_FLAGSHIP_LUXURY_V1_RUNTIME=YES")
    print("GOOGLE_DRIVE_SCOPE=VISUAL_ONLY")
    print("GOOGLE_DRIVE_LIGHT_MODE=PEARL_IVORY_CHAMPAGNE_CLOUD_BLUE")
    print("GOOGLE_DRIVE_DARK_MODE=OBSIDIAN_TITANIUM_CHAMPAGNE_ELECTRIC_BLUE")
    print("GOOGLE_DRIVE_HEADER=EXECUTIVE_CLOUD_STORAGE_CONTROL")
    print("GOOGLE_DRIVE_KPIS=LUXURY_STATUS_HARDWARE")
    print("GOOGLE_DRIVE_OAUTH_PANEL=SECURE_CREDENTIALS_VAULT")
    print("GOOGLE_DRIVE_FIELDS=PREMIUM_HIGH_CONTRAST")
    print("GOOGLE_DRIVE_ACTIONS=METALLIC_CHAMPAGNE_CLOUD_BLUE")
    print("GOOGLE_DRIVE_API_CHANGED=NO")
    print("GOOGLE_DRIVE_SAVE_LOGIC_CHANGED=NO")
    print("GOOGLE_DRIVE_CONNECT_LOGIC_CHANGED=NO")
    print("GOOGLE_DRIVE_DISCONNECT_LOGIC_CHANGED=NO")
    print("GOOGLE_DRIVE_PERMISSIONS_CHANGED=NO")
    print("GOOGLE_DRIVE_DATA_CONTRACT_CHANGED=NO")
    print("TWS_CHANGED=NO")
    print("SLA_CHANGED=NO")
    print("RAMZY_LOGIC_CHANGED=NO")
    print("TCS_CHANGED=NO")
    print(f"SETTINGS_PAGE_BASELINE_GIT_BLOB={EXPECTED_PAGE_GIT_BLOB}")
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
