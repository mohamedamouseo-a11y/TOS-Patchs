#!/usr/bin/env python3
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TARGET_BASE_HEAD = "0bdfe6eef20849622a7680b39d167df315673578"
TARGET_FILE = "frontend/src/pages/ProjectsPage.jsx"
EXPECTED_BLOB = "963de64064dc2f0acb41d23c017ad99f8d2dc301"

REPLACEMENTS = [
    (
        '<div className={cn("tos-page", pageTextClass)} dir={pageDirection}>',
        '<div className={cn("tos-page tos-projects-ui03 space-y-4", pageTextClass)} dir={pageDirection}>',
    ),
    (
        '<div className={cn("grid gap-4 md:grid-cols-2 xl:grid-cols-4", isAr ? "direction-rtl" : "direction-ltr")}>',
        '<div className={cn("grid gap-3 sm:grid-cols-2 xl:grid-cols-4", isAr ? "direction-rtl" : "direction-ltr")}>',
    ),
    (
        'className="group relative flex min-h-[148px] items-center gap-4 overflow-hidden rounded-[26px] border border-zinc-200/60 bg-gradient-to-br from-white via-white to-zinc-50/55 p-5 text-start shadow-[0_14px_42px_rgba(15,23,42,0.055)] ring-1 ring-white/80 transition-all duration-300 hover:-translate-y-1 hover:border-zinc-300/80 hover:shadow-[0_24px_60px_rgba(15,23,42,0.10)] dark:border-zinc-800 dark:from-zinc-900 dark:via-zinc-900 dark:to-zinc-950 dark:ring-white/[0.03]"',
        'className="group relative flex min-h-[118px] items-center gap-3 overflow-hidden rounded-[22px] border border-zinc-200/70 bg-white p-4 text-start shadow-[0_10px_28px_rgba(15,23,42,0.045)] ring-1 ring-white/70 transition-all duration-200 hover:border-zinc-300 hover:shadow-[0_16px_36px_rgba(15,23,42,0.075)] dark:border-zinc-800 dark:bg-zinc-900 dark:ring-white/[0.025]"',
    ),
    (
        'className="pointer-events-none absolute -end-8 -top-8 h-24 w-24 rounded-full bg-zinc-100/80 blur-2xl transition group-hover:scale-125 dark:bg-white/[0.035]"',
        'className="pointer-events-none absolute -end-7 -top-7 h-20 w-20 rounded-full bg-amber-50/70 blur-2xl dark:bg-amber-500/[0.035]"',
    ),
    (
        'className="relative grid h-[82px] w-[82px] shrink-0 place-items-center rounded-full shadow-[0_10px_22px_rgba(15,23,42,0.08)]"',
        'className="relative grid h-[64px] w-[64px] shrink-0 place-items-center rounded-full shadow-[0_8px_18px_rgba(15,23,42,0.07)]"',
    ),
    (
        'className="grid h-[62px] w-[62px] place-items-center rounded-full bg-white shadow-inner ring-1 ring-black/[0.035] dark:bg-zinc-900 dark:ring-white/5"',
        'className="grid h-[48px] w-[48px] place-items-center rounded-full bg-white shadow-inner ring-1 ring-black/[0.035] dark:bg-zinc-900 dark:ring-white/5"',
    ),
    (
        'cn("text-[25px] font-black tracking-[-0.03em]", current.text)',
        'cn("text-[20px] font-black tracking-[-0.03em]", current.text)',
    ),
    (
        'className="relative min-w-0 flex-1 pe-9"',
        'className="relative min-w-0 flex-1 pe-7"',
    ),
    (
        'className="text-[13px] font-black tracking-[-0.01em] text-zinc-950 dark:text-white"',
        'className="text-[12px] font-black tracking-[-0.01em] text-zinc-950 dark:text-white"',
    ),
    (
        'className="mt-1.5 text-[11px] font-bold leading-5 text-zinc-500 dark:text-zinc-400"',
        'className="mt-1 text-[10px] font-bold leading-4 text-zinc-500 dark:text-zinc-400"',
    ),
    (
        'className={cn("mt-2.5 inline-flex rounded-full bg-white px-2.5 py-1 text-[10px] font-black shadow-sm ring-1 ring-zinc-100", current.badge, "dark:bg-white/5 dark:ring-white/10")}',
        'className={cn("mt-2 inline-flex rounded-full bg-zinc-50 px-2.5 py-1 text-[9px] font-black ring-1 ring-zinc-100", current.badge, "dark:bg-white/5 dark:ring-white/10")}',
    ),
    (
        'className={cn("absolute end-4 top-4 grid h-8 w-8 place-items-center rounded-[12px] bg-white shadow-sm ring-1 ring-zinc-100", current.text, "dark:bg-white/5 dark:ring-white/10")}',
        'className={cn("absolute end-3.5 top-3.5 grid h-7 w-7 place-items-center rounded-[10px] bg-zinc-50 ring-1 ring-zinc-100", current.text, "dark:bg-white/5 dark:ring-white/10")}',
    ),
    (
        '<Card className="rounded-[28px] border-zinc-200/60 bg-white/88 p-3.5 shadow-[0_18px_50px_rgba(15,23,42,0.055)] ring-1 ring-white/80 backdrop-blur-xl dark:border-zinc-800 dark:bg-zinc-900/88 dark:ring-white/[0.025] md:p-4">',
        '<Card className="rounded-[24px] border-zinc-200/70 bg-white/92 p-3 shadow-[0_12px_34px_rgba(15,23,42,0.045)] ring-1 ring-white/70 backdrop-blur-xl dark:border-zinc-800 dark:bg-zinc-900/92 dark:ring-white/[0.025] md:p-3.5">',
    ),
    (
        'className="flex flex-col gap-2.5 xl:flex-row xl:items-center"',
        'className="flex flex-col gap-2 xl:flex-row xl:items-center"',
    ),
    (
        'className="h-11 rounded-[14px] border-zinc-200/80 bg-zinc-50/70 px-4 text-sm shadow-[inset_0_1px_0_rgba(255,255,255,0.8)] transition focus:border-zinc-300 focus:bg-white dark:border-zinc-800 dark:bg-zinc-950"',
        'className="h-10 rounded-[13px] border-zinc-200/80 bg-zinc-50/70 px-3.5 text-[13px] shadow-[inset_0_1px_0_rgba(255,255,255,0.8)] transition focus:border-amber-300 focus:bg-white dark:border-zinc-800 dark:bg-zinc-950"',
    ),
    (
        '"flex h-11 min-w-[160px] items-center justify-between rounded-[14px] border px-3.5 shadow-sm transition"',
        '"flex h-10 min-w-[150px] items-center justify-between rounded-[13px] border px-3.5 shadow-sm transition"',
    ),
    (
        '<div className="mt-3.5 overflow-hidden rounded-[20px] border border-zinc-200/60 bg-gradient-to-b from-zinc-50/70 to-white/70 shadow-[inset_0_1px_0_rgba(255,255,255,0.8)] dark:border-zinc-800 dark:from-white/[0.035] dark:to-white/[0.02]">',
        '<div className="mt-3 overflow-hidden rounded-[18px] border border-zinc-200/70 bg-zinc-50/65 shadow-[inset_0_1px_0_rgba(255,255,255,0.8)] dark:border-zinc-800 dark:bg-white/[0.025]">',
    ),
    (
        '<div className="grid gap-4 2xl:grid-cols-[minmax(0,1.22fr)_minmax(390px,.78fr)]">',
        '<div className="grid gap-3 2xl:grid-cols-[minmax(0,1.32fr)_minmax(350px,.68fr)]">',
    ),
    (
        '<section className="overflow-hidden rounded-[26px] border border-zinc-200/70 bg-white shadow-[0_18px_55px_rgba(15,23,42,0.055)] ring-1 ring-white/80 dark:border-zinc-800 dark:bg-zinc-950 dark:ring-white/[0.025]">',
        '<section className="overflow-hidden rounded-[22px] border border-zinc-200/70 bg-white shadow-[0_12px_34px_rgba(15,23,42,0.045)] ring-1 ring-white/70 dark:border-zinc-800 dark:bg-zinc-950 dark:ring-white/[0.025]">',
    ),
    (
        'className="flex flex-col gap-3 border-b border-zinc-100 bg-gradient-to-r from-white via-white to-amber-50/35 px-4 py-4 dark:border-zinc-800 dark:from-zinc-950 dark:via-zinc-950 dark:to-amber-500/[0.035] lg:flex-row lg:items-center lg:justify-between"',
        'className="flex flex-col gap-2 border-b border-zinc-100 bg-zinc-50/45 px-4 py-3 dark:border-zinc-800 dark:bg-white/[0.02] lg:flex-row lg:items-center lg:justify-between"',
    ),
    (
        '"group grid w-full gap-3 border-b border-zinc-100 px-4 py-3.5 text-start transition-all last:border-b-0 hover:bg-zinc-50/80 dark:border-zinc-800 dark:hover:bg-white/[0.035] lg:grid-cols-[minmax(220px,1.45fr)_minmax(100px,.8fr)_92px_120px_72px_104px] lg:items-center"',
        '"group grid w-full gap-3 border-b border-zinc-100 px-4 py-3 text-start transition-colors last:border-b-0 hover:bg-zinc-50/80 dark:border-zinc-800 dark:hover:bg-white/[0.035] lg:grid-cols-[minmax(220px,1.45fr)_minmax(100px,.8fr)_92px_120px_72px_104px] lg:items-center"',
    ),
    (
        '"grid h-11 w-11 shrink-0 place-items-center rounded-[15px] bg-gradient-to-br from-zinc-950 to-zinc-700 text-[11px] font-black tracking-[0.08em] text-white shadow-md dark:from-white dark:to-zinc-300 dark:text-zinc-950"',
        '"grid h-10 w-10 shrink-0 place-items-center rounded-[13px] bg-zinc-950 text-[10px] font-black tracking-[0.08em] text-white shadow-sm dark:bg-white dark:text-zinc-950"',
    ),
    (
        '<aside className="self-start overflow-hidden rounded-[26px] border border-zinc-200/70 bg-white shadow-[0_18px_55px_rgba(15,23,42,0.07)] ring-1 ring-white/80 dark:border-zinc-800 dark:bg-zinc-950 dark:ring-white/[0.025] 2xl:sticky 2xl:top-4">',
        '<aside className="self-start overflow-hidden rounded-[22px] border border-zinc-200/70 bg-white shadow-[0_12px_34px_rgba(15,23,42,0.055)] ring-1 ring-white/70 dark:border-zinc-800 dark:bg-zinc-950 dark:ring-white/[0.025] 2xl:sticky 2xl:top-4">',
    ),
    (
        'className="relative overflow-hidden bg-[radial-gradient(circle_at_85%_15%,rgba(245,158,11,0.18),transparent_30%),linear-gradient(135deg,#07111f_0%,#101827_52%,#07111f_100%)] p-5 text-white"',
        'className="relative overflow-hidden bg-[linear-gradient(135deg,#111827_0%,#0f172a_100%)] p-4 text-white"',
    ),
    (
        'className="grid h-20 w-20 shrink-0 place-items-center rounded-[22px] border border-white/10 bg-white/[0.06] text-xl font-black tracking-[0.09em] shadow-2xl backdrop-blur-xl"',
        'className="grid h-16 w-16 shrink-0 place-items-center rounded-[18px] border border-white/10 bg-white/[0.07] text-base font-black tracking-[0.08em] shadow-lg backdrop-blur-xl"',
    ),
    (
        'className="mt-3 line-clamp-2 text-2xl font-black leading-tight tracking-[-0.025em]"',
        'className="mt-2.5 line-clamp-2 text-xl font-black leading-tight tracking-[-0.02em]"',
    ),
]

def run(args, cwd, check=True):
    result = subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check and result.returncode != 0:
        raise RuntimeError(
            f"Command failed ({result.returncode}): {' '.join(args)}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    return result

def replace_once(path, old, new):
    source = path.read_text()
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"Expected exactly one anchor in {path}, found {count}: {old[:160]!r}")
    path.write_text(source.replace(old, new, 1))

def main():
    repo = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
    output = Path(sys.argv[2] if len(sys.argv) > 2 else "/var/tmp/TOS_UX_UI_PHASE03_PROJECTS.patch").resolve()

    branch = run(["git", "branch", "--show-current"], repo).stdout.strip()
    head = run(["git", "rev-parse", "HEAD"], repo).stdout.strip()
    if branch != "main":
        raise RuntimeError(f"Expected branch main, found {branch}")
    if head != TARGET_BASE_HEAD:
        raise RuntimeError(f"Expected HEAD {TARGET_BASE_HEAD}, found {head}")

    actual_blob = run(["git", "hash-object", "--", TARGET_FILE], repo).stdout.strip()
    if actual_blob != EXPECTED_BLOB:
        raise RuntimeError(f"Unexpected ProjectsPage blob: expected {EXPECTED_BLOB}, found {actual_blob}")

    temp_root = Path(tempfile.mkdtemp(prefix="tos-ui03-projects-"))
    worktree = temp_root / "worktree"
    try:
        run(["git", "worktree", "add", "--detach", str(worktree), TARGET_BASE_HEAD], repo)
        target = worktree / TARGET_FILE
        if not target.is_file():
            raise RuntimeError(f"Missing target file: {TARGET_FILE}")

        for old, new in REPLACEMENTS:
            replace_once(target, old, new)

        changed = run(["git", "diff", "--name-only"], worktree).stdout.strip().splitlines()
        if changed != [TARGET_FILE]:
            raise RuntimeError(f"Unexpected patch scope: {changed}")

        diff_check = run(["git", "diff", "--check"], worktree, check=False)
        if diff_check.returncode != 0:
            raise RuntimeError(f"git diff --check failed:\n{diff_check.stdout}\n{diff_check.stderr}")

        patch = run(["git", "diff", "--binary", "--", TARGET_FILE], worktree).stdout
        if not patch.strip():
            raise RuntimeError("Generated patch is empty")

        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(patch)

        apply_check = subprocess.run(
            ["git", "apply", "--check", str(output)],
            cwd=repo,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if apply_check.returncode != 0:
            raise RuntimeError(f"git apply --check failed against production checkout:\n{apply_check.stderr}")

        digest = hashlib.sha256(output.read_bytes()).hexdigest()
        print(f"PATCH={output}")
        print(f"SHA256={digest}")
        print(f"TARGET_BASE_HEAD={TARGET_BASE_HEAD}")
        print(f"TARGET_FILE={TARGET_FILE}")
        print(f"EXPECTED_BLOB={EXPECTED_BLOB}")
        print("SOURCE_SCOPE=ONE_FILE")
        print("BUSINESS_LOGIC_CHANGED=NO")
        print("ROUTES_CHANGED=NO")
        print("BACKEND_INCLUDED=NO")
    finally:
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(worktree)],
            cwd=repo,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        shutil.rmtree(temp_root, ignore_errors=True)

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
