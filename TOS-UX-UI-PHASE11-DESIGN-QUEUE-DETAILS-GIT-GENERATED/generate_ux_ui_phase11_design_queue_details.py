#!/usr/bin/env python3
import difflib
import hashlib
import subprocess
import sys
from pathlib import Path

TARGET_BASE_HEAD = "10a9bfe1d24e26538e7fe06577ad25479125940b"
TARGET_FILE = "frontend/src/pages/DesignQueuePage.jsx"
EXPECTED_BLOB = "6f8062f24ac08d3ffcf337b815d05266783a91f9"

DETAILS_START = "function DetailMetric("
DETAILS_END = "function mergeDesignQueueProjectOptions("

REPLACEMENTS = [
    (
        '    <div className="flex min-w-0 items-center gap-3 border-b border-slate-100 px-4 py-3 last:border-b-0 sm:border-b-0 sm:border-s sm:last:border-s-0 dark:border-white/10">',
        '    <div className="flex min-w-0 items-center gap-2.5 border-b border-slate-100 px-3 py-2.5 last:border-b-0 sm:border-b-0 sm:border-s sm:last:border-s-0 dark:border-white/10">',
        1,
    ),
    (
        '      <span className={cn("grid h-10 w-10 shrink-0 place-items-center rounded-2xl", toneClass)}><Icon size={18} /></span>',
        '      <span className={cn("grid h-9 w-9 shrink-0 place-items-center rounded-xl", toneClass)}><Icon size={16} /></span>',
        1,
    ),
    (
        '    <section dir={direction} className={cn("overflow-hidden rounded-[24px] border border-amber-100/80 bg-white shadow-sm shadow-amber-950/[0.03] dark:border-white/10 dark:bg-zinc-950", className)}>',
        '    <section dir={direction} className={cn("overflow-hidden rounded-[20px] border border-amber-100/80 bg-white shadow-sm shadow-amber-950/[0.03] dark:border-white/10 dark:bg-zinc-950", className)}>',
        1,
    ),
    (
        '      <div className="flex items-center gap-2 border-b border-amber-100/70 px-4 py-3.5 text-sm font-black text-slate-950 dark:border-white/10 dark:text-white"><Icon size={18} className="text-amber-600 dark:text-amber-300" />{title}</div>',
        '      <div className="flex items-center gap-2 border-b border-amber-100/70 px-3.5 py-3 text-[13px] font-black text-slate-950 dark:border-white/10 dark:text-white"><Icon size={16} className="text-amber-600 dark:text-amber-300" />{title}</div>',
        1,
    ),
    (
        '      <div className="p-4">{children}</div>',
        '      <div className="p-3.5">{children}</div>',
        1,
    ),
    (
        '    <section className="min-h-[calc(100vh-150px)] w-full rounded-[30px] border border-amber-100/80 bg-[#f8f5ee] p-3 shadow-[0_24px_70px_rgba(120,83,20,0.08)] dark:border-white/10 dark:bg-zinc-950" dir={isAr ? "rtl" : "ltr"}>',
        '    <section className="min-h-[calc(100vh-138px)] w-full rounded-[24px] border border-amber-100/80 bg-[#f8f5ee] p-2.5 shadow-[0_16px_52px_rgba(120,83,20,0.07)] dark:border-white/10 dark:bg-zinc-950" dir={isAr ? "rtl" : "ltr"}>',
        1,
    ),
    (
        '      ) : (\n        <div className="space-y-4">',
        '      ) : (\n        <div className="space-y-3">',
        1,
    ),
    (
        '          <header className="relative overflow-hidden rounded-[26px] border border-amber-200/80 bg-[#fffaf0] px-5 py-5 dark:border-amber-400/20 dark:bg-amber-500/[0.06]">',
        '          <header className="relative overflow-hidden rounded-[20px] border border-amber-200/80 bg-[#fffaf0] px-4 py-4 dark:border-amber-400/20 dark:bg-amber-500/[0.06]">',
        1,
    ),
    (
        '            <div className="pointer-events-none absolute -start-8 -top-10 h-36 w-36 rounded-full border-[24px] border-amber-100/50 dark:border-amber-400/5" />',
        '            <div className="pointer-events-none absolute -start-7 -top-9 h-28 w-28 rounded-full border-[20px] border-amber-100/45 dark:border-amber-400/5" />',
        1,
    ),
    (
        '            <div className="pointer-events-none absolute bottom-5 start-10 grid h-16 w-16 place-items-center rounded-[22px] border border-amber-200/60 bg-white/70 text-amber-500 opacity-60 dark:border-amber-400/10 dark:bg-white/5"><Palette size={30} /></div>',
        '            <div className="pointer-events-none absolute bottom-4 start-8 grid h-12 w-12 place-items-center rounded-[16px] border border-amber-200/60 bg-white/70 text-amber-500 opacity-55 dark:border-amber-400/10 dark:bg-white/5"><Palette size={24} /></div>',
        1,
    ),
    (
        '            <div className="relative z-10 flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">',
        '            <div className="relative z-10 flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">',
        1,
    ),
    (
        '                <h2 className="mt-3 text-2xl font-black leading-9 text-slate-950 sm:text-3xl dark:text-white">{task.title}</h2>',
        '                <h2 className="mt-2.5 text-xl font-black leading-8 text-slate-950 sm:text-2xl dark:text-white">{task.title}</h2>',
        1,
    ),
    (
        '                  <span className="rounded-xl border border-amber-200 bg-white px-3 py-2 text-xs font-black text-slate-700 dark:border-amber-400/20 dark:bg-zinc-900 dark:text-zinc-200">',
        '                  <span className="rounded-lg border border-amber-200 bg-white px-2.5 py-1.5 text-[11px] font-black text-slate-700 dark:border-amber-400/20 dark:bg-zinc-900 dark:text-zinc-200">',
        2,
    ),
    (
        '              <div className="w-full shrink-0 rounded-[22px] border border-amber-200/80 bg-white/90 p-3 shadow-sm lg:w-[290px] dark:border-amber-400/20 dark:bg-zinc-900/90">',
        '              <div className="w-full shrink-0 rounded-[18px] border border-amber-200/80 bg-white/90 p-2.5 shadow-sm lg:w-[260px] dark:border-amber-400/20 dark:bg-zinc-900/90">',
        1,
    ),
    (
        '          <div className="grid overflow-hidden rounded-[24px] border border-amber-100 bg-white sm:grid-cols-5 dark:border-white/10 dark:bg-zinc-950">',
        '          <div className="grid overflow-hidden rounded-[18px] border border-amber-100 bg-white sm:grid-cols-5 dark:border-white/10 dark:bg-zinc-950">',
        1,
    ),
    (
        '          <div dir="ltr" className="grid items-start gap-4 xl:grid-cols-[minmax(0,1fr)_320px]">',
        '          <div dir="ltr" className="grid items-start gap-3 xl:grid-cols-[minmax(0,1fr)_290px]">',
        1,
    ),
    (
        '            <div dir={isAr ? "rtl" : "ltr"} className="min-w-0 space-y-4">',
        '            <div dir={isAr ? "rtl" : "ltr"} className="min-w-0 space-y-3">',
        1,
    ),
    (
        '              <div className="grid items-start gap-4 lg:grid-cols-[minmax(0,1.18fr)_minmax(300px,.82fr)]">',
        '              <div className="grid items-start gap-3 lg:grid-cols-[minmax(0,1.22fr)_minmax(280px,.78fr)]">',
        1,
    ),
    (
        '            <aside dir={isAr ? "rtl" : "ltr"} className="space-y-4 xl:sticky xl:top-4">',
        '            <aside dir={isAr ? "rtl" : "ltr"} className="space-y-3 xl:sticky xl:top-3">',
        1,
    ),
]

REQUIRED_MARKERS = [
    "function DetailMetric(",
    "function DetailSection(",
    "function DetailsWorkspace(",
    "onClose",
    "onSave",
    "onDeleteFile",
    "onAddAttachments",
    "onSelfAssign",
    "onReject",
    "onArchive",
    "onRestore",
    "tasksApi.filePreviewUrl(",
]

QUEUE_MARKERS = [
    "function QueueStatRing(",
    "function TaskCard(",
    "function KanbanBoard(",
    "function CapacitySection(",
    "export function DesignQueuePage(",
    "api.tasks.designQueue(",
    "api.tasks.designQueueDetails(",
    "api.tasks.assignDesignQueueTask(",
    "api.tasks.updateDesignCapacity(",
    "api.tasks.selfAssignDesignQueueTask(",
    "api.tasks.rejectDesignQueueTask(",
    "api.tasks.archiveDesignQueueTask(",
    "api.tasks.restoreDesignQueueTask(",
    "tasksApi.uploadTaskFiles(",
]

def run(cmd, cwd):
    return subprocess.check_output(cmd, cwd=cwd, text=True).strip()

def git_blob_sha(data):
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data).hexdigest()

def replace_exact(text, old, new, expected_count, label):
    count = text.count(old)
    if count != expected_count:
        raise RuntimeError(f"ANCHOR_{label}_COUNT={count}; expected {expected_count}")
    return text.replace(old, new)

def split_details(text):
    start = text.find(DETAILS_START)
    end = text.find(DETAILS_END, start + 1)
    if start < 0 or end < 0 or end <= start:
        raise RuntimeError("DETAILS_BLOCK_NOT_FOUND")
    return text[:start], text[start:end], text[end:]

def main():
    if len(sys.argv) != 3:
        print("Usage: generate_ux_ui_phase11_design_queue_details.py <repo> <output.patch>", file=sys.stderr)
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
    prefix, details, suffix = split_details(original)
    original_details = details
    original_main_hash = hashlib.sha256((prefix + suffix).encode("utf-8")).hexdigest()

    for idx, (old, new, expected_count) in enumerate(REPLACEMENTS, start=1):
        details = replace_exact(details, old, new, expected_count, f"{idx:02d}")

    updated = prefix + details + suffix
    if updated == original:
        raise RuntimeError("NO_CHANGES")

    updated_prefix, updated_details, updated_suffix = split_details(updated)
    updated_main_hash = hashlib.sha256((updated_prefix + updated_suffix).encode("utf-8")).hexdigest()
    if updated_main_hash != original_main_hash:
        raise RuntimeError("UI10_MAIN_QUEUE_CHANGED")

    for marker in REQUIRED_MARKERS:
        if original_details.count(marker) != updated_details.count(marker):
            raise RuntimeError(f"DETAILS_BEHAVIOR_MARKER_CHANGED={marker}")

    for marker in QUEUE_MARKERS:
        if original.count(marker) != updated.count(marker):
            raise RuntimeError(f"QUEUE_MARKER_CHANGED={marker}")

    if original.count("api.") != updated.count("api."):
        raise RuntimeError("API_CALL_COUNT_CHANGED")
    if original.count("tasksApi.") != updated.count("tasksApi."):
        raise RuntimeError("TASKS_API_CALL_COUNT_CHANGED")

    for line_no, line in enumerate(updated.splitlines(), start=1):
        if line.rstrip() != line:
            raise RuntimeError(f"TRAILING_WHITESPACE_LINE={line_no}")

    new_bytes = updated.encode("utf-8")
    new_blob = git_blob_sha(new_bytes)

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
    print("DESIGN_DETAILS_SCOPE=DETAILS_WORKSPACE_ONLY")
    print("UI10_MAIN_QUEUE_CHANGED=NO")
    print(f"UI10_MAIN_QUEUE_HASH={original_main_hash}")
    print("DESIGN_BEHAVIOR_CHANGED=NO")
    print("API_CALLS_CHANGED=NO")
    print("TASKS_API_CALLS_CHANGED=NO")
    print("ROUTES_CHANGED=NO")
    print("PERMISSIONS_CHANGED=NO")
    print("BACKEND_INCLUDED=NO")
    print(f"REPLACEMENTS={len(REPLACEMENTS)}")
    print(f"PATCH_SHA256={sha256}")
    print(f"PATCH_PATH={output}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
