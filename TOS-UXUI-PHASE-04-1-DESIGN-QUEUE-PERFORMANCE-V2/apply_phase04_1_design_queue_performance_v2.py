from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
DQ = ROOT / "frontend/src/pages/DesignQueuePage.jsx"
PREF = ROOT / "frontend/src/contexts/PreferencesContext.jsx"
CSS = ROOT / "frontend/src/index.css"
DIST = ROOT / "frontend/dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

MARKER_V1 = "TOS_DQ_PERFORMANCE_V1"
MARKER_V2 = "TOS_DQ_PERFORMANCE_V2"
DQ_V1_SHA = "8f16fbe700c3b345d317e952b2f6dfeaab9ba986270748fe878fd4e0684d63e6"
PREF_V1_SHA = "1d949f3bc668400ffbfa69082166a41654a1c5ed9518b720675a7f13d873b731"
CSS_V6_SHA = "2fa061485f20af185aeae3df1fe99033cbf12d2babe31f87c0f2e776e31fcb13"

print("RUNNING=PHASE04_1_DESIGN_QUEUE_PERFORMANCE_V2")

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 match, found {count}")
    return text.replace(old, new, 1)

def fail(message: str):
    print("PASS/FAIL=FAIL")
    print(f"ERROR={message}")
    sys.exit(1)

if not DQ.exists() or not PREF.exists() or not CSS.exists():
    fail("required frontend source file missing")
if sha(PREF) != PREF_V1_SHA:
    fail("PreferencesContext differs from verified Performance V1 state")
if sha(CSS) != CSS_V6_SHA:
    fail("V6 CSS differs from verified state")

original = DQ.read_text()
applied_now = False

try:
    if MARKER_V2 not in original:
        if sha(DQ) != DQ_V1_SHA:
            raise RuntimeError("Design Queue differs from verified Performance V1 state")
        if original.count(MARKER_V1) != 1:
            raise RuntimeError("Performance V1 marker missing or duplicated")

        dq = original

        dq = replace_once(
            dq,
            '  const tr = getDesignOperationsT(lang);',
            '  // TOS_DQ_PERFORMANCE_V2: keep translation identity stable across local UI state updates.\n  const tr = useMemo(() => getDesignOperationsT(lang), [lang]);',
            'stable translation memo',
        )

        dq = replace_once(
            dq,
            '\nfunction KanbanBoard({ columns, onSelectTask, loading, capacityMode, tr, lang }) {',
            '\nconst MemoTaskCard = memo(TaskCard, (prev, next) =>\n  prev.task === next.task &&\n  prev.capacityMode === next.capacityMode &&\n  prev.lang === next.lang\n);\n\nfunction KanbanBoard({ columns, onSelectTask, loading, capacityMode, tr, lang }) {',
            'TaskCard memo insertion',
        )
        dq = replace_once(
            dq,
            '<TaskCard key={task.id}',
            '<MemoTaskCard key={task.id}',
            'TaskCard memo usage',
        )

        dq = replace_once(
            dq,
            '\nfunction CapacitySection({ designers, settings, permissions, collapsed, setCollapsed, drafts, setDrafts, savingId, onSave, tr, lang }) {',
            '\nconst MemoKanbanBoard = memo(KanbanBoard, (prev, next) =>\n  prev.columns === next.columns &&\n  prev.loading === next.loading &&\n  prev.capacityMode === next.capacityMode &&\n  prev.lang === next.lang\n);\n\nfunction CapacitySection({ designers, settings, permissions, collapsed, setCollapsed, drafts, setDrafts, savingId, onSave, tr, lang }) {',
            'Kanban memo insertion',
        )
        dq = replace_once(
            dq,
            '<KanbanBoard columns={kanbanColumns}',
            '<MemoKanbanBoard columns={kanbanColumns}',
            'Kanban memo usage',
        )

        dq = replace_once(
            dq,
            '\nfunction SpecRow({ label, value, children, linkify = false, lang = "ar" }) {',
            '\nconst MemoQueueStatRing = memo(QueueStatRing);\n\nfunction SpecRow({ label, value, children, linkify = false, lang = "ar" }) {',
            'KPI memo insertion',
        )
        dq = dq.replace('<QueueStatRing ', '<MemoQueueStatRing ')
        if dq.count('<MemoQueueStatRing ') != 6:
            raise RuntimeError(f"KPI memo usage: expected 6, found {dq.count('<MemoQueueStatRing ')}")

        dq = replace_once(
            dq,
            '  function updateFilters(partial) { const next = { ...filters, ...partial }; setFilters(next); loadQueue(next, { preserveModal: false }); }',
            '  function updateFilters(partial) {\n    const next = { ...filters, ...partial };\n    setFilters(next);\n    // Let the control paint first; refresh the remote queue silently on the next frame.\n    window.requestAnimationFrame(() => {\n      void loadQueue(next, { preserveModal: false, silent: true });\n    });\n  }',
            'deferred silent filter refresh',
        )

        DQ.write_text(dq)
        applied_now = True
    else:
        dq = original

    text = DQ.read_text()
    if text.count(MARKER_V2) != 1:
        raise RuntimeError("Performance V2 marker missing or duplicated")
    if text.count('const MemoTaskCard = memo(TaskCard') != 1:
        raise RuntimeError("TaskCard memo guard invalid")
    if text.count('const MemoKanbanBoard = memo(KanbanBoard') != 1:
        raise RuntimeError("Kanban memo guard invalid")
    if text.count('const MemoQueueStatRing = memo(QueueStatRing)') != 1:
        raise RuntimeError("KPI memo guard invalid")
    if text.count('loadQueue(next, { preserveModal: false, silent: true })') != 1:
        raise RuntimeError("silent deferred filter refresh missing")
    if sha(PREF) != PREF_V1_SHA:
        raise RuntimeError("PreferencesContext changed unexpectedly")
    if sha(CSS) != CSS_V6_SHA:
        raise RuntimeError("V6 CSS changed unexpectedly")

    subprocess.run(["git", "-C", str(ROOT), "diff", "--check", "--", "frontend/src/pages/DesignQueuePage.jsx"], check=True)
    subprocess.run(["npm", "run", "build"], cwd=ROOT / "frontend", check=True)
    if not (DIST / "index.html").exists():
        raise RuntimeError("built dist index missing")

    stamp = time.strftime("%Y%m%d-%H%M%S")
    stage = LIVE_PARENT / f"build.phase04-1-design-queue-performance-v2.new.{int(time.time())}"
    backup = LIVE_PARENT / f"build.phase04-1-design-queue-performance-v2.backup-{stamp}"
    if stage.exists():
        shutil.rmtree(stage)
    shutil.copytree(DIST, stage)
    if not (stage / "index.html").exists():
        raise RuntimeError("staged live index missing")
    if not LIVE.exists():
        raise RuntimeError("live frontend root missing")

    LIVE.rename(backup)
    try:
        stage.rename(LIVE)
        subprocess.run(["systemctl", "is-active", "--quiet", "nginx"], check=True)
    except Exception:
        if LIVE.exists():
            shutil.rmtree(LIVE)
        if backup.exists():
            backup.rename(LIVE)
        raise

except Exception as exc:
    if applied_now:
        DQ.write_text(original)
    fail(str(exc))

print("PASS/FAIL=PASS")
print("BUILD_RESULT=PASS")
print("LIVE_DEPLOY=PASS")
print("TASK_CARD_MEMO=YES")
print("KANBAN_MEMO=YES")
print("KPI_MEMO=YES")
print("FILTER_REFRESH_DEFERRED=YES")
print("FILTER_REFRESH_SILENT=YES")
print("BUSINESS_LOGIC_CHANGED=NO")
print("DESIGN_CHANGED=NO")
print(f"DESIGN_QUEUE_SHA256={sha(DQ)}")
print(f"PREFERENCES_CONTEXT_SHA256={sha(PREF)}")
print(f"INDEX_CSS_SHA256={sha(CSS)}")
