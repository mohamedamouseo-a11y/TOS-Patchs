#!/usr/bin/env python3
import difflib
import hashlib
import os
import subprocess
import sys
from pathlib import Path

TARGET_BASE_HEAD = "1a2f6ef9d5611d01f7d2bd777aab3df7f67b03a3"
TARGET_FILE = "frontend/src/pages/ProjectsPage.jsx"
EXPECTED_BLOB = "0fb7fd5b941a7eb73beea32110716401ba38ae38"

REPLACEMENTS = [
    (
        '    <div className="rounded-[28px] border border-zinc-100 bg-white/85 p-4 shadow-sm dark:border-zinc-800 dark:bg-zinc-950/30">\n'
        '      <div className="grid gap-4 lg:grid-cols-[140px_minmax(0,1fr)] lg:items-center">\n'
        '        <div className="border-zinc-100 text-right lg:border-l lg:pl-4 dark:border-zinc-800">\n'
        '          <p className="text-xs font-black text-zinc-500 dark:text-zinc-400">{ui.projectProgress || ui.generalProgress}</p>\n'
        '          <p className="mt-1 text-3xl font-black text-amber-600">{progress}%</p>',
        '    <div className="rounded-[20px] border border-zinc-200/70 bg-white/90 p-3 shadow-[0_8px_24px_rgba(15,23,42,0.04)] dark:border-zinc-800 dark:bg-zinc-950/40">\n'
        '      <div className="grid gap-3 lg:grid-cols-[110px_minmax(0,1fr)] lg:items-center">\n'
        '        <div className="border-zinc-100 text-right lg:border-l lg:pl-3 dark:border-zinc-800">\n'
        '          <p className="text-[11px] font-black text-zinc-500 dark:text-zinc-400">{ui.projectProgress || ui.generalProgress}</p>\n'
        '          <p className="mt-1 text-2xl font-black text-amber-600">{progress}%</p>'
    ),
    (
        '        <div className="grid gap-3 md:grid-cols-6">\n'
        '          {steps.map((step, index) => (\n'
        '            <div key={step.key} className="relative min-w-0 text-center">\n'
        '              {index < steps.length - 1 && <span className={cn("absolute top-4 hidden h-0.5 w-full md:block", step.done ? "bg-emerald-400" : "bg-zinc-200 dark:bg-zinc-700")} />}\n'
        '              <span className={cn("relative z-10 mx-auto grid h-8 w-8 place-items-center rounded-full border bg-white", step.done ? "border-emerald-300 text-emerald-600" : "border-zinc-200 text-zinc-400 dark:border-zinc-700 dark:bg-zinc-950")}>{step.done ? <CheckCircle2 size={16} /> : <span className="h-2 w-2 rounded-full bg-current" />}</span>\n'
        '              <p className="mt-2 truncate text-[11px] font-black text-zinc-700 dark:text-zinc-200">{step.label}</p>\n'
        '              <p className="mt-1 truncate text-[11px] font-bold text-zinc-400">{formatDate(step.date)}</p>',
        '        <div className="grid gap-2 md:grid-cols-6">\n'
        '          {steps.map((step, index) => (\n'
        '            <div key={step.key} className="relative min-w-0 text-center">\n'
        '              {index < steps.length - 1 && <span className={cn("absolute top-3.5 hidden h-px w-full md:block", step.done ? "bg-emerald-400" : "bg-zinc-200 dark:bg-zinc-700")} />}\n'
        '              <span className={cn("relative z-10 mx-auto grid h-7 w-7 place-items-center rounded-full border bg-white", step.done ? "border-emerald-300 text-emerald-600" : "border-zinc-200 text-zinc-400 dark:border-zinc-700 dark:bg-zinc-950")}>{step.done ? <CheckCircle2 size={14} /> : <span className="h-1.5 w-1.5 rounded-full bg-current" />}</span>\n'
        '              <p className="mt-1.5 truncate text-[10px] font-black text-zinc-700 dark:text-zinc-200">{step.label}</p>\n'
        '              <p className="mt-0.5 truncate text-[10px] font-bold text-zinc-400">{formatDate(step.date)}</p>'
    ),
    (
        '    <header className="rounded-[34px] border border-zinc-100 bg-white/95 p-4 shadow-sm shadow-zinc-200/60 dark:border-zinc-800 dark:bg-zinc-900/90 dark:shadow-black/20 md:p-6">',
        '    <header className="rounded-[24px] border border-zinc-200/70 bg-white/95 p-4 shadow-[0_12px_36px_rgba(15,23,42,0.055)] dark:border-zinc-800 dark:bg-zinc-900/90 dark:shadow-black/20 md:p-5">'
    ),
    (
        '      <div dir={locale === "ar" ? "rtl" : "ltr"} className="mb-5 grid grid-cols-[minmax(0,1fr)_auto] items-center gap-3 text-sm font-black text-zinc-500 dark:text-zinc-400">',
        '      <div dir={locale === "ar" ? "rtl" : "ltr"} className="mb-3 grid grid-cols-[minmax(0,1fr)_auto] items-center gap-3 text-xs font-black text-zinc-500 dark:text-zinc-400">'
    ),
    (
        '        <button type="button" onClick={onClose} className="grid h-10 w-10 shrink-0 place-items-center rounded-2xl border border-zinc-100 bg-white text-zinc-500 transition hover:border-zinc-200 hover:bg-zinc-50 hover:text-zinc-950 dark:border-white/10 dark:bg-zinc-950 dark:hover:border-white/20 dark:hover:text-white" aria-label={ui.close || "إغلاق"}>',
        '        <button type="button" onClick={onClose} className="grid h-9 w-9 shrink-0 place-items-center rounded-xl border border-zinc-200/80 bg-white text-zinc-500 shadow-sm transition hover:border-zinc-300 hover:bg-zinc-50 hover:text-zinc-950 dark:border-white/10 dark:bg-zinc-950 dark:hover:border-white/20 dark:hover:text-white" aria-label={ui.close || "إغلاق"}>'
    ),
    (
        '      <div className="grid gap-6 lg:grid-cols-[170px_minmax(0,1fr)_auto] lg:items-start">',
        '      <div className="grid gap-4 lg:grid-cols-[112px_minmax(0,1fr)_auto] lg:items-start">'
    ),
    (
        '          <div className="grid h-32 w-32 place-items-center rounded-[28px] border border-amber-100 bg-amber-50/60 text-center shadow-sm dark:border-amber-400/20 dark:bg-amber-500/10">\n'
        '            <LogoMark className="h-14 w-14" />\n'
        '            <div className="mt-2 text-xs font-black text-zinc-950 dark:text-white">TOS</div>',
        '          <div className="grid h-24 w-24 place-items-center rounded-[20px] border border-amber-100 bg-amber-50/60 text-center shadow-sm dark:border-amber-400/20 dark:bg-amber-500/10">\n'
        '            <LogoMark className="h-10 w-10" />\n'
        '            <div className="mt-1 text-[10px] font-black text-zinc-950 dark:text-white">TOS</div>'
    ),
    (
        '          <h2 dir="auto" className="break-words text-3xl font-black tracking-tight text-zinc-950 dark:text-white md:text-5xl">{project.name}</h2>\n'
        '          <div className="mt-3 flex flex-col items-end gap-1.5 text-sm font-bold text-zinc-500 dark:text-zinc-400">',
        '          <h2 dir="auto" className="break-words text-2xl font-black tracking-[-0.025em] text-zinc-950 dark:text-white md:text-3xl">{project.name}</h2>\n'
        '          <div className="mt-2 flex flex-col items-end gap-1 text-xs font-bold text-zinc-500 dark:text-zinc-400">'
    ),
    (
        '          <div className="mt-5 flex flex-wrap justify-end gap-2">\n'
        '            <Badge tone={STATUS_TONES[project.status]}>{labels.status?.[project.status] || project.status}</Badge>',
        '          <div className="mt-3 flex flex-wrap justify-end gap-1.5">\n'
        '            <Badge tone={STATUS_TONES[project.status]}>{labels.status?.[project.status] || project.status}</Badge>'
    ),
    (
        '          <div className="mt-5 flex flex-wrap justify-end gap-2"><ProjectTypeChips value={project.type} ui={ui} /></div>',
        '          <div className="mt-3 flex flex-wrap justify-end gap-1.5"><ProjectTypeChips value={project.type} ui={ui} /></div>'
    ),
    (
        '      <div className="mt-6"><ProjectProgressTimeline project={project} labels={labels} ui={ui} /></div>\n'
        '      <div className="mt-5 grid gap-3 md:grid-cols-5">',
        '      <div className="mt-4"><ProjectProgressTimeline project={project} labels={labels} ui={ui} /></div>\n'
        '      <div className="mt-4 grid gap-2 md:grid-cols-5">'
    ),
    (
        '      <div className="mt-5 flex flex-wrap items-center justify-around gap-2 rounded-[26px] border border-zinc-100 bg-white/90 p-2 shadow-sm dark:border-zinc-800 dark:bg-zinc-950/30">',
        '      <div className="mt-4 flex flex-wrap items-center justify-around gap-1.5 rounded-[18px] border border-zinc-200/70 bg-zinc-50/70 p-1.5 shadow-sm dark:border-zinc-800 dark:bg-zinc-950/30">'
    ),
    (
        '          <button key={id} type="button" onClick={() => setActiveTab(id)} className={cn("inline-flex min-w-[160px] items-center justify-center gap-2 rounded-2xl px-4 py-3 text-sm font-black transition", activeTab === id ? "bg-amber-100 text-amber-900 shadow-sm dark:bg-amber-300 dark:text-zinc-950" : "text-zinc-500 hover:bg-zinc-50 hover:text-zinc-900 dark:text-zinc-400 dark:hover:bg-white/5 dark:hover:text-white")}>',
        '          <button key={id} type="button" onClick={() => setActiveTab(id)} className={cn("inline-flex min-w-[132px] items-center justify-center gap-2 rounded-[13px] px-3 py-2.5 text-xs font-black transition", activeTab === id ? "bg-white text-amber-800 shadow-sm ring-1 ring-amber-200 dark:bg-amber-300 dark:text-zinc-950 dark:ring-amber-300" : "text-zinc-500 hover:bg-white hover:text-zinc-900 dark:text-zinc-400 dark:hover:bg-white/5 dark:hover:text-white")}> '
    ),
    (
        '    <aside className="grid gap-5 xl:sticky xl:top-6 xl:self-start">',
        '    <aside className="grid gap-4 xl:sticky xl:top-4 xl:self-start">'
    ),
    (
        '        <div className="fixed inset-0 z-50 overflow-y-auto bg-[#fbfaf8] dark:bg-zinc-950" dir={pageDirection}>\n'
        '          <div className="flex min-h-screen w-full max-w-none flex-col bg-[#fbfaf8] dark:bg-zinc-950">\n'
        '            <div className="shrink-0 bg-[#fbfaf8] p-4 dark:bg-zinc-950 md:p-6 xl:p-8">',
        '        <div className="fixed inset-0 z-50 overflow-y-auto bg-[#f7f7f5] dark:bg-zinc-950" dir={pageDirection}>\n'
        '          <div className="flex min-h-screen w-full max-w-none flex-col bg-[#f7f7f5] dark:bg-zinc-950">\n'
        '            <div className="shrink-0 bg-[#f7f7f5] p-3 dark:bg-zinc-950 md:p-4 xl:p-5">'
    ),
    (
        '            <div className="flex-1 bg-[#fbfaf8] p-4 dark:bg-zinc-950 md:p-6 xl:p-8">',
        '            <div className="flex-1 bg-[#f7f7f5] p-3 dark:bg-zinc-950 md:p-4 xl:p-5">'
    ),
    (
        '                  "mb-5 flex flex-wrap items-center justify-between gap-3 rounded-[24px] border p-4 shadow-sm",',
        '                  "mb-4 flex flex-wrap items-center justify-between gap-3 rounded-[18px] border p-3.5 shadow-sm",'
    ),
    (
        '              <div className="grid gap-5 xl:grid-cols-[390px_minmax(0,1fr)]">\n'
        '                <ProjectDetailsSummaryRail',
        '              <div className="grid gap-4 xl:grid-cols-[320px_minmax(0,1fr)]">\n'
        '                <ProjectDetailsSummaryRail'
    ),
    (
        '                />\n\n                <div className="grid gap-5">\n'
        '                  {activeTab === "overview" && (\n'
        '                    <>\n'
        '                      <div className="grid gap-5 lg:grid-cols-2">',
        '                />\n\n                <div className="grid gap-4">\n'
        '                  {activeTab === "overview" && (\n'
        '                    <>\n'
        '                      <div className="grid gap-4 lg:grid-cols-2">'
    ),
]

REQUIRED_MARKERS = [
    'onClick={onOpenTasks}',
    'onClick={onEdit}',
    'onClick={onArchive}',
    'onClick={onRestore}',
    'onClick={onPullFromTcrm}',
    'setActiveTab(id)',
    'api.projects.get(',
    'api.projects.activity(',
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
        print("Usage: generate_ux_ui_phase04_project_details.py <repo> <output.patch>", file=sys.stderr)
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

    original_bytes = original.encode("utf-8")
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
    print("DETAILS_SCOPE=PROJECT_DETAILS_ONLY")
    print("BUSINESS_LOGIC_CHANGED=NO")
    print("ROUTES_CHANGED=NO")
    print("BACKEND_INCLUDED=NO")
    print(f"REPLACEMENTS={len(REPLACEMENTS)}")
    print(f"PATCH_SHA256={sha256}")
    print(f"PATCH_PATH={output}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
