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
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_PAGE_SHA256 = "2ce603e77b544c8f8c0083e47e2c05e9ffd4298d8dff3f6b1a4701acb42b1ad9"
EXPECTED_V1_STYLE_SHA256 = "6691401c241187e5ffd6611ba1d02510f37b954f975ec40021e5cee9072be49a"
EXPECTED_V11_STYLE_SHA256 = "b0a53b84f4cc74eed2f83c5b38d3fd72661bb81d4a7c54507766b8ad36998849"
EXPECTED_V2_STYLE_SHA256 = "e5b14bee3119d2de6e0b6450e555f358c5671ba47dcaaf12813e6ad4e218e4cc"

IMPORT_V2 = 'import "./twsDashboardFlagshipV2LuxuryPolish.css";'
IMPORT_V21 = 'import "./twsDashboardFlagshipV2_1ButtonsLuxuryPolish.css";'

CSS = r''':root {
  --tos-tws-dashboard-flagship-v2-1-buttons-luxury-runtime: 1;
}

/* TWS V2.1 — button system + final luxury fidelity. Visual-only layer. */

/* ---------- Global luxury refinement ---------- */
.tos-tws-flagship-v1 {
  --tws-v21-gold-1: #f3d77f;
  --tws-v21-gold-2: #d9a332;
  --tws-v21-gold-3: #a96f0e;
  --tws-v21-ink: #20170b;
  --tws-v21-ivory: #fffdf8;
  --tws-v21-obsidian: #0d0d0c;
  --tws-v21-titanium: #252522;
}

/* The V2 light hero still stretched taller than its inner panel in screenshots. */
.tos-tws-flagship-v1 .tos-tws-hero-card {
  display: flex !important;
  flex-direction: column !important;
  overflow: hidden !important;
}
.tos-tws-flagship-v1 .tos-tws-hero-card > .tos-tws-hero {
  flex: 1 1 auto !important;
  width: 100% !important;
}

/* Make the page header participate in the same flagship visual language. */
.tos-tws-flagship-v1 > .tos-premium-system-header {
  position: relative;
  border-color: rgba(164,107,12,.16) !important;
  background:
    radial-gradient(circle at 88% 12%, rgba(232,188,87,.18), transparent 25%),
    linear-gradient(135deg,#fffefa,#fff8e9) !important;
  box-shadow:
    0 22px 58px rgba(72,45,3,.075),
    inset 0 1px rgba(255,255,255,.96),
    inset 0 -1px rgba(165,108,13,.04) !important;
}
.tos-tws-flagship-v1 > .tos-premium-system-header::after {
  content: "";
  position: absolute;
  inset-inline: 28px;
  bottom: 0;
  height: 1px;
  pointer-events: none;
  background: linear-gradient(90deg,transparent,rgba(204,147,32,.42),transparent);
}
.tos-tws-flagship-v1 > .tos-premium-system-header h1 {
  letter-spacing: -.035em !important;
}

/* ---------- Header CTA button family ---------- */
.tos-tws-flagship-v1 > .tos-premium-system-header .tos-premium-button {
  position: relative;
  min-height: 44px;
  padding-inline: 17px !important;
  border: 1px solid rgba(153,99,8,.16) !important;
  border-radius: 14px !important;
  font-size: 12px !important;
  font-weight: 900 !important;
  letter-spacing: -.005em;
  transition: transform .16s ease, box-shadow .16s ease, border-color .16s ease, background .16s ease !important;
}
.tos-tws-flagship-v1 > .tos-premium-system-header .tos-premium-button:first-of-type {
  color: #251801 !important;
  border-color: rgba(151,96,6,.24) !important;
  background: linear-gradient(145deg,var(--tws-v21-gold-1),var(--tws-v21-gold-2)) !important;
  box-shadow:
    0 12px 26px rgba(151,96,6,.18),
    inset 0 1px rgba(255,255,255,.48),
    inset 0 -1px rgba(105,63,0,.12) !important;
}
.tos-tws-flagship-v1 > .tos-premium-system-header .tos-premium-button:not(:first-of-type) {
  color: #3d3020 !important;
  background: linear-gradient(180deg,rgba(255,255,255,.92),rgba(250,242,222,.90)) !important;
  box-shadow: 0 9px 20px rgba(70,43,3,.06), inset 0 1px rgba(255,255,255,.96) !important;
}
.tos-tws-flagship-v1 > .tos-premium-system-header .tos-premium-button:hover:not(:disabled) {
  transform: translateY(-2px);
  border-color: rgba(169,108,7,.30) !important;
  box-shadow: 0 15px 32px rgba(112,69,4,.14), inset 0 1px rgba(255,255,255,.92) !important;
}
.tos-tws-flagship-v1 > .tos-premium-system-header button[title] {
  width: 44px !important;
  height: 44px !important;
  border: 1px solid rgba(160,105,13,.14) !important;
  border-radius: 14px !important;
  color: #76500d !important;
  background: linear-gradient(145deg,#fffefa,#f4e6c4) !important;
  box-shadow: 0 9px 22px rgba(75,47,4,.07), inset 0 1px rgba(255,255,255,.94) !important;
  transition: transform .16s ease, box-shadow .16s ease, border-color .16s ease !important;
}
.tos-tws-flagship-v1 > .tos-premium-system-header button[title]:hover {
  transform: translateY(-2px) rotate(2deg);
  border-color: rgba(177,117,17,.27) !important;
  box-shadow: 0 14px 28px rgba(90,56,4,.12), inset 0 1px rgba(255,255,255,.94) !important;
}

/* ---------- Quick create ---------- */
.tos-tws-flagship-v1 .tos-tws-quick-create button {
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(156,100,8,.14) !important;
  box-shadow: 0 9px 20px rgba(63,39,3,.07), inset 0 1px rgba(255,255,255,.35) !important;
  transition: transform .16s ease, box-shadow .16s ease, border-color .16s ease !important;
}
.tos-tws-flagship-v1 .tos-tws-quick-create button:first-of-type {
  color: #251801 !important;
  background: linear-gradient(145deg,#f4d87e,#dda630) !important;
}
.tos-tws-flagship-v1 .tos-tws-quick-create button:not(:first-of-type) {
  color: #42331f !important;
  background: linear-gradient(180deg,#fffefb,#f8efd9) !important;
}
.tos-tws-flagship-v1 .tos-tws-quick-create button:hover:not(:disabled) {
  transform: translateY(-1px);
  border-color: rgba(171,111,9,.25) !important;
  box-shadow: 0 13px 28px rgba(86,52,3,.12), inset 0 1px rgba(255,255,255,.42) !important;
}

/* ---------- Navigation pills ---------- */
.tos-tws-flagship-v1 .tos-tws-tab {
  position: relative;
  min-height: 40px !important;
  padding-inline: 15px !important;
  border-radius: 14px !important;
  font-weight: 900 !important;
  box-shadow: inset 0 1px rgba(255,255,255,.76), 0 4px 12px rgba(64,40,3,.025) !important;
}
.tos-tws-flagship-v1 .tos-tws-tab:hover {
  transform: translateY(-1px) !important;
  border-color: rgba(166,108,12,.16) !important;
}
.tos-tws-flagship-v1 .tos-tws-tabs .tos-tws-tab[class*="bg-zinc-950"] {
  color: #201402 !important;
  border-color: rgba(151,96,5,.24) !important;
  background: linear-gradient(145deg,#f5dc8a,#dba22a) !important;
  box-shadow: 0 11px 24px rgba(146,91,4,.16), inset 0 1px rgba(255,255,255,.52) !important;
}

/* ---------- Refresh: dedicated premium command button ---------- */
.tos-tws-flagship-v1 .tos-tws-filter-row > .tos-premium-button {
  position: relative;
  justify-content: flex-start !important;
  min-height: 46px !important;
  padding-inline: 16px !important;
  border: 1px solid rgba(158,102,10,.16) !important;
  border-radius: 14px !important;
  color: #3d2d16 !important;
  background:
    radial-gradient(circle at 8% 50%, rgba(234,194,99,.22), transparent 18%),
    linear-gradient(180deg,#fffefb,#f8efd9) !important;
  box-shadow:
    0 9px 22px rgba(66,41,3,.06),
    inset 0 1px rgba(255,255,255,.96),
    inset 0 -1px rgba(155,99,8,.05) !important;
  font-size: 12px !important;
  font-weight: 900 !important;
  transition: transform .16s ease, box-shadow .16s ease, border-color .16s ease !important;
}
.tos-tws-flagship-v1 .tos-tws-filter-row > .tos-premium-button svg {
  width: 16px;
  height: 16px;
  color: #9a650d;
  filter: drop-shadow(0 2px 5px rgba(143,91,5,.14));
}
.tos-tws-flagship-v1 .tos-tws-filter-row > .tos-premium-button:hover:not(:disabled) {
  transform: translateY(-1px);
  border-color: rgba(175,115,15,.28) !important;
  background:
    radial-gradient(circle at 8% 50%, rgba(234,194,99,.30), transparent 21%),
    linear-gradient(180deg,#fffdfa,#f5e6c3) !important;
  box-shadow: 0 14px 30px rgba(86,52,3,.11), inset 0 1px rgba(255,255,255,.96) !important;
}
.tos-tws-flagship-v1 .tos-tws-filter-row > .tos-premium-button:active:not(:disabled) {
  transform: translateY(0) scale(.995);
  box-shadow: 0 6px 15px rgba(72,44,3,.07), inset 0 1px 2px rgba(105,67,5,.06) !important;
}

/* ---------- Project select + Grid/List toggle ---------- */
.tos-tws-flagship-v1 .tos-tws-premium-trigger {
  min-height: 46px !important;
  border-radius: 14px !important;
  font-weight: 900 !important;
}
.tos-tws-flagship-v1 .tos-tws-view-toggle {
  padding: 4px !important;
  border-radius: 15px !important;
  background: linear-gradient(180deg,rgba(253,248,235,.86),rgba(245,233,205,.64)) !important;
  box-shadow: inset 0 1px rgba(255,255,255,.82), 0 7px 18px rgba(69,43,3,.04) !important;
}
.tos-tws-flagship-v1 .tos-tws-view-toggle button {
  min-height: 36px;
  border-radius: 11px !important;
  font-weight: 900 !important;
  transition: transform .15s ease, background .15s ease, color .15s ease, box-shadow .15s ease !important;
}
.tos-tws-flagship-v1 .tos-tws-view-toggle button:hover {
  transform: translateY(-1px);
}
.tos-tws-flagship-v1 .tos-tws-view-toggle button[class*="bg-white"] {
  color: #80550c !important;
  background: linear-gradient(145deg,#fffefa,#f2dfad) !important;
  box-shadow: 0 7px 16px rgba(93,58,4,.09), inset 0 1px rgba(255,255,255,.9) !important;
}

/* ---------- Bucket rows ---------- */
.tos-tws-flagship-v1 .tos-tws-bucket .space-y-2 > button {
  transition: transform .15s ease, box-shadow .15s ease, border-color .15s ease, background .15s ease !important;
}
.tos-tws-flagship-v1 .tos-tws-bucket .space-y-2 > button:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 10px 20px rgba(72,44,3,.06), inset 0 1px rgba(255,255,255,.9) !important;
}

/* ---------- File card action bar ---------- */
.tos-tws-flagship-v1 .tos-tws-document-card .tos-premium-button {
  min-height: 38px;
  padding: 8px 13px !important;
  border: 1px solid rgba(147,96,12,.12) !important;
  border-radius: 12px !important;
  font-size: 11px !important;
  font-weight: 900 !important;
  box-shadow: 0 6px 14px rgba(66,41,3,.04), inset 0 1px rgba(255,255,255,.86) !important;
  transition: transform .15s ease, box-shadow .15s ease, border-color .15s ease !important;
}
.tos-tws-flagship-v1 .tos-tws-document-card .tos-premium-button[class*="bg-zinc-100"] {
  color: #45351f !important;
  background: linear-gradient(180deg,#fffefa,#f4ead2) !important;
}
.tos-tws-flagship-v1 .tos-tws-document-card .tos-premium-button[class*="bg-red-50"] {
  color: #a22e2e !important;
  border-color: rgba(170,47,47,.14) !important;
  background: linear-gradient(180deg,#fff8f6,#fbe9e5) !important;
}
.tos-tws-flagship-v1 .tos-tws-document-card .tos-premium-button:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 10px 22px rgba(72,44,3,.08), inset 0 1px rgba(255,255,255,.9) !important;
}
.tos-tws-flagship-v1 .tos-tws-document-card .tos-premium-button[class*="bg-red-50"]:hover:not(:disabled) {
  border-color: rgba(183,55,55,.24) !important;
  box-shadow: 0 10px 22px rgba(155,42,42,.08), inset 0 1px rgba(255,255,255,.85) !important;
}

/* ---------- Bulk action bar ---------- */
.tos-tws-flagship-v1 .tos-tws-bulk-bar .tos-premium-button {
  min-height: 38px;
  border: 1px solid rgba(155,101,12,.14) !important;
  border-radius: 12px !important;
  font-size: 11px !important;
  font-weight: 900 !important;
  box-shadow: inset 0 1px rgba(255,255,255,.82) !important;
}

/* ---------- Pagination as a luxury footer command surface ---------- */
.tos-tws-flagship-v1 .tos-tws-pagination {
  padding: 13px 15px !important;
  border-radius: 20px !important;
  border-color: rgba(162,106,12,.13) !important;
  background:
    linear-gradient(180deg,rgba(255,254,249,.97),rgba(252,244,224,.93)) !important;
  box-shadow: 0 12px 28px rgba(66,40,3,.05), inset 0 1px rgba(255,255,255,.95) !important;
}
.tos-tws-flagship-v1 .tos-tws-pagination__page {
  color: #49351a !important;
  padding: 0 4px;
}
.tos-tws-flagship-v1 .tos-tws-pagination button {
  min-height: 36px !important;
  padding-inline: 13px !important;
  border-radius: 12px !important;
  border-color: rgba(157,101,10,.15) !important;
  color: #4b371b !important;
  background: linear-gradient(180deg,#fffefb,#f6ead0) !important;
  box-shadow: 0 6px 15px rgba(67,41,3,.04), inset 0 1px rgba(255,255,255,.92) !important;
  transition: transform .15s ease, box-shadow .15s ease, border-color .15s ease !important;
}
.tos-tws-flagship-v1 .tos-tws-pagination button:not(:disabled):hover {
  transform: translateY(-1px);
  border-color: rgba(177,116,16,.27) !important;
  box-shadow: 0 10px 21px rgba(77,46,3,.08), inset 0 1px rgba(255,255,255,.92) !important;
}
.tos-tws-flagship-v1 .tos-tws-pagination button:disabled {
  opacity: .34 !important;
  filter: saturate(.55);
}

/* ---------- Dark / Obsidian luxury ---------- */
.dark .tos-tws-flagship-v1 > .tos-premium-system-header {
  border-color: rgba(224,178,76,.13) !important;
  background:
    radial-gradient(circle at 88% 12%, rgba(206,151,35,.10), transparent 26%),
    linear-gradient(135deg,#181815,#0f0f0e 72%,#18140d) !important;
  box-shadow: 0 24px 60px rgba(0,0,0,.28), inset 0 1px rgba(255,255,255,.025) !important;
}
.dark .tos-tws-flagship-v1 > .tos-premium-system-header::after {
  background: linear-gradient(90deg,transparent,rgba(228,181,79,.28),transparent);
}
.dark .tos-tws-flagship-v1 > .tos-premium-system-header .tos-premium-button:first-of-type {
  color: #201402 !important;
  border-color: rgba(229,184,84,.24) !important;
  background: linear-gradient(145deg,#f0cd69,#d49a20) !important;
  box-shadow: 0 13px 30px rgba(0,0,0,.28), 0 0 24px rgba(213,157,39,.08), inset 0 1px rgba(255,255,255,.24) !important;
}
.dark .tos-tws-flagship-v1 > .tos-premium-system-header .tos-premium-button:not(:first-of-type) {
  color: #e7dfd3 !important;
  border-color: rgba(224,178,76,.12) !important;
  background: linear-gradient(145deg,#262623,#1a1a18) !important;
  box-shadow: 0 10px 22px rgba(0,0,0,.20), inset 0 1px rgba(255,255,255,.035) !important;
}
.dark .tos-tws-flagship-v1 > .tos-premium-system-header button[title] {
  color: #dfb75b !important;
  border-color: rgba(224,178,76,.13) !important;
  background: linear-gradient(145deg,#262623,#191917) !important;
  box-shadow: 0 10px 22px rgba(0,0,0,.22), inset 0 1px rgba(255,255,255,.035) !important;
}

.dark .tos-tws-flagship-v1 .tos-tws-quick-create button:first-of-type {
  color: #211501 !important;
  border-color: rgba(224,178,76,.24) !important;
  background: linear-gradient(145deg,#efcd69,#d59b22) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-quick-create button:not(:first-of-type) {
  color: #e8e1d7 !important;
  border-color: rgba(224,178,76,.09) !important;
  background: linear-gradient(145deg,#292926,#20201e) !important;
  box-shadow: 0 9px 20px rgba(0,0,0,.18), inset 0 1px rgba(255,255,255,.025) !important;
}

.dark .tos-tws-flagship-v1 .tos-tws-filter-row > .tos-premium-button {
  color: #e7dfd4 !important;
  border-color: rgba(224,178,76,.13) !important;
  background:
    radial-gradient(circle at 8% 50%, rgba(211,158,42,.10), transparent 19%),
    linear-gradient(145deg,#262623,#1a1a18) !important;
  box-shadow: 0 10px 24px rgba(0,0,0,.20), inset 0 1px rgba(255,255,255,.035) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-filter-row > .tos-premium-button svg {
  color: #e1b95e;
  filter: drop-shadow(0 2px 7px rgba(212,158,39,.16));
}
.dark .tos-tws-flagship-v1 .tos-tws-filter-row > .tos-premium-button:hover:not(:disabled) {
  border-color: rgba(224,178,76,.23) !important;
  background:
    radial-gradient(circle at 8% 50%, rgba(211,158,42,.15), transparent 22%),
    linear-gradient(145deg,#2d2c27,#1d1d1a) !important;
  box-shadow: 0 14px 30px rgba(0,0,0,.26), 0 0 22px rgba(206,151,35,.04), inset 0 1px rgba(255,255,255,.04) !important;
}

.dark .tos-tws-flagship-v1 .tos-tws-view-toggle {
  border-color: rgba(224,178,76,.10) !important;
  background: linear-gradient(180deg,#1b1b19,#151513) !important;
  box-shadow: inset 0 1px rgba(255,255,255,.025), 0 8px 18px rgba(0,0,0,.15) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-view-toggle button[class*="bg-white"] {
  color: #e5bb57 !important;
  background: linear-gradient(145deg,#302a1d,#23211c) !important;
  box-shadow: 0 8px 18px rgba(0,0,0,.22), inset 0 1px rgba(255,255,255,.035) !important;
}

.dark .tos-tws-flagship-v1 .tos-tws-document-card .tos-premium-button {
  border-color: rgba(224,178,76,.08) !important;
  box-shadow: 0 7px 16px rgba(0,0,0,.17), inset 0 1px rgba(255,255,255,.02) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-document-card .tos-premium-button[class*="dark:bg-zinc-800"] {
  color: #dfd8cf !important;
  background: linear-gradient(145deg,#292927,#21211f) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-document-card .tos-premium-button[class*="dark:bg-red-500/10"] {
  color: #e98781 !important;
  border-color: rgba(214,87,78,.12) !important;
  background: linear-gradient(145deg,#311b19,#251716) !important;
}

.dark .tos-tws-flagship-v1 .tos-tws-pagination {
  border-color: rgba(224,178,76,.10) !important;
  color: #aaa197 !important;
  background: linear-gradient(180deg,#171715,#111110) !important;
  box-shadow: 0 14px 32px rgba(0,0,0,.18), inset 0 1px rgba(255,255,255,.02) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-pagination__page {
  color: #e7dfd4 !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-pagination button {
  color: #ddd5ca !important;
  border-color: rgba(224,178,76,.10) !important;
  background: linear-gradient(145deg,#272724,#1c1c1a) !important;
  box-shadow: 0 7px 16px rgba(0,0,0,.17), inset 0 1px rgba(255,255,255,.025) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-pagination button:not(:disabled):hover {
  color: #efc969 !important;
  border-color: rgba(224,178,76,.21) !important;
  background: linear-gradient(145deg,#302c23,#211f1a) !important;
}

/* Focus rings stay premium and visible without browser-blue styling. */
.tos-tws-flagship-v1 button:focus-visible,
.tos-tws-flagship-v1 .tos-tws-premium-trigger:focus-visible {
  outline: none !important;
  box-shadow: 0 0 0 3px rgba(210,155,39,.14), 0 10px 24px rgba(80,49,3,.08) !important;
}
.dark .tos-tws-flagship-v1 button:focus-visible,
.dark .tos-tws-flagship-v1 .tos-tws-premium-trigger:focus-visible {
  box-shadow: 0 0 0 3px rgba(225,180,80,.13), 0 10px 26px rgba(0,0,0,.24) !important;
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

print("RUNNING=TOS_UXUI_SYSTEM_TWS_DASHBOARD_FLAGSHIP_V2_1_BUTTONS_LUXURY_POLISH")

page_before = None
v21_created = False
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
    global page_before, v21_created
    try:
        if page_before is not None:
            PAGE.write_bytes(page_before)
    except Exception:
        pass
    try:
        if v21_created and V21_STYLE.exists():
            V21_STYLE.unlink()
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
    print("TWS_DASHBOARD_FLAGSHIP_V2_1_RUNTIME=NO")
    sys.exit(1)


if ROOT.resolve() == Path("/"):
    fail("unsafe ROOT")

for path in (FRONTEND, PAGE, V1_STYLE, V11_STYLE, V2_STYLE, LIVE_PARENT, *PRESERVE_FILES):
    if not path.exists():
        fail(f"required path missing: {path}")

if sha256(PAGE) != EXPECTED_PAGE_SHA256:
    fail(f"TwsDashboard.jsx V2 baseline mismatch: {sha256(PAGE)}")
if sha256(V1_STYLE) != EXPECTED_V1_STYLE_SHA256:
    fail(f"V1 stylesheet baseline mismatch: {sha256(V1_STYLE)}")
if sha256(V11_STYLE) != EXPECTED_V11_STYLE_SHA256:
    fail(f"V1.1 stylesheet baseline mismatch: {sha256(V11_STYLE)}")
if sha256(V2_STYLE) != EXPECTED_V2_STYLE_SHA256:
    fail(f"V2 stylesheet baseline mismatch: {sha256(V2_STYLE)}")
if V21_STYLE.exists():
    fail(f"unexpected state: V2.1 stylesheet already exists with sha256 {sha256(V21_STYLE)}")

page_text = PAGE.read_text(encoding="utf-8")
if page_text.count(IMPORT_V2) != 1:
    fail(f"V2 import count mismatch: {page_text.count(IMPORT_V2)}")
if IMPORT_V21 in page_text:
    fail("unexpected state: V2.1 import already exists")

required_page_markers = (
    'const TWS_RESULT_PAGE_SIZE = 12;',
    'function TwsPremiumSelect',
    '<SystemPageHeader',
    'className="tos-tws-hero-card overflow-hidden p-0"',
    'className="tos-tws-control-card mt-4"',
    '<RefreshCw size={16} className={loading ? "animate-spin" : ""} />',
    'className="tos-tws-document-card group relative flex flex-col gap-3 p-4"',
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
        fail(f"required TWS V2 source marker missing: {marker}")

for css_path, markers in (
    (V1_STYLE, ('--tos-tws-dashboard-flagship-v1-runtime', '.tos-tws-pagination')),
    (V11_STYLE, ('--tos-tws-dashboard-flagship-v1-1-dark-fidelity-runtime', '.tos-tws-hero-card')),
    (V2_STYLE, ('--tos-tws-dashboard-flagship-v2-luxury-runtime', 'Luxury hero', 'Flagship document cards')),
):
    text = css_path.read_text(encoding="utf-8")
    for marker in markers:
        if marker not in text:
            fail(f"required baseline style marker missing in {css_path.name}: {marker}")

page_before = PAGE.read_bytes()
v1_before = sha256(V1_STYLE)
v11_before = sha256(V11_STYLE)
v2_before = sha256(V2_STYLE)
preserve_before = {str(path): sha256(path) for path in PRESERVE_FILES}

new_page_text = page_text.replace(IMPORT_V2, IMPORT_V2 + "\n" + IMPORT_V21, 1)
if new_page_text.count(IMPORT_V21) != 1:
    fail("V2.1 import transform failed")
if new_page_text.count(IMPORT_V2) != 1:
    fail("V2 import changed unexpectedly")

for marker in (
    '--tos-tws-dashboard-flagship-v2-1-buttons-luxury-runtime: 1;',
    'Refresh: dedicated premium command button',
    'Header CTA button family',
    'File card action bar',
    'Pagination as a luxury footer command surface',
    'Dark / Obsidian luxury',
):
    if marker not in CSS:
        fail(f"V2.1 CSS marker missing before write: {marker}")

try:
    PAGE.write_text(new_page_text, encoding="utf-8")
    V21_STYLE.write_text(CSS, encoding="utf-8")
    v21_created = True
except Exception as exc:
    if V21_STYLE.exists():
        v21_created = True
    fail(f"source write failed: {exc}")

if PAGE.read_text(encoding="utf-8").count(IMPORT_V21) != 1:
    fail("V2.1 import missing after write")
if sha256(V1_STYLE) != v1_before:
    fail("V1 stylesheet changed unexpectedly")
if sha256(V11_STYLE) != v11_before:
    fail("V1.1 stylesheet changed unexpectedly")
if sha256(V2_STYLE) != v2_before:
    fail("V2 stylesheet changed unexpectedly")
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
    b'tos-tws-premium-select',
    b'data-tws-results-pagination',
    b'tos-tws-pagination__page',
)
for marker in built_markers:
    if tree_count(DIST, marker) < 1:
        fail(f"built output missing marker: {marker.decode(errors='ignore')}", build_result="FAIL")

if PAGE.read_text(encoding="utf-8").count(IMPORT_V21) != 1:
    fail("V2.1 import changed during build", build_result="FAIL")
if sha256(V1_STYLE) != v1_before or sha256(V11_STYLE) != v11_before or sha256(V2_STYLE) != v2_before:
    fail("baseline TWS styles changed during build", build_result="FAIL")
for path in PRESERVE_FILES:
    if sha256(path) != preserve_before[str(path)]:
        fail(f"out-of-scope source changed during build: {path}", build_result="FAIL")

# Atomic live deploy. No Git in /var/www/TOS. No service restart.
ts = int(time.time())
candidate = LIVE_PARENT / f"build.tws-dashboard-v2-1-buttons-luxury-candidate-{ts}"
live_backup = LIVE_PARENT / f"build.tws-dashboard-v2-1-buttons-luxury-backup-{ts}"
live_failed = LIVE_PARENT / f"build.tws-dashboard-v2-1-buttons-luxury-failed-{ts}"

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

if PAGE.read_text(encoding="utf-8").count(IMPORT_V21) != 1:
    fail("V2.1 import changed after deploy", build_result="PASS", rollback_deploy=True)
if sha256(V1_STYLE) != v1_before or sha256(V11_STYLE) != v11_before or sha256(V2_STYLE) != v2_before:
    fail("baseline TWS styles changed after deploy", build_result="PASS", rollback_deploy=True)
for path in PRESERVE_FILES:
    if sha256(path) != preserve_before[str(path)]:
        fail(f"out-of-scope source changed after deploy: {path}", build_result="PASS", rollback_deploy=True)

print("PASS/FAIL=PASS")
print("BUILD_RESULT=PASS")
print("LIVE_DEPLOY=PASS")
print("TWS_DASHBOARD_FLAGSHIP_V2_1_RUNTIME=YES")
print("TWS_V2_1_SCOPE=BUTTONS_AND_LUXURY_FIDELITY_ONLY")
print("TWS_LIGHT_HERO_VOID=CORRECTED")
print("TWS_SYSTEM_HEADER=LUXURY_REFINED")
print("TWS_HEADER_CTA_BUTTONS=LUXURY_REFINED")
print("TWS_REFRESH_BUTTON=LUXURY_COMMAND")
print("TWS_QUICK_CREATE_BUTTONS=LUXURY_REFINED")
print("TWS_FILTER_TABS=LUXURY_REFINED")
print("TWS_PROJECT_FILTER=PREMIUM_CUSTOM_PRESERVED")
print("TWS_GRID_LIST_TOGGLE=LUXURY_REFINED")
print("TWS_CARD_ACTIONS=LUXURY_REFINED")
print("TWS_DELETE_ACTION=PREMIUM_DESTRUCTIVE")
print("TWS_PAGINATION=LUXURY_REFINED")
print("TWS_LIGHT_MODE=IVORY_CHAMPAGNE_PLUS")
print("TWS_DARK_MODE=OBSIDIAN_CHAMPAGNE_PLUS")
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
print(f"TWS_DASHBOARD_V1_STYLE_SHA256={sha256(V1_STYLE)}")
print(f"TWS_DASHBOARD_V11_STYLE_SHA256={sha256(V11_STYLE)}")
print(f"TWS_DASHBOARD_V2_STYLE_SHA256={sha256(V2_STYLE)}")
print(f"TWS_DASHBOARD_V21_STYLE_SHA256={sha256(V21_STYLE)}")
print(f"LIVE_BACKUP={live_backup if live_backup.exists() else 'NONE'}")
print("STATUS=READY")
