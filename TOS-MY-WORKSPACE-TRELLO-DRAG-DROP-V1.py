#!/usr/bin/env python3
# TOS-MY-WORKSPACE-TRELLO-DRAG-DROP-V1
# Adds native Trello-style mouse drag/drop to MyTaskWorkspace.
# Frontend-only: uses existing updateTask/updateMyWorkspaceTask/reorderMyWorkspace APIs.

from pathlib import Path
import shutil
import sys
import time

ROOT = Path.cwd()
TARGET = ROOT / "frontend/src/pages/MyTaskWorkspace.jsx"
MARKER = "TOS_MY_WORKSPACE_TRELLO_DRAG_DROP_V1"

def die(message):
    print(f"PATCH=FAIL\nERROR={message}")
    sys.exit(1)

def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        die(f"{label}: expected exactly 1 anchor, found {count}")
    return text.replace(old, new, 1)

if not TARGET.exists():
    die(f"missing file: {TARGET}")

source = TARGET.read_text(encoding="utf-8")
if MARKER in source:
    print("PATCH=SKIP_ALREADY_APPLIED")
    sys.exit(0)

backup = TARGET.with_name(TARGET.name + f".bak-my-workspace-trello-dnd-v1-{int(time.time())}")
shutil.copy2(TARGET, backup)

source = replace_once(
    source,
    '''  FolderSearch,
  Link2,''',
    '''  FolderSearch,
  GripVertical,
  Link2,''',
    "GripVertical import",
)

source = replace_once(
    source,
    '''function WorkspaceTaskCard({ task, ui, isAr, onOpenTask, onOpenSettings, canManagePersonalTask }) {''',
    '''function WorkspaceTaskCard({
  task,
  ui,
  isAr,
  onOpenTask,
  onOpenSettings,
  canManagePersonalTask,
  canDrag = false,
  onDragStart = null,
  onDragEnd = null,
  onDragOverCard = null,
  onDropOnCard = null,
  dragInsertEdge = "",
  isDragging = false,
}) {''',
    "WorkspaceTaskCard signature",
)

source = replace_once(
    source,
    '''  return (
    <article className="group rounded-[16px] border border-zinc-100 bg-white px-2.5 py-2.5 shadow-sm shadow-zinc-200/35 transition hover:-translate-y-0.5 hover:border-amber-200 hover:shadow-md hover:shadow-amber-100/35 dark:border-white/10 dark:bg-zinc-950 dark:shadow-black/20 dark:hover:border-amber-400/40">
      {coverPreview ? (''',
    '''  return (
    <article
      draggable={canDrag}
      data-my-workspace-card-id={task.id}
      data-tos-my-workspace-trello-dnd="v1"
      onDragStart={(event) => {
        if (!canDrag) {
          event.preventDefault();
          return;
        }
        if (event.target?.closest?.("button,input,select,textarea,a,[contenteditable='true']")) {
          event.preventDefault();
          return;
        }
        onDragStart?.(event, task);
      }}
      onDragEnd={() => onDragEnd?.()}
      onDragOver={(event) => {
        if (!canDrag) return;
        onDragOverCard?.(event, task);
      }}
      onDrop={(event) => onDropOnCard?.(event, task)}
      className={`group relative rounded-[16px] border bg-white px-2.5 py-2.5 shadow-sm transition-[border-color,box-shadow,transform,opacity] duration-150 dark:bg-zinc-950 dark:shadow-black/20 ${
        canDrag ? "cursor-grab active:cursor-grabbing" : ""
      } ${
        isDragging
          ? "scale-[0.985] border-amber-300 opacity-45 shadow-lg shadow-amber-100/40 dark:border-amber-400/50"
          : "border-zinc-100 shadow-zinc-200/35 hover:-translate-y-0.5 hover:border-amber-200 hover:shadow-md hover:shadow-amber-100/35 dark:border-white/10 dark:hover:border-amber-400/40"
      }`}
    >
      {dragInsertEdge === "before" ? (
        <div aria-hidden="true" className="pointer-events-none absolute -top-[6px] inset-x-2 z-20 flex items-center">
          <span className="h-2.5 w-2.5 shrink-0 rounded-full border-2 border-white bg-amber-500 shadow-sm dark:border-zinc-950" />
          <span className="h-[3px] flex-1 rounded-full bg-amber-500 shadow-[0_0_0_2px_rgba(245,158,11,0.14)]" />
        </div>
      ) : null}
      {dragInsertEdge === "after" ? (
        <div aria-hidden="true" className="pointer-events-none absolute -bottom-[6px] inset-x-2 z-20 flex items-center">
          <span className="h-2.5 w-2.5 shrink-0 rounded-full border-2 border-white bg-amber-500 shadow-sm dark:border-zinc-950" />
          <span className="h-[3px] flex-1 rounded-full bg-amber-500 shadow-[0_0_0_2px_rgba(245,158,11,0.14)]" />
        </div>
      ) : null}
      {canDrag ? (
        <span
          aria-hidden="true"
          className="pointer-events-none absolute end-2 top-2 z-10 grid h-7 w-7 place-items-center rounded-lg border border-zinc-200 bg-white/95 text-zinc-400 opacity-0 shadow-sm backdrop-blur transition-opacity group-hover:opacity-100 dark:border-white/10 dark:bg-zinc-900/95 dark:text-zinc-500"
        >
          <GripVertical size={14} />
        </span>
      ) : null}
      {coverPreview ? (''',
    "WorkspaceTaskCard draggable shell",
)

source = replace_once(
    source,
    '''  const [savingTask, setSavingTask] = useState(false);
  const [taskFormError, setTaskFormError] = useState("");''',
    '''  const [savingTask, setSavingTask] = useState(false);
  const [taskFormError, setTaskFormError] = useState("");
  // TOS_MY_WORKSPACE_TRELLO_DRAG_DROP_V1
  const [draggedTaskId, setDraggedTaskId] = useState("");
  const [dragOverTaskId, setDragOverTaskId] = useState("");
  const [dragInsertEdge, setDragInsertEdge] = useState("");
  const [dropTargetColumnId, setDropTargetColumnId] = useState("");
  const [dragBusyTaskId, setDragBusyTaskId] = useState("");
  const [waitingClientMoveDraft, setWaitingClientMoveDraft] = useState(null);''',
    "workspace drag state",
)

grouped_anchor = '''  }, [filteredTasks, filters.sort]);

  function updateFilter(key, value) {'''

grouped_replacement = '''  }, [filteredTasks, filters.sort]);

  function resetWorkspaceDragUi() {
    setDraggedTaskId("");
    setDragOverTaskId("");
    setDragInsertEdge("");
    setDropTargetColumnId("");
  }

  function buildWorkspaceOrder(taskId, targetColumnId, targetTaskId = "", edge = "after") {
    const orderedIds = tasks.map((item) => item.id).filter((id) => id !== taskId);
    if (targetTaskId && orderedIds.includes(targetTaskId)) {
      const targetIndex = orderedIds.indexOf(targetTaskId);
      orderedIds.s