#!/usr/bin/env python3
import difflib
import hashlib
import subprocess
import sys
from pathlib import Path

TARGET_BASE_HEAD = "2281b7ef4d72653a94d1331a866da48519a587af"
TARGET_FILE = "frontend/src/pages/ProjectsPage.jsx"
EXPECTED_BLOB = "0498e468f1baf9efc9d94fbb34e830ba26901fc2"

REPLACEMENTS = [
    (
        '''function ProjectEditSummaryPanel({ project, draft, ui, labels }) {
  return (
    <aside className="rounded-[28px] border border-amber-100 bg-amber-50/45 p-5 shadow-sm dark:border-amber-500/20 dark:bg-amber-500/10">
      <div className="mb-5 flex items-center justify-between gap-3">''',
        '''function ProjectEditSummaryPanel({ project, draft, ui, labels }) {
  return (
    <aside className="self-start rounded-[20px] border border-amber-100 bg-amber-50/40 p-4 shadow-[0_10px_28px_rgba(15,23,42,0.045)] dark:border-amber-500/20 dark:bg-amber-500/10 xl:sticky xl:top-4">
      <div className="mb-4 flex items-center justify-between gap-2.5">'''
    ),
    (
        '''      {editingProject && (
        <div className="fixed inset-0 z-[60] grid place-items-center bg-zinc-950/60 p-3 backdrop-blur-sm" dir={pageDirection}>
          <form onSubmit={saveEdit} className="max-h-[94vh] w-full max-w-7xl overflow-y-auto rounded-[34px] border border-white/20 bg-[#fbfaf8] p-5 text-right shadow-2xl dark:bg-zinc-950 md:p-7">''',
        '''      {editingProject && (
        <div className="fixed inset-0 z-[60] grid place-items-center bg-zinc-950/55 p-2 backdrop-blur-sm md:p-3" dir={pageDirection}>
          <form onSubmit={saveEdit} className="max-h-[94vh] w-full max-w-6xl overflow-y-auto rounded-[24px] border border-white/20 bg-[#f7f7f5] p-4 text-right shadow-[0_24px_70px_rgba(15,23,42,0.28)] dark:bg-zinc-950 md:p-5">'''
    ),
    (
        '''            <div className="flex flex-wrap items-start justify-between gap-4">
              <div className="min-w-0">
                <p className="tos-kicker">{ui.editProject}</p>
                <h3 dir="auto" className="break-words text-3xl font-black tracking-tight text-zinc-950 dark:text-white">{ui.editProject}</h3>
                <p className="mt-1 text-sm font-bold text-zinc-500 dark:text-zinc-400">{ui.editProjectHint}</p>''',
        '''            <div className="flex flex-wrap items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="tos-kicker">{ui.editProject}</p>
                <h3 dir="auto" className="break-words text-2xl font-black tracking-[-0.025em] text-zinc-950 dark:text-white">{ui.editProject}</h3>
                <p className="mt-1 text-xs font-bold leading-5 text-zinc-500 dark:text-zinc-400">{ui.editProjectHint}</p>'''
    ),
    (
        '''                <button type="button" onClick={() => { setEditingProject(null); setEditError(""); }} className="grid h-10 w-10 place-items-center rounded-2xl bg-zinc-100 text-zinc-600 dark:bg-white/10 dark:text-zinc-200" aria-label={ui.editProject}>
                  <X size={18} />
                </button>''',
        '''                <button type="button" onClick={() => { setEditingProject(null); setEditError(""); }} className="grid h-9 w-9 place-items-center rounded-xl border border-zinc-200/70 bg-white text-zinc-500 shadow-sm transition hover:bg-zinc-50 hover:text-zinc-950 dark:border-white/10 dark:bg-white/10 dark:text-zinc-200" aria-label={ui.editProject}>
                  <X size={16} />
                </button>'''
    ),
    (
        '''            <Notice type="error" className="mt-5">{editError}</Notice>

            <div className="mt-6 grid gap-5 xl:grid-cols-[290px_minmax(0,1fr)]">
              <ProjectEditSummaryPanel project={editingProject} draft={draft} ui={ui} labels={labels} />

              <div className="grid gap-5">''',
        '''            <Notice type="error" className="mt-4">{editError}</Notice>

            <div className="mt-4 grid gap-4 xl:grid-cols-[260px_minmax(0,1fr)]">
              <ProjectEditSummaryPanel project={editingProject} draft={draft} ui={ui} labels={labels} />

              <div className="grid gap-4">'''
    ),
    (
        '''                <ProjectPanelCard kicker={ui.dates} title={ui.projectDates} icon={CalendarDays}>
                  <div className="grid gap-4 md:grid-cols-3">''',
        '''                <ProjectPanelCard kicker={ui.dates} title={ui.projectDates} icon={CalendarDays}>
                  <div className="grid gap-3 md:grid-cols-3">'''
    ),
    (
        '''                <ProjectPanelCard kicker={ui.clientData} title={ui.clientProjectInfo} icon={UsersRound}>
                  <div className="grid gap-4 md:grid-cols-2">''',
        '''                <ProjectPanelCard kicker={ui.clientData} title={ui.clientProjectInfo} icon={UsersRound}>
                  <div className="grid gap-3 md:grid-cols-2">'''
    ),
    (
        '''                    <TaskRichTextEditor value={draft.description} onChange={(value) => updateDraft("description", value)} placeholder={ui.projectDescriptionPlaceholder} minHeight="min-h-[240px] max-h-[520px] overflow-y-auto" label={ui.description} ui={editorUi} />''',
        '''                    <TaskRichTextEditor value={draft.description} onChange={(value) => updateDraft("description", value)} placeholder={ui.projectDescriptionPlaceholder} minHeight="min-h-[180px] max-h-[380px] overflow-y-auto" label={ui.description} ui={editorUi} />'''
    ),
    (
        '''            <div className="mt-8 flex flex-wrap justify-end gap-2 border-t border-zinc-100 pt-5 dark:border-zinc-800">''',
        '''            <div className="mt-4 flex flex-wrap justify-end gap-2 border-t border-zinc-200/70 pt-4 dark:border-zinc-800">'''
    ),
]

REQUIRED_MARKERS = [
    'onSubmit={saveEdit}',
    'updateDraft("name"',
    'updateDraft("status"',
    'updateDraft("stage"',
    'updateDraft("priority"',
    'updateDraft("startDate"',
    'updateDraft("dueDate"',
    'updateDraft("deliveryDate"',
    'updateDraft("clientName"',
    'updateDraft("description"',
    'setEditingProject(null)',
    'disabled={saving}',
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
        print("Usage: generate_ux_ui_phase06_project_edit.py <repo> <output.patch>", file=sys.stderr)
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
    print("EDIT_SCOPE=PROJECT_EDIT_ONLY")
    print("BUSINESS_LOGIC_CHANGED=NO")
    print("API_CALLS_CHANGED=NO")
    print("ROUTES_CHANGED=NO")
    print("BACKEND_INCLUDED=NO")
    print(f"REPLACEMENTS={len(REPLACEMENTS)}")
    print(f"PATCH_SHA256={sha256}")
    print(f"PATCH_PATH={output}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
