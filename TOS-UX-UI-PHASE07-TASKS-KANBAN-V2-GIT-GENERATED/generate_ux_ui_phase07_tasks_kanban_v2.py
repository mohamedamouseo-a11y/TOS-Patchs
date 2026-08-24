#!/usr/bin/env python3
import difflib
import hashlib
import subprocess
import sys
from pathlib import Path

TARGET_BASE_HEAD = "a80856e3a32dea18260d9efa5ec874acf4460b39"
TARGET_FILE = "frontend/src/components/ProfessionalTaskBoard.jsx"
EXPECTED_BLOB = "4bdb16c8cd6d1e623df2fef72189b2899757d7be"

REPLACEMENTS = [
    (
        '  return (\n    <main className="tos-tasks-page tos-tasks-system-theme-v15 min-h-full overflow-x-hidden bg-[#f7f4ec] px-0 py-3 text-slate-900 md:px-0 md:py-5" dir={boardDirection}>',
        '  return (\n    <main className="tos-tasks-page tos-tasks-system-theme-v15 min-h-full overflow-x-hidden bg-[#f7f7f5] px-0 py-2 text-slate-900 md:px-0 md:py-3" dir={boardDirection}>',
    ),
    (
        '      <div className="tos-tasks-page-shell w-full max-w-none px-2 md:px-3">',
        '      <div className="tos-tasks-page-shell w-full max-w-none px-2.5 md:px-4">',
    ),
    (
        '          <aside className="tos-workspace-management-panel rounded-[32px] border border-white/80 bg-white/92 p-4 shadow-xl shadow-slate-200/60 backdrop-blur-xl">',
        '          <aside className="tos-workspace-management-panel rounded-[24px] border border-white/80 bg-white/94 p-3 shadow-[0_12px_34px_rgba(15,23,42,0.055)] backdrop-blur-xl">',
    ),
    (
        '            <div className="tos-workspace-management-grid mt-4 grid gap-3 xl:grid-cols-[1fr_1fr_1.05fr]">',
        '            <div className="tos-workspace-management-grid mt-3 grid gap-2.5 xl:grid-cols-[1fr_1fr_1.05fr]">',
    ),
    (
        '                      <div className="grid gap-8 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">',
        '                      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">',
    ),
    (
        '                  <section className="mt-4 rounded-[32px] border border-white/85 bg-white/92 p-3 shadow-xl shadow-slate-200/55 ring-1 ring-slate-100/70 backdrop-blur-xl dark:border-white/10 dark:bg-zinc-950/92 dark:shadow-black/30 dark:ring-white/5">',
        '                  <section className="mt-3 rounded-[24px] border border-white/85 bg-white/94 p-3 shadow-[0_12px_34px_rgba(15,23,42,0.05)] ring-1 ring-slate-100/70 backdrop-blur-xl dark:border-white/10 dark:bg-zinc-950/92 dark:shadow-black/30 dark:ring-white/5">',
    ),
    (
        '                    <div className="mb-4 flex flex-col gap-3 border-b border-slate-100 pb-4 dark:border-white/10 md:flex-row md:items-center md:justify-between">',
        '                    <div className="mb-3 flex flex-col gap-2.5 border-b border-slate-100 pb-3 dark:border-white/10 md:flex-row md:items-center md:justify-between">',
    ),
    (
        '                        <h2 className="mt-1 flex items-center gap-2 text-2xl font-black tracking-tight text-slate-950 dark:text-white">',
        '                        <h2 className="mt-1 flex items-center gap-2 text-xl font-black tracking-[-0.02em] text-slate-950 dark:text-white">',
    ),
    (
        '                    <div className={`tos-modern-board-grid tos-modern-board-grid--project-grid grid gap-3 pb-2 ${boardViewMode === "list" ? "grid-cols-1" : "grid-cols-1 md:grid-cols-2 2xl:grid-cols-3"}`}>',
        '                    <div className={`tos-modern-board-grid tos-modern-board-grid--project-grid grid gap-2.5 pb-1 ${boardViewMode === "list" ? "grid-cols-1" : "grid-cols-1 md:grid-cols-2 2xl:grid-cols-3"}`}>',
    ),
    (
        'className={`tos-modern-board-column ${list.listView ? "tos-modern-board-column--list min-h-[360px]" : "min-h-[380px]"} min-w-0 rounded-[24px] border bg-gradient-to-b from-white/86 to-slate-50/86 p-3 shadow-[0_12px_32px_rgba(15,23,42,0.055)] ring-1 backdrop-blur transition hover:-translate-y-0.5 hover:shadow-[0_18px_42px_rgba(15,23,42,0.08)] dark:from-zinc-950/90 dark:to-zinc-900/90 dark:shadow-black/30 ${dropTargetListId === list.id ? "border-blue-300 ring-blue-200 bg-blue-50/40 dark:border-blue-400/40 dark:ring-blue-500/30" : "border-white/80 ring-slate-200/60 dark:border-white/10 dark:ring-white/10"} ${draggedListId === list.id ? "scale-[0.99] opacity-60" : ""}`}>',
        'className={`tos-modern-board-column ${list.listView ? "tos-modern-board-column--list min-h-[330px]" : "min-h-[340px]"} min-w-0 rounded-[20px] border bg-gradient-to-b from-white/90 to-slate-50/88 p-2.5 shadow-[0_9px_26px_rgba(15,23,42,0.05)] ring-1 backdrop-blur transition hover:-translate-y-0.5 hover:shadow-[0_15px_34px_rgba(15,23,42,0.075)] dark:from-zinc-950/90 dark:to-zinc-900/90 dark:shadow-black/30 ${dropTargetListId === list.id ? "border-blue-300 ring-blue-200 bg-blue-50/40 dark:border-blue-400/40 dark:ring-blue-500/30" : "border-white/80 ring-slate-200/60 dark:border-white/10 dark:ring-white/10"} ${draggedListId === list.id ? "scale-[0.99] opacity-60" : ""}`}>',
    ),
    (
        '                          <div className="tos-modern-column-header mb-3 rounded-[22px] border border-blue-100/80 bg-white/95 p-3 shadow-sm shadow-blue-100/40 backdrop-blur dark:border-white/10 dark:bg-zinc-900/95 dark:shadow-black/30">',
        '                          <div className="tos-modern-column-header mb-2.5 rounded-[16px] border border-blue-100/80 bg-white/95 p-2.5 shadow-sm shadow-blue-100/30 backdrop-blur dark:border-white/10 dark:bg-zinc-900/95 dark:shadow-black/30">',
    ),
]

REQUIRED_MARKERS = [
    'openTaskDetails(task)',
    'handleDragStart(event, taskId)',
    'handleCardDrop(event, targetTask)',
    'handleColumnDrop(event, list)',
    'toggleBoardColumnExpanded(listId)',
    'setTaskComposerOpen(true)',
    'onOpenProjectDetails?.(activeTaskProject?.id || projectId)',
    'CardDetailsModal task={selectedTask}',
]

def run(cmd, cwd):
    return subprocess.check_output(cmd, cwd=cwd, text=True).strip()

def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data).hexdigest()

def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"ANCHOR_{label}_COUNT={count}; expected 1")
    return text.replace(old, new, 1)

def main():
    if len(sys.argv) != 3:
        print("Usage: generate_ux_ui_phase07_tasks_kanban_v2.py <repo> <output.patch>", file=sys.stderr)
        return 2

    repo = Path(sys.argv[1]).resolve()
    output = Path(sys.argv[2]).resolve()
    target = repo / TARGET_FILE

    branch = run(["git", "branch", "--show-current"], repo)
    head = run(["git", "rev-parse", "HEAD"], repo)
    blob = run(["git", "hash-object", "--", TARGET_FILE], repo)

    if branch != "main":
        raise RuntimeError(f"BRANCH={branch}; expected main")
    if head != TARGET_BASE_HEAD:
        raise RuntimeError(f"HEAD={head}; expected {TARGET_BASE_HEAD}")
    if blob != EXPECTED_BLOB:
        raise RuntimeError(f"BLOB={blob}; expected {EXPECTED_BLOB}")

    original = target.read_text(encoding="utf-8")
    updated = original

    for idx, (old, new) in enumerate(REPLACEMENTS, start=1):
        updated = replace_once(updated, old, new, f"{idx:02d}")

    if updated == original:
        raise RuntimeError("NO_CHANGES")

    for marker in REQUIRED_MARKERS:
        if original.count(marker) != updated.count(marker):
            raise RuntimeError(f"BEHAVIOR_MARKER_CHANGED={marker}")

    if original.count("tasksApi.") != updated.count("tasksApi."):
        raise RuntimeError("TASKS_API_CALL_COUNT_CHANGED")
    if original.count("api.") != updated.count("api."):
        raise RuntimeError("API_CALL_COUNT_CHANGED")

    for line_no, line in enumerate(updated.splitlines(), start=1):
        if line.rstrip() != line:
            raise RuntimeError(f"TRAILING_WHITESPACE_LINE={line_no}")

    updated_bytes = updated.encode("utf-8")
    new_blob = git_blob_sha(updated_bytes)

    diff = list(difflib.unified_diff(
        original.splitlines(keepends=True),
        updated.splitlines(keepends=True),
        fromfile=f"a/{TARGET_FILE}",
        tofile=f"b/{TARGET_FILE}",
        n=3,
    ))
    patch = (
        f"diff --git a/{TARGET_FILE} b/{TARGET_FILE}\n"
        f"index {EXPECTED_BLOB[:7]}..{new_blob[:7]} 100644\n"
        + "".join(diff)
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(patch, encoding="utf-8")

    sha256 = hashlib.sha256(output.read_bytes()).hexdigest()
    print(f"TARGET_BASE_HEAD={TARGET_BASE_HEAD}")
    print(f"TARGET_FILE={TARGET_FILE}")
    print(f"EXPECTED_BLOB={EXPECTED_BLOB}")
    print(f"NEW_BLOB={new_blob}")
    print("SOURCE_SCOPE=ONE_FILE")
    print("TASKS_SCOPE=KANBAN_BOARD_SHELL_ONLY")
    print("TASK_DETAILS_SCOPE=NOT_INCLUDED")
    print("ANCHOR01_CONTEXTUAL=YES")
    print("DUPLICATE_DESIGN_REQUEST_MAIN_PRESERVED=YES")
    print("BUSINESS_LOGIC_CHANGED=NO")
    print("TASKS_API_CALLS_CHANGED=NO")
    print("API_CALLS_CHANGED=NO")
    print("ROUTES_CHANGED=NO")
    print("BACKEND_INCLUDED=NO")
    print(f"REPLACEMENTS={len(REPLACEMENTS)}")
    print(f"PATCH_SHA256={sha256}")
    print(f"PATCH_PATH={output}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
