from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
COMPONENT = FRONTEND / "src/components/RamzySettingsAdmin.jsx"
STYLE = FRONTEND / "src/components/ramzySettingsFlagshipLuxuryV1.css"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_COMPONENT_GIT_BLOB = "ac4ef21268a574b4682515140fc67de03cadc7a3"
IMPORT_ANCHOR = 'import { Button, Card, Field, Notice, StatCard } from "./ui/Primitives";'
IMPORT_STYLE = 'import "./ramzySettingsFlagshipLuxuryV1.css";'
ROOT_OLD = '<div className="space-y-5">'
ROOT_NEW = '<div className="tos-ramzy-settings-flagship-v1 space-y-5">'
RUNTIME_MARKER = "--tos-ramzy-settings-flagship-luxury-v1-runtime"

CSS = r'''
:root { --tos-ramzy-settings-flagship-luxury-v1-runtime: 1; }

/* =========================================================
   TOS Settings → Ramzy AI — Flagship Luxury V1
   Light: pearl / ivory / champagne + violet intelligence
   Dark: obsidian / titanium / champagne + amethyst glow
   Visual only. No API, permissions, save, memory or agent logic changes.
   ========================================================= */

.tos-ramzy-settings-flagship-v1 {
  position: relative;
  isolation: isolate;
  --ramzy-gold: #c98a18;
  --ramzy-gold-hi: #f5d77f;
  --ramzy-violet: #7752b8;
  --ramzy-ink: #21180f;
}

.tos-ramzy-settings-flagship-v1 > .tos-premium-card {
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(177, 116, 18, .20) !important;
  border-radius: 28px !important;
  background:
    radial-gradient(110% 90% at 92% 118%, transparent 0 47%, rgba(193,126,15,.06) 47.25% 47.55%, transparent 47.85% 51%, rgba(193,126,15,.035) 51.25% 51.5%, transparent 51.8% 100%),
    radial-gradient(circle at 92% 5%, rgba(128,86,190,.07), transparent 26%),
    linear-gradient(145deg,#fff 0%,#fffdf8 62%,#faf2e5 100%) !important;
  box-shadow:
    0 16px 38px rgba(74,45,4,.07),
    inset 0 1px rgba(255,255,255,.98) !important;
}

.tos-ramzy-settings-flagship-v1 > .tos-premium-card::before {
  content: "";
  position: absolute;
  inset-block: 22px;
  inset-inline-start: 0;
  width: 3px;
  border-radius: 999px;
  background: linear-gradient(180deg,#f2ca67 0%,#c18313 55%,#7d4a04 100%);
  box-shadow: 0 0 18px rgba(213,155,39,.17);
  pointer-events: none;
}

/* ---- Executive Ramzy hero ---- */
.tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(1) {
  min-height: 236px;
  padding: 28px !important;
  border-color: rgba(174,112,13,.30) !important;
  background:
    radial-gradient(116% 105% at 76% 142%, transparent 0 39%, rgba(196,128,16,.15) 39.25% 39.55%, transparent 39.85% 42.8%, rgba(196,128,16,.09) 43.05% 43.34%, transparent 43.65% 47%, rgba(196,128,16,.05) 47.24% 47.48%, transparent 47.8% 100%),
    radial-gradient(circle at 89% -3%, rgba(129,83,193,.14), transparent 29%),
    radial-gradient(circle at 98% 17%, rgba(244,210,130,.20), transparent 27%),
    linear-gradient(135deg,#fffefa 0%,#fff9ed 52%,#f5e7d0 100%) !important;
  box-shadow:
    0 22px 50px rgba(79,48,4,.095),
    inset 0 1px rgba(255,255,255,.99) !important;
}

.tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(1)::after {
  content: "RAMZY  •  AGENCY OPERATOR";
  position: absolute;
  inset-inline-end: 28px;
  top: 25px;
  color: rgba(111,76,34,.22);
  font-size: 9px;
  font-weight: 950;
  letter-spacing: .24em;
  text-transform: uppercase;
  pointer-events: none;
}

.tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(1) .tos-kicker {
  color: #9a650c !important;
  letter-spacing: .16em;
  text-transform: uppercase;
}

.tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(1) h3 {
  margin-top: 6px !important;
  font-family: Georgia, "Times New Roman", serif;
  font-size: clamp(1.8rem,2.6vw,2.5rem) !important;
  letter-spacing: -.035em;
  color: #21190f !important;
}

.tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(1) .tos-muted {
  color: #786c5f !important;
  font-weight: 750;
}

.tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(1) > .flex > div:last-child {
  width: 62px !important;
  height: 62px !important;
  border: 1px solid rgba(116,75,180,.20);
  border-radius: 22px !important;
  color: #6f4daa !important;
  background: linear-gradient(145deg,#faf5ff 0%,#e8daf9 58%,#d7c4f0 100%) !important;
  box-shadow: 0 12px 28px rgba(100,62,160,.16), inset 0 1px rgba(255,255,255,.92);
}

/* Hero KPI hardware */
.tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(1) .tos-premium-stat {
  min-height: 124px;
  padding: 17px 16px !important;
  border: 1px solid rgba(166,106,12,.17) !important;
  border-radius: 20px !important;
  background:
    radial-gradient(circle at 88% 10%,rgba(238,199,109,.13),transparent 25%),
    linear-gradient(155deg,rgba(255,255,255,.96),rgba(252,247,237,.94)) !important;
  box-shadow: 0 11px 26px rgba(72,44,4,.055), inset 0 1px rgba(255,255,255,.97) !important;
  transform: none !important;
}

.tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(1) .tos-premium-stat > .flex > div:first-child > div:first-child {
  font-family: Georgia,"Times New Roman",serif;
  font-size: 1.2rem !important;
  color: #241a0f !important;
  line-height: 1.15;
}

.tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(1) .tos-premium-stat > .flex > div:last-child {
  width: 42px !important;
  height: 42px !important;
  border-radius: 999px !important;
  box-shadow: 0 8px 20px rgba(77,47,5,.08), inset 0 1px rgba(255,255,255,.85);
}

/* ---- Provider & API vault panel ---- */
.tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(2) {
  padding: 26px !important;
  background:
    radial-gradient(circle at 92% 4%,rgba(122,78,187,.08),transparent 24%),
    radial-gradient(95% 90% at 88% 117%,transparent 0 49%,rgba(191,124,14,.055) 49.25% 49.55%,transparent 49.85% 100%),
    linear-gradient(145deg,#fff 0%,#fffdf8 100%) !important;
}

.tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(2)::after {
  content: "MODEL & API VAULT";
  position: absolute;
  top: 18px;
  inset-inline-end: 24px;
  color: rgba(118,77,177,.27);
  font-size: 9px;
  font-weight: 950;
  letter-spacing: .18em;
  pointer-events: none;
}

.tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(2) label,
.tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(3) label {
  color: #4b4034;
}

.tos-ramzy-settings-flagship-v1 .tos-premium-field,
.tos-ramzy-settings-flagship-v1 .tos-input {
  min-height: 46px;
  border: 1px solid rgba(158,103,16,.18) !important;
  border-radius: 15px !important;
  background: linear-gradient(180deg,#fffefa,#fffaf0) !important;
  color: #2b2115 !important;
  box-shadow: inset 0 1px rgba(255,255,255,.98), 0 5px 14px rgba(71,44,4,.035);
  transition: border-color .18s ease, box-shadow .18s ease, transform .18s ease;
}

.tos-ramzy-settings-flagship-v1 .tos-premium-field:focus,
.tos-ramzy-settings-flagship-v1 .tos-input:focus {
  border-color: rgba(126,81,186,.58) !important;
  box-shadow: 0 0 0 3px rgba(126,81,186,.10), 0 8px 20px rgba(83,51,3,.06) !important;
}

/* ---- Governance / intelligence controls ---- */
.tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(3) {
  padding: 26px !important;
  background:
    radial-gradient(circle at 95% 2%,rgba(229,183,76,.13),transparent 24%),
    radial-gradient(circle at 5% 95%,rgba(119,77,179,.055),transparent 27%),
    linear-gradient(145deg,#fff 0%,#fdf8ef 100%) !important;
}

.tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(3)::after {
  content: "GOVERNANCE • MEMORY • INTELLIGENCE";
  position: absolute;
  top: 18px;
  inset-inline-end: 24px;
  color: rgba(151,99,15,.24);
  font-size: 9px;
  font-weight: 950;
  letter-spacing: .16em;
  pointer-events: none;
}

.tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(3) > .grid:first-child > label {
  position: relative;
  min-height: 62px;
  padding: 15px 16px !important;
  border: 1px solid rgba(162,105,14,.15) !important;
  border-radius: 18px !important;
  background: linear-gradient(145deg,rgba(255,255,255,.94),rgba(251,246,236,.90)) !important;
  color: #34291e !important;
  box-shadow: 0 8px 20px rgba(68,42,4,.04), inset 0 1px rgba(255,255,255,.96);
}

/* premium switches, semantics preserved */
.tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(3) > .grid:first-child > label input[type="checkbox"] {
  appearance: none;
  -webkit-appearance: none;
  position: relative;
  width: 44px;
  height: 24px;
  flex: 0 0 44px;
  border: 1px solid rgba(129,103,67,.30);
  border-radius: 999px;
  background: linear-gradient(180deg,#eee8dd,#ddd3c4);
  box-shadow: inset 0 2px 5px rgba(71,48,14,.10);
  cursor: pointer;
  transition: .18s ease;
}
.tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(3) > .grid:first-child > label input[type="checkbox"]::after {
  content: "";
  position: absolute;
  width: 18px;
  height: 18px;
  top: 2px;
  left: 3px;
  border-radius: 50%;
  background: linear-gradient(145deg,#fff,#f1eadf);
  box-shadow: 0 2px 7px rgba(52,34,8,.20);
  transition: .18s ease;
}
.tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(3) > .grid:first-child > label input[type="checkbox"]:checked {
  border-color: rgba(121,77,179,.48);
  background: linear-gradient(90deg,#8d68c6,#c18a21);
  box-shadow: inset 0 1px rgba(255,255,255,.20), 0 0 14px rgba(126,82,186,.12);
}
.tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(3) > .grid:first-child > label input[type="checkbox"]:checked::after {
  transform: translateX(19px);
}
.tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(3) > .grid:first-child > label input[type="checkbox"]:disabled {
  opacity: .48;
  cursor: not-allowed;
}

/* System Intelligence jewel panel */
.tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(3) .border-violet-200 {
  border: 1px solid rgba(116,75,180,.22) !important;
  border-radius: 20px !important;
  background:
    radial-gradient(circle at 92% 12%,rgba(125,83,188,.13),transparent 28%),
    linear-gradient(145deg,#fbf7ff 0%,#f5edf9 58%,#fff8e8 100%) !important;
  box-shadow: 0 12px 28px rgba(94,59,146,.08), inset 0 1px rgba(255,255,255,.88);
}
.tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(3) .border-violet-200 > p:first-child {
  color: #6d4aa4 !important;
  letter-spacing: .02em;
}

/* Allowed-role chips */
.tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(3) button[type="button"].rounded-xl.border {
  border-color: rgba(158,103,15,.18) !important;
  border-radius: 999px !important;
  background: linear-gradient(180deg,#fffdf7,#f5ead4);
  color: #675846;
  box-shadow: inset 0 1px rgba(255,255,255,.92);
}
.tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(3) button.border-violet-400 {
  border-color: rgba(119,77,181,.45) !important;
  background: linear-gradient(180deg,#f7f0ff,#e8d8fa) !important;
  color: #67449f !important;
  box-shadow: 0 6px 15px rgba(105,65,164,.09), inset 0 1px rgba(255,255,255,.94);
}

/* Action hardware */
.tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(3) .tos-premium-button {
  min-height: 42px;
  border-radius: 999px !important;
  border: 1px solid rgba(159,103,13,.22);
  padding-inline: 18px !important;
  font-weight: 900 !important;
}
.tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(3) .tos-premium-button:first-child {
  color: #2b1b04 !important;
  border-color: #b9770c !important;
  background: linear-gradient(180deg,#fff0b4 0%,#edc45a 24%,#d49a22 63%,#b36c08 100%) !important;
  box-shadow: 0 10px 21px rgba(113,67,2,.16), inset 0 1px rgba(255,255,255,.83) !important;
}
.tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(3) .tos-premium-button:nth-child(2) {
  background: linear-gradient(180deg,#f7f4ee,#ebe5dc) !important;
  color: #4a4035 !important;
}
.tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(3) .tos-premium-button:nth-child(3) {
  border-color: rgba(180,75,67,.20) !important;
  background: linear-gradient(180deg,#fff4f1,#f6ded9) !important;
  color: #a64e45 !important;
}

/* ---- Runtime audit / observability ---- */
.tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(4) {
  padding: 26px !important;
  background:
    radial-gradient(circle at 94% 4%,rgba(32,148,109,.08),transparent 25%),
    linear-gradient(145deg,#fff 0%,#fffdf8 100%) !important;
}
.tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(4) h3 {
  font-family: Georgia,"Times New Roman",serif;
  color: #241b11 !important;
}
.tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(4) .tos-premium-stat {
  border-color: rgba(165,107,15,.14) !important;
  border-radius: 19px !important;
  background: linear-gradient(155deg,#fff,#fcf8ef) !important;
}
.tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(4) table {
  border-collapse: separate;
  border-spacing: 0;
  overflow: hidden;
}
.tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(4) thead tr {
  border: 0 !important;
  background: linear-gradient(180deg,#f8f2e7,#f3eadc);
  color: #695b49 !important;
}
.tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(4) th,
.tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(4) td {
  border-bottom: 1px solid rgba(162,105,15,.09);
}
.tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(4) tbody tr:hover {
  background: rgba(243,228,198,.24);
}

/* =========================================================
   DARK — obsidian / titanium / champagne / amethyst
   ========================================================= */
.dark .tos-ramzy-settings-flagship-v1 {
  --ramzy-ink: #f7efe3;
}
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card {
  border-color: rgba(229,180,68,.18) !important;
  background:
    radial-gradient(110% 92% at 92% 118%,transparent 0 46%,rgba(239,181,55,.085) 46.25% 46.55%,transparent 46.85% 50%,rgba(239,181,55,.045) 50.25% 50.5%,transparent 50.8% 100%),
    radial-gradient(circle at 93% 3%,rgba(129,81,193,.07),transparent 25%),
    linear-gradient(145deg,#13191d 0%,#0b1114 72%,#110d07 100%) !important;
  box-shadow: 0 20px 45px rgba(0,0,0,.30), inset 0 1px rgba(255,255,255,.025) !important;
}
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card::before {
  background: linear-gradient(180deg,#ffd46e 0%,#c6810d 55%,#7a4300 100%);
  box-shadow: 0 0 18px rgba(244,182,58,.22);
}

.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(1) {
  border-color: rgba(239,188,72,.38) !important;
  background:
    radial-gradient(118% 105% at 75% 140%,transparent 0 37%,rgba(255,201,77,.26) 37.28% 37.58%,transparent 37.9% 40.7%,rgba(255,195,60,.16) 40.98% 41.28%,transparent 41.58% 44.5%,rgba(255,189,45,.085) 44.78% 45.02%,transparent 45.3% 100%),
    radial-gradient(circle at 88% 0%,rgba(137,86,207,.17),transparent 29%),
    linear-gradient(135deg,#0d1418 0%,#11161a 54%,#171007 100%) !important;
  box-shadow: 0 28px 58px rgba(0,0,0,.38), 0 0 36px rgba(214,153,31,.065), inset 0 1px rgba(255,255,255,.03) !important;
}
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(1)::after {
  color: rgba(244,215,148,.44);
}
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(1) h3 { color:#fff6e8 !important; }
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(1) .tos-muted { color:#9da9b3 !important; }
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(1) > .flex > div:last-child {
  border-color: rgba(176,126,239,.28);
  color:#c8a7f5 !important;
  background: linear-gradient(145deg,#2a1d3c,#171322) !important;
  box-shadow: 0 12px 28px rgba(0,0,0,.30),0 0 24px rgba(151,94,221,.14),inset 0 1px rgba(255,255,255,.045);
}

.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(1) .tos-premium-stat {
  border-color: rgba(231,181,68,.20) !important;
  background: radial-gradient(circle at 88% 10%,rgba(230,173,54,.08),transparent 25%),linear-gradient(155deg,#151b1f,#0c1114) !important;
  box-shadow: 0 13px 28px rgba(0,0,0,.26),inset 0 1px rgba(255,255,255,.025) !important;
}
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(1) .tos-premium-stat > .flex > div:first-child > div:first-child { color:#fff2d8 !important; }
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(1) .tos-premium-stat > .flex > div:first-child > div:nth-child(2) { color:#eee8dd !important; }
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(1) .tos-premium-stat > .flex > div:first-child > div:nth-child(3) { color:#8996a1 !important; }

.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(2),
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(3),
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(4) {
  background:
    radial-gradient(circle at 93% 3%,rgba(134,84,201,.065),transparent 25%),
    radial-gradient(105% 90% at 88% 118%,transparent 0 48%,rgba(238,180,59,.075) 48.25% 48.55%,transparent 48.85% 100%),
    linear-gradient(145deg,#12191d,#0a1013) !important;
}

.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(2)::after,
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(3)::after { color:rgba(226,190,119,.33); }

.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(2) label,
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(3) label { color:#d8d1c7; }

.dark .tos-ramzy-settings-flagship-v1 .tos-premium-field,
.dark .tos-ramzy-settings-flagship-v1 .tos-input {
  border-color: rgba(222,177,73,.16) !important;
  background: linear-gradient(180deg,#151b1f,#0e1417) !important;
  color:#f1ece5 !important;
  box-shadow: inset 0 1px rgba(255,255,255,.025),0 6px 17px rgba(0,0,0,.18);
}
.dark .tos-ramzy-settings-flagship-v1 .tos-premium-field:focus,
.dark .tos-ramzy-settings-flagship-v1 .tos-input:focus {
  border-color: rgba(170,116,235,.58) !important;
  box-shadow: 0 0 0 3px rgba(146,91,213,.12),0 8px 22px rgba(0,0,0,.24) !important;
}

.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(3) > .grid:first-child > label {
  border-color: rgba(228,180,71,.15) !important;
  background: linear-gradient(145deg,#151b1f,#0e1417) !important;
  color:#eee8df !important;
  box-shadow: 0 9px 22px rgba(0,0,0,.20),inset 0 1px rgba(255,255,255,.02);
}
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(3) > .grid:first-child > label input[type="checkbox"] {
  border-color: rgba(233,190,92,.20);
  background: linear-gradient(180deg,#32383b,#202629);
}
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(3) > .grid:first-child > label input[type="checkbox"]::after {
  background: linear-gradient(145deg,#f8f4ec,#cfc5b6);
}
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(3) > .grid:first-child > label input[type="checkbox"]:checked {
  border-color: rgba(183,132,239,.50);
  background: linear-gradient(90deg,#7b53b5,#bd8218);
  box-shadow: 0 0 18px rgba(145,88,211,.14),inset 0 1px rgba(255,255,255,.08);
}

.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(3) .border-violet-200 {
  border-color: rgba(161,111,222,.26) !important;
  background: radial-gradient(circle at 90% 10%,rgba(140,87,208,.15),transparent 28%),linear-gradient(145deg,#181421,#12151a) !important;
  box-shadow: 0 14px 30px rgba(0,0,0,.25),0 0 24px rgba(140,87,208,.05),inset 0 1px rgba(255,255,255,.025);
}
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(3) .border-violet-200 > p:first-child { color:#d2b5f5 !important; }
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(3) .border-violet-200 .text-slate-600 { color:#9da6af !important; }

.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(3) button[type="button"].rounded-xl.border {
  border-color: rgba(224,179,76,.17) !important;
  background: linear-gradient(180deg,#171d20,#111619);
  color:#b8afa4;
}
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(3) button.border-violet-400 {
  border-color: rgba(171,118,231,.45) !important;
  background: linear-gradient(180deg,#2b1d3e,#1a1424) !important;
  color:#d4b8f7 !important;
  box-shadow:0 7px 17px rgba(0,0,0,.22),0 0 16px rgba(146,90,214,.08);
}

.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(3) .tos-premium-button:first-child {
  border-color:#d59822 !important;
  color:#150d02 !important;
  background:linear-gradient(180deg,#fff0ad 0%,#edbf50 22%,#ce8d15 60%,#9f5700 100%) !important;
  box-shadow:0 11px 25px rgba(0,0,0,.34),0 0 17px rgba(233,171,47,.11),inset 0 1px rgba(255,255,255,.80) !important;
}
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(3) .tos-premium-button:nth-child(2) {
  border-color:rgba(255,255,255,.08) !important;
  background:linear-gradient(180deg,#1b2226,#11171a) !important;
  color:#d4d0c9 !important;
}
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(3) .tos-premium-button:nth-child(3) {
  border-color:rgba(222,99,88,.24) !important;
  background:linear-gradient(180deg,#2a1919,#1b1213) !important;
  color:#f0a49b !important;
}

.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(4) h3 { color:#fff4e3 !important; }
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(4) .tos-premium-stat {
  border-color:rgba(229,180,68,.15) !important;
  background:linear-gradient(155deg,#151b1f,#0d1215) !important;
}
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(4) thead tr {
  background:linear-gradient(180deg,#1b2226,#151a1d);
  color:#b5a994 !important;
}
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(4) th,
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(4) td { border-color:rgba(229,180,68,.08); }
.dark .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(4) tbody tr:hover { background:rgba(232,178,66,.035); }

@media (max-width: 1023px) {
  .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(1)::after,
  .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(2)::after,
  .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(3)::after { opacity:.55; }
}

@media (max-width: 767px) {
  .tos-ramzy-settings-flagship-v1 > .tos-premium-card { padding:20px !important; border-radius:22px !important; }
  .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(1) { min-height:auto; }
  .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(1)::after,
  .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(2)::after,
  .tos-ramzy-settings-flagship-v1 > .tos-premium-card:nth-child(3)::after { display:none; }
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
    fail(f"Ramzy settings component missing: {COMPONENT}")

component_blob = git_blob_sha(COMPONENT)
if component_blob != EXPECTED_COMPONENT_GIT_BLOB:
    fail(f"Ramzy settings baseline mismatch: expected={EXPECTED_COMPONENT_GIT_BLOB} actual={component_blob}")

source = COMPONENT.read_text()

required_markers = [
    IMPORT_ANCHOR,
    'export function RamzySettingsAdmin({ user })',
    'api.agent.settings()',
    'api.agent.updateSettings(payload)',
    'api.agent.clearMemory()',
    'api.agent.audit()',
    ROOT_OLD,
    'Primary: Gemini | Fallback: Agnes AI',
    'System Intelligence',
    'Ramzy Runtime Audit',
]
for marker in required_markers:
    if marker not in source:
        fail(f"required Ramzy Settings baseline marker missing: {marker}")

if IMPORT_STYLE in source or STYLE.exists():
    fail("Ramzy Settings Flagship Luxury V1 already present")

stamp = int(time.time())
component_backup = COMPONENT.with_name(f"{COMPONENT.name}.ramzy-settings-v1-backup-{stamp}")
shutil.copy2(COMPONENT, component_backup)
live_backup = None
staging = None

try:
    source = source.replace(IMPORT_ANCHOR, IMPORT_ANCHOR + "\n" + IMPORT_STYLE, 1)
    if source.count(ROOT_OLD) != 1:
        fail(f"Ramzy root marker count changed unexpectedly: {source.count(ROOT_OLD)}")
    source = source.replace(ROOT_OLD, ROOT_NEW, 1)

    post_markers = [IMPORT_STYLE, "tos-ramzy-settings-flagship-v1", 'api.agent.updateSettings(payload)', 'api.agent.clearMemory()', 'api.agent.audit()']
    for marker in post_markers:
        if marker not in source:
            fail(f"post-transform marker missing: {marker}")

    COMPONENT.write_text(source)
    STYLE.write_text(CSS)

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists():
        fail("frontend dist missing after build")

    built_css = ""
    for css_file in DIST.rglob("*.css"):
        built_css += css_file.read_text(errors="ignore")
    if RUNTIME_MARKER not in built_css:
        fail("Ramzy Settings Flagship Luxury V1 runtime marker missing from built CSS")

    LIVE_PARENT.mkdir(parents=True, exist_ok=True)
    staging = LIVE_PARENT / f"build.ramzy-settings-flagship-v1-staging-{stamp}"
    live_backup = LIVE_PARENT / f"build.ramzy-settings-flagship-v1-backup-{stamp}"
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
        fail("Ramzy Settings Flagship Luxury V1 runtime marker missing from live build")

    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("RAMZY_SETTINGS_FLAGSHIP_LUXURY_V1_RUNTIME=YES")
    print("RAMZY_SETTINGS_SCOPE=VISUAL_ONLY")
    print("RAMZY_LIGHT_MODE=PEARL_IVORY_CHAMPAGNE_VIOLET")
    print("RAMZY_DARK_MODE=OBSIDIAN_TITANIUM_CHAMPAGNE_AMETHYST")
    print("RAMZY_HERO=EXECUTIVE_AGENCY_OPERATOR")
    print("RAMZY_KPIS=LUXURY_HARDWARE")
    print("RAMZY_PROVIDER_PANEL=PREMIUM_MODEL_API_VAULT")
    print("RAMZY_GOVERNANCE=PREMIUM_SWITCH_CONTROL_GRID")
    print("RAMZY_SYSTEM_INTELLIGENCE=JEWEL_PANEL")
    print("RAMZY_ROLE_CHIPS=PREMIUM")
    print("RAMZY_ACTIONS=METALLIC_CHAMPAGNE")
    print("RAMZY_AUDIT=EXECUTIVE_OBSERVABILITY")
    print("RAMZY_AGENT_LOGIC_CHANGED=NO")
    print("RAMZY_API_CHANGED=NO")
    print("RAMZY_PERMISSIONS_CHANGED=NO")
    print("RAMZY_SAVE_LOGIC_CHANGED=NO")
    print("RAMZY_MEMORY_LOGIC_CHANGED=NO")
    print("RAMZY_PROVIDER_LOGIC_CHANGED=NO")
    print("TWS_CHANGED=NO")
    print("SLA_CHANGED=NO")
    print("TCS_CHANGED=NO")
    print(f"RAMZY_COMPONENT_BASELINE_GIT_BLOB={EXPECTED_COMPONENT_GIT_BLOB}")
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
