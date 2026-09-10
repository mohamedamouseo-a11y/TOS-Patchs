from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
PAGE = FRONTEND / "src/pages/SettingsPage.jsx"
V1_STYLE = FRONTEND / "src/pages/smtpSettingsFlagshipLuxuryV1.css"
V11_STYLE = FRONTEND / "src/pages/smtpSettingsFlagshipLuxuryV1_1DarkShellContrastFix.css"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

V1_IMPORT = 'import "./smtpSettingsFlagshipLuxuryV1.css";'
V11_IMPORT = 'import "./smtpSettingsFlagshipLuxuryV1_1DarkShellContrastFix.css";'
V1_RUNTIME = "--tos-smtp-settings-flagship-luxury-v1-runtime"
V11_RUNTIME = "--tos-smtp-settings-flagship-luxury-v1-1-dark-shell-contrast-runtime"
SMTP_START = "function EmailSettingsAdmin({ user })"
SMTP_END = "\nfunction GoogleDriveAdmin({ user })"

CSS = r'''
:root { --tos-smtp-settings-flagship-luxury-v1-1-dark-shell-contrast-runtime: 1; }

/* =========================================================
   TOS Settings → SMTP Email — Flagship Luxury V1.1
   DARK SHELL + CONTRAST FIX ONLY
   Light mode intentionally untouched.
   No SMTP API / save / test / permissions / data changes.
   ========================================================= */

/* Root SMTP shell: force the entire card into the same obsidian/titanium language. */
html.dark .tos-premium-card.tos-smtp-settings-flagship-v1,
.dark .tos-premium-card.tos-smtp-settings-flagship-v1,
.dark .tos-smtp-settings-flagship-v1 {
  color: #eee8df !important;
  border-color: rgba(239,187,72,.44) !important;
  background:
    radial-gradient(122% 108% at 80% 136%,
      transparent 0 38.5%, rgba(255,201,74,.24) 38.8% 39.06%, transparent 39.36% 42.2%,
      rgba(255,194,56,.135) 42.5% 42.76%, transparent 43.04% 46.0%,
      rgba(255,187,40,.072) 46.3% 46.54%, transparent 46.84% 100%),
    radial-gradient(circle at 92% 3%, rgba(28,182,126,.10), transparent 26%),
    radial-gradient(circle at 99% 12%, rgba(231,177,63,.08), transparent 24%),
    linear-gradient(142deg,#0c1317 0%,#0a1014 58%,#100c07 100%) !important;
  box-shadow:
    0 30px 64px rgba(0,0,0,.42),
    0 0 38px rgba(218,157,32,.065),
    inset 0 1px rgba(255,255,255,.032) !important;
}

html.dark .tos-premium-card.tos-smtp-settings-flagship-v1::before,
.dark .tos-premium-card.tos-smtp-settings-flagship-v1::before {
  background: linear-gradient(180deg,#ffd66f 0%,#ca8611 55%,#784100 100%) !important;
  box-shadow: 0 0 21px rgba(246,184,59,.25) !important;
}

html.dark .tos-premium-card.tos-smtp-settings-flagship-v1::after,
.dark .tos-premium-card.tos-smtp-settings-flagship-v1::after {
  color: rgba(247,218,151,.56) !important;
  text-shadow: 0 0 18px rgba(235,179,63,.11);
}

/* Header / title readability inside the root shell. */
.dark .tos-smtp-settings-flagship-v1 > .flex:first-child {
  border-bottom-color: rgba(232,184,73,.18) !important;
}
.dark .tos-smtp-settings-flagship-v1 > .flex:first-child .tos-kicker {
  color: #edbd50 !important;
}
.dark .tos-smtp-settings-flagship-v1 > .flex:first-child h3,
.dark .tos-smtp-settings-flagship-v1 h3.text-zinc-950,
.dark .tos-smtp-settings-flagship-v1 h3.dark\:text-white {
  color: #fff3df !important;
  text-shadow: 0 1px 0 rgba(0,0,0,.38);
}
.dark .tos-smtp-settings-flagship-v1 > .flex:first-child .tos-muted,
.dark .tos-smtp-settings-flagship-v1 .tos-muted {
  color: #aeb7bd !important;
}
.dark .tos-smtp-settings-flagship-v1 > .flex:first-child > div:last-child {
  border-color: rgba(46,207,148,.30) !important;
  background: linear-gradient(145deg,#123329 0%,#0d241d 58%,#081915 100%) !important;
  color: #70efbd !important;
  box-shadow: 0 12px 30px rgba(0,0,0,.30),0 0 23px rgba(31,188,131,.12),inset 0 1px rgba(255,255,255,.04) !important;
}

/* KPI hardware: keep the cards fully dark and highly readable. */
.dark .tos-smtp-settings-flagship-v1 .tos-premium-stat {
  border-color: rgba(233,184,74,.24) !important;
  background:
    radial-gradient(circle at 88% 9%,rgba(31,194,137,.085),transparent 27%),
    linear-gradient(155deg,#151d21 0%,#0c1317 100%) !important;
  box-shadow: 0 14px 31px rgba(0,0,0,.30),inset 0 1px rgba(255,255,255,.028) !important;
}
.dark .tos-smtp-settings-flagship-v1 .tos-premium-stat > .flex > div:first-child > div:first-child {
  color: #fff0d8 !important;
}
.dark .tos-smtp-settings-flagship-v1 .tos-premium-stat > .flex > div:first-child > div:nth-child(2) {
  color: #eee8de !important;
}
.dark .tos-smtp-settings-flagship-v1 .tos-premium-stat > .flex > div:first-child > div:nth-child(3) {
  color: #99a5ad !important;
}

/* Secure configuration vault. */
.dark .tos-smtp-settings-flagship-v1 > div[class*="md:grid-cols-2"] {
  border-color: rgba(49,197,143,.18) !important;
  background:
    radial-gradient(circle at 94% 5%,rgba(30,188,133,.085),transparent 24%),
    radial-gradient(110% 95% at 90% 118%,transparent 0 48%,rgba(237,179,58,.065) 48.25% 48.5%,transparent 48.8% 100%),
    linear-gradient(145deg,#111b1d 0%,#0b1416 100%) !important;
  box-shadow: 0 16px 34px rgba(0,0,0,.28),inset 0 1px rgba(255,255,255,.024) !important;
}
.dark .tos-smtp-settings-flagship-v1 > div[class*="md:grid-cols-2"]::before {
  color: rgba(82,224,171,.52) !important;
  text-shadow: 0 0 16px rgba(31,190,134,.08);
}

/* Fields / labels. */
.dark .tos-smtp-settings-flagship-v1 .tos-premium-field,
.dark .tos-smtp-settings-flagship-v1 .tos-input {
  border-color: rgba(226,180,76,.24) !important;
  background: linear-gradient(180deg,#151d21 0%,#0e1519 100%) !important;
  color: #f5efe7 !important;
  caret-color: #edc564;
  box-shadow: inset 0 1px rgba(255,255,255,.028),0 7px 18px rgba(0,0,0,.20) !important;
}
.dark .tos-smtp-settings-flagship-v1 .tos-premium-field::placeholder,
.dark .tos-smtp-settings-flagship-v1 .tos-input::placeholder {
  color: #929fa8 !important;
  opacity: 1 !important;
}
.dark .tos-smtp-settings-flagship-v1 .tos-premium-field:focus,
.dark .tos-smtp-settings-flagship-v1 .tos-input:focus {
  border-color: rgba(61,214,159,.58) !important;
  box-shadow: 0 0 0 3px rgba(34,190,136,.11),0 9px 23px rgba(0,0,0,.26) !important;
}
.dark .tos-smtp-settings-flagship-v1 label,
.dark .tos-smtp-settings-flagship-v1 label span,
.dark .tos-smtp-settings-flagship-v1 .text-zinc-500,
.dark .tos-smtp-settings-flagship-v1 .dark\:text-zinc-400 {
  color: #d8d1c8 !important;
}
.dark .tos-smtp-settings-flagship-v1 input[type="checkbox"] {
  accent-color: #d19a25 !important;
}

/* Action row: visually integrated with shell. */
.dark .tos-smtp-settings-flagship-v1 > .mt-5.flex {
  position: relative;
  padding: 16px 0 2px;
  border-top: 1px solid rgba(232,184,74,.10);
}
.dark .tos-smtp-settings-flagship-v1 > .mt-5.flex .tos-premium-button:first-child {
  border: 1px solid rgba(52,202,147,.25) !important;
  background: linear-gradient(180deg,#162620 0%,#0d1b17 100%) !important;
  color: #8ce9c3 !important;
  box-shadow: 0 9px 21px rgba(0,0,0,.26),inset 0 1px rgba(255,255,255,.025) !important;
}
.dark .tos-smtp-settings-flagship-v1 > .mt-5.flex .tos-premium-button:last-child {
  border-color: #d59a22 !important;
  color: #160e02 !important;
  background: linear-gradient(180deg,#fff0ae 0%,#efc356 24%,#d4921b 61%,#a95d03 100%) !important;
  box-shadow: 0 12px 26px rgba(0,0,0,.34),0 0 17px rgba(231,170,47,.12),inset 0 1px rgba(255,255,255,.80) !important;
}

/* Test delivery panel: no pale/white strip in dark mode. */
.dark .tos-smtp-settings-flagship-v1 > div[class*="lg:grid-cols"] {
  border-color: rgba(52,201,147,.21) !important;
  background:
    radial-gradient(circle at 92% 12%,rgba(39,202,147,.08),transparent 25%),
    linear-gradient(145deg,#12201c 0%,#0b1714 100%) !important;
  box-shadow: 0 14px 30px rgba(0,0,0,.26),inset 0 1px rgba(255,255,255,.025) !important;
}
.dark .tos-smtp-settings-flagship-v1 > div[class*="lg:grid-cols"] .tos-premium-button {
  border: 1px solid rgba(63,214,160,.28) !important;
  background: linear-gradient(180deg,#153128 0%,#0d211b 100%) !important;
  color: #8cf0c7 !important;
  box-shadow: 0 8px 19px rgba(0,0,0,.24),inset 0 1px rgba(255,255,255,.025) !important;
}

/* Notices must stay dark, legible and premium. */
.dark .tos-smtp-settings-flagship-v1 .tos-premium-notice {
  box-shadow: inset 0 1px rgba(255,255,255,.025),0 8px 20px rgba(0,0,0,.20) !important;
}
.dark .tos-smtp-settings-flagship-v1 .tos-premium-notice.bg-amber-50,
.dark .tos-smtp-settings-flagship-v1 .tos-premium-notice.dark\:bg-amber-500\/10 {
  border-color: rgba(231,181,73,.24) !important;
  background: linear-gradient(180deg,rgba(61,43,11,.54),rgba(41,30,12,.56)) !important;
  color: #f1cf78 !important;
}

@media (max-width: 767px) {
  .dark .tos-premium-card.tos-smtp-settings-flagship-v1 {
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
    fail(f"SMTP V1 style missing: {V1_STYLE}")

source = PAGE.read_text()
v1_css = V1_STYLE.read_text()

for marker in [
    V1_IMPORT,
    SMTP_START,
    SMTP_END,
    'className="tos-smtp-settings-flagship-v1"',
    "api.emailSettings.status()",
    "api.emailSettings.update(payload)",
    "api.emailSettings.test({ to: form.testTo.trim() || undefined })",
    'SMTP Email Settings',
]:
    if marker not in source:
        fail(f"required SMTP V1 R1 baseline marker missing: {marker}")

if V1_RUNTIME not in v1_css:
    fail("required SMTP V1 runtime marker missing")
if V11_IMPORT in source or V11_STYLE.exists():
    fail("SMTP Settings Flagship Luxury V1.1 dark shell contrast fix already present")

smtp_start = source.index(SMTP_START)
smtp_end = source.index(SMTP_END, smtp_start)
smtp_segment = source[smtp_start:smtp_end]
for marker in [
    'className="tos-smtp-settings-flagship-v1"',
    "api.emailSettings.status()",
    "api.emailSettings.update(payload)",
    "api.emailSettings.test({ to: form.testTo.trim() || undefined })",
]:
    if marker not in smtp_segment:
        fail(f"SMTP scoped V1 R1 marker missing: {marker}")

stamp = int(time.time())
page_backup = PAGE.with_name(f"{PAGE.name}.smtp-settings-v1-1-dark-backup-{stamp}")
shutil.copy2(PAGE, page_backup)
live_backup = None
staging = None

try:
    source = source.replace(V1_IMPORT, V1_IMPORT + "\n" + V11_IMPORT, 1)
    if V11_IMPORT not in source:
        fail("SMTP V1.1 style import injection failed")

    PAGE.write_text(source)
    V11_STYLE.write_text(CSS)

    updated = PAGE.read_text()
    updated_smtp_start = updated.index(SMTP_START)
    updated_smtp_end = updated.index(SMTP_END, updated_smtp_start)
    updated_segment = updated[updated_smtp_start:updated_smtp_end]
    for marker in [
        V11_IMPORT,
        'className="tos-smtp-settings-flagship-v1"',
        "api.emailSettings.status()",
        "api.emailSettings.update(payload)",
        "api.emailSettings.test({ to: form.testTo.trim() || undefined })",
    ]:
        if marker == V11_IMPORT:
            if marker not in updated:
                fail(f"post-transform marker missing: {marker}")
        elif marker not in updated_segment:
            fail(f"post-transform SMTP marker missing: {marker}")

    if V11_RUNTIME not in V11_STYLE.read_text():
        fail("SMTP V1.1 runtime marker missing after style write")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists():
        fail("frontend dist missing after build")

    built_css = ""
    for css_file in DIST.rglob("*.css"):
        built_css += css_file.read_text(errors="ignore")
    if V11_RUNTIME not in built_css:
        fail("SMTP Settings V1.1 runtime marker missing from built CSS")
    if "#0c1317" not in built_css.lower():
        fail("SMTP Settings V1.1 dark shell rule missing from built CSS")

    LIVE_PARENT.mkdir(parents=True, exist_ok=True)
    staging = LIVE_PARENT / f"build.smtp-settings-v1-1-dark-staging-{stamp}"
    live_backup = LIVE_PARENT / f"build.smtp-settings-v1-1-dark-backup-{stamp}"
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
        fail("SMTP Settings V1.1 runtime marker missing from live CSS")
    if "#0c1317" not in live_css.lower():
        fail("SMTP Settings V1.1 dark shell rule missing from live CSS")

    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("SMTP_SETTINGS_FLAGSHIP_LUXURY_V1_1_RUNTIME=YES")
    print("SMTP_V1_R1_BASELINE=PRESERVED")
    print("SMTP_V11_SCOPE=DARK_SHELL_AND_CONTRAST_ONLY")
    print("SMTP_DARK_MAIN_SHELL=OBSIDIAN_TITANIUM_FIXED")
    print("SMTP_DARK_HEADER_CONTRAST=IVORY_CHAMPAGNE_FIXED")
    print("SMTP_DARK_CONFIGURATION_PANEL=INTEGRATED")
    print("SMTP_DARK_FIELDS=HIGH_CONTRAST")
    print("SMTP_DARK_ACTION_ROW=INTEGRATED")
    print("SMTP_DARK_TEST_PANEL=INTEGRATED")
    print("SMTP_LIGHT_MODE_CHANGED=NO")
    print("SMTP_API_CHANGED=NO")
    print("SMTP_SAVE_LOGIC_CHANGED=NO")
    print("SMTP_TEST_LOGIC_CHANGED=NO")
    print("SMTP_PERMISSIONS_CHANGED=NO")
    print("SMTP_DATA_CONTRACT_CHANGED=NO")
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
