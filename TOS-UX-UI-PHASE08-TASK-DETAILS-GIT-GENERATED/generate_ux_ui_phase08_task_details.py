#!/usr/bin/env python3
import difflib
import hashlib
import subprocess
import sys
from pathlib import Path

TARGET_BASE_HEAD = "d945922df692186be8064991e6169a38c1563685"
TARGET_FILE = "frontend/src/components/ProfessionalTaskBoard.jsx"
EXPECTED_BLOB = "0af7bbee8a79cc2bf12c48da4e15f8b8104e9d78"

REPLACEMENTS = [
    (
        '  const referenceDateClass = "rounded-[22px] border border-slate-200 bg-white px-4 py-4 shadow-sm shadow-slate-100/80 dark:border-white/10 dark:bg-zinc-950";',
        '  const referenceDateClass = "rounded-[18px] border border-slate-200 bg-white px-3.5 py-3 shadow-sm shadow-slate-100/70 dark:border-white/10 dark:bg-zinc-950";',
        1,
    ),
    (
        '  const referencePanelClass = "rounded-[28px] border border-slate-200 bg-white p-5 shadow-sm shadow-slate-100/80 dark:border-white/10 dark:bg-zinc-950 dark:shadow-black/20";',
        '  const referencePanelClass = "rounded-[22px] border border-slate-200 bg-white p-4 shadow-sm shadow-slate-100/70 dark:border-white/10 dark:bg-zinc-950 dark:shadow-black/20";',
        1,
    ),
    (
        '  const referenceSelectClass = "h-11 rounded-2xl border border-slate-200 bg-white px-3 text-xs font-black text-slate-700 outline-none transition focus:border-blue-300 focus:ring-4 focus:ring-blue-50 disabled:bg-slate-50 disabled:text-slate-400 dark:border-white/10 dark:bg-zinc-900 dark:text-zinc-100 dark:focus:ring-blue-500/15";',
        '  const referenceSelectClass = "h-10 rounded-xl border border-slate-200 bg-white px-3 text-xs font-black text-slate-700 outline-none transition focus:border-blue-300 focus:ring-4 focus:ring-blue-50 disabled:bg-slate-50 disabled:text-slate-400 dark:border-white/10 dark:bg-zinc-900 dark:text-zinc-100 dark:focus:ring-blue-500/15";',
        1,
    ),
    (
        '    <div className="tos-task-details-fullpage fixed inset-0 z-50 overflow-hidden bg-gradient-to-br from-white via-slate-50 to-amber-50/30 p-0 dark:from-zinc-950 dark:via-zinc-950 dark:to-amber-950/10" dir={modalDirection}>',
        '    <div className="tos-task-details-fullpage fixed inset-0 z-50 overflow-hidden bg-gradient-to-br from-[#fafaf9] via-white to-amber-50/20 p-0 dark:from-zinc-950 dark:via-zinc-950 dark:to-amber-950/10" dir={modalDirection}>',
        1,
    ),
    (
        '        <header className="shrink-0 border-b border-slate-100 bg-white/95 px-4 py-4 backdrop-blur-xl dark:border-white/10 dark:bg-zinc-950/95 sm:px-5">',
        '        <header className="shrink-0 border-b border-slate-100 bg-white/95 px-4 py-3 backdrop-blur-xl dark:border-white/10 dark:bg-zinc-950/95 sm:px-5">',
        1,
    ),
    (
        '              <button ref={closeButtonRef} type="button" aria-label={modalUi.closeTaskDetails} onClick={onClose} className="grid h-11 w-11 place-items-center rounded-full border border-slate-200 bg-white text-slate-700 shadow-sm transition hover:bg-slate-50 focus:outline-none focus:ring-4 focus:ring-slate-100 dark:border-white/10 dark:bg-zinc-900 dark:text-zinc-200"><X size={18} /></button>',
        '              <button ref={closeButtonRef} type="button" aria-label={modalUi.closeTaskDetails} onClick={onClose} className="grid h-9 w-9 place-items-center rounded-xl border border-slate-200 bg-white text-slate-700 shadow-sm transition hover:bg-slate-50 focus:outline-none focus:ring-4 focus:ring-slate-100 dark:border-white/10 dark:bg-zinc-900 dark:text-zinc-200"><X size={17} /></button>',
        1,
    ),
    (
        '              {canArchive && <button type="button" onClick={archiveCard} className="inline-flex h-11 items-center gap-2 rounded-full border border-amber-200 bg-amber-50 px-4 text-xs font-black text-amber-700 shadow-sm transition hover:bg-amber-100 focus:outline-none focus:ring-4 focus:ring-amber-100 dark:border-amber-400/20 dark:bg-amber-500/10 dark:text-amber-200" aria-label={modalUi.archiveCard} title={modalUi.archiveCard}><Archive size={15} /> {modalUi.archiveCard}</button>}',
        '              {canArchive && <button type="button" onClick={archiveCard} className="inline-flex h-9 items-center gap-2 rounded-xl border border-amber-200 bg-amber-50 px-3.5 text-[11px] font-black text-amber-700 shadow-sm transition hover:bg-amber-100 focus:outline-none focus:ring-4 focus:ring-amber-100 dark:border-amber-400/20 dark:bg-amber-500/10 dark:text-amber-200" aria-label={modalUi.archiveCard} title={modalUi.archiveCard}><Archive size={14} /> {modalUi.archiveCard}</button>}',
        1,
    ),
    (
        '        <div ref={taskDetailsBodyRef} onScroll={handleTaskDetailsScroll} className="min-h-0 flex-1 overflow-y-auto p-4 dark:from-zinc-950 dark:via-zinc-950 dark:to-blue-950/20 sm:p-5"><div className="mx-auto max-w-[1760px]">',
        '        <div ref={taskDetailsBodyRef} onScroll={handleTaskDetailsScroll} className="min-h-0 flex-1 overflow-y-auto p-3 dark:from-zinc-950 dark:via-zinc-950 dark:to-blue-950/20 sm:p-4"><div className="mx-auto max-w-[1640px]">',
        1,
    ),
    (
        '          <div className="grid gap-5 xl:grid-cols-[360px_minmax(0,1fr)]" dir="ltr">',
        '          <div className="grid gap-4 xl:grid-cols-[320px_minmax(0,1fr)]" dir="ltr">',
        1,
    ),
    (
        '            <main className="min-w-0 space-y-5 text-right xl:order-2" dir={modalDirection}>',
        '            <main className="min-w-0 space-y-4 text-right xl:order-2" dir={modalDirection}>',
        1,
    ),
    (
        '              <section className="rounded-[32px] border border-slate-200 bg-white p-5 shadow-sm shadow-slate-100/80 dark:border-white/10 dark:bg-zinc-950 dark:shadow-black/20">',
        '              <section className="rounded-[24px] border border-slate-200 bg-white p-4 shadow-sm shadow-slate-100/70 dark:border-white/10 dark:bg-zinc-950 dark:shadow-black/20">',
        1,
    ),
    (
        '                <div className="grid gap-6 lg:grid-cols-[minmax(0,1.25fr)_1px_minmax(280px,0.9fr)] lg:items-stretch">',
        '                <div className="grid gap-4 lg:grid-cols-[minmax(0,1.3fr)_1px_minmax(260px,0.85fr)] lg:items-stretch">',
        1,
    ),
    (
        '                    <label className="rounded-[24px] border border-slate-100 bg-white px-4 py-4 shadow-sm dark:border-white/10 dark:bg-zinc-900">',
        '                    <label className="rounded-[18px] border border-slate-100 bg-white px-3.5 py-3 shadow-sm dark:border-white/10 dark:bg-zinc-900">',
        1,
    ),
    (
        '                    <label className="rounded-[24px] border border-amber-100 bg-amber-50/40 px-4 py-4 shadow-sm dark:border-amber-400/20 dark:bg-amber-500/10">',
        '                    <label className="rounded-[18px] border border-amber-100 bg-amber-50/40 px-3.5 py-3 shadow-sm dark:border-amber-400/20 dark:bg-amber-500/10">',
        1,
    ),
    (
        '                    <div className="rounded-[22px] border border-slate-100 bg-slate-50/80 px-4 py-4 dark:border-white/10 dark:bg-zinc-900/80">',
        '                    <div className="rounded-[18px] border border-slate-100 bg-slate-50/80 px-3.5 py-3 dark:border-white/10 dark:bg-zinc-900/80">',
        2,
    ),
    (
        '                      className="w-full rounded-2xl border border-transparent bg-transparent px-2 py-2 text-right text-4xl font-black tracking-tight text-slate-950 outline-none transition hover:border-slate-100 focus:border-amber-200 focus:bg-amber-50/40 focus:ring-4 focus:ring-amber-50 dark:text-white dark:hover:border-white/10 dark:focus:bg-amber-500/10" dir={isAr ? "rtl" : getTextDirection(draft.title || modalUi.taskTitle)}',
        '                      className="w-full rounded-xl border border-transparent bg-transparent px-2 py-1.5 text-right text-3xl font-black tracking-[-0.03em] text-slate-950 outline-none transition hover:border-slate-100 focus:border-amber-200 focus:bg-amber-50/40 focus:ring-4 focus:ring-amber-50 dark:text-white dark:hover:border-white/10 dark:focus:bg-amber-500/10" dir={isAr ? "rtl" : getTextDirection(draft.title || modalUi.taskTitle)}',
        1,
    ),
    (
        '                    <p className="mt-6 max-w-2xl border-r-4 border-amber-300 pr-4 text-sm font-bold leading-8 text-slate-500 dark:text-zinc-400">{taskHeaderDescription.slice(0, 170)}</p>',
        '                    <p className="mt-4 max-w-2xl border-r-[3px] border-amber-300 pr-3 text-sm font-bold leading-7 text-slate-500 dark:text-zinc-400">{taskHeaderDescription.slice(0, 170)}</p>',
        1,
    ),
    (
        '                    <div className="mt-5 rounded-[24px] border border-amber-100 bg-gradient-to-br from-white to-amber-50/55 px-5 py-4 shadow-sm dark:border-amber-400/20 dark:from-zinc-950 dark:to-amber-500/10">',
        '                    <div className="mt-4 rounded-[20px] border border-amber-100 bg-gradient-to-br from-white to-amber-50/55 px-4 py-3 shadow-sm dark:border-amber-400/20 dark:from-zinc-950 dark:to-amber-500/10">',
        1,
    ),
    (
        '        <footer className="shrink-0 border-t border-slate-100 bg-white/95 px-5 py-3 text-xs font-semibold text-slate-400 dark:border-white/10 dark:bg-zinc-950/95 dark:text-zinc-500">',
        '        <footer className="shrink-0 border-t border-slate-100 bg-white/95 px-5 py-2.5 text-[11px] font-semibold text-slate-400 dark:border-white/10 dark:bg-zinc-950/95 dark:text-zinc-500">',
        1,
    ),
]

REQUIRED_MARKERS = [
    'function CardDetailsModal(',
    'savePatch(',
    'handleTaskStatusChange(',
    'startTimeTimer(',
    'pauseTimeTimer(',
    'stopTimeTimer(',
    'addChecklist(',
    'addComment(',
    'uploadFiles(',
    'onNavigateTask?.(',
    'setActiveTaskTab(',
    'TaskDetailsErrorBoundary',
    'tos-modern-board-grid',
    'tos-workspace-management-panel',
]

def run(cmd, cwd):
    return subprocess.check_output(cmd, cwd=cwd, text=True).strip()

def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data).hexdigest()

def replace_exact(text, old, new, expected_count, label):
    count = text.count(old)
    if count != expected_count:
        raise RuntimeError(f"ANCHOR_{label}_COUNT={count}; expected {expected_count}")
    return text.replace(old, new)

def main():
    if len(sys.argv) != 3:
        print("Usage: generate_ux_ui_phase08_task_details.py <repo> <output.patch>", file=sys.stderr)
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

    for idx, (old, new, expected_count) in enumerate(REPLACEMENTS, start=1):
        updated = replace_exact(updated, old, new, expected_count, f"{idx:02d}")

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
    print("TASK_DETAILS_SCOPE=TASK_DETAILS_ONLY")
    print("KANBAN_SHELL_CHANGED=NO")
    print("TASK_BEHAVIOR_CHANGED=NO")
    print("TASKS_API_CALLS_CHANGED=NO")
    print("API_CALLS_CHANGED=NO")
    print("ROUTES_CHANGED=NO")
    print("PERMISSIONS_CHANGED=NO")
    print("BACKEND_INCLUDED=NO")
    print(f"REPLACEMENTS={len(REPLACEMENTS)}")
    print(f"PATCH_SHA256={sha256}")
    print(f"PATCH_PATH={output}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
