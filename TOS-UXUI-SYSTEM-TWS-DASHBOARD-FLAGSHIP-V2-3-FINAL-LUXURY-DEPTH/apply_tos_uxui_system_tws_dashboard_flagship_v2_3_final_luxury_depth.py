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
V23_STYLE = FRONTEND / "src/pages/tws/twsDashboardFlagshipV2_3FinalLuxuryDepth.css"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_V1_STYLE_SHA256 = "6691401c241187e5ffd6611ba1d02510f37b954f975ec40021e5cee9072be49a"
EXPECTED_V11_STYLE_SHA256 = "b0a53b84f4cc74eed2f83c5b38d3fd72661bb81d4a7c54507766b8ad36998849"
EXPECTED_V2_STYLE_SHA256 = "e5b14bee3119d2de6e0b6450e555f358c5671ba47dcaaf12813e6ad4e218e4cc"

IMPORT_V22 = 'import "./twsDashboardFlagshipV2_2ReferenceLuxuryMatch.css";'
IMPORT_V23 = 'import "./twsDashboardFlagshipV2_3FinalLuxuryDepth.css";'

CSS = r''':root {
  --tos-tws-dashboard-flagship-v2-3-final-luxury-depth-runtime: 1;
}

/* TWS V2.3 — final luxury depth, closely matched to the approved reference direction. */
.tos-tws-flagship-v1 {
  --v23-gold-a: #f9e7aa;
  --v23-gold-b: #e6bd51;
  --v23-gold-c: #c98f18;
  --v23-antique: #8e5a08;
  --v23-pearl: #fffdf8;
  --v23-ivory: #fbf5e9;
  --v23-ink: #18120b;
  --v23-obsidian: #0b0d0e;
  --v23-titanium: #15191c;
  --v23-gold-line: rgba(205,151,41,.26);
}

/* ===== Light: luxury hardware ===== */
.tos-tws-flagship-v1 > .tos-premium-system-header .tos-premium-button,
.tos-tws-flagship-v1 .tos-tws-quick-create button,
.tos-tws-flagship-v1 .tos-tws-tab,
.tos-tws-flagship-v1 .tos-tws-view-toggle button,
.tos-tws-flagship-v1 .tos-tws-card-actions .tos-premium-button,
.tos-tws-flagship-v1 .tos-tws-pagination button {
  position: relative;
  overflow: hidden;
  isolation: isolate;
}

.tos-tws-flagship-v1 > .tos-premium-system-header .tos-premium-button::after,
.tos-tws-flagship-v1 .tos-tws-quick-create button::after,
.tos-tws-flagship-v1 .tos-tws-card-actions .tos-premium-button::after {
  content: "";
  position: absolute;
  z-index: -1;
  inset: 1px;
  border-radius: inherit;
  pointer-events: none;
  background: linear-gradient(115deg, transparent 14%, rgba(255,255,255,.42) 34%, transparent 56%);
  opacity: .42;
}

.tos-tws-flagship-v1 > .tos-premium-system-header .tos-premium-button:first-of-type,
.tos-tws-flagship-v1 .tos-tws-quick-create button:first-of-type,
.tos-tws-flagship-v1 .tos-tws-tabs .tos-tws-tab[class*="bg-zinc-950"],
.tos-tws-flagship-v1 .tos-tws-view-toggle button[class*="bg-white"] {
  color: #211500 !important;
  border-color: rgba(139,84,0,.38) !important;
  background: linear-gradient(180deg,#fff1b9 0%,#f3d374 20%,#ddb03e 58%,#c88d16 100%) !important;
  box-shadow:
    0 10px 24px rgba(129,78,2,.18),
    0 2px 4px rgba(103,61,0,.13),
    inset 0 1px rgba(255,255,255,.82),
    inset 0 -2px rgba(100,58,0,.16) !important;
}

.tos-tws-flagship-v1 > .tos-premium-system-header .tos-premium-button:not(:first-of-type),
.tos-tws-flagship-v1 .tos-tws-quick-create button:not(:first-of-type) {
  color: #3b2a13 !important;
  border-color: rgba(173,115,16,.21) !important;
  background: linear-gradient(180deg,#fffefa,#fbf4e5 58%,#f1e2bd) !important;
  box-shadow:
    0 8px 19px rgba(74,45,2,.07),
    inset 0 1px rgba(255,255,255,.96),
    inset 0 -1px rgba(139,87,5,.07) !important;
}

.tos-tws-flagship-v1 > .tos-premium-system-header .tos-premium-button:hover:not(:disabled),
.tos-tws-flagship-v1 .tos-tws-quick-create button:hover:not(:disabled),
.tos-tws-flagship-v1 .tos-tws-card-actions .tos-premium-button:hover:not(:disabled) {
  transform: translateY(-2px) !important;
  filter: saturate(1.05);
}

/* Compact premium refresh exactly like the reference. */
.tos-tws-flagship-v1 .tos-tws-filter-row > .tos-premium-button {
  width: 118px !important;
  min-width: 118px !important;
  justify-content: center !important;
  min-height: 40px !important;
  padding-inline: 18px !important;
  color: #281a02 !important;
  border: 1px solid rgba(138,84,0,.36) !important;
  border-radius: 12px !important;
  background: linear-gradient(180deg,#fff1b9 0%,#f0ca63 35%,#d9a632 70%,#c48713 100%) !important;
  box-shadow:
    0 10px 22px rgba(129,78,2,.17),
    inset 0 1px rgba(255,255,255,.85),
    inset 0 -2px rgba(95,55,0,.13) !important;
}
.tos-tws-flagship-v1 .tos-tws-filter-row > .tos-premium-button svg {
  color: #744905 !important;
}

/* Control rail closer to the reference frame. */
.tos-tws-flagship-v1 .tos-tws-control-card {
  border-color: rgba(176,117,17,.16) !important;
  border-radius: 21px !important;
  background:
    radial-gradient(ellipse at 84% 120%, rgba(231,203,141,.12), transparent 36%),
    linear-gradient(180deg,#fffefa,#fbf6ec) !important;
  box-shadow: 0 15px 36px rgba(71,43,2,.065), inset 0 1px rgba(255,255,255,.96) !important;
}
.tos-tws-flagship-v1 .tos-tws-tab {
  min-height: 36px !important;
  border-radius: 11px !important;
  border-color: rgba(169,109,12,.13) !important;
  background: linear-gradient(180deg,#fffefb,#f6ead0) !important;
}
.tos-tws-flagship-v1 .tos-tws-tabs .tos-tws-tab[class*="bg-zinc-950"] {
  min-width: 68px;
}
.tos-tws-flagship-v1 .tos-tws-premium-trigger,
.tos-tws-flagship-v1 .tos-tws-filter-row input {
  min-height: 41px !important;
  border-radius: 11px !important;
  border-color: rgba(162,104,10,.14) !important;
  background: linear-gradient(180deg,#fffefa,#fbf7ee) !important;
  box-shadow: inset 0 1px rgba(255,255,255,.95), 0 5px 12px rgba(62,37,2,.025) !important;
}

/* ===== File cards: luxury product-card treatment ===== */
.tos-tws-flagship-v1 .tos-tws-document-card {
  position: relative;
  overflow: hidden !important;
  min-height: 246px !important;
  padding: 16px !important;
  gap: 12px !important;
  border-radius: 18px !important;
  border: 1px solid rgba(188,126,18,.22) !important;
  background:
    radial-gradient(circle at 100% 0%, rgba(244,218,157,.22), transparent 31%),
    linear-gradient(154deg,#fffefb 0%,#fffaf1 54%,#f8eed9 100%) !important;
  box-shadow:
    0 15px 34px rgba(70,42,2,.075),
    0 2px 6px rgba(75,45,2,.035),
    inset 0 1px rgba(255,255,255,.98) !important;
  transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease !important;
}
.tos-tws-flagship-v1 .tos-tws-document-card::before {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(120deg, transparent 0 28%, rgba(255,255,255,.52) 38%, transparent 49%),
    radial-gradient(circle at 7% 7%, rgba(225,181,74,.11), transparent 21%);
  opacity: .72;
}
.tos-tws-flagship-v1 .tos-tws-document-card::after {
  content: "";
  position: absolute;
  inset-inline: 16px;
  top: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(226,174,55,.78), transparent);
  opacity: .85;
}
.tos-tws-flagship-v1 .tos-tws-document-card:hover {
  transform: translateY(-3px) !important;
  border-color: rgba(189,124,13,.34) !important;
  box-shadow:
    0 22px 45px rgba(74,44,1,.11),
    0 4px 9px rgba(73,43,1,.045),
    inset 0 1px rgba(255,255,255,1) !important;
}
.tos-tws-flagship-v1 .tos-tws-document-card > * {
  position: relative;
  z-index: 1;
}

/* Jewel file icons closer to the reference. */
.tos-tws-flagship-v1 .tos-tws-file-icon {
  width: 47px !important;
  height: 47px !important;
  border-radius: 13px !important;
  border: 1px solid rgba(255,255,255,.42) !important;
  box-shadow: 0 10px 23px rgba(0,0,0,.17), inset 0 1px rgba(255,255,255,.34) !important;
}
.tos-tws-flagship-v1 .tos-tws-document-tdoc .tos-tws-file-icon {
  background: linear-gradient(145deg,#5a91ff,#2f6ae8 56%,#1848c5) !important;
  box-shadow: 0 10px 24px rgba(45,104,225,.28), inset 0 1px rgba(255,255,255,.34) !important;
}
.tos-tws-flagship-v1 .tos-tws-document-tsheet .tos-tws-file-icon {
  background: linear-gradient(145deg,#20c889,#07965e 58%,#047044) !important;
  box-shadow: 0 10px 24px rgba(5,146,89,.25), inset 0 1px rgba(255,255,255,.34) !important;
}
.tos-tws-flagship-v1 .tos-tws-document-tslide .tos-tws-file-icon {
  background: linear-gradient(145deg,#ffad45,#f57c0d 58%,#cb5200) !important;
  box-shadow: 0 10px 24px rgba(236,112,8,.25), inset 0 1px rgba(255,255,255,.34) !important;
}

/* Rich inset metadata panel. */
.tos-tws-flagship-v1 .tos-tws-card-meta {
  padding: 12px 13px !important;
  border: 1px solid rgba(179,118,17,.12) !important;
  border-radius: 13px !important;
  background:
    radial-gradient(circle at 100% 0%, rgba(236,202,128,.12), transparent 33%),
    linear-gradient(180deg,#fbf7ef,#f6eedf) !important;
  box-shadow: inset 0 1px rgba(255,255,255,.92), inset 0 -1px rgba(137,86,4,.035) !important;
}
.tos-tws-flagship-v1 .tos-tws-card-meta > div + div {
  border-top: 1px solid rgba(154,100,12,.055);
  padding-top: 5px;
}

/* Action capsules: larger, centered, metallic. */
.tos-tws-flagship-v1 .tos-tws-card-actions {
  margin-top: auto !important;
  padding-top: 2px;
  gap: 8px !important;
  flex-wrap: nowrap !important;
}
.tos-tws-flagship-v1 .tos-tws-card-actions .tos-premium-button {
  flex: 1 1 0 !important;
  justify-content: center !important;
  min-width: 0 !important;
  min-height: 38px !important;
  padding-inline: 10px !important;
  border-radius: 10px !important;
  color: #3d2b10 !important;
  border: 1px solid rgba(173,112,13,.22) !important;
  background: linear-gradient(180deg,#fffdf7,#f7e9c9 65%,#efdbaa) !important;
  box-shadow: 0 7px 16px rgba(65,39,2,.055), inset 0 1px rgba(255,255,255,.94) !important;
}
.tos-tws-flagship-v1 .tos-tws-card-actions .tos-premium-button[class*="bg-red-50"] {
  color: #b12424 !important;
  border-color: rgba(196,54,54,.20) !important;
  background: linear-gradient(180deg,#fffafa,#feeceb 70%,#f8dad7) !important;
  box-shadow: 0 7px 16px rgba(150,32,32,.045), inset 0 1px rgba(255,255,255,.96) !important;
}

/* Buckets get subtle reference depth. */
.tos-tws-flagship-v1 .tos-tws-bucket {
  border-radius: 18px !important;
  border-color: rgba(177,117,16,.17) !important;
  background: linear-gradient(155deg,#fffefa,#fbf5e9) !important;
  box-shadow: 0 13px 30px rgba(68,40,2,.055), inset 0 1px rgba(255,255,255,.95) !important;
}
.tos-tws-flagship-v1 .tos-tws-bucket .space-y-2 > button {
  min-height: 41px !important;
  border-radius: 11px !important;
  border-color: rgba(172,112,15,.13) !important;
  background: linear-gradient(180deg,#fffefb,#faf4e9) !important;
}

/* Pagination reference finish. */
.tos-tws-flagship-v1 .tos-tws-pagination {
  border: 1px solid rgba(180,119,16,.16) !important;
  border-radius: 18px !important;
  background:
    radial-gradient(ellipse at 86% 100%, rgba(231,203,141,.16), transparent 34%),
    linear-gradient(180deg,#fffefa,#fbf6ec) !important;
  box-shadow: 0 12px 28px rgba(68,41,2,.05), inset 0 1px rgba(255,255,255,.95) !important;
}
.tos-tws-flagship-v1 .tos-tws-pagination button:not(:disabled):last-child {
  color: #251700 !important;
  border-color: rgba(138,84,0,.36) !important;
  background: linear-gradient(180deg,#fff0b5,#efca62 46%,#d59d27) !important;
  box-shadow: 0 8px 18px rgba(128,76,0,.16), inset 0 1px rgba(255,255,255,.78) !important;
}

/* ===== Dark: obsidian / titanium / gold-edge reference ===== */
.dark .tos-tws-flagship-v1 > .tos-premium-system-header {
  border-color: rgba(219,167,61,.28) !important;
  background:
    radial-gradient(ellipse at 92% -10%, rgba(213,154,35,.12), transparent 36%),
    linear-gradient(132deg,#101315,#0a0c0d 65%,#13120d) !important;
  box-shadow: 0 20px 48px rgba(0,0,0,.30), inset 0 1px rgba(255,255,255,.03), inset 0 -1px rgba(218,163,48,.05) !important;
}
.dark .tos-tws-flagship-v1 > .tos-premium-system-header h1 {
  color: #f7f0e6 !important;
}
.dark .tos-tws-flagship-v1 > .tos-premium-system-header .tos-premium-button:first-of-type {
  color: #241600 !important;
  background: linear-gradient(180deg,#f7db80,#e5b63d 55%,#bd7e10) !important;
  border-color: rgba(235,190,87,.46) !important;
  box-shadow: 0 0 0 1px rgba(126,78,4,.22), 0 11px 27px rgba(197,133,19,.22), inset 0 1px rgba(255,255,255,.46) !important;
}
.dark .tos-tws-flagship-v1 > .tos-premium-system-header .tos-premium-button:not(:first-of-type) {
  color: #f0e7d8 !important;
  border-color: rgba(223,170,61,.24) !important;
  background: linear-gradient(180deg,#181c1e,#101315) !important;
  box-shadow: inset 0 1px rgba(255,255,255,.035), 0 8px 18px rgba(0,0,0,.22) !important;
}

/* Dark hero: cosmic obsidian with restrained gold planetary arcs. */
.dark .tos-tws-flagship-v1 .tos-tws-hero-card {
  border-color: rgba(218,166,54,.32) !important;
  background: #0a0c0d !important;
  box-shadow: 0 22px 54px rgba(0,0,0,.34), 0 0 0 1px rgba(74,47,5,.18) inset !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-hero {
  background:
    radial-gradient(circle at 76% 34%, rgba(228,171,51,.18) 0 2%, rgba(41,31,16,.88) 18%, rgba(7,9,10,.98) 34%, transparent 35%),
    radial-gradient(circle at 4% 106%, rgba(211,151,30,.16) 0 1%, rgba(36,27,14,.82) 19%, rgba(7,9,10,.98) 35%, transparent 36%),
    radial-gradient(ellipse at 48% 52%, rgba(194,133,26,.08), transparent 30%),
    linear-gradient(128deg,#111517,#090b0c 58%,#11110e) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-hero::before {
  opacity: .8 !important;
  background:
    repeating-radial-gradient(circle at 76% 34%, transparent 0 56px, rgba(224,165,47,.14) 57px 58px, transparent 59px 84px),
    repeating-radial-gradient(circle at 4% 106%, transparent 0 68px, rgba(224,165,47,.11) 69px 70px, transparent 71px 101px) !important;
  transform: none !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-hero::after {
  background:
    linear-gradient(128deg,transparent 5%,rgba(222,166,48,.08) 28%,transparent 45%),
    radial-gradient(circle at 64% 52%, rgba(255,206,101,.11), transparent 15%) !important;
  mix-blend-mode: screen !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-hero h2 {
  color: #f9f3e9 !important;
  text-shadow: 0 2px 16px rgba(0,0,0,.45) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-hero p {
  color: #c7beb1 !important;
}

/* Dark Quick Create: smoked titanium, never white. */
.dark .tos-tws-flagship-v1 .tos-tws-quick-create {
  border-color: rgba(221,169,58,.28) !important;
  background: linear-gradient(155deg,rgba(28,32,34,.96),rgba(13,15,16,.96)) !important;
  box-shadow: 0 20px 42px rgba(0,0,0,.40), inset 0 1px rgba(255,255,255,.035) !important;
  backdrop-filter: blur(22px);
}
.dark .tos-tws-flagship-v1 .tos-tws-quick-create button:first-of-type {
  color: #241600 !important;
  background: linear-gradient(180deg,#f7db80,#e2b139 58%,#bd7d0f) !important;
  border-color: rgba(231,181,76,.42) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-quick-create button:not(:first-of-type) {
  color: #f2eadf !important;
  background: linear-gradient(180deg,#202427,#15181a) !important;
  border-color: rgba(218,164,55,.20) !important;
}

.dark .tos-tws-flagship-v1 .tos-tws-control-card,
.dark .tos-tws-flagship-v1 .tos-tws-pagination {
  border-color: rgba(213,160,50,.22) !important;
  background:
    radial-gradient(ellipse at 90% 120%, rgba(194,130,23,.08), transparent 34%),
    linear-gradient(180deg,#121619,#0c0f11) !important;
  box-shadow: 0 18px 42px rgba(0,0,0,.26), inset 0 1px rgba(255,255,255,.025) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-tab {
  color: #cfc7bc !important;
  border-color: rgba(218,165,55,.14) !important;
  background: linear-gradient(180deg,#1a1e20,#121517) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-tabs .tos-tws-tab[class~="dark:bg-white"] {
  color: #221500 !important;
  border-color: rgba(238,193,91,.42) !important;
  background: linear-gradient(180deg,#f6d779,#e2ad32 58%,#b9750b) !important;
  box-shadow: 0 9px 21px rgba(196,128,14,.18), inset 0 1px rgba(255,255,255,.44) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-filter-row > .tos-premium-button {
  color: #241600 !important;
  border-color: rgba(230,181,77,.40) !important;
  background: linear-gradient(180deg,#f5d67a,#dfaa31 58%,#b8730a) !important;
  box-shadow: 0 9px 22px rgba(190,123,14,.19), inset 0 1px rgba(255,255,255,.46) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-premium-trigger,
.dark .tos-tws-flagship-v1 .tos-tws-filter-row input,
.dark .tos-tws-flagship-v1 .tos-tws-view-toggle {
  color: #ece5dc !important;
  border-color: rgba(216,163,54,.16) !important;
  background: linear-gradient(180deg,#171b1d,#101315) !important;
  box-shadow: inset 0 1px rgba(255,255,255,.025) !important;
}

/* Dark cards: titanium layering + gold edge light. */
.dark .tos-tws-flagship-v1 .tos-tws-document-card {
  border-color: rgba(218,166,55,.30) !important;
  background:
    radial-gradient(circle at 100% 0%, rgba(205,145,32,.08), transparent 31%),
    linear-gradient(155deg,#171b1e 0%,#101416 58%,#0d1012 100%) !important;
  box-shadow:
    0 18px 42px rgba(0,0,0,.27),
    0 0 0 1px rgba(84,55,7,.16) inset,
    inset 0 1px rgba(255,255,255,.025) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-document-card::before {
  background:
    linear-gradient(125deg, transparent 0 28%, rgba(235,185,75,.045) 40%, transparent 52%),
    radial-gradient(circle at 8% 8%, rgba(222,165,50,.05), transparent 20%) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-document-card::after {
  background: linear-gradient(90deg,transparent,rgba(235,184,71,.76),transparent) !important;
  opacity: .66;
}
.dark .tos-tws-flagship-v1 .tos-tws-document-card:hover {
  border-color: rgba(235,184,74,.46) !important;
  box-shadow:
    0 23px 50px rgba(0,0,0,.34),
    0 0 20px rgba(194,128,18,.08),
    0 0 0 1px rgba(113,74,8,.20) inset !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-card-meta {
  color: #a9a39b !important;
  border-color: rgba(221,167,56,.13) !important;
  background: linear-gradient(180deg,#14181a,#0f1214) !important;
  box-shadow: inset 0 1px rgba(255,255,255,.022), inset 0 -1px rgba(0,0,0,.20) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-card-meta span.text-zinc-800,
.dark .tos-tws-flagship-v1 .tos-tws-card-meta span.dark\\:text-zinc-100 {
  color: #f2ede6 !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-card-actions .tos-premium-button {
  color: #e9dfcf !important;
  border-color: rgba(220,167,57,.26) !important;
  background: linear-gradient(180deg,#1b1f21,#121517) !important;
  box-shadow: inset 0 1px rgba(255,255,255,.025), 0 7px 16px rgba(0,0,0,.18) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-card-actions .tos-premium-button:hover:not(:disabled) {
  color: #ffe6a2 !important;
  border-color: rgba(236,188,81,.42) !important;
  background: linear-gradient(180deg,#23282a,#171b1d) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-card-actions .tos-premium-button[class*="bg-red"] {
  color: #ff8d8d !important;
  border-color: rgba(223,77,77,.30) !important;
  background: linear-gradient(180deg,#281819,#1b1213) !important;
}

.dark .tos-tws-flagship-v1 .tos-tws-bucket {
  border-color: rgba(212,159,49,.22) !important;
  background: linear-gradient(155deg,#15191b,#0f1214) !important;
  box-shadow: 0 16px 36px rgba(0,0,0,.24), inset 0 1px rgba(255,255,255,.02) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-bucket .space-y-2 > button {
  color: #ebe4da !important;
  border-color: rgba(215,162,51,.16) !important;
  background: linear-gradient(180deg,#191d1f,#121517) !important;
}

.dark .tos-tws-flagship-v1 .tos-tws-pagination button:not(:disabled):last-child {
  color: #241600 !important;
  border-color: rgba(232,183,80,.42) !important;
  background: linear-gradient(180deg,#f6d97e,#e0aa31 58%,#b8730b) !important;
  box-shadow: 0 9px 22px rgba(190,123,14,.18), inset 0 1px rgba(255,255,255,.45) !important;
}

/* Consistent focus ring for luxury controls. */
.tos-tws-flagship-v1 button:focus-visible,
.tos-tws-flagship-v1 input:focus-visible {
  outline: none !important;
  box-shadow: 0 0 0 3px rgba(224,173,62,.20), 0 0 0 1px rgba(178,117,14,.36) !important;
}

@media (max-width: 900px) {
  .tos-tws-flagship-v1 .tos-tws-card-actions {
    flex-wrap: wrap !important;
  }
  .tos-tws-flagship-v1 .tos-tws-card-actions .tos-premium-button {
    flex: 1 1 calc(50% - 4px) !important;
  }
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
    FRONTEND / "src/pages/SlaInboxPage.jsx",
    FRONTEND / "src/pages/SlaCenterPage.jsx",
    FRONTEND / "src/pages/SlaAdvancedPage.jsx",
    FRONTEND / "src/components/RamzyAssistant.jsx",
    FRONTEND / "src/components/TcsFloatingLauncher.jsx",
    FRONTEND / "src/components/TcsDesktopWindow.jsx",
]

print("RUNNING=TOS_UXUI_SYSTEM_TWS_DASHBOARD_FLAGSHIP_V2_3_FINAL_LUXURY_DEPTH")

page_before = None
v23_created = False
live_backup = None
live_failed = None


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_count(root: Path, needle: bytes) -> int:
    if not root.exists():
        return 0
    total = 0
    for path in root.rglob("*"):
        if path.is_file():
            try:
                total += path.read_bytes().count(needle)
            except OSError:
                pass
    return total


def rollback_source():
    global page_before, v23_created
    try:
        if page_before is not None:
            PAGE.write_bytes(page_before)
    except Exception:
        pass
    try:
        if v23_created and V23_STYLE.exists():
            V23_STYLE.unlink()
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
    print("TWS_DASHBOARD_FLAGSHIP_V2_3_RUNTIME=NO")
    sys.exit(1)


if ROOT.resolve() == Path("/"):
    fail("unsafe ROOT")

for path in (FRONTEND, PAGE, V1_STYLE, V11_STYLE, V2_STYLE, V21_STYLE, V22_STYLE, LIVE_PARENT, *PRESERVE_FILES):
    if not path.exists():
        fail(f"required path missing: {path}")

if sha256(V1_STYLE) != EXPECTED_V1_STYLE_SHA256:
    fail(f"V1 stylesheet baseline mismatch: {sha256(V1_STYLE)}")
if sha256(V11_STYLE) != EXPECTED_V11_STYLE_SHA256:
    fail(f"V1.1 stylesheet baseline mismatch: {sha256(V11_STYLE)}")
if sha256(V2_STYLE) != EXPECTED_V2_STYLE_SHA256:
    fail(f"V2 stylesheet baseline mismatch: {sha256(V2_STYLE)}")
if V23_STYLE.exists():
    fail(f"unexpected state: V2.3 stylesheet already exists: {V23_STYLE}")

page_text = PAGE.read_text(encoding="utf-8")
if page_text.count(IMPORT_V22) != 1:
    fail(f"V2.2 import count mismatch: {page_text.count(IMPORT_V22)}")
if IMPORT_V23 in page_text:
    fail("unexpected state: V2.3 import already exists")

for marker in (
    '--tos-tws-dashboard-flagship-v2-2-reference-luxury-runtime: 1;',
    '.tos-tws-document-tdoc .tos-tws-file-icon',
    '.tos-tws-document-tsheet .tos-tws-file-icon',
    '.tos-tws-document-tslide .tos-tws-file-icon',
    '.tos-tws-card-meta',
    '.tos-tws-card-actions',
    '.dark .tos-tws-flagship-v1',
):
    if marker not in V22_STYLE.read_text(encoding="utf-8"):
        fail(f"required V2.2 stylesheet marker missing: {marker}")

required_page_markers = (
    'const TWS_RESULT_PAGE_SIZE = 12;',
    'function TwsPremiumSelect',
    '<SystemPageHeader',
    'tos-tws-document-${String(doc.type || "TDOC").toLowerCase()}',
    'tos-tws-file-icon grid h-11 w-11',
    'tos-tws-card-meta grid gap-1.5',
    'tos-tws-card-actions flex flex-wrap',
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
        fail(f"required TWS V2.2 source marker missing: {marker}")

page_before = PAGE.read_bytes()
prior_style_hashes = {str(path): sha256(path) for path in (V1_STYLE, V11_STYLE, V2_STYLE, V21_STYLE, V22_STYLE)}
preserve_before = {str(path): sha256(path) for path in PRESERVE_FILES}

new_page_text = page_text.replace(IMPORT_V22, IMPORT_V22 + "\n" + IMPORT_V23, 1)
if new_page_text.count(IMPORT_V23) != 1:
    fail("V2.3 import transform failed")

for marker in (
    '--tos-tws-dashboard-flagship-v2-3-final-luxury-depth-runtime: 1;',
    '.tos-tws-document-card',
    '.tos-tws-card-actions .tos-premium-button',
    '.tos-tws-document-tdoc .tos-tws-file-icon',
    '.dark .tos-tws-flagship-v1 .tos-tws-document-card',
    '.dark .tos-tws-flagship-v1 .tos-tws-quick-create',
    '.tos-tws-pagination button:not(:disabled):last-child',
):
    if marker not in CSS:
        fail(f"V2.3 CSS marker missing before write: {marker}")

try:
    PAGE.write_text(new_page_text, encoding="utf-8")
    V23_STYLE.write_text(CSS, encoding="utf-8")
    v23_created = True
except Exception as exc:
    if V23_STYLE.exists():
        v23_created = True
    fail(f"source write failed: {exc}")

if PAGE.read_text(encoding="utf-8").count(IMPORT_V23) != 1:
    fail("V2.3 import missing after write")
for path in (V1_STYLE, V11_STYLE, V2_STYLE, V21_STYLE, V22_STYLE):
    if sha256(path) != prior_style_hashes[str(path)]:
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
    b'--tos-tws-dashboard-flagship-v2-2-reference-luxury-runtime',
    b'--tos-tws-dashboard-flagship-v2-3-final-luxury-depth-runtime',
    b'tos-tws-file-icon',
    b'tos-tws-card-meta',
    b'tos-tws-card-actions',
    b'data-tws-results-pagination',
)
for marker in built_markers:
    if tree_count(DIST, marker) < 1:
        fail(f"built output missing marker: {marker.decode(errors='ignore')}", build_result="FAIL")

if PAGE.read_text(encoding="utf-8").count(IMPORT_V23) != 1:
    fail("V2.3 import changed during build", build_result="FAIL")
for path in (V1_STYLE, V11_STYLE, V2_STYLE, V21_STYLE, V22_STYLE):
    if sha256(path) != prior_style_hashes[str(path)]:
        fail(f"prior stylesheet changed during build: {path}", build_result="FAIL")
for path in PRESERVE_FILES:
    if sha256(path) != preserve_before[str(path)]:
        fail(f"out-of-scope source changed during build: {path}", build_result="FAIL")

ts = int(time.time())
candidate = LIVE_PARENT / f"build.tws-dashboard-v2-3-final-luxury-candidate-{ts}"
live_backup = LIVE_PARENT / f"build.tws-dashboard-v2-3-final-luxury-backup-{ts}"
live_failed = LIVE_PARENT / f"build.tws-dashboard-v2-3-final-luxury-failed-{ts}"

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

for path in (V1_STYLE, V11_STYLE, V2_STYLE, V21_STYLE, V22_STYLE):
    if sha256(path) != prior_style_hashes[str(path)]:
        fail(f"prior stylesheet changed after deploy: {path}", build_result="PASS", rollback_deploy=True)
for path in PRESERVE_FILES:
    if sha256(path) != preserve_before[str(path)]:
        fail(f"out-of-scope source changed after deploy: {path}", build_result="PASS", rollback_deploy=True)

print("PASS/FAIL=PASS")
print("BUILD_RESULT=PASS")
print("LIVE_DEPLOY=PASS")
print("TWS_DASHBOARD_FLAGSHIP_V2_3_RUNTIME=YES")
print("TWS_V2_3_SCOPE=FINAL_LUXURY_DEPTH_VISUAL_ONLY")
print("TWS_REFERENCE_MATCH=VERY_CLOSE")
print("TWS_HEADER_ACTIONS=METALLIC_HARDWARE_PLUS")
print("TWS_REFRESH_BUTTON=COMPACT_METALLIC_GOLD")
print("TWS_FILTER_TABS=LUXURY_HARDWARE")
print("TWS_DOCUMENT_CARDS=LUXURY_PRODUCT_DEPTH_PLUS")
print("TWS_FILE_ICONS=JEWEL_GLOW_PLUS")
print("TWS_CARD_METADATA=RICH_PEARL_INSET")
print("TWS_CARD_ACTIONS=METALLIC_CAPSULES_PLUS")
print("TWS_DELETE_ACTION=SOFT_LUXURY_DESTRUCTIVE")
print("TWS_DARK_HERO=COSMIC_OBSIDIAN_GOLD")
print("TWS_DARK_QUICK_CREATE=SMOKED_TITANIUM")
print("TWS_DARK_CARDS=TITANIUM_GOLD_EDGE")
print("TWS_PAGINATION=REFERENCE_GOLD_CTA")
print("TWS_PROJECT_FILTER=PREMIUM_CUSTOM_PRESERVED")
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
print(f"TWS_DASHBOARD_V23_STYLE_SHA256={sha256(V23_STYLE)}")
print(f"LIVE_BACKUP={live_backup if live_backup.exists() else 'NONE'}")
print("STATUS=READY")
