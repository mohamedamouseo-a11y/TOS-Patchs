#!/usr/bin/env python3
import difflib
import hashlib
import subprocess
import sys
from pathlib import Path

TARGET_BASE_HEAD = "9350ed57e25bb32dd1902b5d9de8aeafed4dacfe"
TARGET_FILE = "frontend/src/pages/MyTaskWorkspace.jsx"
EXPECTED_BLOB = "e8a770c87264173c2c2925722c6bf408353bdf84"

REPLACEMENTS = [
    (
        '    <div className="grid justify-items-center text-center">',
        '    <div className="grid justify-items-center text-center">',
        1,
    ),
    (
        '      <div className="relative grid h-24 w-24 shrink-0 place-items-center rounded-full" style={ringStyle}>',
        '      <div className="relative grid h-20 w-20 shrink-0 place-items-center rounded-full" style={ringStyle}>',
        1,
    ),
    (
        '        <div className="grid h-[70px] w-[70px] place-items-center rounded-full bg-white shadow-inner dark:bg-zinc-900">',
        '        <div className="grid h-[58px] w-[58px] place-items-center rounded-full bg-white shadow-inner dark:bg-zinc-900">',
        1,
    ),
    (
        '          <span className={`max-w-[64px] text-center text-xl font-black leading-tight ${current.textClass}`}>{value}</span>',
        '          <span className={`max-w-[54px] text-center text-lg font-black leading-tight ${current.textClass}`}>{value}</span>',
        1,
    ),
    (
        '      <div className="mt-3 text-sm font-black text-zinc-950 dark:text-white">{label}</div>',
        '      <div className="mt-2 text-xs font-black text-zinc-950 dark:text-white">{label}</div>',
        1,
    ),
    (
        '      {note ? <div className={`mt-1 text-xs font-black ${current.noteClass}`}>{note}</div> : null}',
        '      {note ? <div className={`mt-0.5 text-[11px] font-black ${current.noteClass}`}>{note}</div> : null}',
        1,
    ),
    (
        '    <article className="group rounded-[18px] border border-zinc-100 bg-white px-3 py-3 shadow-sm shadow-zinc-200/40 transition hover:-translate-y-0.5 hover:border-amber-200 hover:shadow-lg hover:shadow-amber-100/40 dark:border-white/10 dark:bg-zinc-950 dark:shadow-black/20 dark:hover:border-amber-400/40">',
        '    <article className="group rounded-[16px] border border-zinc-100 bg-white px-2.5 py-2.5 shadow-sm shadow-zinc-200/35 transition hover:-translate-y-0.5 hover:border-amber-200 hover:shadow-md hover:shadow-amber-100/35 dark:border-white/10 dark:bg-zinc-950 dark:shadow-black/20 dark:hover:border-amber-400/40">',
        1,
    ),
    (
        '      <div className="mt-3 flex items-center justify-between gap-2 border-t border-zinc-100 pt-3 text-[11px] font-black dark:border-white/10">',
        '      <div className="mt-2.5 flex items-center justify-between gap-2 border-t border-zinc-100 pt-2.5 text-[10px] font-black dark:border-white/10">',
        1,
    ),
    (
        '    <div className="mx-auto w-full max-w-[1480px]" dir={isAr ? "rtl" : "ltr"}>',
        '    <div className="mx-auto w-full max-w-[1580px]" dir={isAr ? "rtl" : "ltr"}>',
        1,
    ),
    (
        '      <div className={`mb-6 grid gap-6 md:grid-cols-5 ${isAr ? "direction-rtl" : "direction-ltr"}`}>',
        '      <div className={`mb-4 grid grid-cols-2 gap-3 md:grid-cols-5 ${isAr ? "direction-rtl" : "direction-ltr"}`}>',
        1,
    ),
    (
        '      <section className="rounded-[34px] border border-zinc-100 bg-white/95 p-5 shadow-[0_24px_80px_rgba(15,23,42,0.08)] dark:border-white/10 dark:bg-zinc-950/95">',
        '      <section className="rounded-[24px] border border-zinc-100 bg-white/96 p-4 shadow-[0_14px_44px_rgba(15,23,42,0.06)] dark:border-white/10 dark:bg-zinc-950/95">',
        1,
    ),
    (
        '      <div className="flex flex-col gap-3 border-b border-zinc-100 pb-5 dark:border-white/10 sm:flex-row sm:items-start sm:justify-between">',
        '      <div className="flex flex-col gap-3 border-b border-zinc-100 pb-4 dark:border-white/10 sm:flex-row sm:items-start sm:justify-between">',
        1,
    ),
    (
        '          <h2 className="text-2xl font-black text-zinc-950 dark:text-white">{isAr ? "مساحة مهامي" : "My Workspace"}</h2>',
        '          <h2 className="text-xl font-black tracking-tight text-zinc-950 dark:text-white">{isAr ? "مساحة مهامي" : "My Workspace"}</h2>',
        1,
    ),
    (
        '      <div className="mt-5 rounded-[24px] border border-zinc-100 bg-zinc-50/60 p-3 dark:border-white/10 dark:bg-white/5">',
        '      <div className="mt-4 rounded-[18px] border border-zinc-100 bg-zinc-50/60 p-2.5 dark:border-white/10 dark:bg-white/5">',
        1,
    ),
    (
        '        <div className="grid gap-3 lg:grid-cols-[minmax(240px,1.4fr)_minmax(170px,0.8fr)_minmax(150px,0.7fr)_minmax(150px,0.7fr)]">',
        '        <div className="grid gap-2.5 lg:grid-cols-[minmax(240px,1.4fr)_minmax(170px,0.8fr)_minmax(150px,0.7fr)_minmax(150px,0.7fr)]">',
        1,
    ),
    (
        '              className={`h-12 w-full rounded-2xl border border-zinc-200 bg-white text-sm font-bold text-zinc-800 outline-none transition placeholder:text-slate-400 focus:border-amber-300 focus:ring-4 focus:ring-amber-50 dark:border-white/10 dark:bg-zinc-950 dark:text-zinc-100 dark:focus:ring-amber-500/10 ${isAr ? "pr-11 pl-4" : "pl-11 pr-4"}`}',
        '              className={`h-10 w-full rounded-xl border border-zinc-200 bg-white text-xs font-bold text-zinc-800 outline-none transition placeholder:text-slate-400 focus:border-amber-300 focus:ring-4 focus:ring-amber-50 dark:border-white/10 dark:bg-zinc-950 dark:text-zinc-100 dark:focus:ring-amber-500/10 ${isAr ? "pr-10 pl-3" : "pl-10 pr-3"}`}',
        1,
    ),
    (
        'className="h-12 rounded-2xl border border-zinc-200 bg-white px-4 text-sm font-black text-zinc-700 outline-none transition focus:border-amber-300 focus:ring-4 focus:ring-amber-50 dark:border-white/10 dark:bg-zinc-950 dark:text-zinc-100 dark:focus:ring-amber-500/10"',
        'className="h-10 rounded-xl border border-zinc-200 bg-white px-3 text-xs font-black text-zinc-700 outline-none transition focus:border-amber-300 focus:ring-4 focus:ring-amber-50 dark:border-white/10 dark:bg-zinc-950 dark:text-zinc-100 dark:focus:ring-amber-500/10"',
        3,
    ),
    (
        '        <div className="mt-5 overflow-x-auto pb-2">',
        '        <div className="mt-4 overflow-x-auto pb-1">',
        1,
    ),
    (
        '          <div className="grid min-w-[1280px] grid-cols-6 gap-3">',
        '          <div className="grid min-w-[1180px] grid-cols-6 gap-2.5">',
        1,
    ),
    (
        '                <section key={column.id} className="overflow-hidden rounded-[26px] border border-zinc-100 bg-white/80 shadow-sm shadow-zinc-200/60 dark:border-white/10 dark:bg-zinc-900/70 dark:shadow-black/20">',
        '                <section key={column.id} className="overflow-hidden rounded-[20px] border border-zinc-100 bg-white/82 shadow-sm shadow-zinc-200/50 dark:border-white/10 dark:bg-zinc-900/70 dark:shadow-black/20">',
        1,
    ),
    (
        '                  <header className="flex items-center justify-between gap-3 px-4 py-3">',
        '                  <header className="flex items-center justify-between gap-2.5 px-3 py-2.5">',
        1,
    ),
    (
        '                  <div className="max-h-[630px] space-y-3 overflow-y-auto border-t border-zinc-100 p-3 dark:border-white/10">',
        '                  <div className="max-h-[660px] space-y-2.5 overflow-y-auto border-t border-zinc-100 p-2.5 dark:border-white/10">',
        1,
    ),
    (
        '                      <div className="rounded-[22px] border border-dashed border-zinc-200 bg-zinc-50/70 px-3 py-8 text-center text-xs font-bold text-slate-400 dark:border-white/10 dark:bg-white/5 dark:text-zinc-500">',
        '                      <div className="rounded-[16px] border border-dashed border-zinc-200 bg-zinc-50/70 px-3 py-5 text-center text-[11px] font-bold text-slate-400 dark:border-white/10 dark:bg-white/5 dark:text-zinc-500">',
        1,
    ),
]

REQUIRED_MARKERS = [
    'function WorkspaceMiniStat(',
    'function WorkspaceTaskCard(',
    'function WorkspaceTaskEditorModal(',
    'export function MyTaskWorkspace(',
    'openCreateTask()',
    'openTaskSettings(task)',
    'saveWorkspaceTask(event)',
    'openTask(task)',
    'tasksApi.getMyWorkspace(',
    'tasksApi.updateMyWorkspaceTask(',
    'tasksApi.createMyWorkspaceTask(',
    '<WorkspaceTaskEditorModal',
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
    if old == new:
        return text
    return text.replace(old, new)


def editor_block(text):
    start_marker = 'function WorkspaceTaskEditorModal('
    end_marker = 'export function MyTaskWorkspace('
    start = text.find(start_marker)
    end = text.find(end_marker, start + 1)
    if start < 0 or end < 0 or end <= start:
        raise RuntimeError('WORKSPACE_EDITOR_BLOCK_NOT_FOUND')
    return text[start:end]


def main():
    if len(sys.argv) != 3:
        print('Usage: generate_ux_ui_phase09_my_workspace.py <repo> <output.patch>', file=sys.stderr)
        return 2

    repo = Path(sys.argv[1]).resolve()
    output = Path(sys.argv[2]).resolve()
    target = repo / TARGET_FILE

    branch = run(['git', 'branch', '--show-current'], repo)
    head = run(['git', 'rev-parse', 'HEAD'], repo)
    blob = run(['git', 'hash-object', '--', TARGET_FILE], repo)

    if branch != 'main':
        raise RuntimeError(f'BRANCH={branch}; expected main')
    if head != TARGET_BASE_HEAD:
        raise RuntimeError(f'HEAD={head}; expected {TARGET_BASE_HEAD}')
    if blob != EXPECTED_BLOB:
        raise RuntimeError(f'BLOB={blob}; expected {EXPECTED_BLOB}')

    original = target.read_text(encoding='utf-8')
    original_editor = editor_block(original)
    updated = original

    for idx, (old, new, expected_count) in enumerate(REPLACEMENTS, start=1):
        updated = replace_exact(updated, old, new, expected_count, f'{idx:02d}')

    if updated == original:
        raise RuntimeError('NO_CHANGES')

    if editor_block(updated) != original_editor:
        raise RuntimeError('WORKSPACE_EDITOR_CHANGED')

    for marker in REQUIRED_MARKERS:
        if original.count(marker) != updated.count(marker):
            raise RuntimeError(f'BEHAVIOR_MARKER_CHANGED={marker}')

    if original.count('tasksApi.') != updated.count('tasksApi.'):
        raise RuntimeError('TASKS_API_CALL_COUNT_CHANGED')

    for line_no, line in enumerate(updated.splitlines(), start=1):
        if line.rstrip() != line:
            raise RuntimeError(f'TRAILING_WHITESPACE_LINE={line_no}')

    updated_bytes = updated.encode('utf-8')
    new_blob = git_blob_sha(updated_bytes)

    diff = list(difflib.unified_diff(
        original.splitlines(keepends=True),
        updated.splitlines(keepends=True),
        fromfile=f'a/{TARGET_FILE}',
        tofile=f'b/{TARGET_FILE}',
        n=3,
    ))
    patch = (
        f'diff --git a/{TARGET_FILE} b/{TARGET_FILE}\n'
        f'index {EXPECTED_BLOB[:7]}..{new_blob[:7]} 100644\n'
        + ''.join(diff)
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(patch, encoding='utf-8')

    sha256 = hashlib.sha256(output.read_bytes()).hexdigest()
    print(f'TARGET_BASE_HEAD={TARGET_BASE_HEAD}')
    print(f'TARGET_FILE={TARGET_FILE}')
    print(f'EXPECTED_BLOB={EXPECTED_BLOB}')
    print(f'NEW_BLOB={new_blob}')
    print('SOURCE_SCOPE=ONE_FILE')
    print('WORKSPACE_SCOPE=MY_WORKSPACE_MAIN_ONLY')
    print('WORKSPACE_EDITOR_CHANGED=NO')
    print('TASK_BEHAVIOR_CHANGED=NO')
    print('TASKS_API_CALLS_CHANGED=NO')
    print('ROUTES_CHANGED=NO')
    print('PERMISSIONS_CHANGED=NO')
    print('BACKEND_INCLUDED=NO')
    print(f'REPLACEMENTS={len(REPLACEMENTS)}')
    print(f'PATCH_SHA256={sha256}')
    print(f'PATCH_PATH={output}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
