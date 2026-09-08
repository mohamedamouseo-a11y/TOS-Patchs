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
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_PAGE_SHA256 = "757b1c7f56a81486bb755ae84979a0b2494ba28b19b4e29691ff5f536bf2a807"
EXPECTED_V1_STYLE_SHA256 = "6691401c241187e5ffd6611ba1d02510f37b954f975ec40021e5cee9072be49a"
EXPECTED_V11_STYLE_SHA256 = "b0a53b84f4cc74eed2f83c5b38d3fd72661bb81d4a7c54507766b8ad36998849"

IMPORT_V11 = 'import "./twsDashboardFlagshipV1_1DarkFidelity.css";'
IMPORT_V2 = 'import "./twsDashboardFlagshipV2LuxuryPolish.css";'

CSS = r''':root {
  --tos-tws-dashboard-flagship-v2-luxury-runtime: 1;
}

.tos-tws-flagship-v1 {
  --tws-v2-champagne: #e7bc57;
  --tws-v2-gold: #c98a1a;
  --tws-v2-ink: #17120b;
  --tws-v2-ivory: #fffdf8;
  --tws-v2-line: rgba(155, 101, 11, .15);
  isolation: isolate;
}

/* Luxury hero */
.tos-tws-flagship-v1 .tos-tws-hero-layout {
  gap: 18px !important;
}
.tos-tws-flagship-v1 .tos-tws-hero-card {
  border: 1px solid rgba(166,108,12,.16) !important;
  border-radius: 32px !important;
  background: linear-gradient(145deg,#fffdfa,#fff8e8) !important;
  box-shadow:
    0 28px 70px rgba(82,52,4,.10),
    0 1px 0 rgba(255,255,255,.96) inset,
    0 -1px 0 rgba(186,129,24,.06) inset !important;
}
.tos-tws-flagship-v1 .tos-tws-hero {
  min-height: 228px !important;
  padding: 30px !important;
  border-radius: 31px !important;
  background:
    radial-gradient(circle at 84% 18%, rgba(222,169,54,.28), transparent 28%),
    radial-gradient(circle at 20% 90%, rgba(232,199,117,.15), transparent 36%),
    linear-gradient(122deg, rgba(255,255,255,.98), rgba(255,249,234,.97) 58%, rgba(249,236,203,.96)) !important;
  box-shadow: inset 0 0 0 1px rgba(255,255,255,.52);
}
.tos-tws-flagship-v1 .tos-tws-hero::before {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  background:
    linear-gradient(90deg, rgba(255,255,255,.0), rgba(255,255,255,.36) 48%, rgba(255,255,255,0)),
    repeating-linear-gradient(107deg, transparent 0 62px, rgba(169,110,10,.05) 63px 65px);
  mask-image: linear-gradient(90deg, transparent 16%, #000 48%, #000 100%);
}
.tos-tws-flagship-v1 .tos-tws-hero h2 {
  max-width: 740px;
  font-size: clamp(30px,3vw,42px) !important;
  line-height: 1.04 !important;
  letter-spacing: -.04em !important;
  color: #17110a !important;
  text-wrap: balance;
}
.tos-tws-flagship-v1 .tos-tws-hero p {
  max-width: 680px;
  color: #6f6354 !important;
  font-size: 14px !important;
  line-height: 1.9 !important;
}
.tos-tws-flagship-v1 .tos-tws-hero > div > div:first-child > span {
  border: 1px solid rgba(169,110,10,.18) !important;
  border-radius: 999px !important;
  color: #7d5107 !important;
  background: linear-gradient(180deg,rgba(255,248,226,.88),rgba(242,214,149,.35)) !important;
  box-shadow: 0 8px 22px rgba(122,77,4,.08), inset 0 1px rgba(255,255,255,.86);
}
.tos-tws-flagship-v1 .tos-tws-quick-create {
  min-width: 238px !important;
  padding: 14px !important;
  border: 1px solid rgba(166,108,12,.18) !important;
  border-radius: 24px !important;
  background: rgba(255,253,247,.80) !important;
  box-shadow: 0 20px 48px rgba(94,59,5,.14), inset 0 1px rgba(255,255,255,.96) !important;
  backdrop-filter: blur(22px) saturate(1.15);
}
.tos-tws-flagship-v1 .tos-tws-quick-create > b {
  color: #9b6509 !important;
  letter-spacing: .06em;
  text-transform: uppercase;
}
.tos-tws-flagship-v1 .tos-tws-quick-create button {
  min-height: 42px;
  border-radius: 14px !important;
  font-weight: 900 !important;
}

/* Executive KPI system */
.tos-tws-flagship-v1 .tos-tws-stats {
  gap: 12px !important;
}
.tos-tws-flagship-v1 .tos-tws-stat {
  min-height: 116px !important;
  padding: 18px !important;
  border: 1px solid rgba(163,108,15,.13) !important;
  border-radius: 24px !important;
  background:
    radial-gradient(circle at 88% 18%, rgba(230,188,92,.12), transparent 32%),
    linear-gradient(150deg,#fff,#fff9ec) !important;
  box-shadow: 0 17px 42px rgba(76,49,5,.075), inset 0 1px rgba(255,255,255,.94) !important;
}
.tos-tws-flagship-v1 .tos-tws-stat::before {
  inset-block: 18px !important;
  width: 4px !important;
  box-shadow: 0 0 18px rgba(215,164,45,.28);
}
.tos-tws-flagship-v1 .tos-tws-stat p {
  letter-spacing: .06em;
  text-transform: uppercase;
}
.tos-tws-flagship-v1 .tos-tws-stat b {
  font-size: 30px !important;
  line-height: 1 !important;
}
.tos-tws-flagship-v1 .tos-tws-stat .grid.h-10.w-10 {
  width: 46px !important;
  height: 46px !important;
  border: 1px solid rgba(161,106,12,.10);
  background: linear-gradient(145deg,#fffaf0,#f3e4bc) !important;
  color: #80550a !important;
  box-shadow: 0 10px 24px rgba(83,53,4,.08), inset 0 1px rgba(255,255,255,.9);
}

/* Command rail */
.tos-tws-flagship-v1 .tos-tws-control-card {
  padding: 18px !important;
  border: 1px solid rgba(166,108,12,.14) !important;
  border-radius: 28px !important;
  background:
    linear-gradient(180deg,rgba(255,254,251,.985),rgba(255,249,237,.96)) !important;
  box-shadow: 0 20px 50px rgba(76,49,5,.075), inset 0 1px rgba(255,255,255,.95) !important;
}
.tos-tws-flagship-v1 .tos-tws-tabs {
  gap: 7px !important;
}
.tos-tws-flagship-v1 .tos-tws-tab {
  min-height: 38px;
  padding-inline: 14px !important;
  border-radius: 13px !important;
  border-color: rgba(155,101,11,.08) !important;
  background: rgba(151,99,10,.055) !important;
  box-shadow: inset 0 1px rgba(255,255,255,.75);
}
.tos-tws-flagship-v1 .tos-tws-tabs .tos-tws-tab[class*="bg-zinc-950"] {
  color: #221603 !important;
  border-color: rgba(164,105,9,.22) !important;
  background: linear-gradient(145deg,#f4d67d,#daa32f) !important;
  box-shadow: 0 10px 24px rgba(158,101,7,.18), inset 0 1px rgba(255,255,255,.48) !important;
}
.tos-tws-flagship-v1 .tos-tws-filter-row {
  margin-top: 14px !important;
  gap: 10px !important;
}
.tos-tws-flagship-v1 .tos-tws-filter-row input {
  min-height: 46px !important;
  border-radius: 14px !important;
  border-color: rgba(162,108,16,.12) !important;
  background: rgba(255,255,255,.86) !important;
  box-shadow: inset 0 1px rgba(255,255,255,.95) !important;
}
.tos-tws-premium-trigger {
  min-height: 46px !important;
  padding: 10px 13px !important;
  border-radius: 14px !important;
  border-color: rgba(162,108,16,.15) !important;
  background: linear-gradient(180deg,#fffefb,#fff9ec) !important;
  box-shadow: 0 8px 20px rgba(74,47,4,.055), inset 0 1px rgba(255,255,255,.95) !important;
}
.tos-tws-premium-menu {
  padding: 8px !important;
  border-radius: 17px !important;
  border-color: rgba(162,108,16,.18) !important;
  box-shadow: 0 28px 68px rgba(57,35,2,.18), inset 0 1px rgba(255,255,255,.96) !important;
}
.tos-tws-premium-option {
  min-height: 40px !important;
  border-radius: 11px !important;
}
.tos-tws-flagship-v1 .tos-tws-view-toggle {
  min-height: 46px;
  border-radius: 14px !important;
  border-color: rgba(163,109,17,.12) !important;
  background: rgba(161,108,16,.045) !important;
}

/* Executive intelligence buckets */
.tos-tws-flagship-v1 .tos-tws-buckets {
  gap: 16px !important;
}
.tos-tws-flagship-v1 .tos-tws-bucket {
  padding: 18px !important;
  border: 1px solid rgba(164,109,16,.12) !important;
  border-radius: 24px !important;
  background:
    radial-gradient(circle at 95% 4%, rgba(231,188,87,.10), transparent 30%),
    linear-gradient(155deg,#fff,#fffaf0) !important;
  box-shadow: 0 16px 38px rgba(73,46,4,.065), inset 0 1px rgba(255,255,255,.95) !important;
}
.tos-tws-flagship-v1 .tos-tws-bucket .mb-3 > .grid {
  border: 1px solid rgba(162,107,14,.09);
  background: linear-gradient(145deg,#fffaf0,#f0dfb1) !important;
  color: #81560a !important;
}
.tos-tws-flagship-v1 .tos-tws-bucket .space-y-2 > button {
  min-height: 43px;
  border-radius: 14px !important;
  border-color: rgba(164,109,16,.10) !important;
  background: rgba(255,255,255,.62) !important;
  box-shadow: inset 0 1px rgba(255,255,255,.88);
}
.tos-tws-flagship-v1 .tos-tws-bucket .space-y-2 > button:hover {
  border-color: rgba(184,124,18,.20) !important;
  background: #fff8e8 !important;
  transform: translateY(-1px);
}

/* Flagship document cards */
.tos-tws-flagship-v1 .tos-tws-document-card {
  position: relative;
  overflow: hidden;
  min-height: 236px;
  padding: 18px !important;
  border: 1px solid rgba(161,106,14,.13) !important;
  border-radius: 25px !important;
  background:
    radial-gradient(circle at 95% 0%, rgba(230,185,80,.11), transparent 30%),
    linear-gradient(154deg,#fff,#fffaf1) !important;
  box-shadow: 0 18px 44px rgba(69,43,3,.075), inset 0 1px rgba(255,255,255,.96) !important;
}
.tos-tws-flagship-v1 .tos-tws-document-card::before {
  content: "";
  position: absolute;
  inset-inline: 18px;
  top: 0;
  height: 2px;
  border-radius: 999px;
  background: linear-gradient(90deg,transparent,rgba(214,160,47,.72),transparent);
  opacity: .58;
}
.tos-tws-flagship-v1 .tos-tws-document-card:hover {
  transform: translateY(-4px) !important;
  border-color: rgba(182,121,17,.25) !important;
  box-shadow: 0 26px 58px rgba(68,42,3,.12), inset 0 1px rgba(255,255,255,.97) !important;
}
.tos-tws-flagship-v1 .tos-tws-document-card > div:first-child .grid.h-11.w-11 {
  width: 48px !important;
  height: 48px !important;
  border-radius: 16px !important;
  box-shadow: 0 10px 24px rgba(20,15,8,.15);
}
.tos-tws-flagship-v1 .tos-tws-document-card > div:nth-child(2) {
  border: 1px solid rgba(162,106,12,.08);
  border-radius: 16px !important;
  background: rgba(248,243,232,.78) !important;
  box-shadow: inset 0 1px rgba(255,255,255,.78);
}
.tos-tws-flagship-v1 .tos-tws-document-card > div:last-child {
  padding-top: 3px;
}
.tos-tws-flagship-v1 .tos-tws-document-card > div:last-child button {
  min-height: 36px;
  border-radius: 11px !important;
  font-weight: 850 !important;
}

/* List + pagination */
.tos-tws-flagship-v1 .tos-tws-list {
  border-radius: 24px !important;
  box-shadow: 0 18px 44px rgba(67,42,3,.075) !important;
}
.tos-tws-flagship-v1 .tos-tws-list-row {
  min-height: 72px;
  padding-block: 14px !important;
}
.tos-tws-pagination {
  margin-top: 18px !important;
  padding: 13px 15px !important;
  border-radius: 20px !important;
  border-color: rgba(162,107,14,.13) !important;
  background: linear-gradient(180deg,#fffdf8,#fff8e9) !important;
  box-shadow: 0 14px 34px rgba(66,41,3,.06) !important;
}
.tos-tws-pagination button {
  min-height: 36px !important;
  border-radius: 11px !important;
}

/* DARK — obsidian / champagne / titanium */
.dark .tos-tws-flagship-v1 {
  --tws-v2-line: rgba(229,187,91,.14);
}
.dark .tos-tws-flagship-v1 .tos-tws-hero-card {
  border-color: rgba(231,188,89,.16) !important;
  background: linear-gradient(145deg,#151410,#0d0d0c) !important;
  box-shadow: 0 30px 74px rgba(0,0,0,.40), inset 0 1px rgba(255,255,255,.025) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-hero {
  min-height: 228px !important;
  background:
    radial-gradient(circle at 82% 16%, rgba(210,157,38,.20), transparent 28%),
    radial-gradient(circle at 18% 92%, rgba(72,87,105,.10), transparent 38%),
    linear-gradient(126deg,#171713,#0b0b0a 60%,#1a150b) !important;
  box-shadow: inset 0 0 0 1px rgba(255,255,255,.018) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-hero h2 { color: #fffaf1 !important; }
.dark .tos-tws-flagship-v1 .tos-tws-hero p { color: #aaa298 !important; }
.dark .tos-tws-flagship-v1 .tos-tws-hero > div > div:first-child > span {
  color: #edc666 !important;
  border-color: rgba(230,185,83,.20) !important;
  background: rgba(218,165,50,.075) !important;
  box-shadow: 0 10px 26px rgba(0,0,0,.20), inset 0 1px rgba(255,255,255,.035);
}
.dark .tos-tws-flagship-v1 .tos-tws-quick-create {
  border-color: rgba(232,188,88,.17) !important;
  background: linear-gradient(145deg,rgba(35,34,30,.82),rgba(18,18,16,.88)) !important;
  box-shadow: 0 24px 54px rgba(0,0,0,.42), inset 0 1px rgba(255,255,255,.035) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-stat,
.dark .tos-tws-flagship-v1 .tos-tws-control-card,
.dark .tos-tws-flagship-v1 .tos-tws-bucket,
.dark .tos-tws-flagship-v1 .tos-tws-document-card,
.dark .tos-tws-flagship-v1 .tos-tws-list {
  border-color: rgba(229,185,88,.12) !important;
  background:
    radial-gradient(circle at 96% 0%, rgba(214,161,43,.055), transparent 28%),
    linear-gradient(155deg,#171715,#0f0f0e) !important;
  box-shadow: 0 20px 48px rgba(0,0,0,.26), inset 0 1px rgba(255,255,255,.018) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-stat .grid.h-10.w-10 {
  border-color: rgba(229,185,88,.12);
  background: linear-gradient(145deg,#24231f,#171715) !important;
  color: #e7be5f !important;
  box-shadow: 0 10px 24px rgba(0,0,0,.24), inset 0 1px rgba(255,255,255,.025);
}
.dark .tos-tws-flagship-v1 .tos-tws-control-card {
  background: linear-gradient(180deg,rgba(22,22,20,.98),rgba(14,14,13,.98)) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-tabs .tos-tws-tab[class~="dark:bg-white/10"] {
  color: #bdb5a9 !important;
  border-color: rgba(232,189,91,.08) !important;
  background: rgba(255,255,255,.045) !important;
  box-shadow: inset 0 1px rgba(255,255,255,.018) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-tabs .tos-tws-tab[class~="dark:bg-white/10"]:hover {
  color: #f5eee3 !important;
  border-color: rgba(230,186,88,.16) !important;
  background: rgba(230,186,88,.07) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-tabs .tos-tws-tab[class~="dark:bg-white"] {
  color: #211500 !important;
  border-color: rgba(231,185,78,.28) !important;
  background: linear-gradient(145deg,#f2cf72,#d79d28) !important;
  box-shadow: 0 12px 28px rgba(0,0,0,.28), 0 0 24px rgba(211,157,39,.10), inset 0 1px rgba(255,255,255,.22) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-filter-row input,
.dark .tos-tws-premium-trigger {
  color: #eee8df !important;
  border-color: rgba(229,185,88,.12) !important;
  background: linear-gradient(180deg,#1a1a18,#141412) !important;
  box-shadow: inset 0 1px rgba(255,255,255,.018) !important;
}
.dark .tos-tws-premium-menu {
  border-color: rgba(232,188,89,.15) !important;
  background: rgba(18,18,16,.995) !important;
  box-shadow: 0 30px 70px rgba(0,0,0,.54), inset 0 1px rgba(255,255,255,.025) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-view-toggle {
  border-color: rgba(229,185,88,.10) !important;
  background: rgba(255,255,255,.03) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-bucket .mb-3 > .grid {
  border-color: rgba(229,185,88,.10);
  background: linear-gradient(145deg,#24231f,#171715) !important;
  color: #e5bc5e !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-bucket .space-y-2 > button {
  color: #eee7dd !important;
  border-color: rgba(229,185,88,.10) !important;
  background: linear-gradient(145deg,#1b1b19,#131312) !important;
  box-shadow: inset 0 1px rgba(255,255,255,.02) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-bucket .space-y-2 > button:hover {
  border-color: rgba(231,186,85,.20) !important;
  background: linear-gradient(145deg,#22211d,#171613) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-document-card::before {
  background: linear-gradient(90deg,transparent,rgba(225,176,68,.70),transparent);
  opacity: .48;
}
.dark .tos-tws-flagship-v1 .tos-tws-document-card > div:nth-child(2) {
  border-color: rgba(229,185,88,.07);
  background: rgba(255,255,255,.026) !important;
  box-shadow: inset 0 1px rgba(255,255,255,.014);
}
.dark .tos-tws-pagination {
  color: #aaa297 !important;
  border-color: rgba(229,185,88,.11) !important;
  background: linear-gradient(180deg,#151513,#0f0f0e) !important;
  box-shadow: 0 16px 38px rgba(0,0,0,.22) !important;
}
.dark .tos-tws-pagination__page { color: #f3ece2 !important; }

@media (max-width: 900px) {
  .tos-tws-flagship-v1 .tos-tws-hero { padding: 22px !important; }
  .tos-tws-flagship-v1 .tos-tws-hero h2 { font-size: 30px !important; }
  .tos-tws-flagship-v1 .tos-tws-document-card { min-height: 0; }
}

@media (prefers-reduced-motion: reduce) {
  .tos-tws-flagship-v1 .tos-tws-document-card,
  .tos-tws-flagship-v1 .tos-tws-tab,
  .tos-tws-flagship-v1 .tos-tws-bucket .space-y-2 > button {
    transition: none !important;
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

print("RUNNING=TOS_UXUI_SYSTEM_TWS_DASHBOARD_FLAGSHIP_V2_LUXURY_POLISH")
page_before = None
v2_created = False
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
    global page_before, v2_created
    try:
        if page_before is not None:
            PAGE.write_bytes(page_before)
    except Exception:
        pass
    try:
        if v2_created and V2_STYLE.exists():
            V2_STYLE.unlink()
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
    print("TWS_DASHBOARD_FLAGSHIP_V2_RUNTIME=NO")
    sys.exit(1)

if ROOT.resolve() == Path("/"):
    fail("unsafe ROOT")

for path in (FRONTEND, PAGE, V1_STYLE, V11_STYLE, LIVE_PARENT, *PRESERVE_FILES):
    if not path.exists():
        fail(f"required path missing: {path}")

if sha256(PAGE) != EXPECTED_PAGE_SHA256:
    fail(f"TwsDashboard.jsx V1.1 baseline mismatch: {sha256(PAGE)}")
if sha256(V1_STYLE) != EXPECTED_V1_STYLE_SHA256:
    fail(f"V1 stylesheet baseline mismatch: {sha256(V1_STYLE)}")
if sha256(V11_STYLE) != EXPECTED_V11_STYLE_SHA256:
    fail(f"V1.1 stylesheet baseline mismatch: {sha256(V11_STYLE)}")
if V2_STYLE.exists():
    fail(f"unexpected state: V2 stylesheet already exists: {sha256(V2_STYLE)}")

page_text = PAGE.read_text(encoding="utf-8")
if page_text.count(IMPORT_V11) != 1:
    fail(f"V1.1 import count mismatch: {page_text.count(IMPORT_V11)}")
if IMPORT_V2 in page_text:
    fail("unexpected state: V2 import already exists")

required_page_markers = (
    'const TWS_RESULT_PAGE_SIZE = 12;',
    'function TwsPremiumSelect',
    'className="tos-tws-hero-card overflow-hidden p-0"',
    'className="tos-tws-bucket p-4"',
    'tos-tws-document-card',
    'data-tws-results-pagination="v1"',
    'api.tws.list(filters)',
    'api.tws.create({ type, title:',
    'api.tws.duplicate(doc.id)',
    'api.tws.archive(doc.id)',
    'api.tws.restore(doc.id)',
    'api.tws.trash(doc.id)',
    'api.tws.favorites.list()',
    'limit: 60',
)
for marker in required_page_markers:
    if marker not in page_text:
        fail(f"required TWS source marker missing: {marker}")

for marker in (
    '--tos-tws-dashboard-flagship-v2-luxury-runtime: 1;',
    '.tos-tws-flagship-v1 .tos-tws-hero-card',
    '.tos-tws-flagship-v1 .tos-tws-stat',
    '.tos-tws-flagship-v1 .tos-tws-control-card',
    '.tos-tws-flagship-v1 .tos-tws-bucket',
    '.tos-tws-flagship-v1 .tos-tws-document-card',
    '.dark .tos-tws-flagship-v1 .tos-tws-document-card',
):
    if marker not in CSS:
        fail(f"V2 CSS marker missing before write: {marker}")

page_before = PAGE.read_bytes()
v1_before = sha256(V1_STYLE)
v11_before = sha256(V11_STYLE)
preserve_before = {str(path): sha256(path) for path in PRESERVE_FILES}

new_page_text = page_text.replace(IMPORT_V11, IMPORT_V11 + "\n" + IMPORT_V2, 1)
if new_page_text.count(IMPORT_V2) != 1:
    fail("V2 import transform failed")

try:
    PAGE.write_text(new_page_text, encoding="utf-8")
    V2_STYLE.write_text(CSS, encoding="utf-8")
    v2_created = True
except Exception as exc:
    if V2_STYLE.exists():
        v2_created = True
    fail(f"source write failed: {exc}")

if PAGE.read_text(encoding="utf-8").count(IMPORT_V2) != 1:
    fail("V2 import missing after write")
if sha256(V1_STYLE) != v1_before or sha256(V11_STYLE) != v11_before:
    fail("V1/V1.1 stylesheet changed unexpectedly")
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
    b'tos-tws-premium-select',
    b'data-tws-results-pagination',
    b'tos-tws-pagination__page',
)
for marker in built_markers:
    if tree_count(DIST, marker) < 1:
        fail(f"built output missing marker: {marker.decode(errors='ignore')}", build_result="FAIL")

if PAGE.read_text(encoding="utf-8").count(IMPORT_V2) != 1:
    fail("V2 import changed during build", build_result="FAIL")
if sha256(V1_STYLE) != v1_before or sha256(V11_STYLE) != v11_before:
    fail("V1/V1.1 styles changed during build", build_result="FAIL")
for path in PRESERVE_FILES:
    if sha256(path) != preserve_before[str(path)]:
        fail(f"out-of-scope source changed during build: {path}", build_result="FAIL")

ts = int(time.time())
candidate = LIVE_PARENT / f"build.tws-dashboard-flagship-v2-candidate-{ts}"
live_backup = LIVE_PARENT / f"build.tws-dashboard-flagship-v2-backup-{ts}"
live_failed = LIVE_PARENT / f"build.tws-dashboard-flagship-v2-failed-{ts}"

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

if PAGE.read_text(encoding="utf-8").count(IMPORT_V2) != 1:
    fail("V2 import changed after deploy", build_result="PASS", rollback_deploy=True)
if sha256(V1_STYLE) != v1_before or sha256(V11_STYLE) != v11_before:
    fail("V1/V1.1 styles changed after deploy", build_result="PASS", rollback_deploy=True)
for path in PRESERVE_FILES:
    if sha256(path) != preserve_before[str(path)]:
        fail(f"out-of-scope source changed after deploy: {path}", build_result="PASS", rollback_deploy=True)

print("PASS/FAIL=PASS")
print("BUILD_RESULT=PASS")
print("LIVE_DEPLOY=PASS")
print("TWS_DASHBOARD_FLAGSHIP_V2_RUNTIME=YES")
print("TWS_V2_SCOPE=LUXURY_VISUAL_POLISH_ONLY")
print("TWS_HERO=LUXURY_FLAGSHIP")
print("TWS_KPI_SYSTEM=EXECUTIVE_LUXURY")
print("TWS_COMMAND_RAIL=PREMIUM_REFINED")
print("TWS_BUCKETS=LAYERED_EXECUTIVE")
print("TWS_DOCUMENT_CARDS=LUXURY_PRODUCT_CARDS")
print("TWS_LIGHT_MODE=IVORY_CHAMPAGNE_LUXURY")
print("TWS_DARK_MODE=OBSIDIAN_CHAMPAGNE_LUXURY")
print("TWS_PROJECT_FILTER=PREMIUM_CUSTOM_PRESERVED")
print("TWS_TRASH_FILTER=PREMIUM_CUSTOM_PRESERVED")
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
print(f"LIVE_BACKUP={live_backup if live_backup.exists() else 'NONE'}")
print("STATUS=READY")
