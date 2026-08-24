#!/usr/bin/env python3
import difflib
import hashlib
import subprocess
import sys
from pathlib import Path

TARGET_BASE_HEAD = "2ecd378d422726d45299e4353b4a9fc30e983207"
TARGET_FILE = "frontend/src/pages/ProjectsPage.jsx"
EXPECTED_BLOB = "422db477233617b335698574f161ccb5c262c0f5"

REPLACEMENTS = [
    (
        '          <Card className="rounded-[34px] border-zinc-100 bg-white/95 p-5 shadow-sm shadow-zinc-200/60 dark:border-zinc-800 dark:bg-zinc-900/90 md:p-7">',
        '          <Card className="rounded-[24px] border-zinc-200/70 bg-white/95 p-4 shadow-[0_12px_36px_rgba(15,23,42,0.05)] dark:border-zinc-800 dark:bg-zinc-900/90 md:p-5">'
    ),
    (
        '            <div className="flex flex-wrap items-start justify-between gap-4">\n              <div>\n                <p className="tos-kicker">{ui.createQuick}</p>\n                <h3 className="text-3xl font-black tracking-tight text-zinc-950 dark:text-white">{ui.createProjectFull}</h3>\n                <p className="mt-2 text-sm font-bold text-zinc-500 dark:text-zinc-400">{ui.createHint}</p>',
        '            <div className="flex flex-wrap items-start justify-between gap-3">\n              <div>\n                <p className="tos-kicker">{ui.createQuick}</p>\n                <h3 className="text-2xl font-black tracking-[-0.025em] text-zinc-950 dark:text-white">{ui.createProjectFull}</h3>\n                <p className="mt-1.5 text-xs font-bold leading-5 text-zinc-500 dark:text-zinc-400">{ui.createHint}</p>'
    ),
    (
        '            <div className="mt-7 rounded-[28px] border border-zinc-100 bg-zinc-50/60 p-4 dark:border-zinc-800 dark:bg-white/5">\n              <div className="grid gap-3 md:grid-cols-4">',
        '            <div className="mt-4 rounded-[20px] border border-zinc-200/70 bg-zinc-50/65 p-2.5 dark:border-zinc-800 dark:bg-white/[0.035]">\n              <div className="grid gap-2 md:grid-cols-4">'
    ),
    (
        '                        "rounded-2xl border px-4 py-3 text-right transition-all",',
        '                        "rounded-[14px] border px-3 py-2.5 text-right transition-all",'
    ),
    (
        '                        <span className={cn("grid h-9 w-9 shrink-0 place-items-center rounded-full border text-sm font-black", active ? "border-amber-400 bg-amber-100 text-amber-800" : done ? "border-emerald-200 bg-emerald-50 text-emerald-700" : available ? "border-zinc-200 bg-white text-zinc-500 dark:border-zinc-700 dark:bg-zinc-900" : "border-zinc-200 bg-zinc-50 text-zinc-300 dark:border-zinc-800 dark:bg-zinc-900/50")}>{step.id}</span>',
        '                        <span className={cn("grid h-8 w-8 shrink-0 place-items-center rounded-full border text-xs font-black", active ? "border-amber-400 bg-amber-100 text-amber-800" : done ? "border-emerald-200 bg-emerald-50 text-emerald-700" : available ? "border-zinc-200 bg-white text-zinc-500 dark:border-zinc-700 dark:bg-zinc-900" : "border-zinc-200 bg-zinc-50 text-zinc-300 dark:border-zinc-800 dark:bg-zinc-900/50")}>{step.id}</span>'
    ),
    (
        '                          <b className={cn("block text-sm font-black", available ? "text-zinc-950 dark:text-white" : "text-zinc-400 dark:text-zinc-600")}>{step.title}</b>\n                          <small className="mt-1 block text-xs font-bold text-zinc-400">{available ? step.note : (ui.lockedStepHint || "أكمل الخطوات السابقة أولًا")}</small>',
        '                          <b className={cn("block text-xs font-black", available ? "text-zinc-950 dark:text-white" : "text-zinc-400 dark:text-zinc-600")}>{step.title}</b>\n                          <small className="mt-0.5 block text-[10px] font-bold leading-4 text-zinc-400">{available ? step.note : (ui.lockedStepHint || "أكمل الخطوات السابقة أولًا")}</small>'
    ),
    (
        '            <form onSubmit={submit} className="mt-6 grid gap-5 xl:grid-cols-[minmax(0,1fr)_310px]" noValidate>\n              <div className="grid gap-4">',
        '            <form onSubmit={submit} className="mt-4 grid gap-4 xl:grid-cols-[minmax(0,1fr)_280px]" noValidate>\n              <div className="grid gap-3">'
    ),
    (
        '                      <label className="block rounded-3xl border border-dashed border-zinc-200 bg-zinc-50 p-7 text-center text-sm font-black text-zinc-600 dark:border-white/10 dark:bg-zinc-950/30 dark:text-zinc-300">\n                        <span className="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-white text-amber-700 shadow-sm ring-1 ring-zinc-100 dark:bg-white/10 dark:text-amber-300 dark:ring-white/10"><FileText size={22} /></span>\n                        <span className="mt-3 block">{ui.projectFiles}</span>\n                        <input type="file" multiple className="mt-4 block w-full text-xs" onChange={(event) => setCreateProjectFiles(Array.from(event.target.files || []))} />\n                        <span className="mt-3 block text-xs font-bold text-zinc-400">{ui.fileCount(createProjectFiles.length)}</span>',
        '                      <label className="block rounded-[20px] border border-dashed border-zinc-200 bg-zinc-50/80 p-5 text-center text-xs font-black text-zinc-600 dark:border-white/10 dark:bg-zinc-950/30 dark:text-zinc-300">\n                        <span className="mx-auto grid h-12 w-12 place-items-center rounded-[14px] bg-white text-amber-700 shadow-sm ring-1 ring-zinc-100 dark:bg-white/10 dark:text-amber-300 dark:ring-white/10"><FileText size={19} /></span>\n                        <span className="mt-2 block">{ui.projectFiles}</span>\n                        <input type="file" multiple className="mt-3 block w-full text-[11px]" onChange={(event) => setCreateProjectFiles(Array.from(event.target.files || []))} />\n                        <span className="mt-2 block text-[11px] font-bold text-zinc-400">{ui.fileCount(createProjectFiles.length)}</span>'
    ),
    (
        '                      <div className="mt-5 grid gap-3">',
        '                      <div className="mt-4 grid gap-2.5">'
    ),
    (
        '                          <label className="flex items-center justify-between gap-3 rounded-2xl border border-zinc-100 bg-zinc-50 px-4 py-3 text-sm font-black text-zinc-700 dark:border-zinc-800 dark:bg-white/5 dark:text-zinc-200">',
        '                          <label className="flex items-center justify-between gap-3 rounded-[14px] border border-zinc-200/70 bg-zinc-50 px-3.5 py-2.5 text-xs font-black text-zinc-700 dark:border-zinc-800 dark:bg-white/5 dark:text-zinc-200">'
    ),
    (
        '                      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-5">',
        '                      <div className="grid gap-2 md:grid-cols-2 xl:grid-cols-5">'
    ),
    (
        '                      <TaskRichTextEditor value={createDraft.description} onChange={(value) => updateCreateDraft("description", value)} placeholder={ui.descriptionPlaceholder} minHeight="min-h-[220px] max-h-[460px] overflow-y-auto" label={ui.description} ui={editorUi} />',
        '                      <TaskRichTextEditor value={createDraft.description} onChange={(value) => updateCreateDraft("description", value)} placeholder={ui.descriptionPlaceholder} minHeight="min-h-[180px] max-h-[360px] overflow-y-auto" label={ui.description} ui={editorUi} />'
    ),
    (
        '              <aside className="rounded-[28px] border border-amber-100 bg-amber-50/50 p-5 shadow-sm dark:border-amber-500/20 dark:bg-amber-500/10">\n                <p className="tos-kicker">{ui.projectSummary}</p>\n                <h4 className="mt-2 break-words text-xl font-black text-zinc-950 dark:text-white">{fieldValue(createDraft.name, ui.newProject)}</h4>\n                <div className="mt-4"><ProjectTypeChips value={createDraft.projectTypeNames} ui={ui} /></div>\n                <div className="mt-5 grid gap-3 text-sm font-bold text-zinc-600 dark:text-zinc-300">',
        '              <aside className="self-start rounded-[20px] border border-amber-100 bg-amber-50/45 p-4 shadow-sm dark:border-amber-500/20 dark:bg-amber-500/10 xl:sticky xl:top-4">\n                <p className="tos-kicker">{ui.projectSummary}</p>\n                <h4 className="mt-1.5 break-words text-lg font-black text-zinc-950 dark:text-white">{fieldValue(createDraft.name, ui.newProject)}</h4>\n                <div className="mt-3"><ProjectTypeChips value={createDraft.projectTypeNames} ui={ui} /></div>\n                <div className="mt-4 grid gap-2.5 text-xs font-bold text-zinc-600 dark:text-zinc-300">'
    ),
    (
        '                <div className="mt-5 rounded-2xl border border-amber-100 bg-white/70 p-4 text-xs font-bold leading-6 text-amber-800 dark:border-amber-500/20 dark:bg-zinc-950/20 dark:text-amber-200">',
        '                <div className="mt-4 rounded-[14px] border border-amber-100 bg-white/70 p-3 text-[11px] font-bold leading-5 text-amber-800 dark:border-amber-500/20 dark:bg-zinc-950/20 dark:text-amber-200">'
    ),
    (
        '              <div className="flex flex-wrap items-center justify-between gap-3 border-t border-zinc-100 pt-5 dark:border-zinc-800 xl:col-span-2">',
        '              <div className="flex flex-wrap items-center justify-between gap-2.5 border-t border-zinc-200/70 pt-4 dark:border-zinc-800 xl:col-span-2">'
    ),
]

REQUIRED_MARKERS = [
    'onSubmit={submit}',
    'setCreateExpanded(false)',
    'setCreateStep((step) => Math.max(1, step - 1))',
    'setCreateStep((step) => Math.min(4, step + 1))',
    'toggleCreateDraftId("teamMemberIds", id)',
    'setCreateProjectFiles(Array.from(event.target.files || []))',
    'createCanSubmit',
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
        print("Usage: generate_ux_ui_phase05_project_create.py <repo> <output.patch>", file=sys.stderr)
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
    print("CREATE_SCOPE=PROJECT_CREATE_WIZARD_ONLY")
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
