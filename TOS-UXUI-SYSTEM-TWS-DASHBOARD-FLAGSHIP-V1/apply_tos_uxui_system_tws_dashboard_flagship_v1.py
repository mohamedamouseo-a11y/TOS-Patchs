from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
PAGE = FRONTEND / "src/pages/tws/TwsDashboard.jsx"
STYLE = FRONTEND / "src/pages/tws/twsDashboardFlagshipV1.css"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_PAGE_GIT_BLOB_SHA = "66ee40a50c2ecc437d0ab88165011063d3fd6829"
STYLE_IMPORT = 'import "./twsDashboardFlagshipV1.css";'
RUNTIME_MARKER = "--tos-tws-dashboard-flagship-v1-runtime"
PAGE_SIZE = 12

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

CSS = r''':root {
  --tos-tws-dashboard-flagship-v1-runtime: 1;
}

.tos-tws-flagship-v1 {
  --tws-gold: #d8a62f;
  --tws-gold-strong: #bd8213;
  --tws-ink: #17130d;
  --tws-muted: #7d7468;
  --tws-line: rgba(177, 121, 18, .14);
  position: relative;
}

/* Executive hero */
.tos-tws-flagship-v1 .tos-tws-hero-card {
  border-color: rgba(191, 138, 31, .18) !important;
  border-radius: 28px !important;
  box-shadow: 0 22px 55px rgba(95, 63, 8, .08) !important;
}
.tos-tws-flagship-v1 .tos-tws-hero {
  min-height: 190px !important;
  color: #21180b !important;
  background:
    linear-gradient(115deg, rgba(255,255,255,.94), rgba(255,248,230,.94)),
    radial-gradient(circle at 76% 18%, rgba(226,174,62,.20), transparent 30%) !important;
}
.tos-tws-flagship-v1 .tos-tws-hero::after {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: repeating-linear-gradient(106deg, transparent 0 56px, rgba(190,132,24,.055) 57px 59px);
  mask-image: linear-gradient(90deg, transparent 28%, #000 62%, #000 100%);
}
.tos-tws-flagship-v1 .tos-tws-hero h2 { color: #17120b !important; letter-spacing: -.025em; }
.tos-tws-flagship-v1 .tos-tws-hero p { color: #756b5e !important; }
.tos-tws-flagship-v1 .tos-tws-hero > div > div:first-child > span {
  color: #8a5b08 !important;
  border: 1px solid rgba(183,123,19,.16);
  background: rgba(221,170,58,.10) !important;
}
.tos-tws-flagship-v1 .tos-tws-quick-create {
  position: relative;
  z-index: 2;
  border: 1px solid rgba(188,132,28,.16);
  background: rgba(255,255,255,.68) !important;
  box-shadow: 0 14px 34px rgba(88,57,7,.08), inset 0 1px rgba(255,255,255,.92);
  backdrop-filter: blur(18px);
}
.tos-tws-flagship-v1 .tos-tws-quick-create > b { color: #916006 !important; }

/* KPI intelligence */
.tos-tws-flagship-v1 .tos-tws-stats { align-content: stretch; }
.tos-tws-flagship-v1 .tos-tws-stat {
  position: relative;
  overflow: hidden;
  min-height: 104px;
  border-color: rgba(177,121,18,.12) !important;
  background: linear-gradient(150deg, #fffefa, #fffaf0) !important;
  box-shadow: 0 12px 30px rgba(73,48,6,.055) !important;
}
.tos-tws-flagship-v1 .tos-tws-stat::before {
  content: "";
  position: absolute;
  inset-block: 14px;
  inset-inline-start: 0;
  width: 3px;
  border-radius: 999px;
  background: #d7a42d;
}
.tos-tws-flagship-v1 .tos-tws-stat:nth-child(2)::before { background: #4b8fce; }
.tos-tws-flagship-v1 .tos-tws-stat:nth-child(3)::before { background: #32a56f; }
.tos-tws-flagship-v1 .tos-tws-stat:nth-child(4)::before { background: #c58b24; }
.tos-tws-flagship-v1 .tos-tws-stat:nth-child(5)::before { background: #e0a91c; }
.tos-tws-flagship-v1 .tos-tws-stat:nth-child(6)::before { background: #8b78cb; }

/* Premium navigation + control rail */
.tos-tws-flagship-v1 .tos-tws-control-card {
  overflow: visible !important;
  position: relative;
  z-index: 40;
  border-color: rgba(181,126,22,.13) !important;
  background: linear-gradient(180deg, rgba(255,254,250,.98), rgba(255,250,240,.94)) !important;
  box-shadow: 0 14px 36px rgba(73,47,5,.05) !important;
}
.tos-tws-flagship-v1 .tos-tws-tab {
  border: 1px solid transparent;
  transition: transform .16s ease, box-shadow .16s ease, background .16s ease, border-color .16s ease;
}
.tos-tws-flagship-v1 .tos-tws-tab:hover { transform: translateY(-1px); }
.tos-tws-flagship-v1 .tos-tws-tabs .tos-tws-tab[class*="bg-zinc-950"] {
  color: #231704 !important;
  border-color: rgba(172,112,5,.16) !important;
  background: linear-gradient(145deg, #f4cf68, #dda428) !important;
  box-shadow: 0 8px 18px rgba(171,111,8,.14);
}
.tos-tws-flagship-v1 .tos-tws-filter-row { align-items: stretch; }
.tos-tws-flagship-v1 .tos-tws-view-toggle {
  border-color: rgba(181,126,22,.13) !important;
  background: rgba(224,171,53,.06) !important;
}

/* Custom premium menu */
.tos-tws-premium-select {
  position: relative;
  min-width: 0;
  z-index: 80;
}
.tos-tws-premium-trigger {
  width: 100%;
  min-height: 42px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 9px 12px;
  border: 1px solid rgba(177,121,18,.15);
  border-radius: 14px;
  color: #231c13;
  background: #fffdf8;
  box-shadow: inset 0 1px rgba(255,255,255,.94);
  font-size: 12px;
  font-weight: 850;
  text-align: start;
  outline: 0;
}
.tos-tws-premium-trigger:hover,
.tos-tws-premium-trigger[data-open="true"] {
  border-color: rgba(191,132,21,.48);
  box-shadow: 0 0 0 3px rgba(209,151,31,.08), inset 0 1px rgba(255,255,255,.94);
}
.tos-tws-premium-chevron {
  width: 22px;
  height: 22px;
  display: grid;
  place-items: center;
  flex: 0 0 auto;
  border: 1px solid rgba(185,126,18,.13);
  border-radius: 8px;
  color: #9a6508;
  background: rgba(219,163,44,.07);
  transition: transform .15s ease;
}
.tos-tws-premium-trigger[data-open="true"] .tos-tws-premium-chevron { transform: rotate(180deg); }
.tos-tws-premium-menu {
  position: absolute;
  z-index: 260;
  top: calc(100% + 7px);
  inset-inline: 0;
  max-height: 280px;
  overflow-y: auto;
  padding: 6px;
  border: 1px solid rgba(181,124,20,.16);
  border-radius: 15px;
  background: rgba(255,253,247,.99);
  box-shadow: 0 22px 54px rgba(64,41,5,.16), inset 0 1px rgba(255,255,255,.96);
  backdrop-filter: blur(18px);
}
.tos-tws-premium-option {
  width: 100%;
  min-height: 38px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 8px 10px;
  border: 0;
  border-radius: 10px;
  color: #32291e;
  background: transparent;
  font-size: 12px;
  font-weight: 820;
  text-align: start;
}
.tos-tws-premium-option:hover { background: rgba(213,156,35,.09); color: #714804; }
.tos-tws-premium-option[data-selected="true"] {
  color: #261902;
  background: linear-gradient(145deg, #f5d169, #dfa62b);
}

/* Template menu */
.tos-tws-flagship-v1 .tos-tws-template-menu {
  z-index: 280 !important;
  width: 220px !important;
  border-color: rgba(184,127,20,.17) !important;
  background: rgba(255,253,247,.99) !important;
  box-shadow: 0 22px 54px rgba(64,41,5,.16) !important;
  backdrop-filter: blur(18px);
}

/* Bucket intelligence */
.tos-tws-flagship-v1 .tos-tws-buckets { gap: 14px; }
.tos-tws-flagship-v1 .tos-tws-bucket {
  border-color: rgba(181,125,21,.11) !important;
  background: linear-gradient(160deg, #fffefa, #fffbf3) !important;
  box-shadow: 0 12px 28px rgba(70,45,4,.045) !important;
}

/* File cards + list */
.tos-tws-flagship-v1 .tos-tws-document-card {
  border-color: rgba(177,121,18,.12) !important;
  background: linear-gradient(160deg, #fff, #fffaf1) !important;
  box-shadow: 0 13px 30px rgba(69,44,4,.055) !important;
  transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease !important;
}
.tos-tws-flagship-v1 .tos-tws-document-card:hover {
  transform: translateY(-2px);
  border-color: rgba(190,130,20,.24) !important;
  box-shadow: 0 19px 40px rgba(70,45,4,.09) !important;
}
.tos-tws-flagship-v1 .tos-tws-list {
  border-color: rgba(179,123,20,.12) !important;
  background: #fffefa !important;
  box-shadow: 0 14px 34px rgba(70,45,4,.055) !important;
}
.tos-tws-flagship-v1 .tos-tws-list-row { transition: background .14s ease; }
.tos-tws-flagship-v1 .tos-tws-list-row:hover { background: rgba(220,166,48,.055); }
.tos-tws-flagship-v1 .tos-tws-bulk-bar {
  border-color: rgba(191,134,25,.24) !important;
  background: linear-gradient(90deg, rgba(244,204,102,.15), rgba(255,250,236,.94)) !important;
  box-shadow: 0 10px 26px rgba(81,52,4,.055);
}

/* Pagination */
.tos-tws-pagination {
  margin-top: 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 11px 13px;
  border: 1px solid rgba(180,124,21,.12);
  border-radius: 18px;
  color: #746a5d;
  background: rgba(255,252,245,.94);
  box-shadow: 0 9px 24px rgba(67,43,4,.04);
}
.tos-tws-pagination__range,
.tos-tws-pagination__page { font-size: 11px; font-weight: 850; }
.tos-tws-pagination__controls { display: flex; align-items: center; gap: 8px; }
.tos-tws-pagination button {
  min-height: 34px;
  padding: 7px 11px;
  border: 1px solid rgba(179,123,21,.15);
  border-radius: 11px;
  color: #392a12;
  background: #fffdf8;
  font-size: 11px;
  font-weight: 900;
}
.tos-tws-pagination button:disabled { opacity: .36; cursor: not-allowed; }
.tos-tws-pagination button:not(:disabled):hover { border-color: rgba(188,127,18,.34); background: #fff8e9; }

/* Dark mode */
.dark .tos-tws-flagship-v1 {
  --tws-line: rgba(220,174,76,.14);
}
.dark .tos-tws-flagship-v1 .tos-tws-hero-card,
.dark .tos-tws-flagship-v1 .tos-tws-stat,
.dark .tos-tws-flagship-v1 .tos-tws-control-card,
.dark .tos-tws-flagship-v1 .tos-tws-bucket,
.dark .tos-tws-flagship-v1 .tos-tws-document-card,
.dark .tos-tws-flagship-v1 .tos-tws-list {
  border-color: rgba(220,174,76,.13) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-hero {
  color: #f5efe5 !important;
  background:
    radial-gradient(circle at 74% 16%, rgba(205,151,35,.11), transparent 31%),
    linear-gradient(135deg, #161612, #0e0e0d 62%, #19150d) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-hero h2 { color: #fffaf1 !important; }
.dark .tos-tws-flagship-v1 .tos-tws-hero p { color: #aaa196 !important; }
.dark .tos-tws-flagship-v1 .tos-tws-hero > div > div:first-child > span {
  color: #e6bd5e !important;
  border-color: rgba(223,178,75,.18);
  background: rgba(223,178,75,.08) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-quick-create {
  border-color: rgba(222,177,75,.15);
  background: rgba(255,255,255,.035) !important;
  box-shadow: 0 18px 42px rgba(0,0,0,.28), inset 0 1px rgba(255,255,255,.025);
}
.dark .tos-tws-flagship-v1 .tos-tws-quick-create > b { color: #e4ba56 !important; }
.dark .tos-tws-flagship-v1 .tos-tws-stat,
.dark .tos-tws-flagship-v1 .tos-tws-control-card,
.dark .tos-tws-flagship-v1 .tos-tws-bucket,
.dark .tos-tws-flagship-v1 .tos-tws-document-card,
.dark .tos-tws-flagship-v1 .tos-tws-list {
  background: linear-gradient(155deg, #171715, #111110) !important;
  box-shadow: 0 16px 40px rgba(0,0,0,.20) !important;
}
.dark .tos-tws-flagship-v1 .tos-tws-tabs .tos-tws-tab[class*="dark:bg-white"] {
  color: #241701 !important;
  background: linear-gradient(145deg, #efc85f, #d89e27) !important;
}
.dark .tos-tws-premium-trigger {
  color: #f0eae0;
  border-color: rgba(222,176,74,.16);
  background: #191917;
  box-shadow: inset 0 1px rgba(255,255,255,.025);
}
.dark .tos-tws-premium-trigger:hover,
.dark .tos-tws-premium-trigger[data-open="true"] { border-color: rgba(222,176,74,.45); }
.dark .tos-tws-premium-chevron { color: #e4b955; border-color: rgba(222,176,74,.15); background: rgba(222,176,74,.07); }
.dark .tos-tws-premium-menu,
.dark .tos-tws-flagship-v1 .tos-tws-template-menu {
  color: #eee8de;
  border-color: rgba(222,176,74,.16) !important;
  background: rgba(20,20,18,.995) !important;
  box-shadow: 0 25px 58px rgba(0,0,0,.46) !important;
}
.dark .tos-tws-premium-option { color: #eee8de; }
.dark .tos-tws-premium-option:hover { color: #fff8ea; background: rgba(222,176,74,.09); }
.dark .tos-tws-premium-option[data-selected="true"] { color: #251801; background: linear-gradient(145deg, #efc85e, #d89d27); }
.dark .tos-tws-flagship-v1 .tos-tws-bulk-bar { border-color: rgba(219,172,70,.18) !important; background: rgba(219,172,70,.07) !important; }
.dark .tos-tws-pagination { color: #9d9589; border-color: rgba(222,176,74,.13); background: rgba(20,20,18,.96); box-shadow: 0 12px 28px rgba(0,0,0,.16); }
.dark .tos-tws-pagination__page { color: #f1eadf; }
.dark .tos-tws-pagination button { color: #eee7dc; border-color: rgba(222,176,74,.14); background: #191917; }
.dark .tos-tws-pagination button:not(:disabled):hover { background: #211f1a; border-color: rgba(222,176,74,.28); }

@media (max-width: 768px) {
  .tos-tws-flagship-v1 .tos-tws-hero-layout { grid-template-columns: 1fr !important; }
  .tos-tws-flagship-v1 .tos-tws-hero { min-height: 0 !important; padding: 20px !important; }
  .tos-tws-pagination { align-items: flex-start; flex-direction: column; }
  .tos-tws-pagination__controls { width: 100%; justify-content: space-between; }
}
'''

PREMIUM_SELECT = r'''
function TwsPremiumSelect({ value, onValueChange, options, ariaLabel }) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef(null);
  const selected = options.find((option) => String(option.value) === String(value));

  useEffect(() => {
    if (!open) return undefined;
    const closeOnOutside = (event) => {
      if (!rootRef.current?.contains(event.target)) setOpen(false);
    };
    const closeOnEscape = (event) => {
      if (event.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", closeOnOutside);
    document.addEventListener("keydown", closeOnEscape);
    return () => {
      document.removeEventListener("mousedown", closeOnOutside);
      document.removeEventListener("keydown", closeOnEscape);
    };
  }, [open]);

  return (
    <div ref={rootRef} className="tos-tws-premium-select">
      <button
        type="button"
        className="tos-tws-premium-trigger"
        data-open={open ? "true" : "false"}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={ariaLabel}
        onClick={() => setOpen((current) => !current)}
      >
        <span className="min-w-0 truncate">{selected?.label || "—"}</span>
        <span className="tos-tws-premium-chevron" aria-hidden="true">⌄</span>
      </button>
      {open && (
        <div className="tos-tws-premium-menu" role="listbox" aria-label={ariaLabel}>
          {options.map((option) => {
            const isSelected = String(option.value) === String(value);
            return (
              <button
                key={String(option.value)}
                type="button"
                role="option"
                aria-selected={isSelected}
                data-selected={isSelected ? "true" : "false"}
                className="tos-tws-premium-option"
                onClick={() => { onValueChange(option.value); setOpen(false); }}
              >
                <span className="min-w-0 truncate">{option.label}</span>
                {isSelected && <span aria-hidden="true">✓</span>}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
'''

print("RUNNING=TOS_UXUI_SYSTEM_TWS_DASHBOARD_FLAGSHIP_V1")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


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


def fail(message: str, original=None):
    if original is not None:
        try:
            PAGE.write_text(original, encoding="utf-8")
        except Exception:
            pass
    if STYLE.exists():
        try:
            STYLE.unlink()
        except Exception:
            pass
    print("PASS/FAIL=FAIL")
    print("ERROR=" + str(message))
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("TWS_DASHBOARD_FLAGSHIP_V1_RUNTIME=NO")
    sys.exit(1)


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        fail(f"{label} guard mismatch: expected 1, found {count}")
    return source.replace(old, new, 1)


if ROOT.resolve() == Path("/"):
    fail("unsafe ROOT")
for path in (FRONTEND, PAGE, LIVE_PARENT, *PRESERVE_FILES):
    if not path.exists():
        fail(f"required path missing: {path}")

actual_blob = git_blob_sha(PAGE)
if actual_blob != EXPECTED_PAGE_GIT_BLOB_SHA:
    fail(f"TwsDashboard.jsx baseline mismatch: {actual_blob}")
if STYLE.exists():
    fail("TWS Dashboard Flagship V1 stylesheet already exists")

original = PAGE.read_text(encoding="utf-8")
if STYLE_IMPORT in original or "tos-tws-flagship-v1" in original or "TWS_RESULT_PAGE_SIZE" in original:
    fail("TWS Dashboard Flagship V1 appears already applied")

for token in (
    'api.tws.list(filters)',
    'api.tws.create({ type, title:',
    'api.tws.updateContent(doc.id',
    'api.tws.duplicate(doc.id)',
    'api.tws.archive(doc.id)',
    'api.tws.restore(doc.id)',
    'api.tws.trash(doc.id)',
    'api.tws.favorites.list()',
    'api.tws.favorites.add(documentId)',
    'api.tws.favorites.remove(documentId)',
    'limit: 60',
    'window.setTimeout(load, 300)',
    '<Field as="select" value={projectFilter}',
    '<Field as="select" value={trashSubView}',
):
    if token not in original:
        fail(f"required TWS behavior anchor missing: {token}")

preserve_before = {str(path): sha256(path) for path in PRESERVE_FILES}
source = original
source = replace_once(source, 'import { useEffect, useMemo, useState } from "react";', 'import { useEffect, useMemo, useRef, useState } from "react";', "useRef import")
source = replace_once(source, 'import { useTwsI18n, twsDateTime } from "./twsI18n";', 'import { useTwsI18n, twsDateTime } from "./twsI18n";\n' + STYLE_IMPORT, "flagship style import")
source = replace_once(source, '\nfunction getTDocTemplates(ui) {', '\nconst TWS_RESULT_PAGE_SIZE = 12;\n' + PREMIUM_SELECT + '\nfunction getTDocTemplates(ui) {', "premium select component")

source = replace_once(source, '    <Card hover className={cn("group relative flex flex-col gap-3 p-4", selected && "ring-2 ring-amber-400")}>', '    <Card hover className={cn("tos-tws-document-card group relative flex flex-col gap-3 p-4", selected && "ring-2 ring-amber-400")}>', "document card class")
source = replace_once(source, '  const [viewMode, setViewMode] = useState("grid");', '  const [viewMode, setViewMode] = useState("grid");\n  const [resultPage, setResultPage] = useState(1);', "result page state")

PAGINATION_STATE = '''  const docTemplates = useMemo(() => getTDocTemplates(ui), [ui]);
  const docTemplateLabels = useMemo(() => getTDocTemplateLabels(ui), [ui]);
  const resultPageCount = Math.max(1, Math.ceil(items.length / TWS_RESULT_PAGE_SIZE));
  const safeResultPage = Math.min(Math.max(1, resultPage), resultPageCount);
  const pagedItems = useMemo(() => {
    const start = (safeResultPage - 1) * TWS_RESULT_PAGE_SIZE;
    return items.slice(start, start + TWS_RESULT_PAGE_SIZE);
  }, [items, safeResultPage]);

  useEffect(() => { setResultPage(1); }, [tab, query, projectFilter, trashSubView]);
  useEffect(() => {
    setResultPage((current) => Math.min(Math.max(1, current), resultPageCount));
  }, [resultPageCount]);'''
source = replace_once(source, '  const docTemplates = useMemo(() => getTDocTemplates(ui), [ui]);\n  const docTemplateLabels = useMemo(() => getTDocTemplateLabels(ui), [ui]);', PAGINATION_STATE, "result pagination state")

source = replace_once(source, '    <div className="tws-reference-ui tws-dashboard-reference tos-page">', '    <div className="tws-reference-ui tws-dashboard-reference tos-tws-flagship-v1 tos-page">', "page root")
source = replace_once(source, '<div className="absolute z-20 mt-1 w-48 overflow-hidden rounded-2xl border border-zinc-100 bg-white shadow-lg dark:border-white/10 dark:bg-zinc-900">', '<div className="tos-tws-template-menu absolute z-20 mt-1 w-48 overflow-hidden rounded-2xl border border-zinc-100 bg-white shadow-lg dark:border-white/10 dark:bg-zinc-900">', "template menu")
source = replace_once(source, '<div className="mt-4 grid gap-4 xl:grid-cols-[1.25fr_0.75fr]">', '<div className="tos-tws-hero-layout mt-4 grid gap-4 xl:grid-cols-[1.25fr_0.75fr]">', "hero layout")
source = replace_once(source, '<Card className="overflow-hidden p-0">', '<Card className="tos-tws-hero-card overflow-hidden p-0">', "hero card")
source = replace_once(source, '<div className="relative min-h-[170px] overflow-hidden bg-gradient-to-br from-zinc-950 via-zinc-900 to-amber-950 p-6 text-white">', '<div className="tos-tws-hero relative min-h-[170px] overflow-hidden bg-gradient-to-br from-zinc-950 via-zinc-900 to-amber-950 p-6 text-white">', "hero surface")
source = replace_once(source, '<div className="grid min-w-[220px] gap-2 rounded-3xl bg-white/10 p-3 backdrop-blur">', '<div className="tos-tws-quick-create grid min-w-[220px] gap-2 rounded-3xl bg-white/10 p-3 backdrop-blur">', "quick create")
source = replace_once(source, '<div className="grid grid-cols-2 gap-3 lg:grid-cols-3 xl:grid-cols-2">', '<div className="tos-tws-stats grid grid-cols-2 gap-3 lg:grid-cols-3 xl:grid-cols-2">', "stats grid")
source = replace_once(source, '<Card key={stat.label} className="p-4">', '<Card key={stat.label} className="tos-tws-stat p-4">', "stat card")
source = replace_once(source, '<Card className="mt-4">', '<Card className="tos-tws-control-card mt-4">', "control card")
source = replace_once(source, '<div className="flex flex-wrap gap-2">\n          {TABS.map', '<div className="tos-tws-tabs flex flex-wrap gap-2">\n          {TABS.map', "tabs rail")
source = replace_once(source, '"inline-flex items-center gap-1.5 rounded-2xl px-3.5 py-2 text-xs font-black transition",', '"tos-tws-tab inline-flex items-center gap-1.5 rounded-2xl px-3.5 py-2 text-xs font-black transition",', "tab class")
source = replace_once(source, '<div className="mt-3 grid gap-3 md:grid-cols-[1fr_220px_auto]">', '<div className="tos-tws-filter-row mt-3 grid gap-3 md:grid-cols-[1fr_220px_auto]">', "filter row")
source = replace_once(source, '<div className="inline-flex items-center justify-center gap-1 rounded-2xl border border-zinc-100 bg-zinc-50 p-1 dark:border-white/10 dark:bg-white/[0.04]">', '<div className="tos-tws-view-toggle inline-flex items-center justify-center gap-1 rounded-2xl border border-zinc-100 bg-zinc-50 p-1 dark:border-white/10 dark:bg-white/[0.04]">', "view toggle")

PROJECT_SELECT_OLD = '''          <Field as="select" value={projectFilter} onChange={(event) => setProjectFilter(event.target.value)}>
            <option value="">{ui.allProjects}</option>
            {projects.map((project) => <option key={project.id} value={project.id}>{project.name}</option>)}
          </Field>'''
PROJECT_SELECT_NEW = '''          <TwsPremiumSelect
            value={projectFilter}
            onValueChange={setProjectFilter}
            ariaLabel={ui.allProjects}
            options={[
              { value: "", label: ui.allProjects },
              ...projects.map((project) => ({ value: project.id, label: project.name })),
            ]}
          />'''
source = replace_once(source, PROJECT_SELECT_OLD, PROJECT_SELECT_NEW, "project premium select")

TRASH_SELECT_OLD = '''            <Field as="select" value={trashSubView} onChange={(event) => setTrashSubView(event.target.value)}>
              <option value="TRASHED">{ui.trash}</option>
              <option value="ARCHIVED">{ui.archiveTab}</option>
            </Field>'''
TRASH_SELECT_NEW = '''            <TwsPremiumSelect
              value={trashSubView}
              onValueChange={setTrashSubView}
              ariaLabel={ui.trash}
              options={[
                { value: "TRASHED", label: ui.trash },
                { value: "ARCHIVED", label: ui.archiveTab },
              ]}
            />'''
source = replace_once(source, TRASH_SELECT_OLD, TRASH_SELECT_NEW, "trash premium select")

source = replace_once(source, '<div className="mt-4 flex flex-wrap items-center gap-2 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 dark:border-amber-400/20 dark:bg-amber-500/10">', '<div className="tos-tws-bulk-bar mt-4 flex flex-wrap items-center gap-2 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-3 dark:border-amber-400/20 dark:bg-amber-500/10">', "bulk bar")
source = replace_once(source, '<div className="mt-4 grid gap-4 xl:grid-cols-4">\n          {dashboardBuckets.map', '<div className="tos-tws-buckets mt-4 grid gap-4 xl:grid-cols-4">\n          {dashboardBuckets.map', "buckets grid")
source = replace_once(source, '<Card key={bucket.id} className="p-4">', '<Card key={bucket.id} className="tos-tws-bucket p-4">', "bucket card")
source = replace_once(source, '<div className="overflow-hidden rounded-3xl border border-zinc-100 bg-white shadow-sm dark:border-white/10 dark:bg-zinc-900">', '<div className="tos-tws-list overflow-hidden rounded-3xl border border-zinc-100 bg-white shadow-sm dark:border-white/10 dark:bg-zinc-900">', "list view")
source = replace_once(source, '<div key={doc.id} className="flex flex-wrap items-center gap-3 border-b border-zinc-100 px-4 py-3 last:border-b-0 dark:border-white/10">', '<div key={doc.id} className="tos-tws-list-row flex flex-wrap items-center gap-3 border-b border-zinc-100 px-4 py-3 last:border-b-0 dark:border-white/10">', "list row")

if source.count('{items.map((doc) =>') != 2:
    fail(f"items.map pagination guard mismatch: expected 2, found {source.count('{items.map((doc) =>')}", original)
source = source.replace('{items.map((doc) =>', '{pagedItems.map((doc) =>')

END_ANCHOR = '''      </div>
    </div>
  );
}'''
PAGINATION_FOOTER = '''      </div>

      {!loading && items.length > TWS_RESULT_PAGE_SIZE && (
        <div data-tws-results-pagination="v1" className="tos-tws-pagination">
          <span className="tos-tws-pagination__range">
            {ui.lang === "en"
              ? `Showing ${(safeResultPage - 1) * TWS_RESULT_PAGE_SIZE + 1}–${Math.min(safeResultPage * TWS_RESULT_PAGE_SIZE, items.length)} of ${items.length}`
              : `عرض ${(safeResultPage - 1) * TWS_RESULT_PAGE_SIZE + 1}–${Math.min(safeResultPage * TWS_RESULT_PAGE_SIZE, items.length)} من ${items.length}`}
          </span>
          <div className="tos-tws-pagination__controls">
            <button type="button" disabled={safeResultPage <= 1} onClick={() => setResultPage((current) => Math.max(1, current - 1))}>{ui.lang === "en" ? "Previous" : "السابق"}</button>
            <span className="tos-tws-pagination__page">{ui.lang === "en" ? `Page ${safeResultPage} of ${resultPageCount}` : `صفحة ${safeResultPage} من ${resultPageCount}`}</span>
            <button type="button" disabled={safeResultPage >= resultPageCount} onClick={() => setResultPage((current) => Math.min(resultPageCount, current + 1))}>{ui.lang === "en" ? "Next" : "التالي"}</button>
          </div>
        </div>
      )}
    </div>
  );
}'''
source = replace_once(source, END_ANCHOR, PAGINATION_FOOTER, "pagination footer")

for token in (
    STYLE_IMPORT,
    'function TwsPremiumSelect',
    'tos-tws-flagship-v1',
    'tos-tws-hero',
    'tos-tws-stat',
    'tos-tws-control-card',
    'tos-tws-premium-select',
    'const TWS_RESULT_PAGE_SIZE = 12;',
    'const pagedItems = useMemo',
    'data-tws-results-pagination="v1"',
    '{pagedItems.map((doc) =>',
):
    if token not in source:
        fail(f"transformed source missing marker: {token}", original)

if '<Field as="select" value={projectFilter}' in source or '<Field as="select" value={trashSubView}' in source:
    fail("visible native TWS dashboard select remains", original)

for token in (
    'api.tws.list(filters)',
    'api.tws.create({ type, title:',
    'api.tws.updateContent(doc.id',
    'api.tws.duplicate(doc.id)',
    'api.tws.archive(doc.id)',
    'api.tws.restore(doc.id)',
    'api.tws.trash(doc.id)',
    'api.tws.favorites.list()',
    'api.tws.favorites.add(documentId)',
    'api.tws.favorites.remove(documentId)',
    'limit: 60',
    'window.setTimeout(load, 300)',
):
    if token not in source:
        fail(f"TWS behavior changed unexpectedly: {token}", original)

try:
    PAGE.write_text(source, encoding="utf-8")
    STYLE.write_text(CSS, encoding="utf-8")
except Exception as exc:
    fail(f"source/style write failed: {exc}", original)

build = subprocess.run(["npm", "run", "build"], cwd=FRONTEND, text=True, capture_output=True)
if build.returncode != 0:
    print(build.stdout[-12000:])
    print(build.stderr[-12000:])
    fail("frontend build failed", original)

if not DIST.exists() or not (DIST / "index.html").exists():
    fail("dist/index.html missing after build", original)

for marker in (
    RUNTIME_MARKER.encode(),
    b'tos-tws-flagship-v1',
    b'tos-tws-premium-select',
    b'data-tws-results-pagination',
    b'TWS_RESULT_PAGE_SIZE',
):
    if tree_count(DIST, marker) < 1:
        fail(f"built output missing TWS V1 marker: {marker.decode(errors='ignore')}", original)

for path in PRESERVE_FILES:
    if sha256(path) != preserve_before[str(path)]:
        fail(f"out-of-scope file changed: {path}", original)

# Atomic live deploy; no service restart and no Git action in /var/www/TOS.
ts = int(time.time())
candidate = LIVE_PARENT / f"build.tws-dashboard-flagship-v1-candidate-{ts}"
backup = LIVE_PARENT / f"build.tws-dashboard-flagship-v1-backup-{ts}"
failed_live = LIVE_PARENT / f"build.tws-dashboard-flagship-v1-failed-{ts}"
try:
    if candidate.exists() or backup.exists() or failed_live.exists():
        raise RuntimeError("timestamped deployment path already exists")
    shutil.copytree(DIST, candidate)
    if not LIVE.exists():
        raise RuntimeError(f"live build missing: {LIVE}")
    LIVE.rename(backup)
    candidate.rename(LIVE)
except Exception as exc:
    try:
        if LIVE.exists() and backup.exists():
            LIVE.rename(failed_live)
            backup.rename(LIVE)
        elif backup.exists() and not LIVE.exists():
            backup.rename(LIVE)
    finally:
        fail(f"live deployment failed and rollback attempted: {exc}", original)

print("PASS/FAIL=PASS")
print("BUILD_RESULT=PASS")
print("LIVE_DEPLOY=PASS")
print("TWS_DASHBOARD_FLAGSHIP_V1_RUNTIME=YES")
print("TWS_HERO_FLAGSHIP=YES")
print("TWS_EXECUTIVE_KPI_GRID=YES")
print("TWS_NAVIGATION_RAIL=PREMIUM")
print("TWS_DOCUMENT_CARDS=FLAGSHIP")
print("TWS_BUCKETS=EXECUTIVE")
print("TWS_GRID_VIEW=PRESERVED_PREMIUM")
print("TWS_LIST_VIEW=PRESERVED_PREMIUM")
print("TWS_PROJECT_FILTER=PREMIUM_CUSTOM")
print("TWS_TRASH_FILTER=PREMIUM_CUSTOM")
print("TWS_NATIVE_VISIBLE_SELECTS_REMAINING=0")
print("TWS_RESULTS_PAGINATION=CLIENT_SIDE")
print("TWS_RESULTS_PAGE_SIZE=12")
print("TWS_RESULTS_PREVIOUS_NEXT=YES")
print("TWS_LIGHT_MODE=IVORY_CHAMPAGNE")
print("TWS_DARK_MODE=OBSIDIAN_TITANIUM")
print("TWS_LIST_API_CHANGED=NO")
print("TWS_CREATE_CHANGED=NO")
print("TWS_CONTENT_UPDATE_CHANGED=NO")
print("TWS_DUPLICATE_CHANGED=NO")
print("TWS_ARCHIVE_CHANGED=NO")
print("TWS_RESTORE_CHANGED=NO")
print("TWS_TRASH_CHANGED=NO")
print("TWS_FAVORITES_CHANGED=NO")
print("TWS_SEARCH_DEBOUNCE_CHANGED=NO")
print("TWS_API_LIMIT_CHANGED=NO")
print("TWS_EDITORS_CHANGED=NO")
print("TWS_SHARE_CHANGED=NO")
print("SLA_INBOX_CHANGED=NO")
print("SLA_CENTER_CHANGED=NO")
print("ADVANCED_SLA_CHANGED=NO")
print("RAMZY_CHANGED=NO")
print("TCS_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print(f"TWS_DASHBOARD_PAGE_SHA256={sha256(PAGE)}")
print(f"TWS_DASHBOARD_STYLE_SHA256={sha256(STYLE)}")
print(f"LIVE_BACKUP={backup}")
print("STATUS=READY")