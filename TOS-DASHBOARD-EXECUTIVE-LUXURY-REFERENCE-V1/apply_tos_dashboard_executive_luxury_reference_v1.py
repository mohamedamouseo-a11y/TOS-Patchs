from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
PAGE = FRONTEND / "src/pages/Dashboard.jsx"
BASE_STYLE = FRONTEND / "src/styles/dashboard-github-reference.css"
LUX_STYLE = FRONTEND / "src/styles/dashboard-executive-luxury-v1.css"
HERO_ASSET = FRONTEND / "public/tos-dashboard-luxury-hero.svg"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

IMPORT_BASE = 'import "../styles/dashboard-github-reference.css";'
IMPORT_LUX = 'import "../styles/dashboard-executive-luxury-v1.css";'
ROOT_MARKER = 'data-dashboard-luxury-v1="true"'
RUNTIME_MARKER = '--tos-dashboard-executive-luxury-v1-runtime: 1;'

CSS = r'''/* TOS Dashboard Executive Luxury Reference V1 */
:root {
  --tos-dashboard-executive-luxury-v1-runtime: 1;
  --tdl-gold-1: #fff0b9;
  --tdl-gold-2: #e9c35c;
  --tdl-gold-3: #b77912;
  --tdl-ink: #1d160d;
  --tdl-muted: #786a57;
  --tdl-ivory: #fffdf8;
  --tdl-pearl: #fbf5e9;
  --tdl-line: rgba(177, 117, 16, .19);
  --tdl-shadow: 0 16px 44px rgba(75, 48, 10, .075);
}

html:not(.dark) body #root .tos-dashboard-page[data-dashboard-luxury-v1="true"] {
  max-width: 1640px !important;
  gap: 18px;
  background:
    radial-gradient(circle at 10% 2%, rgba(222, 179, 82, .10), transparent 24%),
    radial-gradient(circle at 96% 20%, rgba(218, 184, 115, .08), transparent 22%);
}

html:not(.dark) body #root .tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-hero {
  position: relative;
  isolation: isolate;
  min-height: 245px;
  overflow: hidden;
  border: 1px solid rgba(181, 119, 14, .28) !important;
  border-radius: 26px !important;
  background:
    linear-gradient(90deg, rgba(255,253,248,.98) 0%, rgba(255,250,238,.96) 38%, rgba(255,248,228,.52) 61%, rgba(34,23,9,.08) 100%),
    url("/tos-dashboard-luxury-hero.svg") center right / cover no-repeat !important;
  box-shadow:
    0 24px 64px rgba(73, 46, 8, .12),
    inset 0 1px 0 rgba(255,255,255,.96) !important;
}

.tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-hero::after {
  content: "";
  position: absolute;
  inset: 0;
  z-index: -1;
  pointer-events: none;
  background:
    linear-gradient(110deg, transparent 0 35%, rgba(255,255,255,.44) 47%, transparent 57%),
    radial-gradient(circle at 14% 0%, rgba(247,215,139,.20), transparent 26%);
}

.tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-hero-copy {
  position: relative;
  z-index: 2;
  width: min(62%, 760px);
  padding: 4px 0;
}

.tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-hero-copy h2 {
  font-size: clamp(2rem, 3vw, 3.35rem) !important;
  line-height: 1.02 !important;
  letter-spacing: -.055em !important;
  color: var(--tdl-ink) !important;
}

.tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-hero-copy > p {
  max-width: 670px;
  color: #6f604c !important;
}

.tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-hero-signature {
  position: absolute;
  inset-inline-end: 32px;
  top: 34px;
  z-index: 2;
  display: grid;
  width: 210px;
  place-items: center;
  gap: 7px;
  padding: 20px 18px;
  border: 1px solid rgba(255, 226, 158, .25);
  border-radius: 22px;
  background: linear-gradient(145deg, rgba(44,29,12,.78), rgba(19,14,9,.60));
  color: #fff8e7;
  text-align: center;
  box-shadow: 0 20px 42px rgba(38,22,4,.20), inset 0 1px rgba(255,255,255,.12);
  backdrop-filter: blur(12px);
}

.tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-hero-signature > div:first-child {
  display: grid;
  width: 60px;
  height: 60px;
  place-items: center;
  border-radius: 18px;
  background: linear-gradient(145deg, #fff2bd, #d7a536 68%, #9b640a);
  box-shadow: 0 12px 28px rgba(0,0,0,.23), inset 0 1px rgba(255,255,255,.72);
}

.tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-hero-signature strong {
  font-size: 1.08rem;
  letter-spacing: .16em;
}

.tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-hero-signature small {
  color: rgba(255,245,219,.72);
  font-size: 9px;
  font-weight: 800;
  letter-spacing: .18em;
  text-transform: uppercase;
}

.tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-hero-range {
  width: min(100%, 390px);
  margin-top: 18px;
}

html:not(.dark) body #root .tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-hero .tos-dashboard-date-filter {
  padding: 10px 12px !important;
  border: 1px solid rgba(166, 107, 11, .20) !important;
  border-radius: 16px !important;
  background: rgba(255,253,248,.88) !important;
  box-shadow: 0 12px 30px rgba(67, 41, 4, .10), inset 0 1px rgba(255,255,255,.96) !important;
  backdrop-filter: blur(12px);
}

.tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-hero .tos-dashboard-date-filter > div {
  gap: 10px !important;
}

.tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-hero .tos-dashboard-date-filter > div > div:first-child > span {
  width: 34px !important;
  height: 34px !important;
}

.tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-hero .tos-dashboard-date-filter button {
  height: 36px !important;
  background: linear-gradient(180deg,#fffefa,#f5e7c7) !important;
  border-color: rgba(168,110,15,.18) !important;
  box-shadow: inset 0 1px rgba(255,255,255,.9);
}

html:not(.dark) body #root .tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-metric {
  position: relative;
  isolation: isolate;
  min-height: 132px;
  overflow: hidden;
  padding: 17px !important;
  border: 1px solid var(--tdl-line) !important;
  border-radius: 20px !important;
  background:
    radial-gradient(ellipse at 92% 110%, rgba(224,184,94,.16), transparent 44%),
    linear-gradient(155deg,#fffefa 0%,#fffaf1 62%,#f8eedb 100%) !important;
  box-shadow: var(--tdl-shadow), inset 0 1px rgba(255,255,255,.96) !important;
  transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
}

html:not(.dark) body #root .tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-metric::after {
  content: "";
  position: absolute;
  z-index: -1;
  width: 122px;
  height: 62px;
  inset-inline-end: -12px;
  bottom: -12px;
  opacity: .55;
  border-radius: 60% 0 0 0;
  background:
    radial-gradient(ellipse at bottom, rgba(214,164,58,.28), transparent 58%),
    linear-gradient(150deg, transparent 30%, rgba(235,205,142,.30) 31% 48%, transparent 49%);
}

html:not(.dark) body #root .tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-metric:hover {
  transform: translateY(-3px);
  border-color: rgba(184,121,14,.34) !important;
  box-shadow: 0 22px 48px rgba(78,48,5,.12), inset 0 1px rgba(255,255,255,1) !important;
}

.tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-metric > div > span:first-child {
  border: 1px solid rgba(185,124,20,.11);
  box-shadow: 0 8px 18px rgba(93,58,5,.06), inset 0 1px rgba(255,255,255,.72);
}

.tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-metric > div > span:last-child {
  font-size: 2.05rem !important;
}

html:not(.dark) body #root .tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-dark-card {
  position: relative;
  overflow: hidden;
  border: 1px solid var(--tdl-line) !important;
  border-radius: 22px !important;
  background:
    radial-gradient(circle at 100% 0%, rgba(232,198,125,.09), transparent 27%),
    linear-gradient(180deg,#fffefa 0%,#fbf6ec 100%) !important;
  box-shadow: 0 15px 38px rgba(73,44,4,.065), inset 0 1px rgba(255,255,255,.96) !important;
}

.tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-progress-card {
  min-height: 330px;
}

.tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-progress-card [style*="conic-gradient"] {
  width: 176px !important;
  height: 176px !important;
  box-shadow: 0 18px 36px rgba(170,105,5,.11);
}

.tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-quick-card > div:last-child {
  grid-template-columns: repeat(2, minmax(0,1fr));
}

html:not(.dark) body #root .tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-quick-card button.group {
  min-height: 78px;
  border: 1px solid rgba(174,114,15,.17) !important;
  background: linear-gradient(180deg,#fffefa,#f8efdd) !important;
  box-shadow: 0 8px 20px rgba(75,46,4,.04), inset 0 1px rgba(255,255,255,.94) !important;
}

html:not(.dark) body #root .tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-quick-card button.group:hover {
  background: linear-gradient(180deg,#fffdf6,#f4e2b9) !important;
  border-color: rgba(181,119,15,.32) !important;
  box-shadow: 0 14px 28px rgba(80,49,4,.09), inset 0 1px rgba(255,255,255,.96) !important;
}

html:not(.dark) body #root .tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-projects-card [class*="border-zinc-200/60"],
html:not(.dark) body #root .tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-activity-card [class*="border-zinc-100"],
html:not(.dark) body #root .tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-files-card [class*="border-zinc-200/60"] {
  border-color: rgba(180,119,17,.14) !important;
  background: linear-gradient(180deg,#fffdfa,#f8f0e2) !important;
  box-shadow: inset 0 1px rgba(255,255,255,.94) !important;
}

.tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-projects-card [class*="bg-zinc-950"] {
  background: linear-gradient(145deg,#4a3a27,#1e170e) !important;
  border: 1px solid rgba(218,172,74,.28);
  box-shadow: 0 8px 18px rgba(42,26,7,.16);
}

.tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-files-card > div:last-child > div {
  min-height: 86px;
}

.tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-files-card > div:last-child > div:hover {
  transform: translateY(-2px);
}

html:not(.dark) body #root .tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-tws .tos-premium-card {
  border-color: rgba(180,119,17,.18) !important;
  background:
    radial-gradient(circle at 96% 0%, rgba(228,190,106,.11), transparent 30%),
    linear-gradient(180deg,#fffefa,#fbf5e9) !important;
  box-shadow: 0 16px 38px rgba(73,44,4,.065), inset 0 1px rgba(255,255,255,.96) !important;
}

html:not(.dark) body #root .tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-tws .tos-premium-card button {
  border-color: rgba(176,116,17,.14) !important;
  background: linear-gradient(180deg,#fffefa,#f8efde) !important;
}

.tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-date-filter div[class*="absolute"][class*="shadow-2xl"] {
  border-color: rgba(177,116,16,.18) !important;
  background: #fffdf8 !important;
  box-shadow: 0 24px 60px rgba(64,38,3,.16) !important;
}

/* Dark: executive obsidian + antique gold, preserving the same information hierarchy. */
html.dark body #root .tos-dashboard-page[data-dashboard-luxury-v1="true"] {
  --tdl-ink: #f7f2e7;
  --tdl-muted: #b8ad9d;
  background:
    radial-gradient(circle at 9% 1%, rgba(197,139,33,.10), transparent 25%),
    radial-gradient(circle at 95% 15%, rgba(132,93,26,.08), transparent 24%);
}

html.dark body #root .tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-hero {
  border-color: rgba(215,161,51,.27) !important;
  background:
    linear-gradient(90deg, rgba(13,14,14,.98) 0%, rgba(15,15,14,.93) 39%, rgba(16,15,12,.58) 67%, rgba(8,8,8,.16) 100%),
    url("/tos-dashboard-luxury-hero.svg") center right / cover no-repeat !important;
  box-shadow: 0 24px 58px rgba(0,0,0,.32), inset 0 1px rgba(255,255,255,.035) !important;
}

html.dark body #root .tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-hero-copy h2 {
  color: #fff8e9 !important;
}

html.dark body #root .tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-hero-copy > p {
  color: #c5b9a8 !important;
}

html.dark body #root .tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-hero .tos-dashboard-date-filter {
  border-color: rgba(216,162,52,.20) !important;
  background: rgba(22,22,20,.84) !important;
  box-shadow: 0 16px 34px rgba(0,0,0,.26), inset 0 1px rgba(255,255,255,.035) !important;
}

html.dark body #root .tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-metric,
html.dark body #root .tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-dark-card,
html.dark body #root .tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-tws .tos-premium-card {
  border-color: rgba(214,160,50,.16) !important;
  background:
    radial-gradient(circle at 96% 0%, rgba(201,143,32,.07), transparent 30%),
    linear-gradient(180deg,#171a1c 0%,#111416 100%) !important;
  box-shadow: 0 18px 42px rgba(0,0,0,.26), inset 0 1px rgba(255,255,255,.03) !important;
}

html.dark body #root .tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-quick-card button.group,
html.dark body #root .tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-projects-card [class*="border-zinc-200/60"],
html.dark body #root .tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-activity-card [class*="border-zinc-100"],
html.dark body #root .tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-files-card [class*="border-zinc-200/60"],
html.dark body #root .tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-tws .tos-premium-card button {
  border-color: rgba(214,160,50,.12) !important;
  background: linear-gradient(180deg,#202528,#191d1f) !important;
  color: #eee8dc !important;
}

@media (max-width: 1100px) {
  .tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-hero-copy {
    width: min(70%, 720px);
  }
  .tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-hero-signature {
    width: 180px;
    inset-inline-end: 22px;
  }
}

@media (max-width: 760px) {
  html:not(.dark) body #root .tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-hero,
  html.dark body #root .tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-hero {
    min-height: 0;
    background-position: 70% center !important;
  }
  .tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-hero-copy {
    width: 100%;
  }
  .tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-hero-signature {
    display: none;
  }
  .tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-hero-range {
    width: 100%;
  }
  .tos-dashboard-page[data-dashboard-luxury-v1="true"] .tos-dashboard-quick-card > div:last-child {
    grid-template-columns: 1fr;
  }
}

@media (prefers-reduced-motion: reduce) {
  .tos-dashboard-page[data-dashboard-luxury-v1="true"] *,
  .tos-dashboard-page[data-dashboard-luxury-v1="true"] *::before,
  .tos-dashboard-page[data-dashboard-luxury-v1="true"] *::after {
    transition-duration: .01ms !important;
    animation-duration: .01ms !important;
  }
}
'''

SVG = r'''<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="520" viewBox="0 0 1600 520">
<defs>
  <linearGradient id="sky" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#fffaf0"/>
    <stop offset=".46" stop-color="#f8e7be"/>
    <stop offset="1" stop-color="#9a6727"/>
  </linearGradient>
  <linearGradient id="glass" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#fffdf7" stop-opacity=".84"/>
    <stop offset=".55" stop-color="#dcb86f" stop-opacity=".40"/>
    <stop offset="1" stop-color="#3b2a1b" stop-opacity=".46"/>
  </linearGradient>
  <linearGradient id="gold" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#fff0ae"/>
    <stop offset=".48" stop-color="#d69d2a"/>
    <stop offset="1" stop-color="#73470b"/>
  </linearGradient>
  <filter id="blur"><feGaussianBlur stdDeviation="10"/></filter>
</defs>
<rect width="1600" height="520" fill="url(#sky)"/>
<circle cx="1040" cy="126" r="150" fill="#fff7dc" opacity=".46" filter="url(#blur)"/>
<path d="M780 0h820v520H690c170-80 215-180 244-291C960 132 986 58 1090 0z" fill="url(#glass)"/>
<g opacity=".66">
  <rect x="1025" y="48" width="8" height="368" fill="#5d3c19"/>
  <rect x="1110" y="26" width="6" height="386" fill="#6d471c"/>
  <rect x="1186" y="10" width="5" height="398" fill="#6d471c"/>
  <rect x="1260" y="0" width="5" height="410" fill="#5c3b17"/>
  <rect x="1332" y="0" width="5" height="414" fill="#513414"/>
</g>
<path d="M880 70c210 46 430 27 720-38v38c-292 79-510 92-720 52z" fill="url(#gold)" opacity=".88"/>
<path d="M925 335c210-82 430-78 675-22v86c-258-74-496-65-690 44z" fill="#fffaf0" opacity=".80"/>
<path d="M914 344c208-84 441-81 686-25" fill="none" stroke="url(#gold)" stroke-width="7" opacity=".82"/>
<path d="M1180 318c38-80 78-122 118-155" fill="none" stroke="#7f551f" stroke-width="8" stroke-linecap="round"/>
<path d="M1299 164c-20-44-45-79-77-104M1299 164c17-47 49-83 94-105M1297 166c-44-24-87-35-133-31M1298 166c50-8 92-2 132 21M1297 166c-15-59-6-108 12-153" fill="none" stroke="#6e4a1b" stroke-width="7" stroke-linecap="round"/>
<g fill="#46301b" opacity=".45">
  <rect x="910" y="286" width="28" height="120" rx="4"/>
  <rect x="944" y="260" width="35" height="146" rx="4"/>
  <rect x="986" y="304" width="25" height="102" rx="4"/>
  <rect x="1020" y="245" width="44" height="161" rx="4"/>
</g>
<path d="M1050 406h550" stroke="#f1d88b" stroke-width="3" opacity=".65"/>
<path d="M1412 92c24 21 50 46 78 76" stroke="#f5d883" stroke-width="3" opacity=".55"/>
</svg>'''

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

page_before = None
style_before = None
asset_before = None
style_existed = False
asset_existed = False
live_backup = None
live_failed = None

def restore_source():
    try:
        if page_before is not None:
            PAGE.write_bytes(page_before)
        if style_existed:
            LUX_STYLE.write_bytes(style_before)
        elif LUX_STYLE.exists():
            LUX_STYLE.unlink()
        if asset_existed:
            HERO_ASSET.write_bytes(asset_before)
        elif HERO_ASSET.exists():
            HERO_ASSET.unlink()
    except Exception:
        pass

def rollback_live():
    try:
        if live_backup and live_backup.exists():
            if LIVE.exists():
                if live_failed and not live_failed.exists():
                    LIVE.rename(live_failed)
                else:
                    shutil.rmtree(LIVE)
            live_backup.rename(LIVE)
    except Exception:
        pass

def fail(msg, build="FAIL_OR_SKIPPED", rollback_deploy=False):
    if rollback_deploy:
        rollback_live()
    restore_source()
    print("PATCH=TOS-DASHBOARD-EXECUTIVE-LUXURY-REFERENCE-V1")
    print("PASS/FAIL=FAIL")
    print("BUILD=" + build)
    print("DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("ERROR=" + str(msg))
    sys.exit(1)

if ROOT.resolve() == Path("/"):
    fail("unsafe ROOT")
for p in (FRONTEND, PAGE, BASE_STYLE, LIVE_PARENT):
    if not p.exists():
        fail(f"required path missing: {p}")

page_before = PAGE.read_bytes()
style_existed = LUX_STYLE.exists()
asset_existed = HERO_ASSET.exists()
if style_existed:
    style_before = LUX_STYLE.read_bytes()
if asset_existed:
    asset_before = HERO_ASSET.read_bytes()

page = PAGE.read_text(encoding="utf-8")

required = [
    IMPORT_BASE,
    'export function Dashboard({ projects = [], activeProject, user, files = [], clients = [], onNavigate })',
    'className="tos-dashboard-page mx-auto w-full max-w-[1560px]',
    '<QuickAction icon={Plus}',
    '<TwsRecentFilesWidget dashboardSurface />',
]
for marker in required:
    if marker not in page:
        fail(f"required Dashboard baseline marker missing: {marker}")

if ROOT_MARKER not in page:
    if IMPORT_LUX not in page:
        page = page.replace(IMPORT_BASE, IMPORT_BASE + "\n" + IMPORT_LUX, 1)

    if "  MessageCircle,\n" not in page:
        page = page.replace("  FolderOpen,\n  Plus,", "  FolderOpen,\n  MessageCircle,\n  Plus,", 1)

    page = page.replace(
        '<div className="relative z-20 rounded-2xl border border-zinc-200/70 bg-white/90 px-4 py-3 shadow-sm dark:border-white/10 dark:bg-white/[0.035]">',
        '<div className="tos-dashboard-date-filter relative z-20 rounded-2xl border border-zinc-200/70 bg-white/90 px-4 py-3 shadow-sm dark:border-white/10 dark:bg-white/[0.035]">',
        1
    )

    page = page.replace(
        '<div className="rounded-2xl border border-zinc-200/70 bg-white/95 p-4 shadow-sm dark:border-white/10 dark:bg-white/[0.035]">',
        '<div className="tos-dashboard-metric rounded-2xl border border-zinc-200/70 bg-white/95 p-4 shadow-sm dark:border-white/10 dark:bg-white/[0.035]">',
        1
    )

    page = page.replace(
        '<div className="tos-dashboard-page mx-auto w-full max-w-[1560px] space-y-4 p-4 sm:p-5 lg:space-y-5 lg:p-6">',
        '<div data-dashboard-luxury-v1="true" className="tos-dashboard-page mx-auto w-full max-w-[1560px] space-y-4 p-4 sm:p-5 lg:space-y-5 lg:p-6">',
        1
    )

    hero_start = page.find('      <section className="relative overflow-hidden rounded-[24px]')
    next_grid = page.find('      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">', hero_start)
    if hero_start < 0 or next_grid < 0:
        fail("hero/date block boundaries not found")

    hero = r'''      <section className="tos-dashboard-hero px-5 py-5 sm:px-7 sm:py-7 lg:px-8">
        <div className="tos-dashboard-hero-copy">
          <div className="flex flex-wrap items-center gap-2">
            <Badge tone="success"><ShieldCheck size={13} /> {ui("بيانات مباشرة", "Live data")}</Badge>
            <span className="text-[11px] font-black uppercase tracking-[0.18em] text-zinc-500">{ui("نظرة تنفيذية", "Executive overview")}</span>
          </div>
          <h2 className="mt-4 font-black">{tr.welcome} {firstName}</h2>
          <p className="mt-3 text-sm font-semibold leading-6">
            {ui("حوّل العمل اليومي إلى صورة تنفيذية واضحة للمشاريع والعملاء والملفات والنشاط الأخير.", "Turn daily work into a clear executive view of projects, clients, files, and recent activity.")}
          </p>
          <div className="tos-dashboard-hero-range">
            <DateFilterBar
              preset={datePreset}
              setPreset={setDatePreset}
              customStart={customStart}
              setCustomStart={setCustomStart}
              customEnd={customEnd}
              setCustomEnd={setCustomEnd}
              resultCount={filteredResultCount}
              rangeLabel={activeRange.label}
              invalidRange={activeRange.isInvalid}
            />
          </div>
        </div>

        <div className="tos-dashboard-hero-signature">
          <div><LogoMark /></div>
          <strong>TOS</strong>
          <small>{ui("الأفراد · المشاريع · التقدم", "People · Projects · Progress")}</small>
          <div className="mt-2 w-full border-t border-white/10 pt-3">
            <div className="flex items-center justify-center gap-2 text-[10px] font-black">
              <UserRound size={13} />
              <span>{roleLabel(user.role, isEnglish)}</span>
            </div>
          </div>
        </div>
      </section>

'''
    page = page[:hero_start] + hero + page[next_grid:]

    quick_old = r'''          <div className="grid gap-2.5">
            <QuickAction icon={Plus} title={ui("إضافة مشروع", "Add project")} description={ui("فتح نموذج مشروع جديد", "Open new project form")} onClick={() => onNavigate?.("projects:create")} />
            <QuickAction icon={UploadCloud} title={ui("رفع ملف", "Upload file")} description={ui("الانتقال إلى رفع الملفات", "Go to file upload")} onClick={() => onNavigate?.("files:upload")} />
            <QuickAction icon={UserPlus} title={ui("دعوة مستخدم", "Invite user")} description={ui("فتح نموذج الدعوة", "Open invitation form")} onClick={() => onNavigate?.("team:invite")} />
          </div>'''
    quick_new = r'''          <div className="grid gap-2.5 sm:grid-cols-2">
            <QuickAction icon={Plus} title={ui("إضافة مشروع", "Add project")} description={ui("فتح نموذج مشروع جديد", "Open new project form")} onClick={() => onNavigate?.("projects:create")} />
            <QuickAction icon={UploadCloud} title={ui("رفع ملف", "Upload file")} description={ui("الانتقال إلى رفع الملفات", "Go to file upload")} onClick={() => onNavigate?.("files:upload")} />
            <QuickAction icon={UserPlus} title={ui("دعوة مستخدم", "Invite user")} description={ui("فتح نموذج الدعوة", "Open invitation form")} onClick={() => onNavigate?.("team:invite")} />
            <QuickAction icon={MessageCircle} title={ui("فتح TCS", "Open TCS")} description={ui("محادثات الفريق", "Team chat")} onClick={() => onNavigate?.("chat")} />
          </div>'''
    if quick_old not in page:
        fail("quick actions baseline block missing")
    page = page.replace(quick_old, quick_new, 1)

    card_base = 'section className="tos-dashboard-dark-card rounded-[22px] border border-zinc-200/70 bg-white/95 p-5 shadow-sm dark:border-white/10 dark:bg-white/[0.035]"'
    card_classes = [
        "tos-dashboard-progress-card",
        "tos-dashboard-quick-card",
        "tos-dashboard-projects-card",
        "tos-dashboard-activity-card",
        "tos-dashboard-files-card",
    ]
    for extra in card_classes:
        if card_base not in page:
            fail(f"dashboard card baseline missing before {extra}")
        page = page.replace(card_base, f'section className="tos-dashboard-dark-card {extra} rounded-[22px] border border-zinc-200/70 bg-white/95 p-5 shadow-sm dark:border-white/10 dark:bg-white/[0.035]"', 1)

    page = page.replace(
        'className="grid gap-2.5 md:grid-cols-2 xl:grid-cols-3"',
        'className="grid gap-2.5 sm:grid-cols-2 xl:grid-cols-5"',
        1
    )
    page = page.replace('filteredFiles.slice(0, 6).map', 'filteredFiles.slice(0, 5).map', 1)
    page = page.replace('md:col-span-2 xl:col-span-3', 'sm:col-span-2 xl:col-span-5', 1)

try:
    PAGE.write_text(page, encoding="utf-8")
    LUX_STYLE.write_text(CSS, encoding="utf-8")
    HERO_ASSET.parent.mkdir(parents=True, exist_ok=True)
    HERO_ASSET.write_text(SVG, encoding="utf-8")
except Exception as exc:
    fail(f"source write failed: {exc}")

page_after = PAGE.read_text(encoding="utf-8")
for marker in (
    ROOT_MARKER,
    IMPORT_LUX,
    "tos-dashboard-hero",
    "tos-dashboard-hero-signature",
    "tos-dashboard-metric",
    "tos-dashboard-quick-card",
    'title={ui("فتح TCS", "Open TCS")}',
):
    if marker not in page_after:
        fail(f"post-write Dashboard marker missing: {marker}")

if RUNTIME_MARKER not in LUX_STYLE.read_text(encoding="utf-8"):
    fail("luxury stylesheet runtime marker missing")
if "<svg" not in HERO_ASSET.read_text(encoding="utf-8"):
    fail("hero SVG marker missing")

build = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, text=True, capture_output=True)
if build.returncode != 0:
    print(build.stdout[-9000:])
    print(build.stderr[-9000:])
    fail("frontend build failed", build="FAIL")

if not DIST.exists() or not (DIST / "index.html").exists():
    fail("dist/index.html missing after build", build="FAIL")

for marker in (
    b'--tos-dashboard-executive-luxury-v1-runtime',
    b'data-dashboard-luxury-v1',
    b'tos-dashboard-hero-signature',
    b'tos-dashboard-quick-card',
):
    if tree_count(DIST, marker) < 1:
        fail(f"built output missing marker: {marker.decode()}", build="FAIL")

ts = int(time.time())
candidate = LIVE_PARENT / f"build.dashboard-executive-luxury-v1-candidate-{ts}"
live_backup = LIVE_PARENT / f"build.dashboard-executive-luxury-v1-backup-{ts}"
live_failed = LIVE_PARENT / f"build.dashboard-executive-luxury-v1-failed-{ts}"

try:
    for path in (candidate, live_backup, live_failed):
        if path.exists():
            raise RuntimeError(f"deployment path already exists: {path}")
    shutil.copytree(DIST, candidate)
    if LIVE.exists():
        LIVE.rename(live_backup)
    candidate.rename(LIVE)
except Exception as exc:
    rollback_live()
    fail(f"atomic deploy failed: {exc}", build="PASS")

try:
    for marker in (
        b'--tos-dashboard-executive-luxury-v1-runtime',
        b'data-dashboard-luxury-v1',
        b'tos-dashboard-hero-signature',
    ):
        if tree_count(LIVE, marker) < 1:
            raise RuntimeError(f"live marker missing: {marker.decode()}")
    if not (LIVE / "tos-dashboard-luxury-hero.svg").exists():
        raise RuntimeError("live hero asset missing")
except Exception as exc:
    fail(f"live verification failed: {exc}", build="PASS", rollback_deploy=True)

http_code = "SKIPPED"
try:
    check = subprocess.run(
        ["curl", "-k", "-L", "-sS", "--max-time", "15", "-o", "/dev/null", "-w", "%{http_code}", "https://tos.tamiyouz.com/"],
        text=True, capture_output=True
    )
    http_code = (check.stdout or "").strip() or "000"
    if check.returncode != 0 or not http_code.startswith(("2", "3")):
        raise RuntimeError(f"public HTTP check failed: rc={check.returncode} http={http_code}")
except Exception as exc:
    fail(str(exc), build="PASS", rollback_deploy=True)

print("PATCH=TOS-DASHBOARD-EXECUTIVE-LUXURY-REFERENCE-V1")
print("PASS/FAIL=PASS")
print("BUILD=PASS")
print("DEPLOY=ATOMIC")
print(f"HTTP={http_code}")
print("DASHBOARD_REFERENCE=EXECUTIVE_LUXURY")
print("HERO=ARCHITECTURAL_GOLD")
print("DATE_FILTER=HERO_INTEGRATED")
print("KPI_CARDS=LUXURY_DEPTH")
print("QUICK_ACTIONS=2X2_WITH_TCS")
print("LATEST_FILES=5_COLUMN_DESKTOP")
print("LIGHT_MODE=IVORY_GOLD")
print("DARK_MODE=OBSIDIAN_GOLD")
print("BACKEND_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print(f"DASHBOARD_SHA256={sha256(PAGE)}")
print(f"STYLE_SHA256={sha256(LUX_STYLE)}")
print(f"HERO_ASSET_SHA256={sha256(HERO_ASSET)}")
print(f"LIVE_BACKUP={live_backup}")
print("ERROR=NONE")
