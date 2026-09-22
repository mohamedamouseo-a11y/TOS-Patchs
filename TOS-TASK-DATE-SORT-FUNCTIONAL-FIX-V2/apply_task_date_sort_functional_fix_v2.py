#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
FILES = {
    "workspace": ROOT / "frontend/src/pages/MyTaskWorkspace.jsx",
    "board": ROOT / "frontend/src/components/ProfessionalTaskBoard.jsx",
    "backend": ROOT / "backend/src/routes/tasks.routes.js",
}
MARKER = "TOS_TASK_DATE_SORT_FUNCTIONAL_FIX_V2"

def fail(message, originals=None):
    if originals:
        for key, content in originals.items():
            FILES[key].write_text(content, encoding="utf-8")
    print("PATCH=FAIL")
    print(f"ERROR={message}")
    raise SystemExit(1)

if not (ROOT / ".git").is_dir():
    fail(f"TOS git repository not found: {ROOT}")
for key, path in FILES.items():
    if not path.is_file():
        fail(f"Missing target: {path.relative_to(ROOT)}")

originals = {key: path.read_text(encoding="utf-8") for key, path in FILES.items()}

if all(MARKER in content for content in originals.values()):
    print("PATCH=PASS")
    print("ACTION=ALREADY_APPLIED")
    print("ROOT_CAUSE_MY_WORKSPACE=createdAt_was_stripped_from_summary_payload")
    print("ROOT_CAUSE_TASK_BOARD=date_sort_was_not_enforced_per_column")
    print("FILES_CHANGED=0")
    raise SystemExit(0)

workspace = originals["workspace"]
board = originals["board"]
backend = originals["backend"]

backend_old = '''    assigneeId: task.assigneeId || null,
    assigneeIds: taskAssigneeIds(task),
    project: task.project ? { id: task.project.id, name: task.project.name } : null,''';
backend_new = '''    assigneeId: task.assigneeId || null,
    assigneeIds: taskAssigneeIds(task),
    // TOS_TASK_DATE_SORT_FUNCTIONAL_FIX_V2
    createdAt: task.createdAt || null,
    updatedAt: task.updatedAt || null,
    project: task.project ? { id: task.project.id, name: task.project.name } : null,''';

workspace_old = '''  const groupedTasks = useMemo(() => {
    const grouped = Object.fromEntries(workspaceColumns.map((column) => [column.id, []]));
    filteredTasks.forEach((task) => {
      const columnId = getColumnForTask(task);
      grouped[columnId] = grouped[columnId] || [];
      grouped[columnId].push(task);
    });
    return grouped;
  }, [filteredTasks]);''';
workspace_new = '''  const groupedTasks = useMemo(() => {
    const grouped = Object.fromEntries(workspaceColumns.map((column) => [column.id, []]));
    filteredTasks.forEach((task) => {
      const columnId = getColumnForTask(task);
      grouped[columnId] = grouped[columnId] || [];
      grouped[columnId].push(task);
    });
    // TOS_TASK_DATE_SORT_FUNCTIONAL_FIX_V2
    if (filters.sort === "newest" || filters.sort === "oldest") {
      const direction = filters.sort === "oldest" ? 1 : -1;
      const createdTime = (task) => {
        for (const candidate of [task?.createdAt, task?.updatedAt]) {
          const value = new Date(candidate || 0).getTime();
          if (Number.isFinite(value) && value > 0) return value;
        }
        return 0;
      };
      Object.keys(grouped).forEach((key) => {
        grouped[key] = [...grouped[key]].sort((a, b) => (
          direction * (createdTime(a) - createdTime(b))
          || String(a.id || "").localeCompare(String(b.id || ""))
        ));
      });
    }
    return grouped;
  }, [filteredTasks, filters.sort]);''';

board_old = '''  const grouped = useMemo(() => {
    const map = new Map(lists.map((list) => [list.id, []]));
    for (const task of boardTasks) {
      const listId = task.listId || lists.find((list) => list.status === task.status)?.id || lists[0]?.id;
      if (!map.has(listId)) map.set(listId, []);
      map.get(listId).push(task);
    }
    for (const [key, cards] of map.entries()) map.set(key, taskDateSort === "board" ? sortCards(cards) : cards);
    return map;
  }, [boardTasks, lists, taskDateSort]);''';
board_new = '''  const grouped = useMemo(() => {
    const map = new Map(lists.map((list) => [list.id, []]));
    for (const task of boardTasks) {
      const listId = task.listId || lists.find((list) => list.status === task.status)?.id || lists[0]?.id;
      if (!map.has(listId)) map.set(listId, []);
      map.get(listId).push(task);
    }
    // TOS_TASK_DATE_SORT_FUNCTIONAL_FIX_V2
    const createdTime = (task) => {
      for (const candidate of [task?.createdAt, task?.updatedAt]) {
        const value = new Date(candidate || 0).getTime();
        if (Number.isFinite(value) && value > 0) return value;
      }
      return 0;
    };
    for (const [key, cards] of map.entries()) {
      if (taskDateSort === "board") {
        map.set(key, sortCards(cards));
        continue;
      }
      const direction = taskDateSort === "oldest" ? 1 : -1;
      map.set(key, [...cards].sort((a, b) => (
        direction * (createdTime(a) - createdTime(b))
        || (b.position || 0) - (a.position || 0)
        || String(a.id || "").localeCompare(String(b.id || ""))
      )));
    }
    return map;
  }, [boardTasks, lists, taskDateSort]);''';

for label, source, old in [
    ("backend safeMyWorkspaceTask", backend, backend_old),
    ("MyTaskWorkspace groupedTasks", workspace, workspace_old),
    ("ProfessionalTaskBoard grouped", board, board_old),
]:
    count = source.count(old)
    if count != 1:
        fail(f"{label} anchor expected once, found {count}")

backend = backend.replace(backend_old, backend_new, 1)
workspace = workspace.replace(workspace_old, workspace_new, 1)
board = board.replace(board_old, board_new, 1)

FILES["backend"].write_text(backend, encoding="utf-8")
FILES["workspace"].write_text(workspace, encoding="utf-8")
FILES["board"].write_text(board, encoding="utf-8")

try:
    subprocess.run(
        ["git", "-C", str(ROOT), "diff", "--check", "--",
         "backend/src/routes/tasks.routes.js",
         "frontend/src/pages/MyTaskWorkspace.jsx",
         "frontend/src/components/ProfessionalTaskBoard.jsx"],
        check=True,
    )
except Exception:
    fail("git diff --check failed; originals restored", originals)

required = {
    "backend": [
        MARKER,
        "createdAt: task.createdAt || null",
        "updatedAt: task.updatedAt || null",
    ],
    "workspace": [
        MARKER,
        'filters.sort === "newest" || filters.sort === "oldest"',
        "Object.keys(grouped).forEach",
    ],
    "board": [
        MARKER,
        'taskDateSort === "board"',
        'taskDateSort === "oldest" ? 1 : -1',
    ],
}
for key, needles in required.items():
    content = FILES[key].read_text(encoding="utf-8")
    missing = [needle for needle in needles if needle not in content]
    if missing:
        fail(f"Post-patch validation failed for {key}: {missing}", originals)

print("PATCH=PASS")
print("ACTION=APPLIED")
print("ROOT_CAUSE_MY_WORKSPACE=createdAt_was_stripped_from_summary_payload")
print("ROOT_CAUSE_TASK_BOARD=date_sort_was_not_enforced_per_column")
print("MY_WORKSPACE_SORT=createdAt_per_column")
print("TASK_BOARD_SORT=createdAt_per_column")
print("FALLBACK=updatedAt_only_if_createdAt_missing")
print("DEFAULT_ORDER=PRESERVED")
print("DB_CHANGES=NONE")
print("FILES_CHANGED=backend/src/routes/tasks.routes.js,frontend/src/pages/MyTaskWorkspace.jsx,frontend/src/components/ProfessionalTaskBoard.jsx")
print("BUILD=NOT_RUN")
print("DEPLOY=NOT_RUN")
