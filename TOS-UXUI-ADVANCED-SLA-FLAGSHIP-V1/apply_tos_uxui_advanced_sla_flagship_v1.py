from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
PAGE = FRONTEND / "src/pages/SlaAdvancedPage.jsx"
STYLE = FRONTEND / "src/pages/slaAdvancedFlagshipV1.css"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_PAGE_BLOB_SHA = "84e430cd937da8b3c24173c74ec8f6a28b649329"
STYLE_IMPORT = 'import "./slaAdvancedFlagshipV1.css";'
IMPORT_ANCHOR = 'import { usePreferences } from "../contexts/PreferencesContext";'
RUNTIME_MARKER = "--tos-advanced-sla-flagship-v1-runtime"
HISTORY_PAGE_SIZE = 8

PRESERVE_FILES = [
    FRONTEND / "src/pages/SlaInboxPage.jsx",
    FRONTEND / "src/pages/slaInboxFlagshipV1.css",
    FRONTEND / "src/pages/slaInboxFlagshipV1_1DarkContrast.css",
    FRONTEND / "src/pages/SlaCenterPage.jsx",
    FRONTEND / "src/pages/slaCenterFlagshipV1.css",
    FRONTEND / "src/pages/slaCenterFlagshipV1_1DarkTableHeader.css",
    FRONTEND / "src/components/RamzyAssistant.jsx",
    FRONTEND / "src/components/TcsFloatingLauncher.jsx",
    FRONTEND / "src/components/TcsDesktopWindow.jsx",
]

CSS = r''':root {
  --tos-advanced-sla-flagship-v1-runtime: 1;
}

.tos-advanced-sla-flagship-v1 {
  --asla-gold: #c9911f;
  --asla-gold-strong: #9d6707;
  --asla-ink: #17130d;
  --asla-muted: #756c60;
  --asla-line: rgba(201,145,31,.16);
  --asla-soft: #fff9ee;
  position: relative;
}

.tos-advanced-sla-frame { max-width: 1480px !important; }

.tos-advanced-sla-hero {
  position: relative;
  overflow: hidden;
  min-height: 154px;
  padding: 26px 28px;
  border: 1px solid rgba(201,145,31,.18);
  border-radius: 30px;
  background:
    radial-gradient(circle at 86% 10%, rgba(220,166,55,.13), transparent 31%),
    linear-gradient(145deg, rgba(255,255,255,.995), rgba(255,248,234,.96));
  box-shadow: 0 22px 58px rgba(65,43,10,.07), inset 0 1px 0 rgba(255,255,255,.95);
}
.tos-advanced-sla-hero::after {
  content: "";
  position: absolute;
  inset-block: 0;
  inset-inline-end: 4%;
  width: 34%;
  opacity: .58;
  pointer-events: none;
  background: repeating-linear-gradient(105deg, transparent 0 24px, rgba(201,145,31,.11) 25px 27px, transparent 28px 44px);
}
.tos-advanced-sla-hero > * { position: relative; z-index: 1; }
.tos-advanced-sla-hero h1 { font-size: clamp(28px, 3vw, 40px) !important; letter-spacing: -.035em; }
.tos-advanced-sla-status,
.tos-advanced-sla-refresh {
  min-height: 44px;
  border-radius: 15px !important;
  border-color: rgba(201,145,31,.20) !important;
  background: rgba(255,255,255,.88);
  box-shadow: 0 8px 22px rgba(58,39,10,.055);
}
.tos-advanced-sla-refresh { transition: transform 150ms ease, border-color 150ms ease; }
.tos-advanced-sla-refresh:hover { transform: translateY(-1px); border-color: rgba(201,145,31,.34) !important; }

.tos-advanced-sla-kpis { gap: 12px !important; }
.tos-advanced-sla-kpi {
  position: relative;
  min-height: 106px;
  overflow: hidden;
  border: 1px solid rgba(201,145,31,.13);
  border-radius: 23px;
  padding: 17px 18px;
  background: linear-gradient(150deg, rgba(255,255,255,.995), rgba(255,250,241,.93));
  box-shadow: 0 13px 32px rgba(55,40,13,.05);
}
.tos-advanced-sla-kpi::before { content: ""; position: absolute; inset-block: 0; inset-inline-start: 0; width: 3px; background: var(--asla-kpi, #c9911f); }
.tos-advanced-sla-kpi:nth-child(1) { --asla-kpi: #2ba77c; }
.tos-advanced-sla-kpi:nth-child(2) { --asla-kpi: #c9911f; }
.tos-advanced-sla-kpi:nth-child(3) { --asla-kpi: #d69b25; }
.tos-advanced-sla-kpi span { color: #817565; font-size: 11px; font-weight: 900; letter-spacing: .055em; text-transform: uppercase; }
.tos-advanced-sla-kpi strong { display: block; margin-top: 8px; color: #17130d; font-size: 28px; line-height: 1; font-weight: 950; }

.tos-advanced-sla-studio,
.tos-advanced-sla-policies,
.tos-advanced-sla-history {
  overflow: hidden;
  border: 1px solid rgba(201,145,31,.14) !important;
  border-radius: 28px !important;
  background: rgba(255,255,255,.975) !important;
  box-shadow: 0 18px 46px rgba(50,36,10,.055);
}
.tos-advanced-sla-studio { padding: 0 !important; }
.tos-advanced-sla-studio-header,
.tos-advanced-sla-card-header {
  padding: 18px 20px !important;
  border-bottom: 1px solid rgba(201,145,31,.11) !important;
  background: linear-gradient(180deg, rgba(255,252,246,.97), rgba(255,255,255,.95));
}
.tos-advanced-sla-studio > .grid,
.tos-advanced-sla-studio > .mt-4,
.tos-advanced-sla-studio > .mt-5 { margin-inline: 20px; }
.tos-advanced-sla-studio > .mt-5:last-child { margin-bottom: 20px; }
.tos-advanced-sla-new {
  border-color: rgba(201,145,31,.18) !important;
  background: rgba(255,250,240,.82);
}

.tos-advanced-sla-field {
  min-height: 44px;
  border-radius: 14px !important;
  border-color: rgba(201,145,31,.16) !important;
  background: #fffdf8 !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.9);
  transition: border-color 140ms ease, box-shadow 140ms ease, background 140ms ease;
}
.tos-advanced-sla-field:focus {
  border-color: rgba(201,145,31,.65) !important;
  box-shadow: 0 0 0 3px rgba(201,145,31,.10);
  background: #fff !important;
}

.tos-advanced-sla-days {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 5px;
  width: fit-content;
  border: 1px solid rgba(201,145,31,.12);
  border-radius: 16px;
  background: rgba(255,249,239,.72);
}
.tos-advanced-sla-day {
  min-width: 56px;
  min-height: 39px;
  border-radius: 12px !important;
  border: 1px solid rgba(201,145,31,.10) !important;
  background: rgba(255,255,255,.86);
  transition: transform 140ms ease, background 140ms ease, border-color 140ms ease;
}
.tos-advanced-sla-day[data-active="true"] {
  color: #291c03 !important;
  border-color: rgba(157,103,7,.22) !important;
  background: linear-gradient(145deg, #f6d36f, #dda12a) !important;
  box-shadow: 0 7px 18px rgba(177,116,10,.14);
}
.tos-advanced-sla-day:hover { transform: translateY(-1px); }

.tos-advanced-sla-escalation {
  position: relative;
  overflow: hidden;
  border-radius: 22px !important;
  border: 1px solid rgba(201,145,31,.13) !important;
  background: linear-gradient(145deg, #fffdf9, #fff8ed) !important;
  box-shadow: 0 10px 24px rgba(61,43,12,.045);
}
.tos-advanced-sla-escalation::before { content: ""; position: absolute; inset-inline-start: 0; inset-block: 0; width: 3px; background: var(--escalation-color, #d49b27); }
.tos-advanced-sla-escalation[data-level="1"] { --escalation-color: #d6a02b; }
.tos-advanced-sla-escalation[data-level="2"] { --escalation-color: #e38235; }
.tos-advanced-sla-escalation[data-level="3"] { --escalation-color: #e25d5d; }
.tos-advanced-sla-escalation > * { position: relative; z-index: 1; }

.tos-advanced-sla-save {
  min-height: 45px;
  border-radius: 14px !important;
  background: linear-gradient(145deg, #f4cc61, #d99a20) !important;
  box-shadow: 0 12px 28px rgba(183,118,8,.17), inset 0 1px 0 rgba(255,255,255,.40);
  transition: transform 140ms ease, box-shadow 140ms ease;
}
.tos-advanced-sla-save:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 15px 32px rgba(183,118,8,.22); }

.tos-advanced-sla-table-wrap { background: linear-gradient(180deg, rgba(255,255,255,.99), rgba(255,252,247,.94)); }
.tos-advanced-sla-table thead,
.tos-advanced-sla-table thead tr,
.tos-advanced-sla-table thead th { background: #fff9ef !important; }
.tos-advanced-sla-table th { color: #817665 !important; letter-spacing: .045em; border-color: rgba(201,145,31,.10) !important; }
.tos-advanced-sla-table-row { transition: background 140ms ease; }
.tos-advanced-sla-table-row:hover { background: #fff9ed; }
.tos-advanced-sla-history-row:nth-child(even) { background: rgba(255,251,244,.58); }
.tos-advanced-sla-policy-edit { background: rgba(255,251,244,.72); border-color: rgba(201,145,31,.15) !important; }

.tos-advanced-sla-history-pagination {
  border-top: 1px solid rgba(201,145,31,.11);
  background: rgba(255,249,238,.72);
}
.tos-advanced-sla-history-pagination button {
  min-height: 38px;
  border-radius: 12px !important;
  border-color: rgba(201,145,31,.14) !important;
  background: rgba(255,255,255,.88);
}

.dark .tos-advanced-sla-flagship-v1 .text-app { color: #f5f0e7 !important; }
.dark .tos-advanced-sla-flagship-v1 .text-muted { color: #b4ab9e !important; }
.dark .tos-advanced-sla-hero {
  border-color: rgba(222,179,82,.16);
  background:
    radial-gradient(circle at 86% 10%, rgba(222,179,82,.075), transparent 31%),
    linear-gradient(145deg, #1d1c19, #0f0f0e);
  box-shadow: 0 22px 58px rgba(0,0,0,.30), inset 0 1px 0 rgba(255,255,255,.025);
}
.dark .tos-advanced-sla-hero::after { opacity: .34; background: repeating-linear-gradient(105deg, transparent 0 24px, rgba(222,179,82,.13) 25px 27px, transparent 28px 44px); }
.dark .tos-advanced-sla-hero h1 { color: #f6f1e8 !important; }
.dark .tos-advanced-sla-hero p:not(.text-amber-600) { color: #b8afa2 !important; }
.dark .tos-advanced-sla-status,
.dark .tos-advanced-sla-refresh { color: #ece5d9 !important; border-color: rgba(222,179,82,.17) !important; background: #171715 !important; box-shadow: 0 8px 22px rgba(0,0,0,.18); }
.dark .tos-advanced-sla-kpi { border-color: rgba(255,255,255,.07); background: linear-gradient(145deg, #1b1b19, #11110f); box-shadow: 0 15px 38px rgba(0,0,0,.24); }
.dark .tos-advanced-sla-kpi span { color: #bdb4a7; }
.dark .tos-advanced-sla-kpi strong { color: #f6f1e8; }
.dark .tos-advanced-sla-studio,
.dark .tos-advanced-sla-policies,
.dark .tos-advanced-sla-history { border-color: rgba(222,179,82,.12) !important; background: #11110f !important; box-shadow: 0 20px 52px rgba(0,0,0,.27); }
.dark .tos-advanced-sla-studio-header,
.dark .tos-advanced-sla-card-header { border-color: rgba(255,255,255,.06) !important; background: linear-gradient(180deg, #1a1a18, #141412); }
.dark .tos-advanced-sla-new { color: #e8e0d4 !important; border-color: rgba(222,179,82,.16) !important; background: #1a1a18; }
.dark .tos-advanced-sla-field { color: #f1eadf !important; border-color: rgba(222,179,82,.14) !important; background: #171715 !important; box-shadow: inset 0 1px 0 rgba(255,255,255,.025); color-scheme: dark; }
.dark .tos-advanced-sla-field:focus { border-color: rgba(222,179,82,.56) !important; background: #1c1b18 !important; box-shadow: 0 0 0 3px rgba(222,179,82,.08); }
.dark .tos-advanced-sla-field option { color: #eee7dc; background: #171715; }
.dark .tos-advanced-sla-days { border-color: rgba(222,179,82,.12); background: #121210; }
.dark .tos-advanced-sla-day[data-active="false"] { color: #d0c7bb !important; border-color: rgba(255,255,255,.07) !important; background: #1a1a18 !important; }
.dark .tos-advanced-sla-day[data-active="true"] { color: #261a03 !important; }
.dark .tos-advanced-sla-escalation { border-color: rgba(255,255,255,.07) !important; background: linear-gradient(145deg, #1b1b19, #131311) !important; box-shadow: 0 12px 30px rgba(0,0,0,.20); }
.dark .tos-advanced-sla-table-wrap { background: #11110f; }
.dark .tos-advanced-sla-table thead,
.dark .tos-advanced-sla-table thead tr,
.dark .tos-advanced-sla-table thead th { background: #181816 !important; background-color: #181816 !important; background-image: none !important; }
.dark .tos-advanced-sla-table th { color: #bdb3a5 !important; border-color: rgba(255,255,255,.055) !important; }
.dark .tos-advanced-sla-table td { color: #ddd5c9; border-color: rgba(255,255,255,.055) !important; }
.dark .tos-advanced-sla-table td:first-child { color: #f3eee5; }
.dark .tos-advanced-sla-table-row { border-color: rgba(255,255,255,.055) !important; }
.dark .tos-advanced-sla-table-row:hover { background: #1d1b16; }
.dark .tos-advanced-sla-history-row:nth-child(even) { background: #151513; }
.dark .tos-advanced-sla-policy-edit { color: #e9e1d5 !important; border-color: rgba(222,179,82,.14) !important; background: #191917; }
.dark .tos-advanced-sla-history-pagination { border-color: rgba(255,255,255,.06); background: #151513; }
.dark .tos-advanced-sla-history-pagination button { color: #eee7dc !important; border-color: rgba(222,179,82,.15) !important; background: #1b1b19; }
.dark .tos-advanced-sla-history-pagination button:disabled { color: #756e64 !important; }
.dark .tos-advanced-sla-history-pagination span { color: #f0e9dd !important; }

@media (max-width: 900px) {
  .tos-advanced-sla-hero { min-height: 0; padding: 22px; }
  .tos-advanced-sla-hero::after { width: 46%; opacity: .28; }
}
@media (max-width: 640px) {
  .tos-advanced-sla-flagship-v1 { padding-inline: 12px !important; }
  .tos-advanced-sla-hero { padding: 18px; border-radius: 24px; }
  .tos-advanced-sla-hero > div:last-child { width: 100%; display: grid !important; grid-template-columns: 1fr; }
  .tos-advanced-sla-status, .tos-advanced-sla-refresh { justify-content: center; width: 100%; }
  .tos-advanced-sla-studio > .grid,
  .tos-advanced-sla-studio > .mt-4,
  .tos-advanced-sla-studio > .mt-5 { margin-inline: 14px; }
  .tos-advanced-sla-days { width: 100%; display: grid; grid-template-columns: repeat(4, minmax(0,1fr)); }
  .tos-advanced-sla-day { min-width: 0; }
}
'''

print("RUNNING=TOS_UXUI_ADVANCED_SLA_FLAGSHIP_V1")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


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
    print("ADVANCED_SLA_FLAGSHIP_V1_RUNTIME=NO")
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
if actual_blob != EXPECTED_PAGE_BLOB_SHA:
    fail(f"SlaAdvancedPage.jsx baseline mismatch: {actual_blob}")
if STYLE.exists():
    fail("Advanced SLA Flagship V1 stylesheet already exists")

original = PAGE.read_text(encoding="utf-8")
if STYLE_IMPORT in original or "tos-advanced-sla-flagship-v1" in original or "HISTORY_PAGE_SIZE" in original:
    fail("Advanced SLA Flagship V1 appears already applied")

for token in (
    'request("/api/sla/context")',
    'request("/api/sla/policies")',
    'request("/api/sla/history?limit=200")',
    'method: editingId ? "PATCH" : "POST"',
    'method: "DELETE"',
    'if (!context.canManagePolicies) return;',
    'const activePolicyCount = useMemo',
    '{history.map((item) => (',
):
    if token not in original:
        fail(f"required Advanced SLA behavior anchor missing: {token}")

preserve_before = {str(path): sha256(path) for path in PRESERVE_FILES}
source = original
source = replace_once(source, IMPORT_ANCHOR, IMPORT_ANCHOR + "\n" + STYLE_IMPORT, "style import")
source = replace_once(source, 'const TARGET_ROLES = ["MANAGER", "PROJECT_MANAGER", "ADMIN", "SUPER_ADMIN"];', 'const TARGET_ROLES = ["MANAGER", "PROJECT_MANAGER", "ADMIN", "SUPER_ADMIN"];\nconst HISTORY_PAGE_SIZE = 8;', "history page size")
source = replace_once(source, '  const [history, setHistory] = useState([]);', '  const [history, setHistory] = useState([]);\n  const [historyPage, setHistoryPage] = useState(1);', "history page state")

PAGINATION_STATE = '''  const activePolicyCount = useMemo(() => policies.filter((item) => item.isActive).length, [policies]);
  const historyPageCount = Math.max(1, Math.ceil(history.length / HISTORY_PAGE_SIZE));
  const safeHistoryPage = Math.min(Math.max(1, historyPage), historyPageCount);
  const pagedHistory = useMemo(() => {
    const start = (safeHistoryPage - 1) * HISTORY_PAGE_SIZE;
    return history.slice(start, start + HISTORY_PAGE_SIZE);
  }, [history, safeHistoryPage]);

  useEffect(() => {
    setHistoryPage((current) => Math.min(Math.max(1, current), historyPageCount));
  }, [historyPageCount]);'''
source = replace_once(source, '  const activePolicyCount = useMemo(() => policies.filter((item) => item.isActive).length, [policies]);', PAGINATION_STATE, "history pagination memo")

source = replace_once(source, '  const field = "w-full rounded-xl border border-app bg-app-card px-3 py-2.5 text-sm font-bold text-app outline-none focus:border-amber-500";', '  const field = "tos-advanced-sla-field w-full rounded-xl border border-app bg-app-card px-3 py-2.5 text-sm font-bold text-app outline-none focus:border-amber-500";', "premium fields")
source = replace_once(source, '<div className="p-4 sm:p-6">', '<div className="tos-advanced-sla-flagship-v1 p-4 sm:p-6">', "page root")
source = replace_once(source, '<div className="mx-auto max-w-7xl space-y-5">', '<div className="tos-advanced-sla-frame mx-auto max-w-7xl space-y-5">', "page frame")
source = replace_once(source, '<div className="flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">', '<div className="tos-advanced-sla-hero flex flex-col gap-3 lg:flex-row lg:items-end lg:justify-between">', "hero")
source = replace_once(source, '<span className="rounded-xl border border-app px-3 py-2 text-sm font-black">{activePolicyCount} {ar ? "سياسة نشطة" : "active policies"}</span>', '<span className="tos-advanced-sla-status rounded-xl border border-app px-3 py-2 text-sm font-black">{activePolicyCount} {ar ? "سياسة نشطة" : "active policies"}</span>', "active status")
source = replace_once(source, '<button onClick={load} className="inline-flex items-center gap-2 rounded-xl border border-app px-3 py-2 text-sm font-bold hover:bg-app-soft">', '<button onClick={load} className="tos-advanced-sla-refresh inline-flex items-center gap-2 rounded-xl border border-app px-3 py-2 text-sm font-bold hover:bg-app-soft">', "refresh button")

KPI_STRIP = '''        <div className="tos-advanced-sla-kpis grid gap-3 sm:grid-cols-3">
          <div className="tos-advanced-sla-kpi"><span>{ar ? "سياسات نشطة" : "Active policies"}</span><strong>{activePolicyCount}</strong></div>
          <div className="tos-advanced-sla-kpi"><span>{ar ? "إجمالي السياسات" : "Total policies"}</span><strong>{policies.length}</strong></div>
          <div className="tos-advanced-sla-kpi"><span>{ar ? "أحداث SLA محملة" : "Loaded SLA events"}</span><strong>{history.length}</strong></div>
        </div>

'''
source = replace_once(source, '        {error && <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-4 text-sm font-bold text-red-600">', KPI_STRIP + '        {error && <div className="rounded-2xl border border-red-500/30 bg-red-500/10 p-4 text-sm font-bold text-red-600">', "kpi strip")

source = replace_once(source, '<form onSubmit={savePolicy} className="rounded-2xl border border-app bg-app-card p-4 sm:p-5">', '<form onSubmit={savePolicy} className="tos-advanced-sla-studio rounded-2xl border border-app bg-app-card p-4 sm:p-5">', "policy studio")
source = replace_once(source, '<div className="mb-4 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">', '<div className="tos-advanced-sla-studio-header mb-4 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">', "studio header")
source = replace_once(source, '<button type="button" onClick={beginCreate} className="inline-flex items-center gap-2 rounded-xl border border-app px-3 py-2 text-sm font-bold hover:bg-app-soft">', '<button type="button" onClick={beginCreate} className="tos-advanced-sla-new inline-flex items-center gap-2 rounded-xl border border-app px-3 py-2 text-sm font-bold hover:bg-app-soft">', "new policy button")
source = replace_once(source, '<div className="flex flex-wrap gap-2">\n                    {DAYS.map((day) => (', '<div className="tos-advanced-sla-days flex flex-wrap gap-2">\n                    {DAYS.map((day) => (', "business day group")
source = replace_once(source, '<button key={day.id} type="button" onClick={() => toggleDay(day.id)} className={`rounded-xl px-3 py-2 text-sm font-bold ${draft.businessDays.includes(day.id) ? "bg-amber-500 text-zinc-950" : "border border-app hover:bg-app-soft"}`}>', '<button key={day.id} type="button" onClick={() => toggleDay(day.id)} data-active={draft.businessDays.includes(day.id) ? "true" : "false"} className={`tos-advanced-sla-day rounded-xl px-3 py-2 text-sm font-bold ${draft.businessDays.includes(day.id) ? "bg-amber-500 text-zinc-950" : "border border-app hover:bg-app-soft"}`}>', "business day buttons")
source = replace_once(source, '<div key={level} className="rounded-2xl border border-app bg-app-soft p-4">', '<div key={level} data-level={String(level)} className="tos-advanced-sla-escalation rounded-2xl border border-app bg-app-soft p-4">', "escalation cards")
source = replace_once(source, '<button disabled={saving} className="inline-flex items-center gap-2 rounded-xl bg-amber-500 px-4 py-2.5 text-sm font-black text-zinc-950 disabled:opacity-50">', '<button disabled={saving} className="tos-advanced-sla-save inline-flex items-center gap-2 rounded-xl bg-amber-500 px-4 py-2.5 text-sm font-black text-zinc-950 disabled:opacity-50">', "save button")

source = replace_once(source, '<div className="rounded-2xl border border-app bg-app-card">\n              <div className="border-b border-app p-4"><h2 className="font-black text-app">{ar ? "السياسات" : "Policies"}</h2></div>', '<div className="tos-advanced-sla-policies rounded-2xl border border-app bg-app-card">\n              <div className="tos-advanced-sla-card-header border-b border-app p-4"><h2 className="font-black text-app">{ar ? "السياسات" : "Policies"}</h2></div>', "policies card")
source = replace_once(source, '<div className="overflow-x-auto">\n                <table className="w-full min-w-[980px] text-sm">', '<div className="tos-advanced-sla-table-wrap overflow-x-auto">\n                <table className="tos-advanced-sla-table tos-advanced-sla-policy-table w-full min-w-[980px] text-sm">', "policy table")
source = replace_once(source, '<tr key={policy.id} className="border-t border-app">', '<tr key={policy.id} className="tos-advanced-sla-table-row border-t border-app">', "policy rows")
source = replace_once(source, 'className="rounded-lg border border-app px-2.5 py-1.5 text-xs font-bold">{ar ? "تعديل" : "Edit"}</button>', 'className="tos-advanced-sla-policy-edit rounded-lg border border-app px-2.5 py-1.5 text-xs font-bold">{ar ? "تعديل" : "Edit"}</button>', "edit button")

source = replace_once(source, '<div className="rounded-2xl border border-app bg-app-card">\n              <div className="flex items-center gap-2 border-b border-app p-4"><History', '<div data-sla-advanced-history-pagination="v1" className="tos-advanced-sla-history rounded-2xl border border-app bg-app-card">\n              <div className="tos-advanced-sla-card-header flex items-center gap-2 border-b border-app p-4"><History', "history card")
source = replace_once(source, '<div className="overflow-x-auto">\n                <table className="w-full min-w-[1050px] text-sm">', '<div className="tos-advanced-sla-table-wrap overflow-x-auto">\n                <table className="tos-advanced-sla-table tos-advanced-sla-history-table w-full min-w-[1050px] text-sm">', "history table")
source = replace_once(source, '{history.map((item) => (', '{pagedHistory.map((item) => (', "history pagination map")
source = replace_once(source, '<tr key={item.id} className="border-t border-app">', '<tr key={item.id} className="tos-advanced-sla-table-row tos-advanced-sla-history-row border-t border-app">', "history rows")

HISTORY_END = '''                    {!history.length && <tr><td colSpan="6" className="px-4 py-10 text-center text-muted">{ar ? "لا يوجد سجل SLA حتى الآن." : "No SLA history yet."}</td></tr>}
                  </tbody>
                </table>
              </div>
            </div>'''
HISTORY_WITH_PAGINATION = '''                    {!history.length && <tr><td colSpan="6" className="px-4 py-10 text-center text-muted">{ar ? "لا يوجد سجل SLA حتى الآن." : "No SLA history yet."}</td></tr>}
                  </tbody>
                </table>
              </div>
              {history.length > HISTORY_PAGE_SIZE && (
                <div className="tos-advanced-sla-history-pagination flex flex-col gap-3 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
                  <p className="text-xs font-bold text-muted">
                    {ar
                      ? `عرض ${(safeHistoryPage - 1) * HISTORY_PAGE_SIZE + 1}–${Math.min(safeHistoryPage * HISTORY_PAGE_SIZE, history.length)} من ${history.length}`
                      : `Showing ${(safeHistoryPage - 1) * HISTORY_PAGE_SIZE + 1}–${Math.min(safeHistoryPage * HISTORY_PAGE_SIZE, history.length)} of ${history.length}`}
                  </p>
                  <div className="flex items-center gap-2">
                    <button type="button" disabled={safeHistoryPage <= 1} onClick={() => setHistoryPage((current) => Math.max(1, current - 1))} className="border border-app px-3 py-2 text-xs font-black disabled:cursor-not-allowed disabled:opacity-40">{ar ? "السابق" : "Previous"}</button>
                    <span className="min-w-[96px] text-center text-xs font-black text-app">{ar ? `صفحة ${safeHistoryPage} من ${historyPageCount}` : `Page ${safeHistoryPage} of ${historyPageCount}`}</span>
                    <button type="button" disabled={safeHistoryPage >= historyPageCount} onClick={() => setHistoryPage((current) => Math.min(historyPageCount, current + 1))} className="border border-app px-3 py-2 text-xs font-black disabled:cursor-not-allowed disabled:opacity-40">{ar ? "التالي" : "Next"}</button>
                  </div>
                </div>
              )}
            </div>'''
source = replace_once(source, HISTORY_END, HISTORY_WITH_PAGINATION, "history pagination footer")

for token in (
    STYLE_IMPORT,
    'tos-advanced-sla-flagship-v1',
    'tos-advanced-sla-hero',
    'tos-advanced-sla-kpi',
    'tos-advanced-sla-studio',
    'tos-advanced-sla-escalation',
    'tos-advanced-sla-policies',
    'tos-advanced-sla-history',
    'const HISTORY_PAGE_SIZE = 8;',
    'const pagedHistory = useMemo',
    'data-sla-advanced-history-pagination="v1"',
    '{pagedHistory.map((item) => (',
    'Page ${safeHistoryPage} of ${historyPageCount}',
):
    if token not in source:
        fail(f"transformed source missing marker: {token}")

for token in (
    'request("/api/sla/context")',
    'request("/api/sla/policies")',
    'request("/api/sla/history?limit=200")',
    'method: editingId ? "PATCH" : "POST"',
    'method: "DELETE"',
    'if (!context.canManagePolicies) return;',
):
    if token not in source:
        fail(f"Advanced SLA behavior changed unexpectedly: {token}")

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
    b'tos-advanced-sla-flagship-v1',
    b'data-sla-advanced-history-pagination',
    b'Advanced SLA Management',
    b'Breach & Escalation History',
    b'Previous',
    b'Next',
):
    if tree_count(DIST, marker) < 1:
        fail(f"built output missing runtime marker: {marker.decode(errors='ignore')}", original)

for path in PRESERVE_FILES:
    if sha256(path) != preserve_before[str(path)]:
        fail(f"out-of-scope file changed: {path}", original)

# Safe atomic deploy; no Git operations in /var/www/TOS and no service restart.
ts = int(time.time())
candidate = LIVE_PARENT / f"build.advanced-sla-flagship-v1-candidate-{ts}"
backup = LIVE_PARENT / f"build.advanced-sla-flagship-v1-backup-{ts}"
failed_live = LIVE_PARENT / f"build.advanced-sla-flagship-v1-failed-{ts}"
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
print("ADVANCED_SLA_FLAGSHIP_V1_RUNTIME=YES")
print("ADVANCED_SLA_HERO_FLAGSHIP=YES")
print("ADVANCED_SLA_EXECUTIVE_KPI_STRIP=YES")
print("ADVANCED_SLA_POLICY_STUDIO=PREMIUM")
print("ADVANCED_SLA_BUSINESS_DAYS=PREMIUM_SEGMENTED")
print("ADVANCED_SLA_ESCALATION_CARDS=PREMIUM")
print("ADVANCED_SLA_POLICIES_REGISTRY=EXECUTIVE")
print("ADVANCED_SLA_HISTORY=EXECUTIVE")
print("ADVANCED_SLA_HISTORY_PAGINATION=CLIENT_SIDE")
print("ADVANCED_SLA_HISTORY_PAGE_SIZE=8")
print("ADVANCED_SLA_HISTORY_PREVIOUS_NEXT=YES")
print("ADVANCED_SLA_LIGHT_MODE=IVORY_CHAMPAGNE")
print("ADVANCED_SLA_DARK_MODE=OBSIDIAN_TITANIUM")
print("ADVANCED_SLA_CONTEXT_API_CHANGED=NO")
print("ADVANCED_SLA_POLICIES_API_CHANGED=NO")
print("ADVANCED_SLA_HISTORY_API_CHANGED=NO")
print("ADVANCED_SLA_POLICY_CREATE_CHANGED=NO")
print("ADVANCED_SLA_POLICY_EDIT_CHANGED=NO")
print("ADVANCED_SLA_POLICY_DELETE_CHANGED=NO")
print("ADVANCED_SLA_PERMISSION_LOGIC_CHANGED=NO")
print("SLA_INBOX_CHANGED=NO")
print("SLA_CENTER_CHANGED=NO")
print("RAMZY_CHANGED=NO")
print("TCS_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print(f"ADVANCED_SLA_PAGE_SHA256={sha256(PAGE)}")
print(f"ADVANCED_SLA_STYLE_SHA256={sha256(STYLE)}")
print(f"LIVE_BACKUP={backup}")
print("STATUS=READY")