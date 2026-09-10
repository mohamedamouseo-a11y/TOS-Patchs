from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
COMPONENT = FRONTEND / "src/components/RamzySettingsAdmin.jsx"
V1_STYLE = FRONTEND / "src/components/ramzySettingsFlagshipLuxuryV1.css"
V11_STYLE = FRONTEND / "src/components/ramzySettingsFlagshipLuxuryV1_1DarkFidelityContrast.css"
V12_STYLE = FRONTEND / "src/components/ramzySettingsFlagshipLuxuryV1_2AuditTextReadabilityPolish.css"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

V1_IMPORT = 'import "./ramzySettingsFlagshipLuxuryV1.css";'
V11_IMPORT = 'import "./ramzySettingsFlagshipLuxuryV1_1DarkFidelityContrast.css";'
V12_IMPORT = 'import "./ramzySettingsFlagshipLuxuryV1_2AuditTextReadabilityPolish.css";'
V1_RUNTIME = "--tos-ramzy-settings-flagship-luxury-v1-runtime"
V11_RUNTIME = "--tos-ramzy-settings-flagship-luxury-v1-1-dark-fidelity-contrast-runtime"
V12_RUNTIME = "--tos-ramzy-settings-flagship-luxury-v1-2-audit-text-readability-runtime"

CSS = r'''
:root { --tos-ramzy-settings-flagship-luxury-v1-2-audit-text-readability-runtime: 1; }

/* =========================================================
   TOS Settings → Ramzy AI — Flagship Luxury V1.2
   Final dark audit text readability polish only.
   No layout, API, agent, provider, memory, save, permissions,
   audit behavior, light theme, or other module changes.
   ========================================================= */

/* Audit body text: lift one restrained step without washing out dark mode. */
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(4) table tbody td {
  color: #d7dde1 !important;
  font-weight: 600;
  text-shadow: 0 1px 0 rgba(0,0,0,.30);
}

/* Time + provider/model should read clearly but remain secondary. */
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(4) table tbody td:nth-child(1),
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(4) table tbody td:nth-child(2) {
  color: #cfd7dc !important;
}

/* Status is the primary scan target. */
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(4) table tbody td:nth-child(3) {
  color: #dff7ec !important;
  font-weight: 900 !important;
  letter-spacing: .012em;
}

/* User ID needs enough contrast for operational tracing without becoming dominant. */
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(4) table tbody td:nth-child(4) {
  color: #c8d1d7 !important;
}

/* Error column remains semantically red, but lighter and readable. */
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(4) table tbody td:last-child {
  color: #ff9f96 !important;
  font-weight: 650;
}

/* Header labels: slightly brighter champagne titanium. */
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(4) table thead th {
  color: #e4d7bf !important;
  text-shadow: 0 1px 0 rgba(0,0,0,.32);
}

/* Gentle row separation improves readability in long audit tables. */
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(4) table tbody td {
  border-bottom-color: rgba(235,190,88,.105) !important;
}

/* Hover remains premium and improves active-row reading. */
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(4) table tbody tr:hover td {
  background: rgba(236,187,75,.045) !important;
  color: #f4efe8 !important;
}
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(4) table tbody tr:hover td:nth-child(3) {
  color: #e8fff5 !important;
}
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(4) table tbody tr:hover td:last-child {
  color: #ffaaa2 !important;
}
'''


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


if not COMPONENT.exists():
    fail(f"Ramzy settings component missing: {COMPONENT}")
if not V1_STYLE.exists():
    fail(f"Ramzy Settings V1 style missing: {V1_STYLE}")
if not V11_STYLE.exists():
    fail(f"Ramzy Settings V1.1 style missing: {V11_STYLE}")

source = COMPONENT.read_text()
v1_style_text = V1_STYLE.read_text()
v11_style_text = V11_STYLE.read_text()

for marker in [
    V1_IMPORT,
    V11_IMPORT,
    "tos-ramzy-settings-flagship-v1",
    "Ramzy Runtime Audit",
    "api.agent.audit()",
    "api.agent.updateSettings(payload)",
    "api.agent.clearMemory()",
]:
    if marker not in source:
        fail(f"required Ramzy Settings V1.1 baseline marker missing: {marker}")

if V1_RUNTIME not in v1_style_text:
    fail("required Ramzy Settings V1 runtime marker missing")
if V11_RUNTIME not in v11_style_text:
    fail("required Ramzy Settings V1.1 runtime marker missing")
if V12_IMPORT in source or V12_STYLE.exists():
    fail("Ramzy Settings V1.2 audit text readability polish already present")

stamp = int(time.time())
component_backup = COMPONENT.with_name(f"{COMPONENT.name}.ramzy-settings-v1-2-backup-{stamp}")
shutil.copy2(COMPONENT, component_backup)
live_backup = None
staging = None

try:
    source = source.replace(V11_IMPORT, V11_IMPORT + "\n" + V12_IMPORT, 1)
    if V12_IMPORT not in source:
        fail("V1.2 style import injection failed")

    COMPONENT.write_text(source)
    V12_STYLE.write_text(CSS)

    updated = COMPONENT.read_text()
    if V12_IMPORT not in updated:
        fail("V1.2 style import missing after write")
    if V12_RUNTIME not in V12_STYLE.read_text():
        fail("V1.2 runtime marker missing after style write")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists():
        fail("frontend dist missing after build")

    built_css = ""
    for css_file in DIST.rglob("*.css"):
        built_css += css_file.read_text(errors="ignore")
    if V12_RUNTIME not in built_css:
        fail("Ramzy Settings V1.2 runtime marker missing from built CSS")
    if "#d7dde1" not in built_css.lower():
        fail("Ramzy Settings V1.2 audit body contrast rule missing from built CSS")

    LIVE_PARENT.mkdir(parents=True, exist_ok=True)
    staging = LIVE_PARENT / f"build.ramzy-settings-v1-2-audit-text-staging-{stamp}"
    live_backup = LIVE_PARENT / f"build.ramzy-settings-v1-2-audit-text-backup-{stamp}"
    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(DIST, staging)

    if LIVE.exists():
        LIVE.rename(live_backup)
    staging.rename(LIVE)

    live_css = ""
    for css_file in LIVE.rglob("*.css"):
        live_css += css_file.read_text(errors="ignore")
    if V12_RUNTIME not in live_css:
        fail("Ramzy Settings V1.2 runtime marker missing from live build")
    if "#d7dde1" not in live_css.lower():
        fail("Ramzy Settings V1.2 audit body contrast rule missing from live build")

    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("RAMZY_SETTINGS_FLAGSHIP_LUXURY_V1_2_RUNTIME=YES")
    print("RAMZY_V1_1_BASELINE=PRESERVED")
    print("RAMZY_V12_SCOPE=DARK_AUDIT_TEXT_READABILITY_ONLY")
    print("RAMZY_DARK_AUDIT_BODY_TEXT=BRIGHTER_TITANIUM_IVORY")
    print("RAMZY_DARK_AUDIT_HEADER_TEXT=BRIGHTER_CHAMPAGNE")
    print("RAMZY_DARK_AUDIT_STATUS_TEXT=HIGH_CONTRAST_SUCCESS")
    print("RAMZY_DARK_AUDIT_ERROR_TEXT=HIGH_CONTRAST_CORAL")
    print("RAMZY_DARK_AUDIT_ROW_SEPARATION=ENHANCED")
    print("RAMZY_LIGHT_MODE_CHANGED=NO")
    print("RAMZY_LAYOUT_CHANGED=NO")
    print("RAMZY_AGENT_LOGIC_CHANGED=NO")
    print("RAMZY_API_CHANGED=NO")
    print("RAMZY_PERMISSIONS_CHANGED=NO")
    print("RAMZY_SAVE_LOGIC_CHANGED=NO")
    print("RAMZY_MEMORY_LOGIC_CHANGED=NO")
    print("RAMZY_PROVIDER_LOGIC_CHANGED=NO")
    print("RAMZY_AUDIT_LOGIC_CHANGED=NO")
    print("TWS_CHANGED=NO")
    print("SLA_CHANGED=NO")
    print("TCS_CHANGED=NO")
    print(f"LIVE_BACKUP={live_backup if live_backup and live_backup.exists() else 'NONE'}")
    print("STATUS=READY")
except Exception as exc:
    try:
        if component_backup.exists():
            shutil.copy2(component_backup, COMPONENT)
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
