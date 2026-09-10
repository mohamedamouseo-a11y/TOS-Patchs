from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
COMPONENT = FRONTEND / "src/components/settings/TgwsSettingsAdmin.jsx"
STYLE = FRONTEND / "src/components/settings/TgwsSettingsFlagshipLuxuryV1.css"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_COMPONENT_GIT_BLOB = "3c204637663927fced0d5786ad7f2d0e66848933"
IMPORT_ANCHOR = 'import { Badge, Button, Card, Notice, StatCard } from "../ui/Primitives";'
IMPORT_STYLE = 'import "./TgwsSettingsFlagshipLuxuryV1.css";'
ROOT_OLD = '<div className="space-y-5">'
ROOT_NEW = '<div className="tos-tgws-settings-flagship-v1 space-y-5">'
RUNTIME_MARKER = "--tos-tgws-settings-flagship-luxury-v1-runtime"

CSS = r'''
:root { --tos-tgws-settings-flagship-luxury-v1-runtime: 1; }

/* =========================================================
   TOS Settings → TGWS — Flagship Luxury V1
   Light: pearl / ivory / champagne + Google spectrum accents
   Dark: obsidian / titanium / champagne + sapphire / emerald
   Visual only. TGWS API, persistence, mapping and policy logic untouched.
   ========================================================= */

.tos-tgws-settings-flagship-v1 {
  --tgws-gold: #c68a18;
  --tgws-gold-soft: #efd07b;
  --tgws-blue: #3b82f6;
  --tgws-emerald: #18a873;
  position: relative;
}

/* All three functional cards share one flagship hardware language. */
.tos-tgws-settings-flagship-v1 > .tos-premium-card {
  position: relative;
  isolation: isolate;
  overflow: hidden;
  padding: 28px !important;
  border: 1px solid rgba(177,116,18,.23) !important;
  border-radius: 30px !important;
  background:
    radial-gradient(120% 105% at 82% 134%,transparent 0 40%,rgba(194,129,18,.10) 40.25% 40.5%,transparent 40.8% 44%,rgba(194,129,18,.048) 44.25% 44.46%,transparent 44.76% 100%),
    radial-gradient(circle at 94% 4%,rgba(59,130,246,.075),transparent 26%),
    linear-gradient(143deg,#fffefa 0%,#fffaf1 58%,#f7ecd9 100%) !important;
  box-shadow: 0 22px 50px rgba(75,45,4,.075),inset 0 1px rgba(255,255,255,.98) !important;
}

.tos-tgws-settings-flagship-v1 > .tos-premium-card::before {
  content: "";
  position: absolute;
  inset-block: 24px;
  inset-inline-start: 0;
  width: 3px;
  border-radius: 999px;
  background: linear-gradient(180deg,#f7d675,#c88816 58%,#744100 100%);
  box-shadow: 0 0 18px rgba(213,151,31,.16);
  pointer-events: none;
}

.tos-tgws-settings-flagship-v1 > .tos-premium-card::after {
  position: absolute;
  top: 22px;
  inset-inline-end: 26px;
  font-size: 8px;
  font-weight: 950;
  letter-spacing: .18em;
  text-transform: uppercase;
  pointer-events: none;
  opacity: .35;
}
.tos-tgws-settings-flagship-v1 > .tos-premium-card:nth-of-type(1)::after { content:"WORKSPACE  •  CONTROL PLANE"; color:#346f9c; }
.tos-tgws-settings-flagship-v1 > .tos-premium-card:nth-of-type(2)::after { content:"IDENTITY  •  EDITOR MAPPING"; color:#6b4e87; }
.tos-tgws-settings-flagship-v1 > .tos-premium-card:nth-of-type(3)::after { content:"POLICY  •  GOVERNANCE"; color:#8a6116; }

/* Executive section titles. */
.tos-tgws-settings-flagship-v1 .tos-kicker {
  color:#9a650c !important;
  letter-spacing:.17em;
  text-transform:uppercase;
}
.tos-tgws-settings-flagship-v1 h3 {
  color:#21190f;
  letter-spacing:-.025em;
}
.tos-tgws-settings-flagship-v1 > .tos-premium-card:first-child h3 {
  font-family: Georgia,"Times New Roman",serif;
  font-size: clamp(1.9rem,2.7vw,2.55rem) !important;
  letter-spacing:-.035em;
}
.tos-tgws-settings-flagship-v1 .tos-muted {
  color:#746b62 !important;
  font-weight:700;
}

/* Header status badges become polished telemetry pills. */
.tos-tgws-settings-flagship-v1 .tos-premium-badge {
  min-height:28px;
  border-radius:999px !important;
  padding-inline:11px !important;
  box-shadow: inset 0 1px rgba(255,255,255,.75),0 5px 12px rgba(63,42,9,.04);
}

/* Seven TGWS runtime KPI cards. */
.tos-tgws-settings-flagship-v1 .tos-premium-stat {
  min-height:132px;
  padding:17px !important;
  border:1px solid rgba(164,106,15,.16) !important;
  border-radius:19px !important;
  background:
    radial-gradient(circle at 88% 8%,rgba(64,136,215,.07),transparent 26%),
    linear-gradient(155deg,rgba(255,255,255,.98),rgba(251,247,238,.95)) !important;
  box-shadow:0 10px 24px rgba(69,42,4,.045),inset 0 1px rgba(255,255,255,.98) !important;
  transform:none !important;
}
.tos-tgws-settings-flagship-v1 .tos-premium-stat > .flex > div:first-child > div:first-child {
  font-family:Georgia,"Times New Roman",serif;
  font-size:1.12rem !important;
  color:#261b10 !important;
  line-height:1.14;
}
.tos-tgws-settings-flagship-v1 .tos-premium-stat > .flex > div:first-child > div:nth-child(2) {
  color:#3a3228 !important;
  font-weight:850 !important;
}
.tos-tgws-settings-flagship-v1 .tos-premium-stat > .flex > div:first-child > div:nth-child(3) { color:#8b8175 !important; }
.tos-tgws-settings-flagship-v1 .tos-premium-stat > .flex > div:last-child {
  width:42px !important;
  height:42px !important;
  border-radius:999px !important;
  box-shadow:0 7px 18px rgba(57,73,90,.08),inset 0 1px rgba(255,255,255,.88);
}

/* Notices: executive alert rails. */
.tos-tgws-settings-flagship-v1 .tos-premium-notice {
  border-radius:16px !important;
  line-height:1.65;
  box-shadow:inset 0 1px rgba(255,255,255,.55),0 7px 18px rgba(65,46,15,.035);
}

/* Identity mapping command center. */
.tos-tgws-settings-flagship-v1 > .tos-premium-card:nth-of-type(2) {
  background:
    radial-gradient(circle at 92% 4%,rgba(120,82,176,.07),transparent 24%),
    radial-gradient(115% 100% at 82% 134%,transparent 0 42%,rgba(193,128,20,.07) 42.25% 42.50%,transparent 42.8% 100%),
    linear-gradient(143deg,#fffefa,#fbf8f4 60%,#f4ebdc) !important;
}
.tos-tgws-settings-flagship-v1 > .tos-premium-card:nth-of-type(2) > .relative {
  max-width:680px !important;
}
.tos-tgws-settings-flagship-v1 > .tos-premium-card:nth-of-type(2) > .relative input {
  min-height:48px;
  border:1px solid rgba(126,92,161,.18) !important;
  border-radius:15px !important;
  background:linear-gradient(180deg,#fff,#fcf9ff) !important;
  color:#2a2130 !important;
  box-shadow:inset 0 1px rgba(255,255,255,.98),0 5px 14px rgba(74,51,95,.04);
}
.tos-tgws-settings-flagship-v1 > .tos-premium-card:nth-of-type(2) > .relative input:focus {
  border-color:rgba(163,117,39,.55) !important;
  box-shadow:0 0 0 3px rgba(197,141,29,.09),0 8px 18px rgba(59,40,83,.06) !important;
}

/* Mapping table hardware. */
.tos-tgws-settings-flagship-v1 > .tos-premium-card:nth-of-type(2) > .mt-5.overflow-hidden {
  border-color:rgba(150,105,24,.14) !important;
  border-radius:20px !important;
  box-shadow:0 10px 24px rgba(54,37,8,.035),inset 0 1px rgba(255,255,255,.75);
}
.tos-tgws-settings-flagship-v1 > .tos-premium-card:nth-of-type(2) > .mt-5.overflow-hidden > div:first-child {
  background:linear-gradient(180deg,#f7f0e4,#f2eadc) !important;
  color:#766755 !important;
  border-bottom:1px solid rgba(158,111,25,.12);
}
.tos-tgws-settings-flagship-v1 > .tos-premium-card:nth-of-type(2) input[type="email"] {
  border-color:rgba(144,103,39,.18) !important;
  border-radius:13px !important;
  background:linear-gradient(180deg,#fff,#fffaf3) !important;
  color:#2e261c !important;
}

/* Policy vault. */
.tos-tgws-settings-flagship-v1 > .tos-premium-card:nth-of-type(3) {
  background:
    radial-gradient(circle at 94% 3%,rgba(33,159,111,.06),transparent 24%),
    linear-gradient(143deg,#fffefa,#fff9ef 58%,#f4e8d4) !important;
}
.tos-tgws-settings-flagship-v1 > .tos-premium-card:nth-of-type(3) label {
  color:#443b31;
}
.tos-tgws-settings-flagship-v1 > .tos-premium-card:nth-of-type(3) label.flex {
  border-color:rgba(168,110,18,.14) !important;
  background:linear-gradient(145deg,#fffdf8,#f8f2e8) !important;
  box-shadow:inset 0 1px rgba(255,255,255,.9);
}
.tos-tgws-settings-flagship-v1 textarea,
.tos-tgws-settings-flagship-v1 select {
  border:1px solid rgba(159,109,31,.19) !important;
  border-radius:15px !important;
  background:linear-gradient(180deg,#fff,#fffaf2) !important;
  color:#2d251c !important;
  outline:none;
  box-shadow:inset 0 1px rgba(255,255,255,.95),0 5px 14px rgba(66,43,7,.035);
}
.tos-tgws-settings-flagship-v1 textarea:focus,
.tos-tgws-settings-flagship-v1 select:focus {
  border-color:rgba(194,135,25,.55) !important;
  box-shadow:0 0 0 3px rgba(194,135,25,.09) !important;
}
.tos-tgws-settings-flagship-v1 input[type="checkbox"] { accent-color:#c58a19; }

/* Metallic command buttons; preserve variant meaning. */
.tos-tgws-settings-flagship-v1 .tos-premium-button {
  min-height:40px;
  border-radius:999px !important;
  padding-inline:16px !important;
  font-weight:900 !important;
  box-shadow:0 7px 18px rgba(59,41,12,.06),inset 0 1px rgba(255,255,255,.65);
}
.tos-tgws-settings-flagship-v1 .tos-premium-button:not(:disabled) {
  border:1px solid rgba(178,121,18,.20);
}
.tos-tgws-settings-flagship-v1 .tos-premium-button:disabled { opacity:.56; filter:saturate(.72); }

/* =========================================================
   DARK — obsidian / black titanium / champagne + blue/emerald
   ========================================================= */
.dark .tos-tgws-settings-flagship-v1 > .tos-premium-card {
  color:#eee9e1 !important;
  border-color:rgba(238,188,72,.40) !important;
  background:
    radial-gradient(120% 108% at 80% 136%,transparent 0 39%,rgba(255,201,74,.21) 39.25% 39.52%,transparent 39.82% 43%,rgba(255,191,50,.10) 43.25% 43.5%,transparent 43.8% 100%),
    radial-gradient(circle at 92% 3%,rgba(48,155,230,.11),transparent 27%),
    linear-gradient(143deg,#0b1318 0%,#0a1014 61%,#110d07 100%) !important;
  box-shadow:0 28px 60px rgba(0,0,0,.39),0 0 34px rgba(215,154,31,.055),inset 0 1px rgba(255,255,255,.03) !important;
}
.dark .tos-tgws-settings-flagship-v1 > .tos-premium-card::before {
  background:linear-gradient(180deg,#ffd66f,#ca8611 56%,#744000) !important;
  box-shadow:0 0 20px rgba(246,184,59,.23) !important;
}
.dark .tos-tgws-settings-flagship-v1 > .tos-premium-card:nth-of-type(1)::after { color:#9dd8ff; }
.dark .tos-tgws-settings-flagship-v1 > .tos-premium-card:nth-of-type(2)::after { color:#d8b7ff; }
.dark .tos-tgws-settings-flagship-v1 > .tos-premium-card:nth-of-type(3)::after { color:#f4d38a; }
.dark .tos-tgws-settings-flagship-v1 .tos-kicker { color:#ecbd51 !important; }
.dark .tos-tgws-settings-flagship-v1 h3 { color:#fff2df !important; text-shadow:0 1px rgba(0,0,0,.35); }
.dark .tos-tgws-settings-flagship-v1 .tos-muted { color:#aeb8c0 !important; }

.dark .tos-tgws-settings-flagship-v1 .tos-premium-stat {
  border-color:rgba(232,184,74,.23) !important;
  background:radial-gradient(circle at 88% 8%,rgba(54,160,231,.09),transparent 27%),linear-gradient(155deg,#141d22,#0b1318) !important;
  box-shadow:0 13px 29px rgba(0,0,0,.29),inset 0 1px rgba(255,255,255,.028) !important;
}
.dark .tos-tgws-settings-flagship-v1 .tos-premium-stat > .flex > div:first-child > div:first-child { color:#fff0d9 !important; }
.dark .tos-tgws-settings-flagship-v1 .tos-premium-stat > .flex > div:first-child > div:nth-child(2) { color:#eee8df !important; }
.dark .tos-tgws-settings-flagship-v1 .tos-premium-stat > .flex > div:first-child > div:nth-child(3) { color:#99a5ad !important; }

.dark .tos-tgws-settings-flagship-v1 > .tos-premium-card:nth-of-type(2) {
  background:radial-gradient(circle at 92% 4%,rgba(132,86,190,.10),transparent 25%),linear-gradient(143deg,#11131a,#0b1016 62%,#110d08) !important;
}
.dark .tos-tgws-settings-flagship-v1 > .tos-premium-card:nth-of-type(2) > .relative input,
.dark .tos-tgws-settings-flagship-v1 > .tos-premium-card:nth-of-type(2) input[type="email"],
.dark .tos-tgws-settings-flagship-v1 textarea,
.dark .tos-tgws-settings-flagship-v1 select {
  border-color:rgba(193,151,70,.22) !important;
  background:linear-gradient(180deg,#151d22,#0e1519) !important;
  color:#f3eee7 !important;
  -webkit-text-fill-color:#f3eee7 !important;
  caret-color:#efc765;
  box-shadow:inset 0 1px rgba(255,255,255,.028),0 7px 18px rgba(0,0,0,.20) !important;
}
.dark .tos-tgws-settings-flagship-v1 input::placeholder,
.dark .tos-tgws-settings-flagship-v1 textarea::placeholder {
  color:#9ca8b1 !important;
  -webkit-text-fill-color:#9ca8b1 !important;
  opacity:1 !important;
}
.dark .tos-tgws-settings-flagship-v1 > .tos-premium-card:nth-of-type(2) > .mt-5.overflow-hidden {
  border-color:rgba(218,170,71,.18) !important;
  box-shadow:0 13px 30px rgba(0,0,0,.27),inset 0 1px rgba(255,255,255,.02);
}
.dark .tos-tgws-settings-flagship-v1 > .tos-premium-card:nth-of-type(2) > .mt-5.overflow-hidden > div:first-child {
  background:linear-gradient(180deg,#1d1b17,#151719) !important;
  color:#d0c5b5 !important;
  border-bottom-color:rgba(232,184,73,.13) !important;
}
.dark .tos-tgws-settings-flagship-v1 > .tos-premium-card:nth-of-type(2) > .mt-5.overflow-hidden > div:last-child > div {
  background:#0d1418 !important;
  color:#e8e5e0 !important;
}

.dark .tos-tgws-settings-flagship-v1 > .tos-premium-card:nth-of-type(3) {
  background:radial-gradient(circle at 94% 3%,rgba(35,177,124,.08),transparent 25%),linear-gradient(143deg,#0e1716,#0a1113 63%,#110d08) !important;
}
.dark .tos-tgws-settings-flagship-v1 > .tos-premium-card:nth-of-type(3) label { color:#ddd7cf !important; }
.dark .tos-tgws-settings-flagship-v1 > .tos-premium-card:nth-of-type(3) label.flex {
  border-color:rgba(226,181,78,.17) !important;
  background:linear-gradient(145deg,#151b1a,#101515) !important;
}

.dark .tos-tgws-settings-flagship-v1 .tos-premium-notice {
  box-shadow:inset 0 1px rgba(255,255,255,.025),0 8px 20px rgba(0,0,0,.20) !important;
}
.dark .tos-tgws-settings-flagship-v1 .tos-premium-button {
  box-shadow:0 9px 20px rgba(0,0,0,.27),inset 0 1px rgba(255,255,255,.04) !important;
}
.dark .tos-tgws-settings-flagship-v1 .tos-premium-button:not(:disabled) {
  border-color:rgba(232,184,73,.25) !important;
}

@media (max-width: 1023px) {
  .tos-tgws-settings-flagship-v1 > .tos-premium-card { padding:22px !important; border-radius:24px !important; }
}
@media (max-width: 767px) {
  .tos-tgws-settings-flagship-v1 > .tos-premium-card { padding:18px !important; border-radius:21px !important; }
  .tos-tgws-settings-flagship-v1 .tos-premium-stat { min-height:112px; }
}
'''


def fail(message):
    raise RuntimeError(message)


def git_blob_sha(path: Path):
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


if not COMPONENT.exists():
    fail(f"TGWS component missing: {COMPONENT}")

component_blob = git_blob_sha(COMPONENT)
if component_blob != EXPECTED_COMPONENT_GIT_BLOB:
    fail(f"TGWS component baseline mismatch: expected={EXPECTED_COMPONENT_GIT_BLOB} actual={component_blob}")

source = COMPONENT.read_text()
for marker in [
    IMPORT_ANCHOR,
    'const EXPECTED_TGWS_BUILD = "TOS-TGWS-CORE-V1R7";',
    "export function TgwsSettingsAdmin({ user })",
    "tgwsApi.bootstrap()",
    "tgwsApi.updateSettings(payload)",
    "tgwsApi.googleIdentities()",
    "tgwsApi.updateGoogleIdentity(userId, googleEmail)",
    "api.googleDrive.authUrl()",
    "Tamiyouz Google Workspace",
    "Google identity mapping",
    "TGWS Policy",
]:
    if marker not in source:
        fail(f"required TGWS baseline marker missing: {marker}")

if IMPORT_STYLE in source or STYLE.exists():
    fail("TGWS Settings Flagship Luxury V1 already present")
if source.count(ROOT_OLD) != 1:
    fail(f"TGWS root marker count unexpected: {source.count(ROOT_OLD)}")

stamp = int(time.time())
component_backup = COMPONENT.with_name(f"{COMPONENT.name}.tgws-settings-v1-backup-{stamp}")
shutil.copy2(COMPONENT, component_backup)
live_backup = None
staging = None

try:
    source = source.replace(IMPORT_ANCHOR, IMPORT_ANCHOR + "\n" + IMPORT_STYLE, 1)
    source = source.replace(ROOT_OLD, ROOT_NEW, 1)

    if IMPORT_STYLE not in source or ROOT_NEW not in source:
        fail("TGWS flagship transform failed")

    # Functional markers must survive unchanged.
    for marker in [
        'const EXPECTED_TGWS_BUILD = "TOS-TGWS-CORE-V1R7";',
        "tgwsApi.bootstrap()",
        "tgwsApi.updateSettings(payload)",
        "tgwsApi.googleIdentities()",
        "tgwsApi.updateGoogleIdentity(userId, googleEmail)",
        "api.googleDrive.authUrl()",
        "window.dispatchEvent(new CustomEvent(\"tgws-settings-updated\"",
    ]:
        if marker not in source:
            fail(f"post-transform functional marker missing: {marker}")

    COMPONENT.write_text(source)
    STYLE.write_text(CSS)

    if RUNTIME_MARKER not in STYLE.read_text():
        fail("TGWS V1 runtime marker missing after style write")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists():
        fail("frontend dist missing after build")

    built_css = ""
    for css_file in DIST.rglob("*.css"):
        built_css += css_file.read_text(errors="ignore")
    if RUNTIME_MARKER not in built_css:
        fail("TGWS Settings V1 runtime marker missing from built CSS")
    if ".tos-tgws-settings-flagship-v1" not in built_css:
        fail("TGWS Settings V1 scope marker missing from built CSS")

    LIVE_PARENT.mkdir(parents=True, exist_ok=True)
    staging = LIVE_PARENT / f"build.tgws-settings-v1-staging-{stamp}"
    live_backup = LIVE_PARENT / f"build.tgws-settings-v1-backup-{stamp}"
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
        fail("TGWS Settings V1 runtime marker missing from live build")

    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("TGWS_SETTINGS_FLAGSHIP_LUXURY_V1_RUNTIME=YES")
    print("TGWS_SETTINGS_SCOPE=VISUAL_ONLY")
    print("TGWS_LIGHT_MODE=PEARL_IVORY_CHAMPAGNE_GOOGLE_SPECTRUM")
    print("TGWS_DARK_MODE=OBSIDIAN_TITANIUM_CHAMPAGNE_SAPPHIRE_EMERALD")
    print("TGWS_CONTROL_PLANE=EXECUTIVE_FLAGSHIP")
    print("TGWS_KPIS=LUXURY_RUNTIME_HARDWARE")
    print("TGWS_IDENTITY_MAPPING=PREMIUM_EDITOR_COMMAND_CENTER")
    print("TGWS_POLICY=EXECUTIVE_GOVERNANCE_VAULT")
    print("TGWS_FIELDS=PREMIUM_HIGH_CONTRAST")
    print("TGWS_ACTIONS=METALLIC_COMMAND_HARDWARE")
    print("TGWS_API_CHANGED=NO")
    print("TGWS_PERSISTENCE_LOGIC_CHANGED=NO")
    print("TGWS_IDENTITY_MAPPING_LOGIC_CHANGED=NO")
    print("TGWS_POLICY_LOGIC_CHANGED=NO")
    print("TGWS_OAUTH_LOGIC_CHANGED=NO")
    print("TGWS_PERMISSIONS_CHANGED=NO")
    print("TGWS_DATA_CONTRACT_CHANGED=NO")
    print("TWS_CHANGED=NO")
    print("SLA_CHANGED=NO")
    print("RAMZY_LOGIC_CHANGED=NO")
    print("TCS_CHANGED=NO")
    print(f"TGWS_COMPONENT_BASELINE_GIT_BLOB={EXPECTED_COMPONENT_GIT_BLOB}")
    print(f"LIVE_BACKUP={live_backup if live_backup and live_backup.exists() else 'NONE'}")
    print("STATUS=READY")
except Exception as exc:
    try:
        if component_backup.exists():
            shutil.copy2(component_backup, COMPONENT)
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
