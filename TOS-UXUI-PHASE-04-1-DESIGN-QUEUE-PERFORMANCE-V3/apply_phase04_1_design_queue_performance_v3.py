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
PKG = ROOT / "frontend/package.json"
DIST = ROOT / "frontend/dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

MARKER_V2 = "TOS_DQ_PERFORMANCE_V2"
MARKER_V3 = "TOS_DQ_PERFORMANCE_V3"
DQ_V2_SHA = "5e77e839396fa9ee7b0e761d5cb679a820f3004791024aaaa8f4fdded3d2dd16"
PREF_V1_SHA = "1d949f3bc668400ffbfa69082166a41654a1c5ed9518b720675a7f13d873b731"
CSS_V6_SHA = "2fa061485f20af185aeae3df1fe99033cbf12d2babe31f87c0f2e776e31fcb13"

print("RUNNING=PHASE04_1_DESIGN_QUEUE_PERFORMANCE_V3")

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

for path in (DQ, PREF, CSS, PKG):
    if not path.exists():
        fail(f"required file missing: {path}")

if sha(PREF) != PREF_V1_SHA:
    fail("PreferencesContext differs from verified Performance V1 state")
if sha(CSS) != CSS_V6_SHA:
    fail("V6 CSS differs from verified state")
if '"@tanstack/react-virtual"' not in PKG.read_text():
    fail("@tanstack/react-virtual dependency missing")

original = DQ.read_text()
applied_now = False

try:
    if MARKER_V3 not in original:
        if sha(DQ) != DQ_V2_SHA:
            raise RuntimeError("Design Queue differs from verified Performance V2 state")
        if original.count(MARKER_V2) != 1:
            raise RuntimeError("Performance V2 marker missing or duplicated")

        dq = original
        dq = replace_once(
            dq,
            'import { memo, useEffect, useMemo, useRef, useState } from "react";',
            'import { memo, useEffect, useMemo, useRef, useState } from "react";\nimport { useVirtualizer } from "@tanstack/react-virtual";',
            'react virtual import',
        )

        insertion_anchor = '''const MemoTaskCard = memo(TaskCard, (prev, next) =>
  prev.task === next.task &&
  prev.capacityMode === next.capacityMode &&
  prev.lang === next.lang
);

function KanbanBoard({ columns, onSelectTask, loading, capacityMode, tr, lang }) {'''

        virtualized_block = '''const MemoTaskCard = memo(TaskCard, (prev, next) =>
  prev.task === next.task &&
  prev.capacityMode === next.capacityMode &&
  prev.lang === next.lang
);

function VirtualTaskList({ tasks, onSelectTask, capacityMode, tr, lang, emptyLabel }) {
  // TOS_DQ_PERFORMANCE_V3: only mount the cards visible in each Kanban column.
  const scrollRef = useRef(null);
  const virtualizer = useVirtualizer({
    count: tasks.length,
    getScrollElement: () => scrollRef.current,
    estimateSize: () => 154,
    overscan: 4,
    getItemKey: (index) => tasks[index]?.id || index,
  });
  const virtualItems = virtualizer.getVirtualItems();

  return (
    <div ref={scrollRef} className="min-h-0 flex-1 overflow-y-auto p-2">
      {!tasks.length ? (
        <div className="grid min-h-20 place-items-center rounded-xl border border-dashed border-zinc-200 bg-white/70 px-3 text-center text-[11px] font-bold text-zinc-400 dark:border-white/10 dark:bg-white/[0.02]">{emptyLabel}</div>
      ) : (
        <div className="relative w-full" style={{ height: `${virtualizer.getTotalSize()}px` }}>
          {virtualItems.map((item) => {
            const task = tasks[item.index];
            return (
              <div
                key={task.id}
                data-index={item.index}
                ref={virtualizer.measureElement}
                className="absolute left-0 top-0 w-full pb-2"
                style={{ transform: `translateY(${item.start}px)` }}
              >
                <MemoTaskCard task={task} onSelect={onSelectTask} capacityMode={capacityMode} tr={tr} lang={lang} />
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function KanbanBoard({ columns, onSelectTask, loading, capacityMode, tr, lang }) {'''

        dq = replace_once(dq, insertion_anchor, virtualized_block, 'virtual list insertion')

        old_list = '''<div className="min-h-0 flex-1 space-y-2 overflow-y-auto p-2">{tasks.map((task) => <MemoTaskCard key={task.id} task={task} onSelect={onSelectTask} capacityMode={capacityMode} tr={tr} lang={lang} />)}{!tasks.length && <div className="grid min-h-20 place-items-center rounded-xl border border-dashed border-zinc-200 bg-white/70 px-3 text-center text-[11px] font-bold text-zinc-400 dark:border-white/10 dark:bg-white/[0.02]">{tr.queue.noColumnTasks}</div>}</div>'''
        new_list = '''<VirtualTaskList tasks={tasks} onSelectTask={onSelectTask} capacityMode={capacityMode} tr={tr} lang={lang} emptyLabel={tr.queue.noColumnTasks} />'''
        dq = replace_once(dq, old_list, new_list, 'Kanban task list virtualization')

        DQ.write_text(dq)
        applied_now = True

    text = DQ.read_text()
    if text.count(MARKER_V3) != 1:
        raise RuntimeError("Performance V3 marker missing or duplicated")
    if text.count('useVirtualizer({') != 1:
        raise RuntimeError("virtualizer hook missing or duplicated")
    if text.count('<VirtualTaskList tasks={tasks}') != 1:
        raise RuntimeError("virtual task list usage invalid")
    if 'tasks.map((task) => <MemoTaskCard' in text:
        raise RuntimeError("eager Kanban card map still present")
    if sha(PREF) != PREF_V1_SHA:
        raise RuntimeError("PreferencesContext changed unexpectedly")
    if sha(CSS) != CSS_V6_SHA:
        raise RuntimeError("V6 CSS changed unexpectedly")

    subprocess.run(["git", "-C", str(ROOT), "diff", "--check", "--", "frontend/src/pages/DesignQueuePage.jsx"], check=True)
    subprocess.run(["npm", "run", "build"], cwd=ROOT / "frontend", check=True)
    if not (DIST / "index.html").exists():
        raise RuntimeError("built dist index missing")

    stamp = time.strftime("%Y%m%d-%H%M%S")
    stage = LIVE_PARENT / f"build.phase04-1-design-queue-performance-v3.new.{int(time.time())}"
    backup = LIVE_PARENT / f"build.phase04-1-design-queue-performance-v3.backup-{stamp}"
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
print("KANBAN_VIRTUALIZED=YES")
print("EAGER_CARD_RENDER_REMOVED=YES")
print("OVERSCAN=4")
print("BUSINESS_LOGIC_CHANGED=NO")
print("DESIGN_CHANGED=NO")
print(f"DESIGN_QUEUE_SHA256={sha(DQ)}")
print(f"PREFERENCES_CONTEXT_SHA256={sha(PREF)}")
print(f"INDEX_CSS_SHA256={sha(CSS)}")
