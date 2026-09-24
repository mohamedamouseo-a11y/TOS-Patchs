#!/usr/bin/env python3
# TOS-TASK-BOARD-TRELLO-DRAG-DROP-V1
# Frontend-only patch. No backend/DB/dependency changes.

from pathlib import Path
import shutil
import sys
import time

ROOT = Path.cwd()
BOARD = ROOT / "frontend/src/components/ProfessionalTaskBoard.jsx"
PARTS = ROOT / "frontend/src/features/tasks/taskBoardParts.jsx"
MARKER = "TOS_TASK_BOARD_TRELLO_DRAG_DROP_V1"

def die(msg):
    print(f"PATCH=FAIL\nERROR={msg}")
    sys.exit(1)

def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        die(f"{label}: expected exactly 1 anchor, found {count}")
    return text.replace(old, new, 1)

for file in (BOARD, PARTS):
    if not file.exists():
        die(f"missing file: {file}")

board = BOARD.read_text(encoding="utf-8")
parts = PARTS.read_text(encoding="utf-8")

if MARKER in board or MARKER in parts:
    print("PATCH=SKIP_ALREADY_APPLIED")
    sys.exit(0)

stamp = int(time.time())
for file in (BOARD, PARTS):
    shutil.copy2(file, file.with_name(file.name + f".bak-trello-dnd-v1-{stamp}"))

board = replace_once(
    board,
    '''  const [draggedTaskId, setDraggedTaskId] = useState(null);
  const [draggedListId, setDraggedListId] = useState(null);''',
    '''  const [draggedTaskId, setDraggedTaskId] = useState(null);
  // TOS_TASK_BOARD_TRELLO_DRAG_DROP_V1
  const [dragOverTaskId, setDragOverTaskId] = useState("");
  const [dragInsertEdge, setDragInsertEdge] = useState("");
  const [draggedListId, setDraggedListId] = useState(null);''',
    "board drag state",
)

old_handlers = '''  function handleDragStart(event, taskId) {
    if (!event?.dataTransfer) return;
    setDraggedTaskId(taskId);
    event.dataTransfer.effectAllowed = "move";
    event.dataTransfer.setData("text/plain", taskId);
  }

  function handleDragEnd() {
    setDraggedTaskId(null);
    setDropTargetListId("");
  }

  async function handleColumnDrop(event, list) {
    event.preventDefault();
    const taskId = event.dataTransfer.getData("text/plain") || draggedTaskId;
    const task = tasks.find((item) => item.id === taskId);
    setDraggedTaskId(null);
    setDropTargetListId("");
    setDropTargetListId("");
    if (!task) return;
    await moveCard(task, list);
  }

  async function handleCardDrop(event, targetTask) {
    event.preventDefault();
    event.stopPropagation();
    const taskId = event.dataTransfer.getData("text/plain") || draggedTaskId;
    const task = tasks.find((item) => item.id === taskId);
    setDraggedTaskId(null);
    if (!task || task.id === targetTask.id) return;

    const targetList = lists.find((list) => list.id === targetTask.listId) || lists.find((list) => list.status === targetTask.status) || lists[0];
    if (!targetList) return;
    const columnTasks = (grouped.get(targetList.id) || []).filter((item) => item.id !== task.id);
    const targetIndex = columnTasks.findIndex((item) => item.id === targetTask.id);
    const rect = event.currentTarget.getBoundingClientRect();
    const insertBefore = event.clientY < rect.top + rect.height / 2;
    const insertIndex = insertBefore ? targetIndex : targetIndex + 1;
    await moveCard(task, targetList, insertIndex);
  }
'''

new_handlers = '''  function resetCardDragUi() {
    setDraggedTaskId(null);
    setDropTargetListId("");
    setDragOverTaskId("");
    setDragInsertEdge("");
  }

  function handleDragStart(event, taskId) {
    if (!event?.dataTransfer) return;
    setDraggedTaskId(taskId);
    setDragOverTaskId("");
    setDragInsertEdge("");
    event.dataTransfer.effectAllowed = "move";
    event.dataTransfer.setData("application/x-tos-task", taskId);
    event.dataTransfer.setData("text/plain", taskId);
  }

  function handleDragEnd() {
    resetCardDragUi();
  }

  function handleCardDragOver(event, targetTask) {
    if (!draggedTaskId || draggedListId || !targetTask || targetTask.id === draggedTaskId) return;
    event.preventDefault();
    event.stopPropagation();
    if (event.dataTransfer) event.dataTransfer.dropEffect = "move";

    const rect = event.currentTarget.getBoundingClientRect();
    const edge = event.clientY < rect.top + rect.height / 2 ? "before" : "after";
    setDragOverTaskId(targetTask.id);
    setDragInsertEdge(edge);

    const targetListId = targetTask.listId || lists.find((list) => list.status === targetTask.status)?.id || "";
    if (targetListId) setDropTargetListId(targetListId);
  }

  async function handleColumnDrop(event, list) {
    event.preventDefault();
    const taskId = event.dataTransfer.getData("application/x-tos-task") || event.dataTransfer.getData("text/plain") || draggedTaskId;
    const task = tasks.find((item) => item.id === taskId);
    resetCardDragUi();
    if (!task) return;
    await moveCard(task, list);
  }

  async function handleCardDrop(event, targetTask) {
    event.preventDefault();
    event.stopPropagation();
    const taskId = event.dataTransfer.getData("application/x-tos-task") || event.dataTransfer.getData("text/plain") || draggedTaskId;
    const task = tasks.find((item) => item.id === taskId);
    const rememberedEdge = dragOverTaskId === targetTask.id ? dragInsertEdge : "";
    resetCardDragUi();
    if (!task || task.id === targetTask.id) return;

    const targetList = lists.find((list) => list.id === targetTask.listId) || lists.find((list) => list.status === targetTask.status) || lists[0];
    if (!targetList) return;
    const columnTasks = (grouped.get(targetList.id) || []).filter((item) => item.id !== task.id);
    const targetIndex = columnTasks.findIndex((item) => item.id === targetTask.id);
    const rect = event.currentTarget.getBoundingClientRect();
    const insertBefore = rememberedEdge
      ? rememberedEdge === "before"
      : event.clientY < rect.top + rect.height / 2;
    const insertIndex = insertBefore ? targetIndex : targetIndex + 1;
    await moveCard(task, targetList, insertIndex);
  }
'''

board = replace_once(board, old_handlers, new_handlers, "board drag handlers")

board = replace_once(
    board,
    '''                                onDragStart={handleDragStart}
                                onDragEnd={handleDragEnd}
                                onDropOnCard={handleCardDrop}
                                isDragging={draggedTaskId === task.id}''',
    '''                                onDragStart={handleDragStart}
                                onDragEnd={handleDragEnd}
                                onDragOverCard={handleCardDragOver}
                                onDropOnCard={handleCardDrop}
                                dragInsertEdge={dragOverTaskId === task.id ? dragInsertEdge : ""}
                                isDragging={draggedTaskId === task.id}''',
    "TaskCard drag props",
)

parts = replace_once(
    parts,
    '''function TaskCard({ task, density = "comfortable", lists = [], onOpen, onOpenDetails, onPrefetch = null, onDone, onArchive, onEditDesignRequest = null, onMoveToList, onDragStart, onDragEnd, onDropOnCard, isDragging, canEditCards, canArchiveCards, canComment = false, onSendWaitingClientReply = null, selected = false, quickOpen = false, onToggleSelected, ui = getTaskUiText("en") }) {''',
    '''function TaskCard({ task, density = "comfortable", lists = [], onOpen, onOpenDetails, onPrefetch = null, onDone, onArchive, onEditDesignRequest = null, onMoveToList, onDragStart, onDragEnd, onDragOverCard, onDropOnCard, dragInsertEdge = "", isDragging, canEditCards, canArchiveCards, canComment = false, onSendWaitingClientReply = null, selected = false, quickOpen = false, onToggleSelected, ui = getTaskUiText("en") }) {''',
    "TaskCard signature",
)

parts = replace_once(
    parts,
    '''      onDragStart={(event) => {
        if (!canEditCards) return;
        if (typeof window !== "undefined") window.getSelection?.()?.removeAllRanges?.();
        onDragStart(event, task.id);
      }}
      onDragEnd={onDragEnd}
      onDragOver={(event) => event.preventDefault()}
      onDrop={(event) => onDropOnCard(event, task)}
      initial={false}
      animate={{ opacity: isDragging || isTouchDragging ? 0.5 : 1 }}
      transition={{ duration: 0 }}
      className={`tos-modern-task-card group relative select-none overflow-hidden rounded-[22px] border bg-white shadow-[0_8px_24px_rgba(15,23,42,0.05)] ring-1 transition-colors duration-150 hover:border-slate-300 hover:shadow-[0_10px_26px_rgba(15,23,42,0.06)] active:cursor-grabbing dark:bg-zinc-950 dark:shadow-black/30 dark:ring-white/5 dark:hover:border-white/20 ${cardStateClass} ${isTouchDragging ? "z-30 cursor-grabbing ring-4 ring-slate-200 dark:ring-white/20" : ""}`}
    >
      <div''',
    '''      onDragStart={(event) => {
        if (!canEditCards) return;
        const interactiveTarget = event.target?.closest?.("button,input,select,textarea,a,[contenteditable='true']");
        if (interactiveTarget) {
          event.preventDefault();
          return;
        }
        if (typeof window !== "undefined") window.getSelection?.()?.removeAllRanges?.();
        onDragStart(event, task.id);
      }}
      onDragEnd={onDragEnd}
      onDragOver={(event) => {
        if (!canEditCards) return;
        event.preventDefault();
        onDragOverCard?.(event, task);
      }}
      onDrop={(event) => onDropOnCard(event, task)}
      initial={false}
      animate={{
        opacity: isDragging || isTouchDragging ? 0.48 : 1,
        scale: isDragging || isTouchDragging ? 0.985 : 1,
      }}
      transition={{ duration: 0.08 }}
      data-tos-trello-dnd="v1"
      className={`tos-modern-task-card group relative select-none overflow-visible rounded-[22px] border bg-white shadow-[0_8px_24px_rgba(15,23,42,0.05)] ring-1 transition-[border-color,box-shadow,transform,opacity] duration-150 hover:border-slate-300 hover:shadow-[0_10px_26px_rgba(15,23,42,0.06)] dark:bg-zinc-950 dark:shadow-black/30 dark:ring-white/5 dark:hover:border-white/20 ${canEditCards ? "cursor-grab active:cursor-grabbing" : ""} ${cardStateClass} ${isTouchDragging ? "z-30 cursor-grabbing ring-4 ring-slate-200 dark:ring-white/20" : ""}`}
    >
      {dragInsertEdge === "before" && (
        <div aria-hidden="true" className="pointer-events-none absolute -top-[7px] inset-x-2 z-30 flex items-center">
          <span className="h-3 w-3 shrink-0 rounded-full border-2 border-white bg-blue-600 shadow-sm dark:border-zinc-950" />
          <span className="h-[3px] flex-1 rounded-full bg-blue-600 shadow-[0_0_0_2px_rgba(37,99,235,0.12)]" />
        </div>
      )}
      {dragInsertEdge === "after" && (
        <div aria-hidden="true" className="pointer-events-none absolute -bottom-[7px] inset-x-2 z-30 flex items-center">
          <span className="h-3 w-3 shrink-0 rounded-full border-2 border-white bg-blue-600 shadow-sm dark:border-zinc-950" />
          <span className="h-[3px] flex-1 rounded-full bg-blue-600 shadow-[0_0_0_2px_rgba(37,99,235,0.12)]" />
        </div>
      )}
      {canEditCards && (
        <span aria-hidden="true" className="pointer-events-none absolute end-2 top-2 z-20 grid h-7 w-7 place-items-center rounded-lg border border-slate-200 bg-white/90 text-slate-400 opacity-0 shadow-sm backdrop-blur transition-opacity group-hover:opacity-100 dark:border-white/10 dark:bg-zinc-900/90 dark:text-zinc-500">
          <GripVertical size={14} />
        </span>
      )}
      <div''',
    "TaskCard DnD surface",
)

parts = replace_once(
    parts,
    '''        className={`relative flex ${isCompact ? "min-h-[148px]" : "min-h-[166px]"} w-full cursor-pointer flex-col p-3 focus:outline-none focus:ring-4 focus:ring-slate-100 dark:focus:ring-white/10 ${titleDirection === "rtl" ? "text-right" : "text-left"}`}''',
    '''        className={`relative flex ${isCompact ? "min-h-[148px]" : "min-h-[166px]"} w-full flex-col p-3 focus:outline-none focus:ring-4 focus:ring-slate-100 dark:focus:ring-white/10 ${canEditCards ? "cursor-grab pe-10 active:cursor-grabbing" : "cursor-pointer"} ${titleDirection === "rtl" ? "text-right" : "text-left"}`}''',
    "TaskCard cursor/grip spacing",
)

BOARD.write_text(board, encoding="utf-8")
PARTS.write_text(parts, encoding="utf-8")

print("PATCH=PASS")
print("PATCH_NAME=TOS-TASK-BOARD-TRELLO-DRAG-DROP-V1")
print(f"FILES_CHANGED={BOARD.relative_to(ROOT)};{PARTS.relative_to(ROOT)}")
print("BACKEND_UNCHANGED=YES")
print("DB_UNCHANGED=YES")
print("DEPENDENCIES_ADDED=NO")
print("EXISTING_MOVE_API_PRESERVED=YES")
print("WAITING_CLIENT_REASON_GATE_PRESERVED=YES")
print("PERMISSION_ENGINE_PRESERVED=YES")
print("NEXT=build frontend, deploy atomically, verify /tasks")
