#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
REL = Path("frontend/src/components/ProfessionalTaskBoard.jsx")
TARGET = ROOT / REL
MARKER = "TOS_TASK_BOARD_CREATED_DATE_SORT_V1"

def fail(message):
    print("PATCH=FAIL")
    print(f"ERROR={message}")
    raise SystemExit(1)

if not (ROOT / ".git").is_dir():
    fail(f"TOS git repository not found: {ROOT}")
if not TARGET.is_file():
    fail(f"Missing target: {REL}")

original = TARGET.read_text(encoding="utf-8")

if MARKER in original:
    required = [
        'const [taskDateSort, setTaskDateSort] = useState("board");',
        'taskDateSort === "oldest" ? 1 : -1',
        'taskDateSort === "board" ? sortCards(cards) : cards',
        '<option value="newest">{isAr ? "الأحدث أولًا" : "Newest first"}</option>',
        '<option value="oldest">{isAr ? "الأقدم أولًا" : "Oldest first"}</option>',
        'cardDensity, taskDateSort',
    ]
    missing = [item for item in required if item not in original]
    if missing:
        fail("Marker exists but implementation is incomplete")
    print("PATCH=PASS")
    print("ACTION=ALREADY_APPLIED")
    print("DATE_FIELD=createdAt")
    print("SORT_OPTIONS=board,newest,oldest")
    print("SAVED_VIEW=PASS")
    print("FILES_CHANGED=0")
    raise SystemExit(0)

replacements = [
    (
'''  const [boardViewMode, setBoardViewMode] = useState("kanban");
  const [focusMode, setFocusMode] = useState(false);''',
'''  const [boardViewMode, setBoardViewMode] = useState("kanban");
  // TOS_TASK_BOARD_CREATED_DATE_SORT_V1
  const [taskDateSort, setTaskDateSort] = useState("board");
  const [focusMode, setFocusMode] = useState(false);'''
    ),
    (
'''  const boardTasks = useMemo(() => sortTasksForView(baseBoardTasks, boardViewMode, ui), [baseBoardTasks, boardViewMode, ui]);''',
'''  const boardTasks = useMemo(() => {
    const sortedForView = sortTasksForView(baseBoardTasks, boardViewMode, ui);
    if (taskDateSort === "board") return sortedForView;
    const direction = taskDateSort === "oldest" ? 1 : -1;
    const createdTime = (task) => {
      const value = new Date(task?.createdAt || 0).getTime();
      return Number.isFinite(value) ? value : 0;
    };
    return [...sortedForView].sort((a, b) => (
      direction * (createdTime(a) - createdTime(b))
      || (b.position || 0) - (a.position || 0)
      || String(a.id || "").localeCompare(String(b.id || ""))
    ));
  }, [baseBoardTasks, boardViewMode, taskDateSort, ui]);'''
    ),
    (
'''    for (const [key, cards] of map.entries()) map.set(key, sortCards(cards));
    return map;
  }, [boardTasks, lists]);''',
'''    for (const [key, cards] of map.entries()) map.set(key, taskDateSort === "board" ? sortCards(cards) : cards);
    return map;
  }, [boardTasks, lists, taskDateSort]);'''
    ),
    (
'''    setStatusFilter("");
    setActiveSavedViewId("");''',
'''    setStatusFilter("");
    setTaskDateSort("board");
    setActiveSavedViewId("");'''
    ),
    (
'''    return { query, quickFilter, dueFilter, priorityFilter, serviceTypeFilter, serviceIdFilter, departmentFilter, assigneeFilter, labelFilter, statusFilter, cardDensity };''',
'''    return { query, quickFilter, dueFilter, priorityFilter, serviceTypeFilter, serviceIdFilter, departmentFilter, assigneeFilter, labelFilter, statusFilter, cardDensity, taskDateSort };'''
    ),
    (
'''    setStatusFilter(filters.statusFilter || "");
    if (filters.cardDensity) setCardDensity(filters.cardDensity);''',
'''    setStatusFilter(filters.statusFilter || "");
    setTaskDateSort(["board", "newest", "oldest"].includes(filters.taskDateSort) ? filters.taskDateSort : "board");
    if (filters.cardDensity) setCardDensity(filters.cardDensity);'''
    ),
    (
'''                        <div className="rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-black text-slate-600 dark:border-white/10 dark:bg-zinc-900 dark:text-zinc-300">
                          {boardTasks.length} {isAr ? "مهمة ظاهرة" : "visible tasks"}
                        </div>''',
'''                        <div className="rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-black text-slate-600 dark:border-white/10 dark:bg-zinc-900 dark:text-zinc-300">
                          {boardTasks.length} {isAr ? "مهمة ظاهرة" : "visible tasks"}
                        </div>
                        <div className="relative">
                          <CalendarClock size={14} className={`pointer-events-none absolute top-1/2 -translate-y-1/2 text-slate-400 ${isAr ? "right-3" : "left-3"}`} />
                          <select
                            value={taskDateSort}
                            onChange={(event) => {
                              setTaskDateSort(event.target.value);
                              setActiveSavedViewId("");
                              setSelectedTaskIds([]);
                            }}
                            aria-label={isAr ? "ترتيب المهام حسب تاريخ الإنشاء" : "Sort tasks by creation date"}
                            title={isAr ? "ترتيب المهام حسب تاريخ الإنشاء" : "Sort tasks by creation date"}
                            className={`h-9 appearance-none rounded-2xl border border-slate-200 bg-slate-50 text-xs font-black text-slate-600 outline-none transition hover:bg-white focus:border-amber-300 focus:ring-4 focus:ring-amber-100/70 dark:border-white/10 dark:bg-zinc-900 dark:text-zinc-300 dark:focus:border-amber-400/40 dark:focus:ring-amber-500/10 ${isAr ? "pr-9 pl-8" : "pl-9 pr-8"}`}
                          >
                            <option value="board">{isAr ? "ترتيب اللوحة" : "Board order"}</option>
                            <option value="newest">{isAr ? "الأحدث أولًا" : "Newest first"}</option>
                            <option value="oldest">{isAr ? "الأقدم أولًا" : "Oldest first"}</option>
                          </select>
                          <ChevronDown size={14} className={`pointer-events-none absolute top-1/2 -translate-y-1/2 text-slate-400 ${isAr ? "left-3" : "right-3"}`} />
                        </div>'''
    ),
]

patched = original
for index, (old, new) in enumerate(replacements, start=1):
    count = patched.count(old)
    if count != 1:
        fail(f"Anchor {index} expected once, found {count}")
    patched = patched.replace(old, new, 1)

required_after = [
    MARKER,
    'const [taskDateSort, setTaskDateSort] = useState("board");',
    'taskDateSort === "oldest" ? 1 : -1',
    'taskDateSort === "board" ? sortCards(cards) : cards',
    '<option value="newest">{isAr ? "الأحدث أولًا" : "Newest first"}</option>',
    '<option value="oldest">{isAr ? "الأقدم أولًا" : "Oldest first"}</option>',
    'cardDensity, taskDateSort',
]
if any(item not in patched for item in required_after):
    fail("Post-patch validation failed")

TARGET.write_text(patched, encoding="utf-8")
try:
    subprocess.run(
        ["git", "-C", str(ROOT), "diff", "--check", "--", str(REL)],
        check=True,
    )
except Exception:
    TARGET.write_text(original, encoding="utf-8")
    fail("git diff --check failed; source restored")

print("PATCH=PASS")
print("ACTION=APPLIED")
print("DATE_FIELD=createdAt")
print("SORT_OPTIONS=board,newest,oldest")
print("SCOPE=ALL_VISIBLE_BOARD_TASKS")
print("EXISTING_FILTERS=PRESERVED")
print("MANUAL_BOARD_ORDER=PRESERVED_WHEN_BOARD_SELECTED")
print("SAVED_VIEW=PASS")
print(f"FILES_CHANGED={REL}")
print("BUILD=NOT_RUN")
print("DEPLOY=NOT_RUN")
