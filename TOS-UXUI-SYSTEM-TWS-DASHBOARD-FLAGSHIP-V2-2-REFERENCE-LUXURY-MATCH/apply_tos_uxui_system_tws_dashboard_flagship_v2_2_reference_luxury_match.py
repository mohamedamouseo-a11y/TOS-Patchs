from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
PAGE = FRONTEND / "src/pages/tws/TwsDashboard.jsx"
V1_STYLE = FRONTEND / "src/pages/tws/twsDashboardFlagshipV1.css"
V11_STYLE = FRONTEND / "src/pages/tws/twsDashboardFlagshipV1_1DarkFidelity.css"
V2_STYLE = FRONTEND / "src/pages/tws/twsDashboardFlagshipV2LuxuryPolish.css"
V21_STYLE = FRONTEND / "src/pages/tws/twsDashboardFlagshipV2_1ButtonsLuxuryPolish.css"
V22_STYLE = FRONTEND / "src/pages/tws/twsDashboardFlagshipV2_2ReferenceLuxuryMatch.css"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_V1_STYLE_SHA256 = "6691401c241187e5ffd6611ba1d02510f37b954f975ec40021e5cee9072be49a"
EXPECTED_V11_STYLE_SHA256 = "b0a53b84f4cc74eed2f83c5b38d3fd72661bb81d4a7c54507766b8ad36998849"
EXPECTED_V2_STYLE_SHA256 = "e5b14bee3119d2de6e0b6450e555f358c5671ba47dcaaf12813e6ad4e218e4cc"

IMPORT_V1 = 'import "./twsDashboardFlagshipV1.css";'
IMPORT_V11 = 'import "./twsDashboardFlagshipV1_1DarkFidelity.css";'
IMPORT_V2 = 'import "./twsDashboardFlagshipV2LuxuryPolish.css";'
IMPORT_V21 = 'import "./twsDashboardFlagshipV2_1ButtonsLuxuryPolish.css";'
IMPORT_V22 = 'import "./twsDashboardFlagshipV2_2ReferenceLuxuryMatch.css";'

CSS = r''':root {
  --tos-tws-dashboard-flagship-v2-2-reference-luxury-runtime: 1;
}

/*
 * TWS Flagship V2.2 — Reference Luxury Match
 * Visual direction: pearl ivory + champagne metal + soft gold edge light.
 * File cards use jewel-tone type icons (T-Doc blue, T-Sheet emerald, T-Slide orange).
 * Dark mode mirrors the same hierarchy using obsidian, smoked titanium and restrained champagne.
 */

.tos-tws-flagship-v1 {
  --v22-pearl: #fffdf8;
  --v22-cream: #fbf6ec;
  --v22-champagne: #f2d889;
  --v22-gold: #d5a73b;
  --v22-antique: #a96f12;
  --v22-ink: #18130d;
  --v22-muted: #766d62;
  --v22-line: rgba(170,111,14,.18);
}

/* ---------- Page / system header ---------- */
.tos-tws-flagship-v1 > .tos-premium-system-header {
  overflow: hidden !important;
  border: 1px solid rgba(178,119,19,.20) !important;
  border-radius: 26px !important;
  background:
    radial-gradient(ellipse at 92% -10%, rgba(244,215,145,.36), transparent 38%),
    radial-gradient(ellipse at 52% 140%, rgba(225,191,115,.14), transparent 44%),
    linear-gradient(112deg,#fffefb 0%,#fffdf8 42%,#fbf4e6 100%) !important;
  box-shadow:
    0 18px 45px rgba(77,48,5,.075),
    inset 0 1px 0 rgba(255,255,255,.96),
    inset 0 -1px 0 rgba(158,100,8,.05) !important;
}
.tos-tws-flagship-v1 > .tos-premium-system-header::before {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  opacity: .7;
  background:
    radial-gradient(110% 100% at 75% 0%, transparent 46%, rgba(214,167,68,.09) 47%, transparent 48%),
    radial-gradient(100% 90% at 67% 0%, transparent 52%, rgba(214,167,68,.055) 53%, transparent 54%);
}
.tos-tws-flagship-v1 > .tos-premium-system-header > div {
  padding-block: 22px !important;
}
.tos-tws-flagship-v1 > .tos-premium-system-header h1 {
  color: #16110b !important;
  font-family: ui-serif, Georgia, Cambria, "Times New Roman", serif;
  font-size: clamp(24px,2vw,31px) !important;
  letter-spacing: -.035em !important;
}
.tos-tws-flagship-v1 > .tos-premium-system-header p:first-child {
  color: #a86f10 !important;
  letter-spacing: .22em !important;
}

/* Header metallic actions */
.tos-tws-flagship-v1 > .tos-premium-system-header .tos-premium-button {
  min-height: 42px !important;
  border-radius: 13px !important;
  border: 1px solid rgba(159,102,8,.20) !important;
  font-weight: 900 !important;
  box-shadow:
    0 8px 20px rgba(77,47,3,.075),
    inset 0 1px rgba(255,255,255,.70),
    inset 0 -1px rgba(107,64,2,.08) !important;
}
.tos-tws-flagship-v1 > .tos-premium-system-header .tos-premium-button:first-of-type {
  color: #251802 !important;
  background: linear-gradient(180deg,#f8e39f 0%,#e7bd4d 54%,#d6a22b 100%) !important;
  border-color: rgba(144,89,3,.34) !important;
  box-shadow:
    0 10px 24px rgba(153,98,7,.20),
    inset 0 1px rgba(255,255,255,.66),
    inset 0 -2px rgba(108,64,1,.10) !important;
}
.tos-tws-flagship-v1 > .tos-premium-system-header .tos-premium-button:not(:first-of-type) {
  color: #3b2b16 !important;
  background: linear-gradient(180deg,#fffefa,#f6ead0) !important;
}
.tos-tws-flagship-v1 > .tos-premium-system-header .tos-premium-button:hover:not(:disabled) {
  transform: translateY(-2px) !important;
  border-color: rgba(166,107,10,.38) !important;
  box-shadow: 0 14px 30px rgba(98,59,3,.15), inset 0 1px rgba(255,255,255,.82) !important;
}
.tos-tws-flagship-v1 > .tos-premium-system-header button[title] {
  border-radius: 13px !important;
  border: 1px solid rgba(170,112,16,.18) !important;
  color: #94610a !important;
  background: linear-gradient(145deg,#fffdf7,#f0ddb0) !important;
  box-shadow: 0 8px 19px rgba(76,46,3,.07), inset 0 1px rgba(255,255,255,.9) !important;
}

/* ---------- Hero — pearl silk / champagne linework ---------- */
.tos-tws-flagship-v1 .tos-tws-hero-layout {
  gap: 16px !important;
}
.tos-tws-flagship-v1 .tos-tws-hero-card {
  border: 1px solid rgba(178,118,17,.25) !important;
  border-radius: 22px !important;
  background: #fdf8ed !important;
  box-shadow: 0 18px 40px rgba(72,44,3,.08), inset 0 1px rgba(255,255,255,.94) !important;
}
.tos-tws-flagship-v1 .tos-tws-hero {
  min-height: 236px !important;
  padding: 28px !important;
  border-radius: 21px !important;
  background:
    radial-gradient(110% 120% at 4% 15%, rgba(255,255,255,.96) 0 31%, transparent 32%),
    radial-gradient(105% 90% at 85% 105%, rgba(239,215,158,.46) 0 32%, transparent 33%),
    radial-gradient(95% 105% at 65% -18%, rgba(255,255,255,.87) 0 34%, transparent 35%),
    linear-gradient(118deg,#fffef9 0%,#fbf3e0 54%,#efe0b9 100%) !important;
}
.tos-tws-flagship-v1 .tos-tws-hero::before {
  content: "";
  position: absolute;
  inset: -20% -8%;
  pointer-events: none;
  opacity: .82;
  background:
    repeating-radial-gradient(ellipse at 12% 48%, transparent 0 55px, rgba(197,138,29,.12) 56px 57px, transparent 58px 84px),
    repeating-radial-gradient(ellipse at 98% 52%, transparent 0 72px, rgba(197,138,29,.08) 73px 74px, transparent 75px 106px);
  transform: rotate(-6deg) scale(1.08);
  mask-image: linear-gradient(90deg,#000 0%,rgba(0,0,0,.72) 70%,rgba(0,0,0,.25) 100%);
}
.tos-tws-flagship-v1 .tos-tws-hero::after {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(120deg, transparent 15%, rgba(255,255,255,.72) 39%, transparent 57%),
    radial-gradient(circle at 8% 85%, rgba(184,122,14,.12), transparent 17%);
  mix-blend-mode: soft-light;
}
.tos-tws-flagship-v1 .tos-tws-hero h2 {
  color: #17110b !important;
  font-family: ui-serif, Georgia, Cambria, "Times New Roman", serif;
  font-size: clamp(31px,3.1vw,46px) !important;
  line-height: 1.02 !important;
  letter-spacing: -.045em !important;
  text-shadow: 0 1px rgba(255,255,255,.70);
}
.tos-tws-flagship-v1 .tos-tws-hero p {
  color: #5e564c !important;
  max-width: 690px;
  line-height: 1.75 !important;
}
.tos-tws-flagship-v1 .tos-tws-hero > div > div:first-child > span {
  color: #8c5b08 !important;
  border: 1px solid rgba(170,109,10,.20) !important;
  background: rgba(255,249,233,.72) !important;
  box-shadow: 0 6px 16px rgba(107,66,5,.07), inset 0 1px rgba(255,255,255,.88) !important;
}

/* Quick Create: elevated pearl palette */
.tos-tws-flagship-v1 .tos-tws-quick-create {
  min-width: 230px !important;
  padding: 12px !important;
  border-radius: 21px !important;
  border: 1px solid rgba(168,108,11,.21) !important;
  background: rgba(255,252,244,.79) !important;
  box-shadow: 0 18px 38px rgba(91,55,4,.12), inset 0 1px rgba(255,255,255,.98) !important;
  backdrop-filter: blur(22px) saturate(1.12);
}
.tos-tws-flagship-v1 .tos-tws-quick-create > b {
  color: #96610a !important;
  font-size: 10px !important;
  letter-spacing: .08em !important;
}
.tos-tws-flagship-v1 .tos-tws-quick-create button {
  min-height: 41px !important;
  border-radius: 12px !important;
  border: 1px solid rgba(159,102,8,.17) !important;
}
.tos-tws-flagship-v1 .tos-tws-quick-create button:first-of-type {
  color: #231702 !important;
  background: linear-gradient(180deg,#f8e6a8,#e3b947 62%,#d3a12e) !important;
  box-shadow: 0 8px 18px rgba(150,94,6,.16), inset 0 1px rgba(255,255,255,.6) !important;
}
.tos-tws-flagship-v1 .tos-tws-quick-create button:not(:first-of-type) {
  color: #382b1b !important;
  background: linear-gradient(180deg,#fffefa,#f5ead1) !important;
}

/* ---------- KPI tiles ---------- */
.tos-tws-flagship-v1 .tos-tws-stat {
  min-height: 108px !important;
  border-radius: 18px !important;
  border: 1px solid rgba(168,109,14,.14) !important;
  background: linear-gradient(152deg,#fffefa,#fbf5e9) !important;
  box-shadow: 0 13px 31px rgba(69,42,3,.065), inset 0 1px rgba(255,255,255,.96) !important;
}
.tos-tws-flagship-v1 .tos-tws-stat b {
  font-size: 29px !important;
}
.tos-tws-flagship-v1 .tos-tws-stat .grid.h-10.w-10 {
  width: 45px !important;
  height: 45px !important;
  border-radius: 14px !important;
  border: 1px solid rgba(171,110,11,.17) !important;
  color: #9b650a !important;
  background: linear-gradient(145deg,#fffaf0,#efddb1) !important;
  box-shadow: 0 8px 19px rgba(78,47,3,.08), inset 0 1px rgba(255,255,255,.9) !important;
}

/* ---------- Command surface ---------- */
.tos-tws-flagship-v1 .tos-tws-control-card {
  padding: 16px !important;
  border-radius: 20px !important;
  border: 1px solid rgba(165,106,10,.15) !important;
  background: linear-gradient(180deg,#fffefa,#fbf7ef) !important;
  box-shadow: 0 15px 35px rgba(65,39,3,.06), inset 0 1px rgba(255,255,255,.96) !important;
}
.tos-tws-flagship-v1 .tos-tws-tabs {
  gap: 8px !important;
}
.tos-tws-flagship-v1 .tos-tws-tab {
  min-height: 39px !important;
  border-radius: 12px !important;
  border: 1px solid rgba(157,99,6,.13) !important;
  color: #3e3121 !important;
  background: linear-gradient(180deg,#fffefa,#f5ebd7) !important;
  box-shadow: 0 6px 15px rgba(62,37,2,.04), inset 0 1px rgba(255,255,255,.90) !important;
}
.tos-tws-flagship-v1 .tos-tws-tabs .tos-tws-tab[class*="bg-zinc-950"] {
  color: #211501 !important;
  border-color: rgba(145,88,3,.34) !important;
  background: linear-gradient(180deg,#f7df91,#e3b643 58%,#ce9821) !important;
  box-shadow: 0 9px 20px rgba(143,87,4,.17), inset 0 1px rgba(255,255,255,.62) !important;
}
.tos-tws-flagship-v1 .tos-tws-filter-row {
  margin-top: 11px !important;
  gap: 9px !important;
}
.tos-tws-flagship-v1 .tos-tws-filter-row input {
  min-height: 45px !important;
  border-radius: 12px !important;
  border: 1px solid rgba(154,97,8,.14) !important;
  background: linear-gradient(180deg,#fffefa,#fbf8f1) !important;
  box-shadow: inset 0 1px 2px rgba(67,40,3,.035), 0 5px 14px rgba(65,39,3,.025) !important;
}
.tos-tws-premium-trigger {
  min-height: 45px !important;
  border-radius: 12px !important;
  border-color: rgba(157,99,6,.16) !important;
  background: linear-gradient(180deg,#fffefa,#f6ecd8) !important;
  box-shadow: 0 6px 16px rgba(64,38,2,.04), inset 0 1px rgba(255,255,255,.92) !important;
}
.tos-tws-flagship-v1 .tos-tws-view-toggle {
  border-radius: 12px !important;
  border-color: rgba(156,99,7,.14) !important;
  background: linear-gradient(180deg,#fffefa,#f3e6c8) !important;
}
.tos-tws-flagship-v1 .tos-tws-view-toggle button {
  min-height: 35px !important;
  border-radius: 9px !important;
}
.tos-tws-flagship-v1 .tos-tws-view-toggle button[class*="bg-white"] {
  color: #4c3309 !important;
  background: linear-gradient(180deg,#f9e6a7,#e0b343) !important;
  box-shadow: 0 6px 15px rgba(133,80,3,.13), inset 0 1px rgba(255,255,255,.65) !important;
}

/* Refresh becomes a real command button, not a full-width bar. */
.tos-tws-flagship-v1 .tos-tws-filter-row > .tos-premium-button {
  width: max-content !important;
  min-width: 138px !important;
  min-height: 40px !important;
  justify-self: start !important;
  justify-content: center !important;
  padding-inline: 17px !important;
  border-radius: 11px !important;
  color: #382407 !important;
  border: 1px solid rgba(149,91,3,.31) !important;
  background: linear-gradient(180deg,#f8e3a0,#e1b442 62%,#cf9821) !important;
  box-shadow:
    0 8px 19px rgba(132,79,3,.14),
    inset 0 1px rgba(255,255,255,.67),
    inset 0 -1px rgba(94,55,1,.08) !important;
}
.tos-tws-flagship-v1 .tos-tws-filter-row > .tos-premium-button svg {
  color: #694302 !important;
}
.tos-tws-flagship-v1 .tos-tws-filter-row > .tos-premium-button:hover:not(:disabled) {
  transform: translateY(-2px) !important;
  background: linear-gradient(180deg,#fae9b1,#e6bb4d 62%,#d5a02a) !important;
  box-shadow: 0 12px 25px rgba(132,79,3,.20), inset 0 1px rgba(255,255,255,.75) !important;
}

/* ---------- Four executive buckets ---------- */
.tos-tws-flagship-v1 .tos-tws-buckets {
  gap: 14px !important;
}
.tos-tws-flagship-v1 .tos-tws-bucket {
  padding: 14px !important;
  border-radius: 18px !important;
  border: 1px solid rgba(167,108,11,.13) !important;
  background: linear-gradient(155deg,#fffefa,#fbf6eb) !important;
  box-shadow: 0 12px 29px rgba(63,38,2,.055), inset 0 1px rgba(255,255,255,.95) !important;
}
.tos-tws-flagship-v1 .tos-tws-bucket .mb-3 > .grid {
  border: 1px solid rgba(157,98,6,.16) !important;
  color: #946008 !important;
  background: linear-gradient(145deg,#fff9e8,#efda9e) !important;
  box-shadow: 0 6px 15px rgba(84,51,3,.06), inset 0 1px rgba(255,255,255,.9);
}
.tos-tws-flagship-v1 .tos-tws-bucket .space-y-2 > button {
  min-height: 40px !important;
  border-radius: 11px !important;
  border-color: rgba(153,96,6,.12) !important;
  background: linear-gradient(180deg,#fffefa,#fbf8f1) !important;
  box-shadow: 0 4px 10px rgba(59,35,2,.025), inset 0 1px rgba(255,255,255,.9) !important;
}
.tos-tws-flagship-v1 .tos-tws-bucket .space-y-2 > button:hover {
  transform: translateY(-1px) !important;
  border-color: rgba(167,106,8,.24) !important;
  background: #fff7e5 !important;
  box-shadow: 0 8px 17px rgba(70,42,2,.06) !important;
}

/* ---------- Document cards — reference-match product cards ---------- */
.tos-tws-flagship-v1 .tos-tws-document-card {
  min-height: 238px !important;
  padding: 14px !important;
  gap: 11px !important;
  border-radius: 18px !important;
  border: 1px solid rgba(165,105,8,.16) !important;
  background:
    radial-gradient(circle at 100% 0%, rgba(237,207,135,.18), transparent 31%),
    linear-gradient(150deg,#fffefa,#fbf7ef) !important;
  box-shadow:
    0 12px 28px rgba(65,39,2,.06),
    inset 0 1px rgba(255,255,255,.97) !important;
}
.tos-tws-flagship-v1 .tos-tws-document-card::before {
  inset-inline: 14px !important;
  height: 1px !important;
  background: linear-gradient(90deg,transparent,rgba(205,149,35,.60),transparent) !important;
}
.tos-tws-flagship-v1 .tos-tws-document-card:hover {
  transform: translateY(-3px) !important;
  border-color: rgba(174,112,10,.28) !important;
  box-shadow: 0 19px 38px rgba(70,42,2,.10), inset 0 1px rgba(255,255,255,.98) !important;
}

/* Jewel file icons */
.tos-tws-flagship-v1 .tos-tws-file-icon {
  width: 46px !important;
  height: 46px !important;
  border-radius: 13px !important;
  color: #fff !important;
  border: 1px solid rgba(255,255,255,.28) !important;
  box-shadow:
    0 9px 18px rgba(40,40,40,.15),
    inset 0 1px rgba(255,255,255,.34),
    inset 0 -2px rgba(0,0,0,.10) !important;
}
.tos-tws-flagship-v1 .tos-tws-document-tdoc .tos-tws-file-icon {
  background: linear-gradient(145deg,#5f91ff 0%,#3267e8 55%,#1d49be 100%) !important;
  box-shadow: 0 9px 20px rgba(47,97,220,.25), inset 0 1px rgba(255,255,255,.38), inset 0 -2px rgba(0,0,0,.10) !important;
}
.tos-tws-flagship-v1 .tos-tws-document-tsheet .tos-tws-file-icon {
  background: linear-gradient(145deg,#34ba75 0%,#119457 56%,#08713f 100%) !important;
  box-shadow: 0 9px 20px rgba(16,137,79,.24), inset 0 1px rgba(255,255,255,.38), inset 0 -2px rgba(0,0,0,.10) !important;
}
.tos-tws-flagship-v1 .tos-tws-document-tslide .tos-tws-file-icon {
  background: linear-gradient(145deg,#ffad43 0%,#f17c16 55%,#ca5307 100%) !important;
  box-shadow: 0 9px 20px rgba(220,101,11,.24), inset 0 1px rgba(255,255,255,.38), inset 0 -2px rgba(0,0,0,.10) !important;
}

.tos-tws-flagship-v1 .tos-tws-document-card b[title] {
  font-size: 14px !important;
  letter-spacing: -.015em;
}
.tos-tws-flagship-v1 .tos-tws-document-card > div:first-child > button:nth-child(2) > div:nth-child(2) p {
  color: #81766a !important;
}
.tos-tws-flagship-v1 .tos-tws-document-card > div:first-child > button:last-child {
  color: #caa345 !important;
}

/* Metadata: pearl inset panel */
.tos-tws-flagship-v1 .tos-tws-card-meta {
  padding: 11px 12px !important;
  gap: 5px !important;
  border: 1px solid rgba(164,103,7,.08) !important;
  border-radius: 13px !important;
  color: #7d746a !important;
  background: linear-gradient(180deg,rgba(248,242,230,.92),rgba(251,248,241,.96)) !important;
  box-shadow: inset 0 1px 2px rgba(76,45,2,.025), inset 0 1px rgba(255,255,255,.92) !important;
}
.tos-tws-flagship-v1 .tos-tws-card-meta > div > span:last-child {
  color: #332a20 !important;
  font-weight: 850 !important;
}

/* Card action bar */
.tos-tws-flagship-v1 .tos-tws-card-actions {
  gap: 8px !important;
  margin-top: auto !important;
  padding-top: 1px;
}
.tos-tws-flagship-v1 .tos-tws-card-actions .tos-premium-button {
  min-height: 36px !important;
  padding: 7px 13px !important;
  border-radius: 10px !important;
  border: 1px solid rgba(157,98,6,.18) !important;
  color: #4b3512 !important;
  background: linear-gradient(180deg,#fffdf8,#f3e3bd) !important;
  box-shadow: 0 6px 14px rgba(72,43,2,.055), inset 0 1px rgba(255,255,255,.92) !important;
}
.tos-tws-flagship-v1 .tos-tws-card-actions .tos-premium-button:hover:not(:disabled) {
  transform: translateY(-1px) !important;
  border-color: rgba(168,106,7,.30) !important;
  background: linear-gradient(180deg,#fff9e7,#ecd59d) !important;
  box-shadow: 0 9px 18px rgba(91,54,2,.09), inset 0 1px rgba(255,255,255,.94) !important;
}
.tos-tws-flagship-v1 .tos-tws-card-actions .tos-premium-button[class*="bg-red-50"] {
  color: #b12727 !important;
  border-color: rgba(183,45,45,.17) !important;
  background: linear-gradient(180deg,#fff8f7,#f9dfdc) !important;
  box-shadow: 0 6px 14px rgba(132,33,33,.05), inset 0 1px rgba(255,255,255,.92) !important;
}
.tos-tws-flagship-v1 .tos-tws-card-actions .tos-premium-button[class*="bg-red-50"]:hover:not(:disabled) {
  border-color: rgba(190,51,51,.27) !important;
  background: linear-gradient(180deg,#fff4f3,#f4d1cd) !important;
}

/* ---------- List view ---------- */
.tos-tws-flagship-v1 .tos-tws-list {
  border-radius: 18px !important;
  border-color: rgba(163,103,7,.15) !important;
  background: linear-gradient(180deg,#fffefa,#fbf7ef) !important;
  box-shadow: 0 14px 32px rgba(65,39,2,.06) !important;
}
.tos-tws-flagship-v1 .tos-tws-list-row {
  border-color: rgba(161,102,7,.09) !important;
}

/* ---------- Pagination ---------- */
.tos-tws-pagination {
  min-height: 52px;
  border-radius: 15px !important;
  border-color: rgba(162,102,7,.14) !important;
  background: linear-gradient(180deg,#fffefa,#faf4e7) !important;
  box-shadow: 0 10px 24px rgba(62,37,2,.045), inset 0 1px rgba(255,255,255,.94) !important;
}
.tos-tws-pagination button {
  border-radius: 10px !important;
  border-color: rgba(153,95,4,.18) !important;
  background: linear-gradient(180deg,#fffefa,#f3e3bd) !important;
}
.tos-tws-pagination button:not(:disabled):last-child {
  color: #322006 !important;
  border-color: rgba(145,87,2,.32) !important;
  background: linear-gradient(180deg,#f7e29c,#ddad37) !important;
  box-shadow: 0 7px 15px rgba(122,72,2,.12), inset 0 1px rgba(255,255,255,.67) !important;
}

/* ==================== DARK — Obsidian Champagne reference ==================== */
.dark .tos-tws-flagship-v1 {
  --v22-pearl: #171714;
  --v22-cream: #11110f;
  --v22-ink: #f5efe4;
  --v22-muted: #aaa195;
}
.dark .tos-tws-flagship-v1 > .tos-premium-system-header {
  border-color: rgba(221,176,76,.16) !important;
  background:
    radial-gradient(ellipse at 90% 0%, rgba(211,157,39,.10), transparent 34%),
    linear-gradient(125deg,#171714,#10100f 56%,#18150f) !important;
  box-shadow: 0 22px 55px rgba(0,0,0,.28), inset 0 1px rgba(255,255,255,.025) !important;
}
.dark .tos-tws-flagship-v1 > .tos-premium-system-header h1 { color: #fff9ef !important; }
.dark .tos-tws-flagship-v1 > .tos-premium-system-header .tos-premium-button:not(:first-of-type) {
  color: #e8dfd2 !important;
  border-color: rgba(221,176,76,.12) !important;
  background: linear-gradient(180deg,#24231f,#1a1a18) !important;
}
.dark .tos-tws-flagship-v1 > .tos-premium-system-header button[title] {
  color: #e0b859 !important;
  border-color: rgba(221,176,76,.14) !important;
  background: linear-gradient(145deg,#24231f,#181816) !important;
}

.dark .tos-tws-flagship-v1 .tos-tws-hero-card {
  border-color: rgba(219,172,69,.18) !important;
  background: #121210 !important;
  box-shadow: 0 20px 48px rgba(0,0,0,.30), inset 0 1px rgba(255,255,255,.025) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-hero {
  background:
    radial-gradient(105% 120% at 7% 10%, rgba(62,62,58,.68) 0 30%, transparent 31%),
    radial-gradient(110% 90% at 88% 110%, rgba(113,82,19,.28) 0 32%, transparent 33%),
    radial-gradient(90% 105% at 66% -20%, rgba(49,49,46,.54) 0 31%, transparent 32%),
    linear-gradient(118deg,#171714,#0e0e0d 56%,#211b0e) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-hero::before {
  opacity: .36;
  background:
    repeating-radial-gradient(ellipse at 12% 48%, transparent 0 55px, rgba(224,179,78,.14) 56px 57px, transparent 58px 84px),
    repeating-radial-gradient(ellipse at 98% 52%, transparent 0 72px, rgba(224,179,78,.10) 73px 74px, transparent 75px 106px);
}
.dark .tos-tws-flagship-v1 .tos-tws-hero::after {
  opacity: .35;
  background: linear-gradient(120deg,transparent 15%,rgba(255,255,255,.18) 39%,transparent 57%) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-hero h2 { color: #fff9ef !important; text-shadow: 0 2px 12px rgba(0,0,0,.3); }
.dark .tos-tws-flagship-v1 .tos-tws-hero p { color: #b2a99d !important; }
.dark .tos-tws-flagship-v1 .tos-tws-hero > div > div:first-child > span {
  color: #e5bd60 !important;
  border-color: rgba(222,175,73,.17) !important;
  background: rgba(223,176,75,.07) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-quick-create {
  border-color: rgba(221,176,76,.16) !important;
  background: rgba(27,27,25,.82) !important;
  box-shadow: 0 18px 40px rgba(0,0,0,.31), inset 0 1px rgba(255,255,255,.035) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-quick-create button:not(:first-of-type) {
  color: #e8e1d7 !important;
  border-color: rgba(221,176,76,.10) !important;
  background: linear-gradient(180deg,#2b2a27,#20201e) !important;
}

.dark .tos-tws-flagship-v1 .tos-tws-stat,
.dark .tos-tws-flagship-v1 .tos-tws-control-card,
.dark .tos-tws-flagship-v1 .tos-tws-bucket,
.dark .tos-tws-flagship-v1 .tos-tws-document-card,
.dark .tos-tws-flagship-v1 .tos-tws-list {
  color: #eee7dc !important;
  border-color: rgba(222,176,76,.13) !important;
  background: linear-gradient(155deg,#191917,#111110) !important;
  box-shadow: 0 16px 38px rgba(0,0,0,.22), inset 0 1px rgba(255,255,255,.02) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-stat .grid.h-10.w-10,
.dark .tos-tws-flagship-v1 .tos-tws-bucket .mb-3 > .grid {
  color: #e0b557 !important;
  border-color: rgba(222,176,76,.15) !important;
  background: linear-gradient(145deg,#2a281f,#1b1a17) !important;
  box-shadow: 0 8px 18px rgba(0,0,0,.20), inset 0 1px rgba(255,255,255,.025) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-tab {
  color: #c9c0b5 !important;
  border-color: rgba(222,176,76,.09) !important;
  background: linear-gradient(180deg,#24231f,#1a1a18) !important;
  box-shadow: inset 0 1px rgba(255,255,255,.025) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-tabs .tos-tws-tab[class~="dark:bg-white"] {
  color: #211501 !important;
  border-color: rgba(222,176,76,.25) !important;
  background: linear-gradient(180deg,#f0ce6f,#d6a22b) !important;
  box-shadow: 0 9px 21px rgba(0,0,0,.23), inset 0 1px rgba(255,255,255,.30) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-filter-row input,
.dark .tos-tws-premium-trigger {
  color: #eee7dc !important;
  border-color: rgba(222,176,76,.12) !important;
  background: linear-gradient(180deg,#1d1d1b,#171715) !important;
  box-shadow: inset 0 1px rgba(255,255,255,.02) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-view-toggle {
  border-color: rgba(222,176,76,.12) !important;
  background: linear-gradient(180deg,#22211e,#181816) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-filter-row > .tos-premium-button {
  color: #211501 !important;
  border-color: rgba(222,176,76,.27) !important;
  background: linear-gradient(180deg,#f0ce70,#d4a029) !important;
  box-shadow: 0 9px 20px rgba(0,0,0,.22), inset 0 1px rgba(255,255,255,.28) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-filter-row > .tos-premium-button svg { color: #342000 !important; }

.dark .tos-tws-flagship-v1 .tos-tws-bucket .space-y-2 > button {
  color: #eee7dc !important;
  border-color: rgba(222,176,76,.10) !important;
  background: linear-gradient(180deg,#20201e,#181816) !important;
  box-shadow: inset 0 1px rgba(255,255,255,.02) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-bucket .space-y-2 > button:hover {
  border-color: rgba(222,176,76,.20) !important;
  background: linear-gradient(180deg,#292821,#1d1c18) !important;
}

.dark .tos-tws-flagship-v1 .tos-tws-card-meta {
  color: #9f978e !important;
  border-color: rgba(222,176,76,.07) !important;
  background: linear-gradient(180deg,#1e1e1c,#191917) !important;
  box-shadow: inset 0 1px rgba(255,255,255,.015) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-card-meta > div > span:last-child { color: #eee8df !important; }
.dark .tos-tws-flagship-v1 .tos-tws-card-actions .tos-premium-button {
  color: #e4ddd2 !important;
  border-color: rgba(222,176,76,.10) !important;
  background: linear-gradient(180deg,#2a2926,#20201e) !important;
  box-shadow: 0 6px 13px rgba(0,0,0,.16), inset 0 1px rgba(255,255,255,.02) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-card-actions .tos-premium-button:hover:not(:disabled) {
  color: #f0c966 !important;
  border-color: rgba(222,176,76,.21) !important;
  background: linear-gradient(180deg,#302d24,#24211b) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-card-actions .tos-premium-button[class*="dark:bg-red-500/10"],
.dark .tos-tws-flagship-v1 .tos-tws-card-actions .tos-premium-button[class*="bg-red-50"] {
  color: #f18b83 !important;
  border-color: rgba(225,80,72,.16) !important;
  background: linear-gradient(180deg,#2c1d1b,#241716) !important;
}
.dark .tos-tws-pagination {
  color: #aaa196 !important;
  border-color: rgba(222,176,76,.11) !important;
  background: linear-gradient(180deg,#181816,#121210) !important;
  box-shadow: 0 12px 27px rgba(0,0,0,.20), inset 0 1px rgba(255,255,255,.015) !important;
}
.dark .tos-tws-pagination button {
  color: #d7cec2 !important;
  border-color: rgba(222,176,76,.10) !important;
  background: linear-gradient(180deg,#24231f,#1b1b19) !important;
}
.dark .tos-tws-pagination button:not(:disabled):last-child {
  color: #211501 !important;
  border-color: rgba(222,176,76,.24) !important;
  background: linear-gradient(180deg,#efcc6d,#d39d26) !important;
}

@media (max-width: 900px) {
  .tos-tws-flagship-v1 .tos-tws-hero { padding: 22px !important; }
  .tos-tws-flagship-v1 .tos-tws-filter-row > .tos-premium-button { width: 100% !important; justify-self: stretch !important; }
}
'''

PRESERVE_FILES = [
    FRONTEND / "src/pages/tws/TwsPage.jsx",
    FRONTEND / "src/pages/tws/TDocsEditor.jsx",
    FRONTEND / "src/pages/tws/TSheetsEditor.jsx",
    FRONTEND / "src/pages/tws/TSlidesEditor.jsx",
    FRONTEND / "src/pages/tws/TwsShareViewer.jsx",
    FRONTEND / "src/pages/tws/TwsShareSettingsPage.jsx",
    FRONTEND / "src/pages/tws/TwsShared.jsx",
    FRONTEND / "src/pages/tws/TwsRecentFilesWidget.jsx",
    FRONTEND / "src/pages/tws/TwsTaskAttachments.jsx",
    FRONTEND / "src/pages/tws/twsI18n.js",
    FRONTEND / "src/components/ui/Primitives.jsx",
    FRONTEND / "src/pages/SlaInboxPage.jsx",
    FRONTEND / "src/pages/SlaCenterPage.jsx",
    FRONTEND / "src/pages/SlaAdvancedPage.jsx",
    FRONTEND / "src/pages/slaInboxFlagshipV1.css",
    FRONTEND / "src/pages/slaInboxFlagshipV1_1DarkContrast.css",
    FRONTEND / "src/pages/slaCenterFlagshipV1.css",
    FRONTEND / "src/pages/slaCenterFlagshipV1_1DarkTableHeader.css",
    FRONTEND / "src/pages/slaAdvancedFlagshipV1.css",
    FRONTEND / "src/pages/slaAdvancedFlagshipV1_1PremiumSelectsDarkContrast.css",
    FRONTEND / "src/pages/slaAdvancedFlagshipV1_2DropdownOverflowLayerFix.css",
    FRONTEND / "src/components/RamzyAssistant.jsx",
    FRONTEND / "src/components/TcsFloatingLauncher.jsx",
    FRONTEND / "src/components/TcsDesktopWindow.jsx",
]

print("RUNNING=TOS_UXUI_SYSTEM_TWS_DASHBOARD_FLAGSHIP_V2_2_REFERENCE_LUXURY_MATCH")

page_before = None
v22_created = False
live_backup = None
live_failed = None


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_count(root: Path, needle: bytes) -> int:
    if not root.exists():
        return 0
    total = 0
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            total += path.read_bytes().count(needle)
        except OSError:
            pass
    return total


def rollback_source():
    global page_before, v22_created
    try:
        if page_before is not None:
            PAGE.write_bytes(page_before)
    except Exception:
        pass
    try:
        if v22_created and V22_STYLE.exists():
            V22_STYLE.unlink()
    except Exception:
        pass


def rollback_live():
    global live_backup, live_failed
    try:
        if live_backup is None or not live_backup.exists():
            return
        if LIVE.exists():
            if live_failed is not None and not live_failed.exists():
                LIVE.rename(live_failed)
            else:
                shutil.rmtree(LIVE)
        live_backup.rename(LIVE)
    except Exception:
        pass


def fail(message: str, build_result="FAIL_OR_SKIPPED", rollback_deploy=False):
    if rollback_deploy:
        rollback_live()
    rollback_source()
    print("PASS/FAIL=FAIL")
    print("ERROR=" + str(message))
    print("BUILD_RESULT=" + build_result)
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("TWS_DASHBOARD_FLAGSHIP_V2_2_RUNTIME=NO")
    sys.exit(1)


if ROOT.resolve() == Path("/"):
    fail("unsafe ROOT")

for path in (FRONTEND, PAGE, V1_STYLE, V11_STYLE, V2_STYLE, V21_STYLE, LIVE_PARENT, *PRESERVE_FILES):
    if not path.exists():
        fail(f"required path missing: {path}")

if sha256(V1_STYLE) != EXPECTED_V1_STYLE_SHA256:
    fail(f"V1 stylesheet baseline mismatch: {sha256(V1_STYLE)}")
if sha256(V11_STYLE) != EXPECTED_V11_STYLE_SHA256:
    fail(f"V1.1 stylesheet baseline mismatch: {sha256(V11_STYLE)}")
if sha256(V2_STYLE) != EXPECTED_V2_STYLE_SHA256:
    fail(f"V2 stylesheet baseline mismatch: {sha256(V2_STYLE)}")
if V22_STYLE.exists():
    fail(f"unexpected state: V2.2 stylesheet already exists: {V22_STYLE}")

page_text = PAGE.read_text(encoding="utf-8")
for imp in (IMPORT_V1, IMPORT_V11, IMPORT_V2, IMPORT_V21):
    if page_text.count(imp) != 1:
        fail(f"required import count mismatch for {imp}: {page_text.count(imp)}")
if IMPORT_V22 in page_text:
    fail("unexpected state: V2.2 import already exists")

v21_text = V21_STYLE.read_text(encoding="utf-8")
for marker in (
    '--tos-tws-dashboard-flagship-v2-1-buttons-luxury-runtime: 1;',
    '.tos-tws-filter-row > .tos-premium-button',
    '.tos-tws-document-card .tos-premium-button',
    '.dark .tos-tws-flagship-v1',
):
    if marker not in v21_text:
        fail(f"required V2.1 baseline marker missing: {marker}")

required_page_markers = (
    'const TWS_RESULT_PAGE_SIZE = 12;',
    'function TwsPremiumSelect',
    '<SystemPageHeader',
    'className="tos-tws-hero-card overflow-hidden p-0"',
    'className="tos-tws-control-card mt-4"',
    '<RefreshCw size={16} className={loading ? "animate-spin" : ""} />',
    'tos-tws-document-card group relative flex flex-col gap-3 p-4',
    'data-tws-results-pagination="v1"',
    'api.tws.list(filters)',
    'api.tws.duplicate(doc.id)',
    'api.tws.archive(doc.id)',
    'api.tws.restore(doc.id)',
    'api.tws.trash(doc.id)',
    'limit: 60',
)
for marker in required_page_markers:
    if marker not in page_text:
        fail(f"required TWS V2.1 source marker missing: {marker}")

page_before = PAGE.read_bytes()
v1_before = sha256(V1_STYLE)
v11_before = sha256(V11_STYLE)
v2_before = sha256(V2_STYLE)
v21_before = sha256(V21_STYLE)
preserve_before = {str(path): sha256(path) for path in PRESERVE_FILES}

# Scope the markup-only transformations to DocumentCard. No handlers, props, API calls or behavior are altered.
doc_start = page_text.find("function DocumentCard(")
doc_end = page_text.find("\nfunction LoadingGrid", doc_start)
if doc_start < 0 or doc_end < 0:
    fail("DocumentCard function boundaries not found")

doc_segment = page_text[doc_start:doc_end]

old_card = '<Card hover className={cn("tos-tws-document-card group relative flex flex-col gap-3 p-4", selected && "ring-2 ring-amber-400")}>'
new_card = '<Card hover className={cn("tos-tws-document-card group relative flex flex-col gap-3 p-4", `tos-tws-document-${String(doc.type || "TDOC").toLowerCase()}`, selected && "ring-2 ring-amber-400")}>'
old_icon = '<div className="grid h-11 w-11 shrink-0 place-items-center rounded-2xl bg-zinc-950 text-white shadow-sm dark:bg-white dark:text-zinc-950">'
new_icon = '<div className="tos-tws-file-icon grid h-11 w-11 shrink-0 place-items-center rounded-2xl bg-zinc-950 text-white shadow-sm dark:bg-white dark:text-zinc-950">'
old_meta = '<div className="grid gap-1.5 rounded-2xl bg-zinc-50 p-3 text-[11px] font-bold text-zinc-500 dark:bg-white/[0.04] dark:text-zinc-400">'
new_meta = '<div className="tos-tws-card-meta grid gap-1.5 rounded-2xl bg-zinc-50 p-3 text-[11px] font-bold text-zinc-500 dark:bg-white/[0.04] dark:text-zinc-400">'
old_actions = '<div className="flex flex-wrap items-center gap-2">'
new_actions = '<div className="tos-tws-card-actions flex flex-wrap items-center gap-2">'

for old, label in ((old_card, "document card type class"), (old_icon, "file icon class"), (old_meta, "metadata class")):
    if doc_segment.count(old) != 1:
        fail(f"{label} baseline count mismatch inside DocumentCard: {doc_segment.count(old)}")
if doc_segment.count(old_actions) != 1:
    fail(f"card actions baseline count mismatch inside DocumentCard: {doc_segment.count(old_actions)}")

doc_new = doc_segment.replace(old_card, new_card, 1)
doc_new = doc_new.replace(old_icon, new_icon, 1)
doc_new = doc_new.replace(old_meta, new_meta, 1)
doc_new = doc_new.replace(old_actions, new_actions, 1)

new_page_text = page_text[:doc_start] + doc_new + page_text[doc_end:]
new_page_text = new_page_text.replace(IMPORT_V21, IMPORT_V21 + "\n" + IMPORT_V22, 1)

for marker in (
    IMPORT_V22,
    'tos-tws-document-${String(doc.type || "TDOC").toLowerCase()}',
    'tos-tws-file-icon grid h-11 w-11',
    'tos-tws-card-meta grid gap-1.5',
    'tos-tws-card-actions flex flex-wrap',
):
    if new_page_text.count(marker) != 1:
        fail(f"V2.2 page transform marker count mismatch: {marker} -> {new_page_text.count(marker)}")

css_text = CSS
for marker in (
    '--tos-tws-dashboard-flagship-v2-2-reference-luxury-runtime: 1;',
    '.tos-tws-document-tdoc .tos-tws-file-icon',
    '.tos-tws-document-tsheet .tos-tws-file-icon',
    '.tos-tws-document-tslide .tos-tws-file-icon',
    '.tos-tws-card-meta',
    '.tos-tws-card-actions',
    '.tos-tws-filter-row > .tos-premium-button',
    '.dark .tos-tws-flagship-v1',
):
    if marker not in css_text:
        fail(f"V2.2 CSS marker missing before write: {marker}")

try:
    PAGE.write_text(new_page_text, encoding="utf-8")
    V22_STYLE.write_text(css_text, encoding="utf-8")
    v22_created = True
except Exception as exc:
    if V22_STYLE.exists():
        v22_created = True
    fail(f"source write failed: {exc}")

if PAGE.read_text(encoding="utf-8").count(IMPORT_V22) != 1:
    fail("V2.2 import missing after write")
for path, expected in ((V1_STYLE, v1_before), (V11_STYLE, v11_before), (V2_STYLE, v2_before), (V21_STYLE, v21_before)):
    if sha256(path) != expected:
        fail(f"prior flagship stylesheet changed unexpectedly: {path}")
for path in PRESERVE_FILES:
    if sha256(path) != preserve_before[str(path)]:
        fail(f"out-of-scope source changed before build: {path}")

build = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, text=True, capture_output=True)
if build.returncode != 0:
    print(build.stdout[-12000:])
    print(build.stderr[-12000:])
    fail("frontend build failed", build_result="FAIL")

if not DIST.exists() or not (DIST / "index.html").exists():
    fail("dist/index.html missing after build", build_result="FAIL")

built_markers = (
    b'--tos-tws-dashboard-flagship-v1-runtime',
    b'--tos-tws-dashboard-flagship-v1-1-dark-fidelity-runtime',
    b'--tos-tws-dashboard-flagship-v2-luxury-runtime',
    b'--tos-tws-dashboard-flagship-v2-1-buttons-luxury-runtime',
    b'--tos-tws-dashboard-flagship-v2-2-reference-luxury-runtime',
    b'tos-tws-file-icon',
    b'tos-tws-card-meta',
    b'tos-tws-card-actions',
    b'data-tws-results-pagination',
)
for marker in built_markers:
    if tree_count(DIST, marker) < 1:
        fail(f"built output missing marker: {marker.decode(errors='ignore')}", build_result="FAIL")

if PAGE.read_text(encoding="utf-8").count(IMPORT_V22) != 1:
    fail("V2.2 import changed during build", build_result="FAIL")
for path, expected in ((V1_STYLE, v1_before), (V11_STYLE, v11_before), (V2_STYLE, v2_before), (V21_STYLE, v21_before)):
    if sha256(path) != expected:
        fail(f"prior stylesheet changed during build: {path}", build_result="FAIL")
for path in PRESERVE_FILES:
    if sha256(path) != preserve_before[str(path)]:
        fail(f"out-of-scope source changed during build: {path}", build_result="FAIL")

ts = int(time.time())
candidate = LIVE_PARENT / f"build.tws-dashboard-v2-2-reference-luxury-candidate-{ts}"
live_backup = LIVE_PARENT / f"build.tws-dashboard-v2-2-reference-luxury-backup-{ts}"
live_failed = LIVE_PARENT / f"build.tws-dashboard-v2-2-reference-luxury-failed-{ts}"

try:
    for path in (candidate, live_backup, live_failed):
        if path.exists():
            raise RuntimeError(f"timestamped deployment path already exists: {path}")
    shutil.copytree(DIST, candidate)
    if LIVE.exists():
        LIVE.rename(live_backup)
    candidate.rename(LIVE)
except Exception as exc:
    rollback_live()
    fail(f"atomic live deploy failed: {exc}", build_result="PASS")

try:
    if not (LIVE / "index.html").exists():
        raise RuntimeError("live index.html missing")
    for marker in built_markers:
        if tree_count(LIVE, marker) < 1:
            raise RuntimeError(f"live output missing marker: {marker.decode(errors='ignore')}")
except Exception as exc:
    fail(f"live runtime verification failed: {exc}", build_result="PASS", rollback_deploy=True)

if PAGE.read_text(encoding="utf-8").count(IMPORT_V22) != 1:
    fail("V2.2 import changed after deploy", build_result="PASS", rollback_deploy=True)
for path, expected in ((V1_STYLE, v1_before), (V11_STYLE, v11_before), (V2_STYLE, v2_before), (V21_STYLE, v21_before)):
    if sha256(path) != expected:
        fail(f"prior stylesheet changed after deploy: {path}", build_result="PASS", rollback_deploy=True)
for path in PRESERVE_FILES:
    if sha256(path) != preserve_before[str(path)]:
        fail(f"out-of-scope source changed after deploy: {path}", build_result="PASS", rollback_deploy=True)

print("PASS/FAIL=PASS")
print("BUILD_RESULT=PASS")
print("LIVE_DEPLOY=PASS")
print("TWS_DASHBOARD_FLAGSHIP_V2_2_RUNTIME=YES")
print("TWS_V2_2_SCOPE=REFERENCE_LUXURY_VISUAL_ONLY")
print("TWS_REFERENCE_DIRECTION=PEARL_IVORY_CHAMPAGNE")
print("TWS_HERO=PEARL_SILK_REFERENCE_MATCH")
print("TWS_HEADER_ACTIONS=CHAMPAGNE_METALLIC")
print("TWS_REFRESH_BUTTON=COMPACT_CHAMPAGNE_COMMAND")
print("TWS_FILTER_TABS=REFERENCE_LUXURY_PILLS")
print("TWS_PROJECT_FILTER=PREMIUM_CUSTOM_PRESERVED")
print("TWS_GRID_LIST_TOGGLE=REFERENCE_LUXURY")
print("TWS_DOCUMENT_CARDS=REFERENCE_PRODUCT_CARDS")
print("TWS_FILE_ICONS=JEWEL_TYPE_COLORED")
print("TWS_TDOC_ICON=ROYAL_BLUE")
print("TWS_TSHEET_ICON=EMERALD")
print("TWS_TSLIDE_ICON=AMBER_ORANGE")
print("TWS_CARD_METADATA=PEARL_INSET")
print("TWS_CARD_ACTIONS=CHAMPAGNE_CAPSULES")
print("TWS_DELETE_ACTION=SOFT_PREMIUM_DESTRUCTIVE")
print("TWS_LIGHT_MODE=PEARL_IVORY_CHAMPAGNE_REFERENCE")
print("TWS_DARK_MODE=OBSIDIAN_CHAMPAGNE_REFERENCE")
print("TWS_RESULTS_PAGINATION=PRESERVED")
print("TWS_RESULTS_PAGE_SIZE=12")
print("TWS_LIST_API_CHANGED=NO")
print("TWS_CREATE_CHANGED=NO")
print("TWS_CONTENT_UPDATE_CHANGED=NO")
print("TWS_DUPLICATE_CHANGED=NO")
print("TWS_ARCHIVE_CHANGED=NO")
print("TWS_RESTORE_CHANGED=NO")
print("TWS_TRASH_CHANGED=NO")
print("TWS_FAVORITES_CHANGED=NO")
print("SLA_INBOX_CHANGED=NO")
print("SLA_CENTER_CHANGED=NO")
print("ADVANCED_SLA_CHANGED=NO")
print("RAMZY_CHANGED=NO")
print("TCS_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print(f"TWS_DASHBOARD_PAGE_SHA256={sha256(PAGE)}")
print(f"TWS_DASHBOARD_V22_STYLE_SHA256={sha256(V22_STYLE)}")
print(f"LIVE_BACKUP={live_backup if live_backup.exists() else 'NONE'}")
print("STATUS=READY")
