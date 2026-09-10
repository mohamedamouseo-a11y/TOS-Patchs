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
V12_STYLE = FRONTEND / "src/pages/smtpSettingsFlagshipLuxuryV1_2DarkFieldValueContrastFix.css"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

V1_IMPORT = 'import "./smtpSettingsFlagshipLuxuryV1.css";'
V11_IMPORT = 'import "./smtpSettingsFlagshipLuxuryV1_1DarkShellContrastFix.css";'
V12_IMPORT = 'import "./smtpSettingsFlagshipLuxuryV1_2DarkFieldValueContrastFix.css";'
V1_RUNTIME = "--tos-smtp-settings-flagship-luxury-v1-runtime"
V11_RUNTIME = "--tos-smtp-settings-flagship-luxury-v1-1-dark-shell-contrast-runtime"
V12_RUNTIME = "--tos-smtp-settings-flagship-luxury-v1-2-dark-field-value-contrast-runtime"
SMTP_START = "function EmailSettingsAdmin({ user })"
SMTP_END = "\nfunction GoogleDriveAdmin({ user })"

CSS = r'''
:root { --tos-smtp-settings-flagship-luxury-v1-2-dark-field-value-contrast-runtime: 1; }

/* =========================================================
   TOS Settings → SMTP Email — Flagship Luxury V1.2
   DARK FIELD VALUE CONTRAST FIX ONLY
   Light mode intentionally untouched.
   No layout / SMTP API / save / test / permissions / data changes.
   ========================================================= */

/*
 * Explicit input-level selectors + -webkit-text-fill-color are intentional.
 * This prevents browser/autofill/native input paint from leaving the actual
 * SMTP values visually dark while the surrounding V1.1 shell is dark.
 */
html.dark .tos-smtp-settings-flagship-v1 input.tos-premium-field,
html.dark .tos-smtp-settings-flagship-v1 input.tos-input,
.dark .tos-smtp-settings-flagship-v1 input.tos-premium-field,
.dark .tos-smtp-settings-flagship-v1 input.tos-input {
  color: #f5efe7 !important;
  -webkit-text-fill-color: #f5efe7 !important;
  caret-color: #efc765 !important;
  opacity: 1 !important;
}

/* Keep numeric/host/user/from/password values equally legible. */
.dark .tos-smtp-settings-flagship-v1 input[type="text"],
.dark .tos-smtp-settings-flagship-v1 input[type="number"],
.dark .tos-smtp-settings-flagship-v1 input[type="email"],
.dark .tos-smtp-settings-flagship-v1 input[type="password"] {
  color: #f5efe7 !important;
  -webkit-text-fill-color: #f5efe7 !important;
  opacity: 1 !important;
}

/* Saved-password / optional-test placeholders: secondary, but readable. */
.dark .tos-smtp-settings-flagship-v1 input.tos-premium-field::placeholder,
.dark .tos-smtp-settings-flagship-v1 input.tos-input::placeholder,
.dark .tos-smtp-settings-flagship-v1 input[type="text"]::placeholder,
.dark .tos-smtp-settings-flagship-v1 input[type="number"]::placeholder,
.dark .tos-smtp-settings-flagship-v1 input[type="email"]::placeholder,
.dark .tos-smtp-settings-flagship-v1 input[type="password"]::placeholder {
  color: #aab4bc !important;
  -webkit-text-fill-color: #aab4bc !important;
  opacity: 1 !important;
}

/* Disabled/read-only states stay readable without looking active. */
.dark .tos-smtp-settings-flagship-v1 input.tos-premium-field:disabled,
.dark .tos-smtp-settings-flagship-v1 input.tos-input:disabled,
.dark .tos-smtp-settings-flagship-v1 input.tos-premium-field[readonly],
.dark .tos-smtp-settings-flagship-v1 input.tos-input[readonly] {
  color: #d8e0e4 !important;
  -webkit-text-fill-color: #d8e0e4 !important;
  opacity: .78 !important;
}

/* Chromium/WebKit autofill must not reintroduce dark text or pale fill. */
.dark .tos-smtp-settings-flagship-v1 input.tos-premium-field:-webkit-autofill,
.dark .tos-smtp-settings-flagship-v1 input.tos-premium-field:-webkit-autofill:hover,
.dark .tos-smtp-settings-flagship-v1 input.tos-premium-field:-webkit-autofill:focus,
.dark .tos-smtp-settings-flagship-v1 input.tos-input:-webkit-autofill,
.dark .tos-smtp-settings-flagship-v1 input.tos-input:-webkit-autofill:hover,
.dark .tos-smtp-settings-flagship-v1 input.tos-input:-webkit-autofill:focus {
  -webkit-text-fill-color: #f5efe7 !important;
  caret-color: #efc765 !important;
  -webkit-box-shadow: 0 0 0 1000px #11191d inset !important;
  box-shadow: 0 0 0 1000px #11191d inset !important;
  transition: background-color 9999s ease-out 0s;
}

/* Focus keeps the premium emerald signal introduced in V1/V1.1. */
.dark .tos-smtp-settings-flagship-v1 input.tos-premium-field:focus,
.dark .tos-smtp-settings-flagship-v1 input.tos-input:focus {
  color: #fff8ee !important;
  -webkit-text-fill-color: #fff8ee !important;
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
if not V11_STYLE.exists():
    fail(f"SMTP V1.1 style missing: {V11_STYLE}")

source = PAGE.read_text()
v1_css = V1_STYLE.read_text()
v11_css = V11_STYLE.read_text()

for marker in [
    V1_IMPORT,
    V11_IMPORT,
    SMTP_START,
    SMTP_END,
    'className="tos-smtp-settings-flagship-v1"',
    "api.emailSettings.status()",
    "api.emailSettings.update(payload)",
    "api.emailSettings.test({ to: form.testTo.trim() || undefined })",
    'SMTP Email Settings',
]:
    if marker not in source:
        fail(f"required SMTP V1.1 baseline marker missing: {marker}")

if V1_RUNTIME not in v1_css:
    fail("required SMTP V1 runtime marker missing")
if V11_RUNTIME not in v11_css:
    fail("required SMTP V1.1 runtime marker missing")
if V12_IMPORT in source or V12_STYLE.exists():
    fail("SMTP Settings Flagship Luxury V1.2 dark field value contrast fix already present")

smtp_start = source.index(SMTP_START)
smtp_end = source.index(SMTP_END, smtp_start)
smtp_segment = source[smtp_start:smtp_end]
for marker in [
    'className="tos-smtp-settings-flagship-v1"',
    "api.emailSettings.status()",
    "api.emailSettings.update(payload)",
    "api.emailSettings.test({ to: form.testTo.trim() || undefined })",
    'placeholder="SMTP Host"',
    'placeholder="SMTP Port"',
    'placeholder="SMTP User"',
    'placeholder="From Email"',
]:
    if marker not in smtp_segment:
        fail(f"SMTP scoped V1.1 marker missing: {marker}")

stamp = int(time.time())
page_backup = PAGE.with_name(f"{PAGE.name}.smtp-settings-v1-2-field-contrast-backup-{stamp}")
shutil.copy2(PAGE, page_backup)
live_backup = None
staging = None

try:
    source = source.replace(V11_IMPORT, V11_IMPORT + "\n" + V12_IMPORT, 1)
    if V12_IMPORT not in source:
        fail("SMTP V1.2 style import injection failed")

    PAGE.write_text(source)
    V12_STYLE.write_text(CSS)

    updated = PAGE.read_text()
    updated_start = updated.index(SMTP_START)
    updated_end = updated.index(SMTP_END, updated_start)
    updated_segment = updated[updated_start:updated_end]
    for marker in [
        V12_IMPORT,
        'className="tos-smtp-settings-flagship-v1"',
        "api.emailSettings.status()",
        "api.emailSettings.update(payload)",
        "api.emailSettings.test({ to: form.testTo.trim() || undefined })",
    ]:
        if marker == V12_IMPORT:
            if marker not in updated:
                fail(f"post-transform marker missing: {marker}")
        elif marker not in updated_segment:
            fail(f"post-transform SMTP marker missing: {marker}")

    if V12_RUNTIME not in V12_STYLE.read_text():
        fail("SMTP V1.2 runtime marker missing after style write")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists():
        fail("frontend dist missing after build")

    built_css = ""
    for css_file in DIST.rglob("*.css"):
        built_css += css_file.read_text(errors="ignore")
    lower_built = built_css.lower()
    if V12_RUNTIME not in built_css:
        fail("SMTP Settings V1.2 runtime marker missing from built CSS")
    if "-webkit-text-fill-color:#f5efe7" not in lower_built.replace(" ", ""):
        fail("SMTP V1.2 high-contrast field value rule missing from built CSS")

    LIVE_PARENT.mkdir(parents=True, exist_ok=True)
    staging = LIVE_PARENT / f"build.smtp-settings-v1-2-field-contrast-staging-{stamp}"
    live_backup = LIVE_PARENT / f"build.smtp-settings-v1-2-field-contrast-backup-{stamp}"
    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(DIST, staging)

    if LIVE.exists():
        LIVE.rename(live_backup)
    staging.rename(LIVE)

    live_css = ""
    for css_file in LIVE.rglob("*.css"):
        live_css += css_file.read_text(errors="ignore")
    lower_live = live_css.lower()
    if V12_RUNTIME not in live_css:
        fail("SMTP Settings V1.2 runtime marker missing from live build")
    if "-webkit-text-fill-color:#f5efe7" not in lower_live.replace(" ", ""):
        fail("SMTP V1.2 high-contrast field value rule missing from live build")

    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("SMTP_SETTINGS_FLAGSHIP_LUXURY_V1_2_RUNTIME=YES")
    print("SMTP_V1_1_BASELINE=PRESERVED")
    print("SMTP_V12_SCOPE=DARK_FIELD_VALUE_CONTRAST_ONLY")
    print("SMTP_DARK_FIELD_VALUES=IVORY_HIGH_CONTRAST")
    print("SMTP_DARK_PLACEHOLDERS=TITANIUM_HIGH_CONTRAST")
    print("SMTP_DARK_AUTOFILL_TEXT=IVORY_HIGH_CONTRAST")
    print("SMTP_DARK_DISABLED_READONLY_TEXT=READABLE_TITANIUM")
    print("SMTP_LIGHT_MODE_CHANGED=NO")
    print("SMTP_LAYOUT_CHANGED=NO")
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
        if V12_STYLE.exists():
            V12_STYLE.unlink()
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
