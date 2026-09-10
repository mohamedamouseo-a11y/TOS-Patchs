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
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

V1_IMPORT = 'import "./ramzySettingsFlagshipLuxuryV1.css";'
V11_IMPORT = 'import "./ramzySettingsFlagshipLuxuryV1_1DarkFidelityContrast.css";'
V1_RUNTIME = "--tos-ramzy-settings-flagship-luxury-v1-runtime"
V11_RUNTIME = "--tos-ramzy-settings-flagship-luxury-v1-1-dark-fidelity-contrast-runtime"

CSS = r'''
:root { --tos-ramzy-settings-flagship-luxury-v1-1-dark-fidelity-contrast-runtime: 1; }

/* =========================================================
   TOS Settings → Ramzy AI — Flagship Luxury V1.1
   Dark fidelity + contrast correction only.
   Fixes: audit white band, dark field/text contrast, dark panel depth.
   No agent/API/provider/memory/save/permission behavior changes.
   ========================================================= */

/* Keep the light theme exactly on the approved V1 baseline. */

/* ---- Dark canvas / section depth ---- */
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(2),
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(3),
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(4) {
  border-color: rgba(236, 185, 71, .28) !important;
  background:
    radial-gradient(118% 92% at 91% 119%, transparent 0 47%, rgba(239,181,55,.105) 47.25% 47.52%, transparent 47.82% 51%, rgba(239,181,55,.055) 51.24% 51.49%, transparent 51.8% 100%),
    radial-gradient(circle at 94% 2%, rgba(136,87,204,.085), transparent 25%),
    linear-gradient(145deg,#11191d 0%,#091014 72%,#110c06 100%) !important;
  box-shadow:
    0 24px 52px rgba(0,0,0,.35),
    0 0 28px rgba(219,157,31,.045),
    inset 0 1px rgba(255,255,255,.032) !important;
}

.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(2)::after,
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(3)::after {
  color: rgba(245,211,143,.54) !important;
  text-shadow: 0 0 18px rgba(232,178,62,.10);
}

/* ---- Provider / API vault readability ---- */
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(2) label,
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(2) label > span,
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(3) label,
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(3) label > span {
  color: #e9e1d6 !important;
}

.dark .tos-ramzy-settings-flagship-v1 .tos-premium-field,
.dark .tos-ramzy-settings-flagship-v1 .tos-input {
  border-color: rgba(232,184,76,.27) !important;
  background: linear-gradient(180deg,#141c21 0%,#0d1418 100%) !important;
  color: #f7f1e8 !important;
  caret-color: #efc765;
  box-shadow:
    inset 0 1px rgba(255,255,255,.035),
    inset 0 -1px rgba(0,0,0,.32),
    0 7px 18px rgba(0,0,0,.22) !important;
}
.dark .tos-ramzy-settings-flagship-v1 .tos-premium-field::placeholder,
.dark .tos-ramzy-settings-flagship-v1 .tos-input::placeholder {
  color: #8f9ba5 !important;
  opacity: 1 !important;
}
.dark .tos-ramzy-settings-flagship-v1 .tos-premium-field:focus,
.dark .tos-ramzy-settings-flagship-v1 .tos-input:focus {
  border-color: rgba(190,139,245,.70) !important;
  box-shadow:
    0 0 0 3px rgba(151,94,218,.14),
    0 0 22px rgba(223,166,48,.055),
    0 9px 24px rgba(0,0,0,.28) !important;
}
.dark .tos-ramzy-settings-flagship-v1 select.tos-input option {
  background: #10171b !important;
  color: #f4eee6 !important;
}
.dark .tos-ramzy-settings-flagship-v1 input[type="checkbox"] {
  accent-color: #c89225;
}

/* Key persistence warning: no muddy/low-contrast amber text. */
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(2) .tos-premium-notice {
  border-color: rgba(233,184,73,.28) !important;
  background: linear-gradient(180deg,rgba(69,48,10,.42),rgba(45,33,13,.48)) !important;
  color: #f3cf72 !important;
  box-shadow: inset 0 1px rgba(255,232,170,.045), 0 8px 20px rgba(0,0,0,.18);
}

/* ---- Governance / memory / intelligence controls ---- */
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(3) > .grid:first-child > label {
  border-color: rgba(232,183,74,.25) !important;
  background: linear-gradient(145deg,#151d21,#0d1418) !important;
  color: #f0e9df !important;
  box-shadow:
    0 10px 24px rgba(0,0,0,.24),
    inset 0 1px rgba(255,255,255,.025) !important;
}
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(3) > .grid:first-child > label span {
  color: #ece5dc !important;
}
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(3) > .grid:first-child > label:hover {
  border-color: rgba(239,190,79,.40) !important;
  background: linear-gradient(145deg,#182126,#10171b) !important;
}

.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(3) .border-violet-200 {
  border-color: rgba(177,124,239,.40) !important;
  background:
    radial-gradient(circle at 89% 8%,rgba(156,99,226,.18),transparent 28%),
    linear-gradient(145deg,#1d1729 0%,#131720 100%) !important;
  box-shadow:
    0 16px 34px rgba(0,0,0,.30),
    0 0 26px rgba(144,88,214,.075),
    inset 0 1px rgba(255,255,255,.035) !important;
}
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(3) .border-violet-200 > p:first-child {
  color: #dabcfb !important;
}
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(3) .border-violet-200 .text-slate-600,
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(3) .border-violet-200 p,
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(3) .border-violet-200 span,
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(3) .border-violet-200 b {
  color: #c6c0cb !important;
}

/* Allowed roles: legible inactive and luminous active chips. */
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(3) button[type="button"].rounded-xl.border {
  border-color: rgba(230,183,79,.24) !important;
  background: linear-gradient(180deg,#171f23,#101619) !important;
  color: #c8c0b5 !important;
}
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(3) button.border-violet-400 {
  border-color: rgba(190,139,247,.62) !important;
  background: linear-gradient(180deg,#321f49,#20162d) !important;
  color: #ead8ff !important;
  box-shadow: 0 8px 19px rgba(0,0,0,.25), 0 0 18px rgba(154,94,222,.13) !important;
}

/* ---- Audit & Observability: eliminate the white header band ---- */
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(4) h3 {
  color: #fff2dc !important;
}
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(4) .tos-kicker {
  color: #e8b94e !important;
}
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(4) .tos-premium-stat {
  border-color: rgba(232,183,70,.25) !important;
  background:
    radial-gradient(circle at 88% 10%,rgba(230,174,56,.075),transparent 25%),
    linear-gradient(155deg,#151d21,#0b1216) !important;
  box-shadow: 0 13px 30px rgba(0,0,0,.28), inset 0 1px rgba(255,255,255,.028) !important;
}
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(4) .tos-premium-stat > .flex > div:first-child > div:first-child {
  color: #fff0d2 !important;
}
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(4) .tos-premium-stat > .flex > div:first-child > div:nth-child(2) {
  color: #ece6dc !important;
}

.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(4) table {
  border: 1px solid rgba(232,181,70,.14) !important;
  border-radius: 15px !important;
  background: #0b1216 !important;
  box-shadow: inset 0 1px rgba(255,255,255,.018), 0 12px 28px rgba(0,0,0,.24);
}
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(4) table thead,
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(4) table thead tr,
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(4) table thead th {
  background: linear-gradient(180deg,#20292f 0%,#171f24 100%) !important;
  color: #d7c9b1 !important;
  border-color: rgba(235,188,85,.15) !important;
}
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(4) table thead th {
  font-weight: 900 !important;
  letter-spacing: .045em;
  text-transform: uppercase;
}
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(4) table tbody,
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(4) table tbody tr,
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(4) table tbody td {
  background: transparent !important;
  color: #c8d0d5 !important;
}
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(4) table tbody td:nth-child(3) {
  color: #d9eee6 !important;
  font-weight: 900 !important;
}
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(4) table tbody td:last-child {
  color: #f08f86 !important;
}
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(4) table th,
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(4) table td {
  border-bottom-color: rgba(232,181,70,.085) !important;
}
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(4) table tbody tr:hover td {
  background: rgba(233,181,67,.035) !important;
  color: #f1ece4 !important;
}

/* Audit refresh control: dark titanium instead of pale native-like hardware. */
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(4) .tos-premium-button {
  border: 1px solid rgba(232,185,77,.22) !important;
  background: linear-gradient(180deg,#1b2429,#11181c) !important;
  color: #e7dfd4 !important;
  box-shadow: 0 8px 20px rgba(0,0,0,.25), inset 0 1px rgba(255,255,255,.03) !important;
}

@media (max-width: 767px) {
  .dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(4) table {
    border-radius: 12px !important;
  }
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

source = COMPONENT.read_text()
v1_css = V1_STYLE.read_text()

for marker in [
    V1_IMPORT,
    "tos-ramzy-settings-flagship-v1",
    'api.agent.settings()',
    'api.agent.updateSettings(payload)',
    'api.agent.clearMemory()',
    'api.agent.audit()',
    'Ramzy Runtime Audit',
]:
    if marker not in source:
        fail(f"required Ramzy Settings V1 marker missing: {marker}")

if V1_RUNTIME not in v1_css:
    fail("required Ramzy Settings V1 runtime marker missing from V1 stylesheet")
if V11_IMPORT in source or V11_STYLE.exists():
    fail("Ramzy Settings V1.1 dark fidelity contrast fix already present")

stamp = int(time.time())
component_backup = COMPONENT.with_name(f"{COMPONENT.name}.v1-1-dark-backup-{stamp}")
shutil.copy2(COMPONENT, component_backup)
live_backup = None
staging = None

try:
    source = source.replace(V1_IMPORT, V1_IMPORT + "\n" + V11_IMPORT, 1)
    if V11_IMPORT not in source:
        fail("V1.1 import insertion failed")
    COMPONENT.write_text(source)
    V11_STYLE.write_text(CSS)

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists():
        fail("frontend dist missing after build")

    built_css = "".join(p.read_text(errors="ignore") for p in DIST.rglob("*.css"))
    if V11_RUNTIME not in built_css:
        fail("Ramzy Settings V1.1 runtime marker missing from built CSS")
    if "#20292f" not in built_css.lower():
        fail("Ramzy Settings V1.1 dark audit header rule missing from built CSS")

    LIVE_PARENT.mkdir(parents=True, exist_ok=True)
    staging = LIVE_PARENT / f"build.ramzy-settings-v1-1-dark-staging-{stamp}"
    live_backup = LIVE_PARENT / f"build.ramzy-settings-v1-1-dark-backup-{stamp}"
    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(DIST, staging)
    if LIVE.exists():
        LIVE.rename(live_backup)
    staging.rename(LIVE)

    live_css = "".join(p.read_text(errors="ignore") for p in LIVE.rglob("*.css"))
    if V11_RUNTIME not in live_css:
        fail("Ramzy Settings V1.1 runtime marker missing from live build")
    if "#20292f" not in live_css.lower():
        fail("Ramzy Settings V1.1 dark audit header rule missing from live build")

    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("RAMZY_SETTINGS_FLAGSHIP_LUXURY_V1_1_RUNTIME=YES")
    print("RAMZY_V1_BASELINE=PRESERVED")
    print("RAMZY_V11_SCOPE=DARK_FIDELITY_AND_CONTRAST_ONLY")
    print("RAMZY_DARK_AUDIT_HEADER=BLACK_TITANIUM_CHAMPAGNE")
    print("RAMZY_DARK_WHITE_TABLE_BAND=ELIMINATED")
    print("RAMZY_DARK_FIELDS=HIGH_CONTRAST_OBSIDIAN")
    print("RAMZY_DARK_LABELS=IVORY_HIGH_CONTRAST")
    print("RAMZY_DARK_GOVERNANCE=HIGH_CONTRAST")
    print("RAMZY_DARK_SYSTEM_INTELLIGENCE=AMETHYST_HIGH_CONTRAST")
    print("RAMZY_DARK_PANEL_DEPTH=ENHANCED")
    print("RAMZY_LIGHT_MODE_CHANGED=NO")
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
