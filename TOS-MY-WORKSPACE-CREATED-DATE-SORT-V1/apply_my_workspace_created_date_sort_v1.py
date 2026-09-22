#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
REL = Path("frontend/src/pages/MyTaskWorkspace.jsx")
TARGET = ROOT / REL
MARKER = "TOS_MY_WORKSPACE_CREATED_DATE_SORT_V1"

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
        'sort: ""',
        'filters.sort === "oldest" ? 1 : -1',
        '<option value="newest">{isAr ? "الأحدث أولًا" : "Newest first"}</option>',
        '<option value="oldest">{isAr ? "الأقدم أولًا" : "Oldest first"}</option>',
    ]
    if any(item not in original for item in required):
        fail("Marker exists but implementation is incomplete")
    print("PATCH=PASS")
    print("ACTION=ALREADY_APPLIED")
    print("DATE_FIELD=createdAt")
    print("SORT_OPTIONS=default,newest,oldest")
    print("FILES_CHANGED=0")
    raise SystemExit(0)

replacements = [
    (
'''  const [filters, setFilters] = useState({ search: "", projectId: "", day: "", month: "" });''',
'''  // TOS_MY_WORKSPACE_CREATED_DATE_SORT_V1
  const [filters, setFilters] = useState({ search: "", projectId: "", day: "", month: "", sort: "" });'''
    ),
    (
'''  const filteredTasks = useMemo(() => {
    const normalizedSearch = filters.search.trim().toLowerCase();
    return tasks.filter((task) => {
      if (normalizedSearch && !String(task.title || "").toLowerCase().includes(normalizedSearch)) return false;
      if (filters.projectId === personalProjectFilterValue && task.projectId) return false;
      if (filters.projectId && filters.projectId !== personalProjectFilterValue && task.projectId !== filters.projectId) return false;
      if (filters.day && formatDateKey(task.dueDate) !== filters.day) return false;
      if (filters.month && formatMonthKey(task.dueDate) !== filters.month) return false;
      return true;
    });
  }, [filters, tasks]);''',
'''  const filteredTasks = useMemo(() => {
    const normalizedSearch = filters.search.trim().toLowerCase();
    const result = tasks.filter((task) => {
      if (normalizedSearch && !String(task.title || "").toLowerCase().includes(normalizedSearch)) return false;
      if (filters.projectId === personalProjectFilterValue && task.projectId) return false;
      if (filters.projectId && filters.projectId !== personalProjectFilterValue && task.projectId !== filters.projectId) return false;
      if (filters.day && formatDateKey(task.dueDate) !== filters.day) return false;
      if (filters.month && formatMonthKey(task.dueDate) !== filters.month) return false;
      return true;
    });
    if (!filters.sort) return result;
    const direction = filters.sort === "oldest" ? 1 : -1;
    const createdTime = (task) => {
      const value = new Date(task?.createdAt || 0).getTime();
      return Number.isFinite(value) ? value : 0;
    };
    return [...result].sort((a, b) => (
      direction * (createdTime(a) - createdTime(b))
      || String(a.id || "").localeCompare(String(b.id || ""))
    ));
  }, [filters, tasks]);'''
    ),
    (
'''        <div className="grid gap-2.5 lg:grid-cols-[minmax(240px,1.4fr)_minmax(170px,0.8fr)_minmax(150px,0.7fr)_minmax(150px,0.7fr)]">''',
'''        <div className="grid gap-2.5 lg:grid-cols-[minmax(240px,1.4fr)_minmax(170px,0.8fr)_minmax(150px,0.7fr)_minmax(150px,0.7fr)_minmax(160px,0.75fr)]">'''
    ),
    (
'''          <select value={filters.month} onChange={(event) => updateFilter("month", event.target.value)} className="h-10 rounded-xl border border-zinc-200 bg-white px-3 text-xs font-black text-zinc-700 outline-none transition focus:border-amber-300 focus:ring-4 focus:ring-amber-50 dark:border-white/10 dark:bg-zinc-950 dark:text-zinc-100 dark:focus:ring-amber-500/10">
            <option value="">{isAr ? "الشهر" : "Month"}</option>
            {monthOptions.map((month) => <option key={month.value} value={month.value}>{month.label}</option>)}
          </select>''',
'''          <select value={filters.month} onChange={(event) => updateFilter("month", event.target.value)} className="h-10 rounded-xl border border-zinc-200 bg-white px-3 text-xs font-black text-zinc-700 outline-none transition focus:border-amber-300 focus:ring-4 focus:ring-amber-50 dark:border-white/10 dark:bg-zinc-950 dark:text-zinc-100 dark:focus:ring-amber-500/10">
            <option value="">{isAr ? "الشهر" : "Month"}</option>
            {monthOptions.map((month) => <option key={month.value} value={month.value}>{month.label}</option>)}
          </select>
          <select value={filters.sort} onChange={(event) => updateFilter("sort", event.target.value)} className="h-10 rounded-xl border border-zinc-200 bg-white px-3 text-xs font-black text-zinc-700 outline-none transition focus:border-amber-300 focus:ring-4 focus:ring-amber-50 dark:border-white/10 dark:bg-zinc-950 dark:text-zinc-100 dark:focus:ring-amber-500/10">
            <option value="">{isAr ? "ترتيب التاريخ" : "Date order"}</option>
            <option value="newest">{isAr ? "الأحدث أولًا" : "Newest first"}</option>
            <option value="oldest">{isAr ? "الأقدم أولًا" : "Oldest first"}</option>
          </select>'''
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
    'sort: ""',
    'filters.sort === "oldest" ? 1 : -1',
    '<option value="newest">{isAr ? "الأحدث أولًا" : "Newest first"}</option>',
    '<option value="oldest">{isAr ? "الأقدم أولًا" : "Oldest first"}</option>',
]
if any(item not in patched for item in required_after):
    fail("Post-patch validation failed")

TARGET.write_text(patched, encoding="utf-8")
try:
    subprocess.run(["git", "-C", str(ROOT), "diff", "--check", "--", str(REL)], check=True)
except Exception:
    TARGET.write_text(original, encoding="utf-8")
    fail("git diff --check failed; source restored")

print("PATCH=PASS")
print("ACTION=APPLIED")
print("SCREEN=MY_WORKSPACE")
print("DATE_FIELD=createdAt")
print("SORT_OPTIONS=default,newest,oldest")
print("EXISTING_FILTERS=PRESERVED")
print(f"FILES_CHANGED={REL}")
print("BUILD=NOT_RUN")
print("DEPLOY=NOT_RUN")
