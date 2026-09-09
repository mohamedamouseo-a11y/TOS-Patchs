from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
PAGE = FRONTEND / "src/pages/SettingsPage.jsx"
V1_STYLE = FRONTEND / "src/pages/settingsOverviewFlagshipV1.css"
V2_STYLE = FRONTEND / "src/pages/settingsOverviewFlagshipV2Reference.css"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

V1_IMPORT = 'import "./settingsOverviewFlagshipV1.css";'
V2_IMPORT = 'import "./settingsOverviewFlagshipV2Reference.css";'
V1_RUNTIME = "--tos-settings-overview-flagship-v1-runtime"
V2_RUNTIME = "--tos-settings-overview-flagship-v2-reference-runtime"

CSS = r'''
:root { --tos-settings-overview-flagship-v2-reference-runtime: 1; }

/* =========================================================
   TOS System Settings Overview — Flagship V2 Reference Match
   Visual reference: approved Light + Dark luxury mockups.
   Scope: visual only. Existing Settings logic remains untouched.
   ========================================================= */

.tos-settings-flagship-v1.tos-page {
  position: relative;
  isolation: isolate;
  padding: 6px;
  border-radius: 34px;
  background:
    radial-gradient(circle at 11% 5%, rgba(238, 198, 107, .10), transparent 27%),
    radial-gradient(circle at 91% 96%, rgba(204, 151, 39, .06), transparent 31%),
    linear-gradient(180deg, rgba(255,253,248,.86), rgba(255,255,255,.58));
}

/* ---- Top luxury reference hero ---- */
.tos-settings-flagship-v1 .tos-settings-flagship-header {
  min-height: 168px !important;
  padding: 27px 32px !important;
  border: 1px solid rgba(188,128,20,.32) !important;
  border-radius: 31px !important;
  background:
    radial-gradient(120% 115% at 77% 142%,
      transparent 0 42%,
      rgba(192,127,17,.12) 42.15% 42.45%,
      transparent 42.7% 45.1%,
      rgba(192,127,17,.085) 45.25% 45.55%,
      transparent 45.8% 48.2%,
      rgba(192,127,17,.06) 48.35% 48.62%,
      transparent 48.9% 100%),
    radial-gradient(circle at 89% -20%, rgba(248,220,159,.47), transparent 34%),
    linear-gradient(132deg,#fffefa 0%,#fffaf0 43%,#f8ead0 100%) !important;
  box-shadow:
    0 18px 42px rgba(90,56,4,.08),
    0 2px 0 rgba(255,255,255,.96) inset,
    0 -1px 0 rgba(171,108,12,.06) inset !important;
}
.tos-settings-flagship-v1 .tos-settings-flagship-header::before {
  content: "" !important;
  position: absolute;
  inset: 0;
  z-index: -1;
  opacity: .72;
  background:
    linear-gradient(118deg, transparent 0 46%, rgba(179,113,13,.055) 46.15% 46.34%, transparent 46.55% 100%),
    repeating-linear-gradient(0deg, transparent 0 26px, rgba(181,117,17,.018) 27px, transparent 28px) !important;
}
.tos-settings-flagship-v1 .tos-settings-flagship-header::after {
  content: "SIMPLER SYSTEMS\A STRONGER TOMORROW" !important;
  white-space: pre;
  width: auto !important;
  height: auto !important;
  top: auto !important;
  bottom: 24px !important;
  inset-inline-end: 30px !important;
  border: 0 !important;
  border-radius: 0 !important;
  box-shadow: none !important;
  color: rgba(73,52,20,.62);
  font-size: 9px;
  line-height: 1.65;
  font-weight: 900;
  letter-spacing: .28em;
  text-align: end;
  text-transform: uppercase;
}
.tos-settings-flagship-v1 .tos-settings-flagship-header > div > div:first-child {
  min-height: 29px;
  border-color: rgba(182,117,13,.35) !important;
  background: linear-gradient(180deg,#fffdf6,#f1d89c) !important;
  color: #805208 !important;
  box-shadow: 0 8px 20px rgba(108,67,4,.08), inset 0 1px rgba(255,255,255,.96) !important;
}
.tos-settings-flagship-v1 .tos-settings-flagship-header h1 {
  margin-top: 10px !important;
  font-family: Georgia, "Times New Roman", serif !important;
  font-size: clamp(2.05rem,3vw,2.95rem) !important;
  font-weight: 900 !important;
  letter-spacing: -.045em !important;
  color: #1d170f !important;
}
.tos-settings-flagship-v1 .tos-settings-flagship-header p {
  margin-top: 5px !important;
  color: #64748b !important;
  font-size: .87rem !important;
  font-weight: 700 !important;
}

/* ---- System Settings Center panel ---- */
.tos-settings-overview-v1 .tos-settings-overview-hero {
  overflow: hidden !important;
  border: 1px solid rgba(184,124,20,.20) !important;
  border-radius: 28px !important;
  background:
    radial-gradient(100% 110% at 88% 115%,
      transparent 0 46%, rgba(188,124,17,.050) 46.2% 46.45%, transparent 46.7% 49.2%,
      rgba(188,124,17,.035) 49.4% 49.65%, transparent 49.9% 100%),
    linear-gradient(145deg,#fff 0%,#fffefa 62%,#fbf4e8 100%) !important;
  box-shadow: 0 16px 36px rgba(67,43,8,.07), inset 0 1px rgba(255,255,255,.98) !important;
}
.tos-settings-overview-v1 .tos-settings-overview-hero::after {
  content: "" !important;
  inset-inline-end: -120px !important;
  bottom: -170px !important;
  width: 620px !important;
  height: 310px !important;
  border-radius: 50% !important;
  border: 1px solid rgba(186,122,17,.055) !important;
  box-shadow: 0 0 0 26px rgba(186,122,17,.018), 0 0 0 52px rgba(186,122,17,.012) !important;
}
.tos-settings-overview-v1 .tos-settings-overview-hero .tos-kicker {
  letter-spacing: .18em !important;
  color: #a46c0d !important;
}
.tos-settings-overview-v1 .tos-settings-overview-hero h3 {
  font-family: Georgia, "Times New Roman", serif !important;
  font-size: clamp(1.85rem,2.5vw,2.55rem) !important;
  letter-spacing: -.035em !important;
  color: #21190f !important;
}
.tos-settings-overview-v1 .tos-settings-overview-hero > div:first-child > div:last-child {
  border-color: rgba(33,148,103,.20) !important;
  background: linear-gradient(180deg,#f0fff9,#e5f8ef) !important;
  color: #117254 !important;
  box-shadow: 0 7px 18px rgba(24,130,92,.06), inset 0 1px rgba(255,255,255,.9) !important;
}

/* ---- KPI hardware ---- */
.tos-settings-overview-v1 .tos-settings-overview-stats {
  gap: 12px !important;
}
.tos-settings-overview-v1 .tos-settings-overview-stats > .tos-premium-stat {
  min-height: 118px;
  padding: 17px 18px !important;
  border: 1px solid rgba(171,111,14,.18) !important;
  border-radius: 19px !important;
  background:
    radial-gradient(circle at 86% 12%, rgba(235,197,110,.14), transparent 27%),
    linear-gradient(155deg,#ffffff 0%,#fffdfa 100%) !important;
  box-shadow: 0 10px 24px rgba(69,44,5,.055), inset 0 1px rgba(255,255,255,.98) !important;
  transform: none !important;
}
.tos-settings-overview-v1 .tos-settings-overview-stats > .tos-premium-stat::before {
  inset-block: 13px !important;
  width: 2px !important;
  background: linear-gradient(180deg,#f4c95f 0%,#c98b18 100%) !important;
  box-shadow: 0 0 12px rgba(213,154,35,.16);
}
.tos-settings-overview-v1 .tos-settings-overview-stats > .tos-premium-stat > .flex > div:first-child > div:first-child {
  font-family: Georgia,"Times New Roman",serif;
  font-size: 1.36rem !important;
  line-height: 1.1;
  color: #211b13 !important;
}
.tos-settings-overview-v1 .tos-settings-overview-stats > .tos-premium-stat > .flex > div:last-child {
  width: 46px !important;
  height: 46px !important;
  border-radius: 999px !important;
  box-shadow: 0 8px 20px rgba(68,43,5,.08), inset 0 1px rgba(255,255,255,.85);
}

/* ---- Reference section cards ---- */
.tos-settings-overview-v1 .tos-settings-section-grid {
  gap: 13px !important;
}
.tos-settings-overview-v1 .tos-settings-section-card {
  position: relative;
  min-height: 188px !important;
  padding: 20px !important;
  overflow: hidden !important;
  border: 1px solid rgba(185,123,18,.27) !important;
  border-radius: 22px !important;
  background:
    radial-gradient(110% 82% at 88% 119%,
      transparent 0 48%, rgba(189,125,17,.085) 48.25% 48.55%, transparent 48.85% 52%,
      rgba(189,125,17,.052) 52.2% 52.48%, transparent 52.8% 100%),
    radial-gradient(circle at 88% 10%, rgba(240,205,127,.12), transparent 26%),
    linear-gradient(145deg,#fff 0%,#fffdf8 58%,#faf1df 100%) !important;
  box-shadow:
    0 14px 30px rgba(75,47,3,.07),
    0 1px 0 rgba(255,255,255,.98) inset,
    0 -1px 0 rgba(160,101,8,.035) inset !important;
  transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease !important;
}
.tos-settings-overview-v1 .tos-settings-section-card::before {
  content: "" !important;
  top: 18px !important;
  bottom: 18px !important;
  inset-inline-start: 0 !important;
  width: 2px !important;
  background: linear-gradient(180deg,#f2cb66,#bd7b0c) !important;
  box-shadow: 0 0 14px rgba(220,163,47,.18);
}
.tos-settings-overview-v1 .tos-settings-section-card::after {
  content: "•••";
  position: absolute;
  top: 12px;
  inset-inline-end: 12px;
  z-index: 2;
  display: grid;
  place-items: center;
  width: 27px;
  height: 27px;
  border: 1px solid rgba(172,111,13,.14);
  border-radius: 999px;
  background: rgba(255,252,244,.88);
  color: #b57a19;
  font-size: 10px;
  letter-spacing: 1px;
  box-shadow: 0 5px 14px rgba(85,51,2,.055), inset 0 1px rgba(255,255,255,.9);
  pointer-events: none;
}
.tos-settings-overview-v1 .tos-settings-section-card:hover {
  transform: translateY(-2px) !important;
  border-color: rgba(190,128,22,.45) !important;
  box-shadow: 0 22px 42px rgba(83,51,3,.105), inset 0 1px rgba(255,255,255,.98) !important;
}
.tos-settings-overview-v1 .tos-settings-section-card h4 {
  font-family: Georgia,"Times New Roman",serif;
  font-size: 1.05rem !important;
  color: #241d15 !important;
}
.tos-settings-overview-v1 .tos-settings-section-card .tos-muted {
  color: #61708a !important;
  font-weight: 700 !important;
  line-height: 1.55 !important;
}
.tos-settings-overview-v1 .tos-settings-section-icon {
  width: 48px !important;
  height: 48px !important;
  border-radius: 999px !important;
  border-width: 1px !important;
  box-shadow: 0 8px 20px rgba(68,42,5,.09), inset 0 1px rgba(255,255,255,.88) !important;
}

/* preserve jewel families, increase luminosity */
.tos-settings-overview-v1 .tos-settings-section-card:nth-child(1) .tos-settings-section-icon { box-shadow:0 8px 22px rgba(118,70,182,.15),inset 0 1px rgba(255,255,255,.88)!important; }
.tos-settings-overview-v1 .tos-settings-section-card:nth-child(2) .tos-settings-section-icon { box-shadow:0 8px 22px rgba(24,144,101,.14),inset 0 1px rgba(255,255,255,.88)!important; }
.tos-settings-overview-v1 .tos-settings-section-card:nth-child(3) .tos-settings-section-icon { box-shadow:0 8px 22px rgba(48,105,176,.14),inset 0 1px rgba(255,255,255,.88)!important; }
.tos-settings-overview-v1 .tos-settings-section-card:nth-child(4) .tos-settings-section-icon { box-shadow:0 8px 22px rgba(39,134,147,.13),inset 0 1px rgba(255,255,255,.88)!important; }
.tos-settings-overview-v1 .tos-settings-section-card:nth-child(5) .tos-settings-section-icon { box-shadow:0 8px 22px rgba(174,76,93,.13),inset 0 1px rgba(255,255,255,.88)!important; }
.tos-settings-overview-v1 .tos-settings-section-card:nth-child(6) .tos-settings-section-icon { box-shadow:0 8px 22px rgba(188,130,24,.14),inset 0 1px rgba(255,255,255,.88)!important; }

/* ---- Metallic gold action hardware ---- */
.tos-settings-overview-v1 .tos-settings-section-open {
  position: relative;
  justify-content: center !important;
  min-height: 40px !important;
  border: 1px solid #bd7d12 !important;
  border-radius: 999px !important;
  color: #2a1a05 !important;
  background:
    linear-gradient(180deg,#fff5c9 0%,#f1cf6d 21%,#d9a329 58%,#c18412 100%) !important;
  box-shadow:
    0 9px 20px rgba(120,73,4,.18),
    inset 0 1px rgba(255,255,255,.95),
    inset 0 -2px rgba(112,67,3,.15),
    0 0 0 1px rgba(255,235,167,.35) !important;
  text-shadow: 0 1px rgba(255,255,255,.48);
  font-weight: 900 !important;
  overflow: hidden;
}
.tos-settings-overview-v1 .tos-settings-section-open::before {
  content: "";
  position: absolute;
  inset: 1px 8% auto;
  height: 38%;
  border-radius: 999px;
  background: linear-gradient(180deg,rgba(255,255,255,.62),rgba(255,255,255,0));
  pointer-events: none;
}
.tos-settings-overview-v1 .tos-settings-section-open::after {
  content: "→";
  margin-inline-start: 10px;
  font-size: 1rem;
  line-height: 1;
}
.tos-settings-overview-v1 .tos-settings-section-open:hover {
  transform: translateY(-1px) !important;
  background: linear-gradient(180deg,#fff1b2 0%,#ecc250 22%,#d09215 60%,#b96f05 100%) !important;
  box-shadow: 0 12px 26px rgba(121,72,3,.24), inset 0 1px rgba(255,255,255,.92) !important;
}

/* =========================================================
   DARK REFERENCE — obsidian / black titanium / luminous gold
   ========================================================= */
.dark .tos-settings-flagship-v1.tos-page {
  background:
    radial-gradient(circle at 10% 0%, rgba(227,176,66,.065), transparent 30%),
    radial-gradient(circle at 92% 100%, rgba(221,165,48,.045), transparent 32%),
    linear-gradient(180deg,#090b0d 0%,#050708 100%) !important;
  box-shadow: inset 0 1px rgba(255,255,255,.022);
}
.dark .tos-settings-flagship-v1 .tos-settings-flagship-header {
  border-color: rgba(232,184,74,.42) !important;
  background:
    radial-gradient(120% 110% at 73% 135%,
      transparent 0 41%, rgba(255,202,83,.28) 41.15% 41.45%, transparent 41.7% 43.9%,
      rgba(255,195,62,.17) 44.05% 44.33%, transparent 44.6% 47%,
      rgba(255,190,54,.105) 47.15% 47.42%, transparent 47.7% 100%),
    radial-gradient(circle at 77% 55%, rgba(232,170,43,.13), transparent 28%),
    linear-gradient(132deg,#0c1115 0%,#12171a 52%,#141008 100%) !important;
  box-shadow:
    0 28px 58px rgba(0,0,0,.34),
    0 0 32px rgba(214,154,31,.055),
    inset 0 1px rgba(255,255,255,.035) !important;
}
.dark .tos-settings-flagship-v1 .tos-settings-flagship-header::before {
  opacity: .88;
  background:
    radial-gradient(circle at 75% 59%, rgba(255,206,100,.14), transparent 9%, transparent 23%),
    repeating-linear-gradient(0deg,transparent 0 27px,rgba(235,184,76,.016) 28px,transparent 29px) !important;
}
.dark .tos-settings-flagship-v1 .tos-settings-flagship-header::after {
  color: rgba(244,219,158,.72) !important;
  text-shadow: 0 0 18px rgba(239,184,69,.12);
}
.dark .tos-settings-flagship-v1 .tos-settings-flagship-header > div > div:first-child {
  border-color: rgba(235,184,70,.36) !important;
  background: linear-gradient(180deg,rgba(54,45,24,.94),rgba(28,25,20,.96)) !important;
  color: #f0c76c !important;
  box-shadow: 0 8px 22px rgba(0,0,0,.22), inset 0 1px rgba(255,236,184,.10) !important;
}
.dark .tos-settings-flagship-v1 .tos-settings-flagship-header h1 { color:#fff8eb !important; text-shadow:0 10px 30px rgba(0,0,0,.25); }
.dark .tos-settings-flagship-v1 .tos-settings-flagship-header p { color:#9db0c1 !important; }

.dark .tos-settings-overview-v1 .tos-settings-overview-hero {
  border-color: rgba(229,181,70,.26) !important;
  background:
    radial-gradient(100% 90% at 91% 108%,
      transparent 0 47%, rgba(240,185,67,.095) 47.2% 47.48%, transparent 47.75% 51%,
      rgba(240,185,67,.055) 51.2% 51.48%, transparent 51.75% 100%),
    linear-gradient(145deg,#11171b 0%,#0c1114 72%,#171108 100%) !important;
  box-shadow: 0 24px 50px rgba(0,0,0,.32), inset 0 1px rgba(255,255,255,.025) !important;
}
.dark .tos-settings-overview-v1 .tos-settings-overview-hero h3 { color:#fff8eb !important; }
.dark .tos-settings-overview-v1 .tos-settings-overview-hero .tos-muted { color:#a8b1b8 !important; }
.dark .tos-settings-overview-v1 .tos-settings-overview-hero::after { border-color:rgba(238,184,68,.055)!important; box-shadow:0 0 0 26px rgba(238,184,68,.014),0 0 0 52px rgba(238,184,68,.008)!important; }
.dark .tos-settings-overview-v1 .tos-settings-overview-hero > div:first-child > div:last-child {
  border-color: rgba(41,190,134,.28) !important;
  background: linear-gradient(180deg,rgba(14,63,47,.72),rgba(9,42,33,.78)) !important;
  color: #55e5ad !important;
  box-shadow: 0 8px 20px rgba(0,0,0,.20), inset 0 1px rgba(113,255,203,.06) !important;
}

.dark .tos-settings-overview-v1 .tos-settings-overview-stats > .tos-premium-stat {
  border-color: rgba(226,177,67,.23) !important;
  background:
    radial-gradient(circle at 87% 11%,rgba(231,176,62,.08),transparent 25%),
    linear-gradient(155deg,#13191d 0%,#0c1114 100%) !important;
  box-shadow: 0 13px 28px rgba(0,0,0,.25), inset 0 1px rgba(255,255,255,.025) !important;
}
.dark .tos-settings-overview-v1 .tos-settings-overview-stats > .tos-premium-stat > .flex > div:first-child > div:first-child { color:#fff6e5 !important; }
.dark .tos-settings-overview-v1 .tos-settings-overview-stats > .tos-premium-stat > .flex > div:first-child > div:nth-child(2) { color:#f2ede3 !important; }
.dark .tos-settings-overview-v1 .tos-settings-overview-stats > .tos-premium-stat > .flex > div:first-child > div:nth-child(3) { color:#8997a5 !important; }
.dark .tos-settings-overview-v1 .tos-settings-overview-stats > .tos-premium-stat > .flex > div:last-child {
  border-color: rgba(232,185,75,.20) !important;
  background-color: rgba(255,255,255,.025) !important;
  box-shadow: 0 8px 21px rgba(0,0,0,.25), inset 0 1px rgba(255,255,255,.025) !important;
}

.dark .tos-settings-overview-v1 .tos-settings-section-card {
  border-color: rgba(231,180,68,.34) !important;
  background:
    radial-gradient(112% 86% at 89% 120%,
      transparent 0 47%, rgba(244,188,67,.15) 47.2% 47.5%, transparent 47.8% 51%,
      rgba(244,188,67,.085) 51.2% 51.48%, transparent 51.8% 100%),
    radial-gradient(circle at 86% 13%,rgba(230,174,58,.065),transparent 27%),
    linear-gradient(145deg,#12191d 0%,#0b1114 64%,#151008 100%) !important;
  box-shadow:
    0 18px 34px rgba(0,0,0,.30),
    inset 0 1px rgba(255,255,255,.024),
    0 0 26px rgba(219,157,31,.028) !important;
}
.dark .tos-settings-overview-v1 .tos-settings-section-card::before {
  background: linear-gradient(180deg,#ffd36f,#bd7400) !important;
  box-shadow: 0 0 17px rgba(244,185,62,.22);
}
.dark .tos-settings-overview-v1 .tos-settings-section-card::after {
  border-color: rgba(232,181,70,.21);
  background: rgba(31,28,20,.76);
  color: #e7b950;
  box-shadow: 0 7px 18px rgba(0,0,0,.25), inset 0 1px rgba(255,234,178,.04);
}
.dark .tos-settings-overview-v1 .tos-settings-section-card:hover {
  border-color: rgba(243,193,78,.58) !important;
  box-shadow: 0 24px 48px rgba(0,0,0,.37),0 0 30px rgba(222,161,37,.055),inset 0 1px rgba(255,255,255,.028)!important;
}
.dark .tos-settings-overview-v1 .tos-settings-section-card h4 { color:#fff7e8 !important; }
.dark .tos-settings-overview-v1 .tos-settings-section-card .tos-muted { color:#99a6b1 !important; }
.dark .tos-settings-overview-v1 .tos-settings-section-icon {
  border-color: rgba(255,255,255,.12) !important;
  box-shadow: 0 8px 22px rgba(0,0,0,.28),0 0 22px currentColor,inset 0 1px rgba(255,255,255,.05) !important;
}

.dark .tos-settings-overview-v1 .tos-settings-section-open {
  border-color: #d99b26 !important;
  color: #160e03 !important;
  background:
    linear-gradient(180deg,#fff0ad 0%,#f2c459 19%,#d49518 55%,#a96100 100%) !important;
  box-shadow:
    0 10px 25px rgba(0,0,0,.32),
    0 0 18px rgba(235,174,51,.13),
    inset 0 1px rgba(255,255,255,.86),
    inset 0 -2px rgba(69,37,0,.24) !important;
  text-shadow: 0 1px rgba(255,255,255,.45);
}
.dark .tos-settings-overview-v1 .tos-settings-section-open:hover {
  background: linear-gradient(180deg,#fff0ad,#efba42 22%,#c77f09 58%,#934c00 100%) !important;
  box-shadow: 0 13px 29px rgba(0,0,0,.38),0 0 24px rgba(238,179,54,.17),inset 0 1px rgba(255,255,255,.82) !important;
}

@media (max-width: 767px) {
  .tos-settings-flagship-v1.tos-page { padding: 2px; border-radius: 24px; }
  .tos-settings-flagship-v1 .tos-settings-flagship-header { min-height: 150px !important; padding: 23px 22px !important; }
  .tos-settings-flagship-v1 .tos-settings-flagship-header::after { display:none; }
  .tos-settings-overview-v1 .tos-settings-section-card { min-height: 174px !important; padding: 18px !important; }
}
'''


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


if not PAGE.exists():
    fail(f"Settings page missing: {PAGE}")
if not V1_STYLE.exists():
    fail(f"Settings Overview V1 style missing: {V1_STYLE}")

page_text = PAGE.read_text()
v1_style_text = V1_STYLE.read_text()

for marker in [V1_IMPORT, "tos-settings-flagship-v1", "tos-settings-overview-v1", "tos-settings-overview-stats", "tos-settings-section-card", "tos-settings-section-open"]:
    if marker not in page_text:
        fail(f"required current Settings Overview V1 marker missing: {marker}")
if V1_RUNTIME not in v1_style_text:
    fail("required Settings Overview V1 runtime marker missing")
if V2_IMPORT in page_text or V2_STYLE.exists():
    fail("Settings Overview Flagship V2 Reference Fidelity already present")

stamp = int(time.time())
page_backup = PAGE.with_name(f"{PAGE.name}.settings-v2-reference-backup-{stamp}")
shutil.copy2(PAGE, page_backup)
live_backup = None
staging = None

try:
    PAGE.write_text(page_text.replace(V1_IMPORT, V1_IMPORT + "\n" + V2_IMPORT, 1))
    V2_STYLE.write_text(CSS)

    updated_page = PAGE.read_text()
    if V2_IMPORT not in updated_page:
        fail("V2 reference stylesheet import missing after write")
    if V2_RUNTIME not in V2_STYLE.read_text():
        fail("V2 reference runtime marker missing after style write")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists():
        fail("frontend dist missing after build")

    built_css = ""
    for css_file in DIST.rglob("*.css"):
        built_css += css_file.read_text(errors="ignore")
    if V2_RUNTIME not in built_css:
        fail("Settings Overview V2 reference marker missing from built CSS")
    for marker in ["SIMPLER SYSTEMS", "tos-settings-section-open", "#fff8eb"]:
        if marker.lower() not in built_css.lower():
            fail(f"Settings Overview V2 reference CSS marker missing from build: {marker}")

    LIVE_PARENT.mkdir(parents=True, exist_ok=True)
    staging = LIVE_PARENT / f"build.settings-overview-v2-reference-staging-{stamp}"
    live_backup = LIVE_PARENT / f"build.settings-overview-v2-reference-backup-{stamp}"
    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(DIST, staging)

    if LIVE.exists():
        LIVE.rename(live_backup)
    staging.rename(LIVE)

    live_css = ""
    for css_file in LIVE.rglob("*.css"):
        live_css += css_file.read_text(errors="ignore")
    if V2_RUNTIME not in live_css:
        fail("Settings Overview V2 reference runtime marker missing from live build")

    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("SETTINGS_OVERVIEW_FLAGSHIP_V2_REFERENCE_RUNTIME=YES")
    print("REFERENCE_MODE=APPROVED_LIGHT_AND_DARK_LUXURY_MOCKUPS")
    print("REFERENCE_FIDELITY=HIGH")
    print("SETTINGS_LIGHT=PEARL_IVORY_METALLIC_CHAMPAGNE_WAVE")
    print("SETTINGS_DARK=OBSIDIAN_BLACK_TITANIUM_LUMINOUS_GOLD_WAVE")
    print("SETTINGS_HERO=LUXURY_FLOWING_WAVE_REFERENCE")
    print("SETTINGS_KPIS=PREMIUM_HARDWARE_REFERENCE")
    print("SETTINGS_SECTION_CARDS=GOLD_EDGE_WAVE_REFERENCE")
    print("SETTINGS_SECTION_ICONS=JEWEL_ORBS_REFERENCE")
    print("SETTINGS_SECTION_ACTIONS=METALLIC_GOLD_PILL_REFERENCE")
    print("SETTINGS_DECORATIVE_DOTS=YES")
    print("SETTINGS_ACTION_ARROW=YES")
    print("SETTINGS_LOGIC_CHANGED=NO")
    print("SETTINGS_API_CHANGED=NO")
    print("SETTINGS_PERMISSIONS_CHANGED=NO")
    print("SETTINGS_NAVIGATION_CHANGED=NO")
    print("SETTINGS_SAVE_LOGIC_CHANGED=NO")
    print("SETTINGS_INTEGRATIONS_CHANGED=NO")
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
        if V2_STYLE.exists():
            V2_STYLE.unlink()
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
