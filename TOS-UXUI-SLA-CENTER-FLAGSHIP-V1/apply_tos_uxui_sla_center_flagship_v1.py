from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
PAGE = FRONTEND / "src/pages/SlaCenterPage.jsx"
STYLE = FRONTEND / "src/pages/slaCenterFlagshipV1.css"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_PAGE_SHA256 = "ff5abf65cee7dbcc0d010a00b811a0eb507d84817bb37e8ffad3b39fae556724"
RUNTIME_MARKER = "--tos-sla-center-flagship-v1-runtime"
IMPORT_ANCHOR = 'import { usePreferences } from "../contexts/PreferencesContext";'
STYLE_IMPORT = 'import "./slaCenterFlagshipV1.css";'

PRESERVE_FILES = [
    FRONTEND / "src/pages/SlaInboxPage.jsx",
    FRONTEND / "src/pages/slaInboxFlagshipV1.css",
    FRONTEND / "src/pages/slaInboxFlagshipV1_1DarkContrast.css",
    FRONTEND / "src/components/RamzyAssistant.jsx",
    FRONTEND / "src/components/TcsFloatingLauncher.jsx",
    FRONTEND / "src/components/TcsDesktopWindow.jsx",
]

CSS = r''':root {
  --tos-sla-center-flagship-v1-runtime: 1;
}

.tos-sla-center-flagship-v1 {
  --slac-gold: #c9901d;
  --slac-gold-strong: #9f6808;
  --slac-ink: #17130d;
  --slac-muted: #746b5e;
  --slac-line: rgba(201,144,29,.16);
  --slac-card: rgba(255,255,255,.97);
  --slac-soft: #fffaf0;
  position: relative;
}

.tos-sla-center-frame { max-width: 1480px !important; }

.tos-sla-center-hero {
  position: relative;
  overflow: hidden;
  min-height: 150px;
  padding: 26px 28px;
  border: 1px solid rgba(201,144,29,.18);
  border-radius: 30px;
  background:
    radial-gradient(circle at 86% 12%, rgba(216,162,50,.12), transparent 30%),
    linear-gradient(145deg, rgba(255,255,255,.995), rgba(255,248,234,.96));
  box-shadow: 0 22px 58px rgba(70,48,13,.07), inset 0 1px 0 rgba(255,255,255,.94);
}

.tos-sla-center-hero::after {
  content: "";
  position: absolute;
  inset-block: 0;
  inset-inline-end: 4%;
  width: 34%;
  pointer-events: none;
  opacity: .6;
  background: repeating-linear-gradient(105deg, transparent 0 24px, rgba(201,144,29,.11) 25px 27px, transparent 28px 44px);
}

.tos-sla-center-hero > * { position: relative; z-index: 1; }
.tos-sla-center-hero h1 { font-size: clamp(28px, 3vw, 40px) !important; letter-spacing: -.035em; }
.tos-sla-center-hero > div:last-child { align-self: center; }

.tos-sla-center-inbox-button,
.tos-sla-center-refresh-button {
  min-height: 44px;
  border-radius: 15px !important;
  border-color: rgba(201,144,29,.20) !important;
  background: rgba(255,255,255,.88);
  box-shadow: 0 8px 22px rgba(56,39,11,.055);
  transition: transform 150ms ease, border-color 150ms ease, box-shadow 150ms ease, background 150ms ease;
}
.tos-sla-center-inbox-button:hover,
.tos-sla-center-refresh-button:hover { transform: translateY(-1px); border-color: rgba(201,144,29,.34) !important; }

.tos-sla-center-kpi-grid { gap: 12px !important; }
.tos-sla-center-kpi {
  position: relative;
  overflow: hidden;
  min-height: 124px;
  border: 1px solid rgba(201,144,29,.13) !important;
  border-radius: 24px !important;
  padding: 18px !important;
  background: linear-gradient(150deg, rgba(255,255,255,.995), rgba(255,250,241,.93)) !important;
  box-shadow: 0 14px 34px rgba(55,40,13,.055) !important;
}
.tos-sla-center-kpi::before {
  content: "";
  position: absolute;
  inset-block: 0;
  inset-inline-start: 0;
  width: 3px;
  background: var(--slac-kpi, #c9901d);
}
.tos-sla-center-kpi:nth-child(1) { --slac-kpi: #2ca77c; }
.tos-sla-center-kpi:nth-child(2) { --slac-kpi: #ef6363; }
.tos-sla-center-kpi:nth-child(3) { --slac-kpi: #e3a329; }
.tos-sla-center-kpi:nth-child(4) { --slac-kpi: #c9901d; }
.tos-sla-center-kpi > div { position: relative; z-index: 1; }
.tos-sla-center-kpi > div > div:last-child {
  border: 1px solid color-mix(in srgb, var(--slac-kpi) 22%, transparent);
  color: var(--slac-kpi) !important;
  background: color-mix(in srgb, var(--slac-kpi) 8%, white) !important;
  box-shadow: 0 8px 20px color-mix(in srgb, var(--slac-kpi) 9%, transparent);
}

.tos-sla-center-drilldown,
.tos-sla-center-aging {
  overflow: hidden;
  border: 1px solid rgba(201,144,29,.14) !important;
  border-radius: 28px !important;
  background: rgba(255,255,255,.97) !important;
  box-shadow: 0 18px 46px rgba(50,36,10,.055);
}

.tos-sla-center-drilldown-header,
.tos-sla-center-aging-header {
  padding: 18px 20px !important;
  background: linear-gradient(180deg, rgba(255,252,246,.96), rgba(255,255,255,.94));
}
.tos-sla-center-drilldown-header h2,
.tos-sla-center-aging-header h2 { font-size: 16px; }

.tos-sla-center-dimensions {
  padding: 5px;
  border: 1px solid rgba(201,144,29,.12);
  border-radius: 16px;
  background: rgba(255,249,239,.72);
}
.tos-sla-center-dimension {
  min-height: 38px;
  border-radius: 12px !important;
  border: 1px solid transparent !important;
  transition: transform 140ms ease, background 140ms ease, border-color 140ms ease;
}
.tos-sla-center-dimension[data-active="true"] {
  color: #2a1d04 !important;
  border-color: rgba(165,108,6,.20) !important;
  background: linear-gradient(145deg, #f6d36f, #dda12a) !important;
  box-shadow: 0 7px 18px rgba(177,116,10,.13);
}
.tos-sla-center-dimension[data-active="false"] { background: rgba(255,255,255,.82); border-color: rgba(201,144,29,.10) !important; }

.tos-sla-center-table-wrap { background: linear-gradient(180deg, rgba(255,255,255,.98), rgba(255,252,247,.92)); }
.tos-sla-center-table thead { background: #fffaf1 !important; }
.tos-sla-center-table th { color: #847968 !important; letter-spacing: .04em; }
.tos-sla-center-table-row { transition: background 140ms ease; }
.tos-sla-center-table-row:hover { background: #fff9ec; }
.tos-sla-center-compliance-track { background: #f3ede3 !important; }
.tos-sla-center-compliance-fill { background: linear-gradient(90deg, #e2ad37, #c98d19) !important; box-shadow: 0 0 10px rgba(201,141,25,.16); }

.tos-sla-center-aging-row {
  min-height: 76px;
  padding: 15px 18px !important;
  transition: background 140ms ease;
}
.tos-sla-center-aging-row:nth-child(even) { background: rgba(255,251,244,.62); }
.tos-sla-center-aging-row:hover { background: #fff8e9; }
.tos-sla-center-late-pill { box-shadow: inset 0 0 0 1px rgba(239,99,99,.12); }
.tos-sla-center-policy-pill { border-color: rgba(201,144,29,.15) !important; background: rgba(255,255,255,.82); }
.tos-sla-center-pagination { background: rgba(255,250,241,.70); }
.tos-sla-center-pagination button { background: rgba(255,255,255,.88); border-color: rgba(201,144,29,.14) !important; }

.dark .tos-sla-center-flagship-v1 {
  --slac-ink: #f5f0e7;
  --slac-muted: #b3aa9c;
  --slac-line: rgba(222,179,82,.15);
  --slac-card: #151513;
  --slac-soft: #181714;
}
.dark .tos-sla-center-flagship-v1 .text-app { color: #f5f0e7 !important; }
.dark .tos-sla-center-flagship-v1 .text-muted { color: #b4ab9e !important; }
.dark .tos-sla-center-hero {
  border-color: rgba(222,179,82,.16);
  background:
    radial-gradient(circle at 86% 10%, rgba(222,179,82,.075), transparent 31%),
    linear-gradient(145deg, #1d1c19, #0f0f0e);
  box-shadow: 0 22px 58px rgba(0,0,0,.30), inset 0 1px 0 rgba(255,255,255,.025);
}
.dark .tos-sla-center-hero::after { opacity: .34; background: repeating-linear-gradient(105deg, transparent 0 24px, rgba(222,179,82,.13) 25px 27px, transparent 28px 44px); }
.dark .tos-sla-center-hero h1 { color: #f6f1e8 !important; }
.dark .tos-sla-center-hero p { color: #b8afa2 !important; }
.dark .tos-sla-center-hero > div:first-child > p:first-child { color: #efc65f !important; }
.dark .tos-sla-center-inbox-button,
.dark .tos-sla-center-refresh-button { color: #ece5d9 !important; border-color: rgba(222,179,82,.17) !important; background: #171715 !important; box-shadow: 0 8px 22px rgba(0,0,0,.18); }
.dark .tos-sla-center-kpi { border-color: rgba(255,255,255,.07) !important; background: linear-gradient(145deg, #1b1b19, #11110f) !important; box-shadow: 0 15px 38px rgba(0,0,0,.24) !important; }
.dark .tos-sla-center-kpi p:first-child { color: #c6bdb0 !important; }
.dark .tos-sla-center-kpi p:last-child { color: #f6f1e8 !important; }
.dark .tos-sla-center-kpi > div > div:last-child { background: color-mix(in srgb, var(--slac-kpi) 13%, #151513) !important; box-shadow: none; }
.dark .tos-sla-center-drilldown,
.dark .tos-sla-center-aging { border-color: rgba(222,179,82,.12) !important; background: #11110f !important; box-shadow: 0 20px 52px rgba(0,0,0,.27); }
.dark .tos-sla-center-drilldown-header,
.dark .tos-sla-center-aging-header { border-color: rgba(255,255,255,.06) !important; background: linear-gradient(180deg, #1a1a18, #141412); }
.dark .tos-sla-center-dimensions { border-color: rgba(222,179,82,.12); background: #121210; }
.dark .tos-sla-center-dimension[data-active="false"] { color: #d0c7bb !important; border-color: rgba(255,255,255,.07) !important; background: #1a1a18 !important; }
.dark .tos-sla-center-dimension[data-active="true"] { color: #261a03 !important; }
.dark .tos-sla-center-table-wrap { background: #11110f; }
.dark .tos-sla-center-table thead { background: #181816 !important; }
.dark .tos-sla-center-table th { color: #a89f92 !important; border-color: rgba(255,255,255,.05) !important; }
.dark .tos-sla-center-table-row { border-color: rgba(255,255,255,.055) !important; }
.dark .tos-sla-center-table-row:hover { background: #1d1b16; }
.dark .tos-sla-center-table td { color: #ddd5c9; }
.dark .tos-sla-center-table td:first-child { color: #f3eee5 !important; }
.dark .tos-sla-center-compliance-track { background: #292720 !important; }
.dark .tos-sla-center-aging-row { border-color: rgba(255,255,255,.055) !important; }
.dark .tos-sla-center-aging-row:nth-child(even) { background: #151513; }
.dark .tos-sla-center-aging-row:hover { background: #1c1a15; }
.dark .tos-sla-center-aging-row p:first-child { color: #f2ede4 !important; }
.dark .tos-sla-center-policy-pill { color: #ddd5c9; border-color: rgba(222,179,82,.14) !important; background: #191917; }
.dark .tos-sla-center-pagination { border-color: rgba(255,255,255,.06) !important; background: #151513; }
.dark .tos-sla-center-pagination button { color: #eee7dc !important; border-color: rgba(222,179,82,.15) !important; background: #1b1b19; }
.dark .tos-sla-center-pagination button:disabled { color: #756e64 !important; }
.dark .tos-sla-center-pagination span { color: #f0e9dd !important; }

@media (max-width: 900px) {
  .tos-sla-center-hero { min-height: 0; padding: 22px; }
  .tos-sla-center-hero::after { width: 46%; opacity: .28; }
}
@media (max-width: 640px) {
  .tos-sla-center-flagship-v1 { padding-inline: 12px !important; }
  .tos-sla-center-hero { padding: 18px; border-radius: 24px; }
  .tos-sla-center-hero > div:last-child { width: 100%; display: grid !important; grid-template-columns: 1fr; }
  .tos-sla-center-inbox-button, .tos-sla-center-refresh-button { justify-content: center; width: 100%; }
  .tos-sla-center-dimensions { width: 100%; display: grid !important; grid-template-columns: repeat(3, minmax(0,1fr)); }
  .tos-sla-center-aging-row { padding: 14px !important; }
}
'''

print("RUNNING=TOS_UXUI_SLA_CENTER_FLAGSHIP_V1")

def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def tree_count(root: Path, needle: bytes) -> int:
    if not root.exists(): return 0
    total = 0
    for p in root.rglob("*"):
        if p.is_file():
            try: total += p.read_bytes().count(needle)
            except OSError: pass
    return total

def fail(message: str, original=None):
    if original is not None:
        try: PAGE.write_text(original, encoding="utf-8")
        except Exception: pass
    if STYLE.exists():
        try: STYLE.unlink()
        except Exception: pass
    print("PASS/FAIL=FAIL")
    print("ERROR=" + str(message))
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("SLA_CENTER_FLAGSHIP_V1_RUNTIME=NO")
    sys.exit(1)

def replace_once(source, old, new, label):
    count = source.count(old)
    if count != 1: fail(f"{label} guard mismatch: expected 1, found {count}")
    return source.replace(old, new, 1)

if ROOT.resolve() == Path("/"): fail("unsafe ROOT")
for p in (FRONTEND, PAGE, LIVE_PARENT, *PRESERVE_FILES):
    if not p.exists(): fail(f"required path missing: {p}")
if sha256(PAGE) != EXPECTED_PAGE_SHA256:
    fail(f"SlaCenterPage.jsx pagination baseline mismatch: {sha256(PAGE)}")
if STYLE.exists(): fail("slaCenterFlagshipV1.css already exists")

original = PAGE.read_text(encoding="utf-8")
if STYLE_IMPORT in original or "tos-sla-center-flagship-v1" in original:
    fail("SLA Center Flagship V1 appears already applied")

for token in (
    'request("/api/sla/dashboard")',
    'window.setInterval(() => load({ quiet: true }), 60_000)',
    'const BREACH_PAGE_SIZE = 6;',
    'data-sla-breach-pagination="v1"',
    'const pagedBreaches = useMemo',
    'href="/sla-inbox"',
):
    if token not in original: fail(f"required SLA Center behavior/pagination anchor missing: {token}")

preserve_before = {str(p): sha256(p) for p in PRESERVE_FILES}
source = original
source = replace_once(source, IMPORT_ANCHOR, IMPORT_ANCHOR + '\n' + STYLE_IMPORT, "style import")
source = replace_once(source, '<div className="p-4 sm:p-6">', '<div className="tos-sla-center-flagship-v1 p-4 sm:p-6">', "page root")
source = replace_once(source, '<div className="mx-auto max-w-7xl space-y-5">', '<div className="tos-sla-center-frame mx-auto max-w-7xl space-y-5">', "page frame")
source = replace_once(source, '<div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">', '<div className="tos-sla-center-hero flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">', "hero")
source = replace_once(source, 'className="rounded-xl border border-app px-3 py-2 text-sm font-bold hover:bg-app-soft"', 'className="tos-sla-center-inbox-button rounded-xl border border-app px-3 py-2 text-sm font-bold hover:bg-app-soft"', "inbox button")
source = replace_once(source, 'className="inline-flex items-center gap-2 rounded-xl border border-app px-3 py-2 text-sm font-bold hover:bg-app-soft"', 'className="tos-sla-center-refresh-button inline-flex items-center gap-2 rounded-xl border border-app px-3 py-2 text-sm font-bold hover:bg-app-soft"', "refresh button")
source = replace_once(source, '<div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">', '<div className="tos-sla-center-kpi-grid grid gap-3 sm:grid-cols-2 xl:grid-cols-4">', "kpi grid")
source = replace_once(source, '<div key={label} className="rounded-2xl border border-app bg-app-card p-4 shadow-sm">', '<div key={label} className="tos-sla-center-kpi rounded-2xl border border-app bg-app-card p-4 shadow-sm">', "kpi cards")

DRILL = '<div className="rounded-2xl border border-app bg-app-card">\n              <div className="flex flex-col gap-3 border-b border-app p-4 sm:flex-row sm:items-center sm:justify-between">'
source = replace_once(source, DRILL, '<div className="tos-sla-center-drilldown rounded-2xl border border-app bg-app-card">\n              <div className="tos-sla-center-drilldown-header flex flex-col gap-3 border-b border-app p-4 sm:flex-row sm:items-center sm:justify-between">', "drilldown card")
source = replace_once(source, '<div className="flex flex-wrap gap-2">\n                  {DIMENSIONS.map((item) => (', '<div className="tos-sla-center-dimensions flex flex-wrap gap-2">\n                  {DIMENSIONS.map((item) => (', "dimension group")
source = replace_once(source, 'className={`rounded-xl px-3 py-2 text-sm font-bold ${dimension === item ? "bg-app text-app-card" : "border border-app hover:bg-app-soft"}`}', 'data-active={dimension === item ? "true" : "false"} className={`tos-sla-center-dimension rounded-xl px-3 py-2 text-sm font-bold ${dimension === item ? "bg-app text-app-card" : "border border-app hover:bg-app-soft"}`}', "dimension buttons")
source = replace_once(source, '<div className="overflow-x-auto">\n                <table className="w-full min-w-[820px] text-sm">', '<div className="tos-sla-center-table-wrap overflow-x-auto">\n                <table className="tos-sla-center-table w-full min-w-[820px] text-sm">', "table")
source = replace_once(source, '<tr key={row.id} className="border-t border-app">', '<tr key={row.id} className="tos-sla-center-table-row border-t border-app">', "table row")
source = replace_once(source, '<div className="h-1.5 w-24 overflow-hidden rounded-full bg-app-soft"><div className="h-full bg-amber-500" style={{ width: `${Math.max(0, Math.min(100, row.compliancePct))}%` }} /></div>', '<div className="tos-sla-center-compliance-track h-1.5 w-24 overflow-hidden rounded-full bg-app-soft"><div className="tos-sla-center-compliance-fill h-full bg-amber-500" style={{ width: `${Math.max(0, Math.min(100, row.compliancePct))}%` }} /></div>', "compliance bar")

source = replace_once(source, '<div data-sla-breach-pagination="v1" className="rounded-2xl border border-app bg-app-card">', '<div data-sla-breach-pagination="v1" className="tos-sla-center-aging rounded-2xl border border-app bg-app-card">', "aging card")
source = replace_once(source, '<div className="flex items-center justify-between border-b border-app p-4">\n                <div>\n                  <h2 className="font-black text-app">{ar ? "أقدم الاختراقات النشطة" : "Breach Aging"}</h2>', '<div className="tos-sla-center-aging-header flex items-center justify-between border-b border-app p-4">\n                <div>\n                  <h2 className="font-black text-app">{ar ? "أقدم الاختراقات النشطة" : "Breach Aging"}</h2>', "aging header")
source = replace_once(source, '<div key={item.taskId} className="flex flex-col gap-2 p-4 md:flex-row md:items-center md:justify-between">', '<div key={item.taskId} className="tos-sla-center-aging-row flex flex-col gap-2 p-4 md:flex-row md:items-center md:justify-between">', "aging row")
source = replace_once(source, 'className="rounded-full bg-red-500/10 px-2.5 py-1 text-xs font-black text-red-600"', 'className="tos-sla-center-late-pill rounded-full bg-red-500/10 px-2.5 py-1 text-xs font-black text-red-600"', "late pill")
source = replace_once(source, 'className="rounded-full border border-app px-2.5 py-1 text-xs font-bold"', 'className="tos-sla-center-policy-pill rounded-full border border-app px-2.5 py-1 text-xs font-bold"', "policy pill")
source = replace_once(source, '<div className="flex flex-col gap-3 border-t border-app px-4 py-3 sm:flex-row sm:items-center sm:justify-between">', '<div className="tos-sla-center-pagination flex flex-col gap-3 border-t border-app px-4 py-3 sm:flex-row sm:items-center sm:justify-between">', "pagination footer")

for token in (
    STYLE_IMPORT,
    'tos-sla-center-flagship-v1',
    'tos-sla-center-hero',
    'tos-sla-center-kpi',
    'tos-sla-center-drilldown',
    'tos-sla-center-table',
    'tos-sla-center-aging',
    'tos-sla-center-pagination',
    'data-sla-breach-pagination="v1"',
):
    if token not in source: fail(f"transformed source missing marker: {token}")

try:
    PAGE.write_text(source, encoding="utf-8")
    STYLE.write_text(CSS, encoding="utf-8")
except Exception as exc:
    fail(f"source/style write failed: {exc}", original)

build = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, text=True, capture_output=True)
if build.returncode != 0:
    print(build.stdout[-12000:]); print(build.stderr[-12000:])
    fail("frontend build failed", original)
if not DIST.exists() or not (DIST / "index.html").exists(): fail("dist/index.html missing", original)
for marker in (RUNTIME_MARKER.encode(), b'tos-sla-center-flagship-v1', b'data-sla-breach-pagination', b'Breach Aging', b'SLA Drill-down'):
    if tree_count(DIST, marker) < 1: fail(f"built output missing marker: {marker.decode(errors='ignore')}", original)
for p in PRESERVE_FILES:
    if sha256(p) != preserve_before[str(p)]: fail(f"out-of-scope file changed: {p}", original)

# Safe atomic live deploy.
ts = int(time.time())
candidate = LIVE_PARENT / f"build.sla-center-flagship-v1-candidate-{ts}"
backup = LIVE_PARENT / f"build.sla-center-flagship-v1-backup-{ts}"
failed_live = LIVE_PARENT / f"build.sla-center-flagship-v1-failed-{ts}"
try:
    shutil.copytree(DIST, candidate)
    if not LIVE.exists(): raise RuntimeError(f"live build missing: {LIVE}")
    LIVE.rename(backup)
    candidate.rename(LIVE)
except Exception as exc:
    try:
        if LIVE.exists() and backup.exists(): LIVE.rename(failed_live); backup.rename(LIVE)
        elif backup.exists() and not LIVE.exists(): backup.rename(LIVE)
    finally:
        fail(f"live deployment failed and rollback attempted: {exc}", original)

print("PASS/FAIL=PASS")
print("BUILD_RESULT=PASS")
print("LIVE_DEPLOY=PASS")
print("SLA_CENTER_FLAGSHIP_V1_RUNTIME=YES")
print("SLA_CENTER_HERO_FLAGSHIP=YES")
print("SLA_CENTER_KPI_STRIP=EXECUTIVE")
print("SLA_CENTER_DRILLDOWN=PREMIUM_DATA_CONSOLE")
print("SLA_CENTER_DIMENSION_SWITCHER=PREMIUM")
print("SLA_CENTER_COMPLIANCE_BARS=REFINED")
print("SLA_CENTER_BREACH_AGING=EXECUTIVE")
print("SLA_CENTER_PAGINATION_V1_PRESERVED=YES")
print("SLA_CENTER_LIGHT_MODE=IVORY_CHAMPAGNE")
print("SLA_CENTER_DARK_MODE=OBSIDIAN_TITANIUM")
print("SLA_CENTER_API_CHANGED=NO")
print("SLA_CENTER_POLLING_CHANGED=NO")
print("SLA_CENTER_DATA_CALCULATIONS_CHANGED=NO")
print("SLA_INBOX_CHANGED=NO")
print("RAMZY_CHANGED=NO")
print("TCS_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print(f"SLA_CENTER_PAGE_SHA256={sha256(PAGE)}")
print(f"SLA_CENTER_STYLE_SHA256={sha256(STYLE)}")
print(f"LIVE_BACKUP={backup}")
print("STATUS=READY")
