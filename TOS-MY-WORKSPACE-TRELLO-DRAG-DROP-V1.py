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
      orderedIds.splice(edge === "before" ? targetIndex : targetIndex + 1, 0, taskId);
      return orderedIds;
    }

    const targetColumnTaskIds = tasks
      .filter((item) => item.id !== taskId && getColumnForTask(item) === targetColumnId)
      .map((item) => item.id);
    const lastTargetId = targetColumnTaskIds[targetColumnTaskIds.length - 1];
    const insertIndex = lastTargetId && orderedIds.includes(lastTargetId)
      ? orderedIds.indexOf(lastTargetId) + 1
      : orderedIds.length;
    orderedIds.splice(insertIndex, 0, taskId);
    return orderedIds;
  }

  async function commitWorkspaceMove(task, targetColumn, targetTaskId = "", edge = "after", blockedReason = undefined) {
    if (!task?.id || !targetColumn?.id || dragBusyTaskId) return;
    const targetStatus = normalizeStatus(targetColumn.statuses?.[0] || "TODO");
    const currentStatus = normalizeStatus(task.status);
    const nextOrderIds = buildWorkspaceOrder(task.id, targetColumn.id, targetTaskId, edge);
    const previousTasks = tasks;

    const optimisticTask = {
      ...task,
      status: targetStatus,
      ...(targetStatus === "WAITING_CLIENT" && blockedReason !== undefined ? { blockedReason } : {}),
      ...(currentStatus === "WAITING_CLIENT" && targetStatus !== "WAITING_CLIENT" ? { blockedReason: null } : {}),
    };
    const optimisticMap = new Map(tasks.map((item) => [item.id, item.id === task.id ? optimisticTask : item]));
    setTasks(nextOrderIds.map((id) => optimisticMap.get(id)).filter(Boolean));
    setDragBusyTaskId(task.id);
    setError("");

    try {
      if (targetStatus !== currentStatus) {
        const statusPatch = {
          status: targetStatus,
          ...(targetStatus === "WAITING_CLIENT" && blockedReason !== undefined ? { blockedReason } : {}),
        };
        if (task.personalOwnerId === user?.id) {
          await tasksApi.updateMyWorkspaceTask(task.id, statusPatch);
        } else {
          await tasksApi.updateTask(task.id, statusPatch);
        }
      }
      await tasksApi.reorderMyWorkspace({ taskIds: nextOrderIds });
      await loadWorkspace({ showLoading: false });
    } catch (err) {
      setTasks(previousTasks);
      setError(err?.message || (isAr ? "تعذر نقل المهمة. تمت إعادة اللوحة لحالتها السابقة." : "Could not move the task. The board was restored."));
      await loadWorkspace({ showLoading: false }).catch(() => null);
    } finally {
      setDragBusyTaskId("");
      resetWorkspaceDragUi();
    }
  }

  function requestWorkspaceMove(task, targetColumn, targetTaskId = "", edge = "after") {
    if (!task?.id || !targetColumn?.id || dragBusyTaskId) return;
    const targetStatus = normalizeStatus(targetColumn.statuses?.[0] || "TODO");
    const currentStatus = normalizeStatus(task.status);
    if (targetStatus === "WAITING_CLIENT" && currentStatus !== "WAITING_CLIENT") {
      setWaitingClientMoveDraft({
        task,
        targetColumn,
        targetTaskId,
        edge,
        reason: "",
      });
      resetWorkspaceDragUi();
      return;
    }
    commitWorkspaceMove(task, targetColumn, targetTaskId, edge).catch(() => null);
  }

  function confirmWaitingClientMove() {
    const draft = waitingClientMoveDraft;
    const reason = String(draft?.reason || "").trim();
    if (!draft?.task || !draft?.targetColumn || !reason) return;
    setWaitingClientMoveDraft(null);
    commitWorkspaceMove(draft.task, draft.targetColumn, draft.targetTaskId, draft.edge, reason).catch(() => null);
  }

  function handleWorkspaceDragStart(event, task) {
    if (!event?.dataTransfer || !task?.id || dragBusyTaskId || filters.sort) {
      event?.preventDefault?.();
      return;
    }
    setDraggedTaskId(task.id);
    setDragOverTaskId("");
    setDragInsertEdge("");
    event.dataTransfer.effectAllowed = "move";
    event.dataTransfer.setData("application/x-tos-my-workspace-task", task.id);
    event.dataTransfer.setData("text/plain", task.id);
  }

  function handleWorkspaceDragEnd() {
    resetWorkspaceDragUi();
  }

  function handleWorkspaceCardDragOver(event, targetTask) {
    if (!draggedTaskId || !targetTask?.id || targetTask.id === draggedTaskId) return;
    event.preventDefault();
    event.stopPropagation();
    if (event.dataTransfer) event.dataTransfer.dropEffect = "move";
    const rect = event.currentTarget.getBoundingClientRect();
    setDragOverTaskId(targetTask.id);
    setDragInsertEdge(event.clientY < rect.top + rect.height / 2 ? "before" : "after");
    setDropTargetColumnId(getColumnForTask(targetTask));
  }

  function handleWorkspaceCardDrop(event, targetTask) {
    event.preventDefault();
    event.stopPropagation();
    const taskId = event.dataTransfer?.getData("application/x-tos-my-workspace-task")
      || event.dataTransfer?.getData("text/plain")
      || draggedTaskId;
    const task = tasks.find((item) => item.id === taskId);
    const targetColumn = workspaceColumns.find((column) => column.id === getColumnForTask(targetTask));
    const edge = dragOverTaskId === targetTask.id && dragInsertEdge ? dragInsertEdge : "after";
    resetWorkspaceDragUi();
    if (!task || !targetColumn || task.id === targetTask.id) return;
    requestWorkspaceMove(task, targetColumn, targetTask.id, edge);
  }

  function handleWorkspaceColumnDragOver(event, column) {
    if (!draggedTaskId || !column?.id) return;
    event.preventDefault();
    if (event.dataTransfer) event.dataTransfer.dropEffect = "move";
    setDropTargetColumnId(column.id);
  }

  function handleWorkspaceColumnDrop(event, column) {
    if (event.target?.closest?.("[data-my-workspace-card-id]")) return;
    event.preventDefault();
    const taskId = event.dataTransfer?.getData("application/x-tos-my-workspace-task")
      || event.dataTransfer?.getData("text/plain")
      || draggedTaskId;
    const task = tasks.find((item) => item.id === taskId);
    resetWorkspaceDragUi();
    if (!task || !column) return;
    requestWorkspaceMove(task, column);
  }

  function updateFilter(key, value) {'''

source = replace_once(
    source,
    grouped_anchor,
    grouped_replacement,
    "workspace drag engine",
)

source = replace_once(
    source,
    '''            <option value="">{isAr ? "ترتيب التاريخ" : "Date order"}</option>''',
    '''            <option value="">{isAr ? "ترتيب اللوحة (سحب يدوي)" : "Board order (manual drag)"}</option>''',
    "manual board order label",
)

old_board = '''            {workspaceColumns.map((column) => {
              const columnTasks = groupedTasks[column.id] || [];
              return (
                <section key={column.id} className="overflow-hidden rounded-[20px] border border-zinc-100 bg-white/[0.82] shadow-sm shadow-zinc-200/50 dark:border-white/10 dark:bg-zinc-900/70 dark:shadow-black/20">
                  <div className={`h-1.5 ${column.topClass}`} />
                  <header className="flex items-center justify-between gap-2.5 px-3 py-2.5">
                    <div>
                      <h3 className={`text-base font-black ${column.toneClass.split(" ").filter((part) => part.startsWith("text-") || part.startsWith("dark:text-")).join(" ")}`}>{isAr ? column.labelAr : column.labelEn}</h3>
                      <p className="mt-1 text-[11px] font-bold text-slate-400 dark:text-zinc-500">{isAr ? "حسب حالة المهمة" : "By task status"}</p>
                    </div>
                    <span className={`grid h-9 min-w-9 place-items-center rounded-full px-2 text-xs font-black ring-1 ${column.pillClass}`}>{columnTasks.length}</span>
                  </header>
                  <div className="max-h-[660px] space-y-2.5 overflow-y-auto border-t border-zinc-100 p-2.5 dark:border-white/10">
                    {columnTasks.length ? columnTasks.map((task) => (
                      <WorkspaceTaskCard
                        key={task.id}
                        task={task}
                        ui={ui}
                        isAr={isAr}
                        onOpenTask={openTask}
                        onOpenSettings={openTaskSettings}
                        canManagePersonalTask={task.personalOwnerId === user?.id}
                      />
                    )) : (
                      <div className="rounded-[16px] border border-dashed border-zinc-200 bg-zinc-50/70 px-3 py-5 text-center text-[11px] font-bold text-slate-400 dark:border-white/10 dark:bg-white/5 dark:text-zinc-500">
                        <FolderKanban className="mx-auto mb-2" size={18} />
                        {isAr ? "لا توجد مهام في هذه الحالة" : "No tasks in this status"}
                      </div>
                    )}
                  </div>
                </section>
              );
            })}'''

new_board = '''            {workspaceColumns.map((column) => {
              const columnTasks = groupedTasks[column.id] || [];
              const isDropTarget = Boolean(draggedTaskId && dropTargetColumnId === column.id);
              const manualDragEnabled = !filters.sort;
              return (
                <section
                  key={column.id}
                  data-my-workspace-column-id={column.id}
                  onDragOver={(event) => manualDragEnabled && handleWorkspaceColumnDragOver(event, column)}
                  onDrop={(event) => manualDragEnabled && handleWorkspaceColumnDrop(event, column)}
                  className={`overflow-hidden rounded-[20px] border bg-white/[0.82] shadow-sm transition-[border-color,box-shadow,transform,background-color] duration-150 dark:bg-zinc-900/70 dark:shadow-black/20 ${
                    isDropTarget
                      ? "scale-[1.008] border-amber-300 bg-amber-50/45 shadow-lg shadow-amber-100/60 ring-2 ring-amber-200/70 dark:border-amber-400/50 dark:bg-amber-500/10 dark:ring-amber-400/20"
                      : "border-zinc-100 shadow-zinc-200/50 dark:border-white/10"
                  }`}
                >
                  <div className={`h-1.5 ${column.topClass}`} />
                  <header className="flex items-center justify-between gap-2.5 px-3 py-2.5">
                    <div>
                      <h3 className={`text-base font-black ${column.toneClass.split(" ").filter((part) => part.startsWith("text-") || part.startsWith("dark:text-")).join(" ")}`}>{isAr ? column.labelAr : column.labelEn}</h3>
                      <p className="mt-1 text-[11px] font-bold text-slate-400 dark:text-zinc-500">
                        {manualDragEnabled
                          ? (isAr ? "اسحب الكروت لنقلها أو ترتيبها" : "Drag cards to move or reorder")
                          : (isAr ? "ألغِ ترتيب التاريخ لتفعيل السحب" : "Clear date sorting to enable drag")}
                      </p>
                    </div>
                    <span className={`grid h-9 min-w-9 place-items-center rounded-full px-2 text-xs font-black ring-1 ${column.pillClass}`}>{columnTasks.length}</span>
                  </header>
                  <div className="min-h-[120px] max-h-[660px] space-y-2.5 overflow-y-auto border-t border-zinc-100 p-2.5 dark:border-white/10">
                    {isDropTarget ? (
                      <div className="rounded-[14px] border border-dashed border-amber-300 bg-amber-50/80 px-3 py-2 text-center text-[10px] font-black text-amber-700 dark:border-amber-400/40 dark:bg-amber-500/10 dark:text-amber-200">
                        {isAr ? "اترك الكارت هنا" : "Drop card here"}
                      </div>
                    ) : null}
                    {columnTasks.length ? columnTasks.map((task) => (
                      <WorkspaceTaskCard
                        key={task.id}
                        task={task}
                        ui={ui}
                        isAr={isAr}
                        onOpenTask={openTask}
                        onOpenSettings={openTaskSettings}
                        canManagePersonalTask={task.personalOwnerId === user?.id}
                        canDrag={manualDragEnabled && !dragBusyTaskId}
                        onDragStart={handleWorkspaceDragStart}
           