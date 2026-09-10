from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
PAGE = FRONTEND / "src/pages/SettingsPage.jsx"
V1_STYLE = FRONTEND / "src/pages/googleDriveSettingsFlagshipLuxuryV1.css"
V11_STYLE = FRONTEND / "src/pages/googleDriveSettingsFlagshipLuxuryV1_1DarkShellContrastFix.css"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

V1_IMPORT = 'import "./googleDriveSettingsFlagshipLuxuryV1.css";'
V11_IMPORT = 'import "./googleDriveSettingsFlagshipLuxuryV1_1DarkShellContrastFix.css";'
V1_RUNTIME = "--tos-gdrive-settings-flagship-luxury-v1-runtime"
V11_RUNTIME = "--tos-gdrive-settings-flagship-luxury-v1-1-dark-shell-contrast-runtime"
DRIVE_START = "function GoogleDriveAdmin({ user })"
DRIVE_END = "\n\n\n\nfunction formatBackupBytes"

CSS = r'''
:root { --tos-gdrive-settings-flagship-luxury-v1-1-dark-shell-contrast-runtime: 1; }

/* =========================================================
   TOS Settings → Google Drive — Flagship Luxury V1.1
   DARK SHELL + CONTRAST FIX ONLY
   Light mode intentionally untouched.
   No OAuth/API/save/connect/disconnect/permissions/data changes.
   ========================================================= */

html.dark .tos-premium-card.tos-gdrive-settings-flagship-v1,
.dark .tos-premium-card.tos-gdrive-settings-flagship-v1,
.dark .tos-gdrive-settings-flagship-v1 {
  color: #eee9e2 !important;
  border-color: rgba(239,188,72,.46) !important;
  background:
    radial-gradient(120% 108% at 80% 136%,
      transparent 0 38.5%, rgba(255,201,74,.24) 38.8% 39.06%, transparent 39.36% 42.2%,
      rgba(255,194,56,.13) 42.5% 42.76%, transparent 43.04% 46%,
      rgba(255,187,40,.07) 46.3% 46.54%, transparent 46.84% 100%),
    radial-gradient(circle at 91% 3%, rgba(48,157,230,.14), transparent 27%),
    radial-gradient(circle at 98% 14%, rgba(48,205,221,.08), transparent 25%),
    linear-gradient(142deg,#0b1318 0%,#091014 60%,#100c07 100%) !important;
  box-shadow:
    0 30px 64px rgba(0,0,0,.43),
    0 0 38px rgba(218,157,32,.065),
    inset 0 1px rgba(255,255,255,.032) !important;
}

.dark .tos-gdrive-settings-flagship-v1::before {
  background: linear-gradient(180deg,#ffd66f 0%,#ca8611 55%,#744000 100%) !important;
  box-shadow: 0 0 22px rgba(246,184,59,.27) !important;
}

.dark .tos-gdrive-settings-flagship-v1::after {
  color: rgba(184,224,249,.52) !important;
  text-shadow: 0 0 18px rgba(61,168,236,.11) !important;
}

/* Executive title area */
.dark .tos-gdrive-settings-flagship-v1 > .flex:first-child {
  border-bottom-color: rgba(232,184,73,.17) !important;
}
.dark .tos-gdrive-settings-flagship-v1 > .flex:first-child .tos-kicker {
  color: #edbd50 !important;
}
.dark .tos-gdrive-settings-flagship-v1 > .flex:first-child h3,
.dark .tos-gdrive-settings-flagship-v1 h3.text-zinc-950,
.dark .tos-gdrive-settings-flagship-v1 h3.dark\\:text-white {
  color: #fff3df !important;
  text-shadow: 0 1px 0 rgba(0,0,0,.38) !important;
}
.dark .tos-gdrive-settings-flagship-v1 > .flex:first-child .tos-muted,
.dark .tos-gdrive-settings-flagship-v1 .tos-muted {
  color: #aeb8c0 !important;
}
.dark .tos-gdrive-settings-flagship-v1 > .flex:first-child > div:last-child {
  border-color: rgba(74,177,239,.36) !important;
  background: linear-gradient(145deg,#0e2940 0%,#0b2031 60%,#081823 100%) !important;
  color: #72c8ff !important;
  box-shadow: 0 12px 30px rgba(0,0,0,.31),0 0 24px rgba(55,165,235,.14),inset 0 1px rgba(255,255,255,.04) !important;
}

/* KPI cards remain dark and coherent with shell */
.dark .tos-gdrive-settings-flagship-v1 .tos-premium-stat {
  border-color: rgba(233,184,74,.25) !important;
  background:
    radial-gradient(circle at 88% 9%,rgba(53,160,229,.10),transparent 27%),
    linear-gradient(155deg,#141d22 0%,#0b1318 100%) !important;
  box-shadow: 0 14px 31px rgba(0,0,0,.31),inset 0 1px rgba(255,255,255,.028) !important;
}
.dark .tos-gdrive-settings-flagship-v1 .tos-premium-stat > .flex > div:first-child > div:first-child {
  color: #fff0d8 !important;
}
.dark .tos-gdrive-settings-flagship-v1 .tos-premium-stat > .flex > div:first-child > div:nth-child(2) {
  color: #eee8de !important;
}
.dark .tos-gdrive-settings-flagship-v1 .tos-premium-stat > .flex > div:first-child > div:nth-child(3) {
  color: #9ca8b1 !important;
}

/* OAuth credentials vault */
.dark .tos-gdrive-settings-flagship-v1 > div[class*="md:grid-cols-2"] {
  border-color: rgba(70,171,235,.22) !important;
  background:
    radial-gradient(circle at 94% 5%,rgba(47,155,229,.10),transparent 25%),
    radial-gradient(110% 95% at 90% 118%,transparent 0 48%,rgba(237,179,58,.07) 48.25% 48.5%,transparent 48.8% 100%),
    linear-gradient(145deg,#101b22 0%,#0a141a 100%) !important;
  box-shadow: 0 16px 34px rgba(0,0,0,.29),inset 0 1px rgba(255,255,255,.025) !important;
}
.dark .tos-gdrive-settings-flagship-v1 > div[class*="md:grid-cols-2"]::before {
  color: rgba(114,201,255,.56) !important;
  text-shadow: 0 0 16px rgba(61,168,236,.10) !important;
}
.dark .tos-gdrive-settings-flagship-v1 .tos-premium-field,
.dark .tos-gdrive-settings-flagship-v1 .tos-input {
  border-color: rgba(87,168,220,.26) !important;
  background: linear-gradient(180deg,#151e24 0%,#0f171c 100%) !important;
  color: #f2f5f7 !important;
  -webkit-text-fill-color: #f2f5f7 !important;
  caret-color: #efc765 !important;
  box-shadow: inset 0 1px rgba(255,255,255,.028),0 7px 18px rgba(0,0,0,.20) !important;
}
.dark .tos-gdrive-settings-flagship-v1 .tos-premium-field::placeholder,
.dark .tos-gdrive-settings-flagship-v1 .tos-input::placeholder {
  color: #a8b2bb !important;
  -webkit-text-fill-color: #a8b2bb !important;
  opacity: 1 !important;
}
.dark .tos-gdrive-settings-flagship-v1 .tos-premium-field:focus,
.dark .tos-gdrive-settings-flagship-v1 .tos-input:focus {
  border-color: rgba(87,184,244,.62) !important;
  box-shadow: 0 0 0 3px rgba(57,165,232,.12),0 9px 23px rgba(0,0,0,.26) !important;
}
.dark .tos-gdrive-settings-flagship-v1 label,
.dark .tos-gdrive-settings-flagship-v1 label span,
.dark .tos-gdrive-settings-flagship-v1 p.text-xs,
.dark .tos-gdrive-settings-flagship-v1 .text-zinc-500,
.dark .tos-gdrive-settings-flagship-v1 .dark\\:text-zinc-400,
.dark .tos-gdrive-settings-flagship-v1 .dark\\:text-zinc-500 {
  color: #d6d9dc !important;
}

/* Notices: remove grey/pale strips and integrate with dark shell */
.dark .tos-gdrive-settings-flagship-v1 .tos-premium-notice {
  border-radius: 16px !important;
  box-shadow: inset 0 1px rgba(255,255,255,.025),0 8px 20px rgba(0,0,0,.20) !important;
}
.dark .tos-gdrive-settings-flagship-v1 .tos-premium-notice.bg-amber-50,
.dark .tos-gdrive-settings-flagship-v1 .tos-premium-notice.dark\\:bg-amber-500\/10 {
  border-color: rgba(231,181,73,.34) !important;
  background: linear-gradient(180deg,rgba(45,38,24,.86),rgba(27,26,24,.90)) !important;
  color: #f0cb67 !important;
}
.dark .tos-gdrive-settings-flagship-v1 .tos-premium-notice.bg-red-50,
.dark .tos-gdrive-settings-flagship-v1 .tos-premium-notice.dark\\:bg-red-500\/10 {
  border-color: rgba(238,90,99,.28) !important;
  background: linear-gradient(180deg,rgba(57,22,25,.72),rgba(34,16,18,.78)) !important;
  color: #ff9da5 !important;
}

/* Action command rail */
.dark .tos-gdrive-settings-flagship-v1 > .mt-5.flex {
  border-color: rgba(64,168,232,.22) !important;
  background:
    radial-gradient(circle at 92% 12%,rgba(50,163,233,.08),transparent 26%),
    linear-gradient(145deg,#0d1b24 0%,#09151d 100%) !important;
  box-shadow: 0 14px 30px rgba(0,0,0,.27),inset 0 1px rgba(255,255,255,.025) !important;
}
.dark .tos-gdrive-settings-flagship-v1 > .mt-5.flex .tos-premium-button:nth-child(1),
.dark .tos-gdrive-settings-flagship-v1 > .mt-5.flex .tos-premium-button:nth-child(2) {
  border: 1px solid rgba(72,171,235,.30) !important;
  background: linear-gradient(180deg,#12293a 0%,#0b1d2a 100%) !important;
  color: #8fd5ff !important;
  box-shadow: 0 9px 21px rgba(0,0,0,.27),inset 0 1px rgba(255,255,255,.025) !important;
}
.dark .tos-gdrive-settings-flagship-v1 > .mt-5.flex .tos-premium-button:nth-child(3) {
  border-color: #d59a22 !important;
  color: #160e02 !important;
  background: linear-gradient(180deg,#fff0ae 0%,#efc356 24%,#d4921b 61%,#a95d03 100%) !important;
  box-shadow: 0 12px 26px rgba(0,0,0,.34),0 0 17px rgba(231,170,47,.12),inset 0 1px rgba(255,255,255,.80) !important;
}
.dark .tos-gdrive-settings-flagship-v1 > .mt-5.flex .tos-premium-button:nth-child(4) {
  border: 1px solid rgba(239,84,97,.30) !important;
  background: linear-gradient(180deg,#32181c 0%,#231014 100%) !important;
  color: #ff8f99 !important;
  box-shadow: 0 9px 21px rgba(0,0,0,.27),inset 0 1px rgba(255,255,255,.02) !important;
}

@media (max-width: 767px) {
  .dark .tos-premium-card.tos-gdrive-settings-flagship-v1 {
    border-radius: 22px !important;
  }
}
'''


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


if not PAGE.exists():
    fail(f"Settings page missing: {PAGE}")
if not V1_STYLE.exists():
    fail(f"Google Drive V1 style missing: {V1_STYLE}")

source = PAGE.read_text()
v1_css = V1_STYLE.read_text()

for marker in [
    V1_IMPORT,
    DRIVE_START,
    DRIVE_END,
    'className="tos-gdrive-settings-flagship-v1"',
    "api.googleDrive.status()",
    "api.googleDrive.authUrl()",
    "api.googleDrive.updateSettings(payload)",
    "api.googleDrive.disconnect()",
    'Google Drive Storage Settings',
]:
    if marker not in source:
        fail(f"required Google Drive V1 baseline marker missing: {marker}")

if V1_RUNTIME not in v1_css:
    fail("required Google Drive V1 runtime marker missing")
if V11_IMPORT in source or V11_STYLE.exists():
    fail("Google Drive Settings Flagship Luxury V1.1 dark shell contrast fix already present")

drive_start = source.index(DRIVE_START)
drive_end = source.index(DRIVE_END, drive_start)
drive_segment = source[drive_start:drive_end]
for marker in [
    'className="tos-gdrive-settings-flagship-v1"',
    "api.googleDrive.status()",
    "api.googleDrive.authUrl()",
    "api.googleDrive.updateSettings(payload)",
    "api.googleDrive.disconnect()",
]:
    if marker not in drive_segment:
        fail(f"Google Drive scoped V1 marker missing: {marker}")

stamp = int(time.time())
page_backup = PAGE.with_name(f"{PAGE.name}.google-drive-v1-1-dark-backup-{stamp}")
shutil.copy2(PAGE, page_backup)
live_backup = None
staging = None

try:
    source = source.replace(V1_IMPORT, V1_IMPORT + "\n" + V11_IMPORT, 1)
    if V11_IMPORT not in source:
        fail("Google Drive V1.1 style import injection failed")

    PAGE.write_text(source)
    V11_STYLE.write_text(CSS)

    updated = PAGE.read_text()
    updated_start = updated.index(DRIVE_START)
    updated_end = updated.index(DRIVE_END, updated_start)
    updated_segment = updated[updated_start:updated_end]
    for marker in [
        V11_IMPORT,
        'className="tos-gdrive-settings-flagship-v1"',
        "api.googleDrive.status()",
        "api.googleDrive.authUrl()",
        "api.googleDrive.updateSettings(payload)",
        "api.googleDrive.disconnect()",
    ]:
        if marker == V11_IMPORT:
            if marker not in updated:
                fail(f"post-transform marker missing: {marker}")
        elif marker not in updated_segment:
            fail(f"post-transform Google Drive marker missing: {marker}")

    if V11_RUNTIME not in V11_STYLE.read_text():
        fail("Google Drive V1.1 runtime marker missing after style write")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists():
        fail("frontend dist missing after build")

    built_css = ""
    for css_file in DIST.rglob("*.css"):
        built_css += css_file.read_text(errors="ignore")
    if V11_RUNTIME not in built_css:
        fail("Google Drive Settings V1.1 runtime marker missing from built CSS")

    LIVE_PARENT.mkdir(parents=True, exist_ok=True)
    staging = LIVE_PARENT / f"build.google-drive-v1-1-dark-staging-{stamp}"
    live_backup = LIVE_PARENT / f"build.google-drive-v1-1-dark-backup-{stamp}"
    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(DIST, staging)

    if LIVE.exists():
        LIVE.rename(live_backup)
    staging.rename(LIVE)

    live_css = ""
    for css_file in LIVE.rglob("*.css"):
        live_css += css_file.read_text(errors="ignore")
    if V11_RUNTIME not in live_css:
        fail("Google Drive Settings V1.1 runtime marker missing from live build")

    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("GOOGLE_DRIVE_SETTINGS_FLAGSHIP_LUXURY_V1_1_RUNTIME=YES")
    print("GOOGLE_DRIVE_V1_BASELINE=PRESERVED")
    print("GOOGLE_DRIVE_V11_SCOPE=DARK_SHELL_AND_CONTRAST_ONLY")
    print("GOOGLE_DRIVE_DARK_MAIN_SHELL=OBSIDIAN_TITANIUM_FIXED")
    print("GOOGLE_DRIVE_DARK_HEADER_CONTRAST=IVORY_CHAMPAGNE_FIXED")
    print("GOOGLE_DRIVE_DARK_OAUTH_PANEL=INTEGRATED")
    print("GOOGLE_DRIVE_DARK_FIELDS=HIGH_CONTRAST")
    print("GOOGLE_DRIVE_DARK_NOTICES=INTEGRATED")
    print("GOOGLE_DRIVE_DARK_ACTION_RAIL=INTEGRATED")
    print("GOOGLE_DRIVE_LIGHT_MODE_CHANGED=NO")
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
    print(f"LIVE_BACKUP={live_backup if live_backup and live_backup.exists() else 'NONE'}")
    print("STATUS=READY")
except Exception as exc:
    try:
        if page_backup.exists():
            shutil.copy2(page_backup, PAGE)
        if V11_STYLE.exists():
            V11_STYLE.unlink()
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
