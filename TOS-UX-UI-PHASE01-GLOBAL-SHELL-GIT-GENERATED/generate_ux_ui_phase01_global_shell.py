#!/usr/bin/env python3
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TARGET_BASE_HEAD = "32c6931336d8f0cf10b80cd772d1b53ed391c6b8"
EXPECTED_BLOBS = {
    "frontend/src/App.jsx": "6e20d97091d117980344d459f63c149301a4e119",
    "frontend/src/components/layout/Sidebar.jsx": "ddd6fb773dc7da34cde0d7e803e149097ab827c2",
    "frontend/src/components/layout/Topbar.jsx": "778da33825df78642f551356ac135fbbefd77839",
}
EXPECTED_PATHS = sorted(EXPECTED_BLOBS)

def run(args, cwd, check=True):
    result = subprocess.run(
        args, cwd=cwd, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    if check and result.returncode != 0:
        raise RuntimeError(
            f"Command failed ({result.returncode}): {' '.join(args)}\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    return result

def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one anchor, found {count}")
    return text.replace(old, new, 1)

def replace_many(text, old, new, label, minimum=1):
    count = text.count(old)
    if count < minimum:
        raise RuntimeError(f"{label}: expected at least {minimum} anchors, found {count}")
    return text.replace(old, new)

def patch_app(path):
    text = path.read_text()
    loading_component = r'''
function SystemPageLoading({ label = "Loading..." }) {
  return (
    <div className="mx-auto w-full max-w-[1560px] p-4 sm:p-6 lg:p-8" role="status" aria-live="polite">
      <div className="mb-6 flex items-center justify-between gap-4">
        <div className="min-w-0 flex-1 space-y-2">
          <div className="h-6 w-44 max-w-[55%] animate-pulse rounded-lg bg-zinc-200/80 dark:bg-zinc-800" />
          <div className="h-3 w-72 max-w-[75%] animate-pulse rounded-full bg-zinc-100 dark:bg-zinc-900" />
        </div>
        <div className="h-10 w-28 animate-pulse rounded-xl border border-zinc-200/70 bg-white dark:border-white/10 dark:bg-zinc-900" />
      </div>
      <div className="grid gap-4 md:grid-cols-3">
        {[0, 1, 2].map((item) => (
          <div key={item} className="h-28 animate-pulse rounded-2xl border border-zinc-200/70 bg-white/80 shadow-sm dark:border-white/10 dark:bg-zinc-900/70" />
        ))}
      </div>
      <div className="mt-4 h-72 animate-pulse rounded-2xl border border-zinc-200/70 bg-white/80 shadow-sm dark:border-white/10 dark:bg-zinc-900/70" />
      <span className="sr-only">{label}</span>
    </div>
  );
}

'''
    text = replace_once(
        text,
        'function MainApp({ user, initialActivePage = null }) {',
        loading_component + 'function MainApp({ user, initialActivePage = null }) {',
        "App loading component insertion",
    )
    text = replace_once(
        text,
        'className="tos-premium-system-v14 h-screen overflow-hidden bg-app font-sans text-app"',
        'className="tos-premium-system-v14 h-screen overflow-hidden bg-app-soft p-2 font-sans text-app sm:p-3 lg:p-4"',
        "App root frame",
    )
    text = replace_once(
        text,
        'className="tos-premium-app-frame flex h-screen w-full max-w-none gap-0 overflow-hidden"',
        'className="tos-premium-app-frame flex h-full w-full max-w-none gap-2 overflow-hidden lg:gap-3"',
        "App shared frame",
    )
    text = replace_once(
        text,
        'className="tos-premium-main-shell min-w-0 flex-1 overflow-hidden border-0 border-app bg-app-card shadow-none lg:border-s"',
        'className="tos-premium-main-shell min-w-0 flex-1 overflow-hidden rounded-[26px] border border-zinc-200/70 bg-app-card shadow-[0_20px_60px_rgba(15,23,42,0.08)] ring-1 ring-white/80 dark:border-white/10 dark:ring-white/5"',
        "App main shell",
    )
    text = replace_once(
        text,
        'className="tos-premium-page-viewport h-[calc(100%-78px)] overflow-y-auto bg-app-soft"',
        'className="tos-premium-page-viewport h-[calc(100%-72px)] overflow-y-auto bg-app-soft"',
        "App viewport height",
    )
    text = replace_once(
        text,
        '{loading && PROJECT_LOADING_BLOCKED_PAGES.has(active) && <div className="p-6 text-zinc-500 dark:text-zinc-400">{tr.loading}</div>}',
        '{loading && PROJECT_LOADING_BLOCKED_PAGES.has(active) && <SystemPageLoading label={tr.loading} />}',
        "App global loading fallback",
    )
    text = replace_many(
        text,
        '<div className="p-6 text-sm font-bold text-muted">{tr.loading ?? "Loading..."}</div>',
        '<SystemPageLoading label={tr.loading ?? "Loading..."} />',
        "App suspense fallbacks",
        minimum=3,
    )
    path.write_text(text)

def patch_sidebar(path):
    text = path.read_text()
    swaps = [
        ('const SIDEBAR_COLLAPSED_WIDTH = 96;', 'const SIDEBAR_COLLAPSED_WIDTH = 88;', "collapsed width"),
        ('const SIDEBAR_DEFAULT_WIDTH = 256;', 'const SIDEBAR_DEFAULT_WIDTH = 248;', "default width"),
        (
            '"tos-premium-sidebar relative h-full min-w-0 max-w-full shrink-0 overflow-hidden rounded-[28px] border border-slate-200/80 bg-white/90 text-slate-900 shadow-[0_20px_60px_rgba(15,23,42,0.08)] ring-1 ring-slate-100 backdrop-blur-xl",',
            '"tos-premium-sidebar relative h-full min-w-0 max-w-full shrink-0 overflow-hidden rounded-[26px] border border-slate-200/70 bg-white/95 text-slate-900 shadow-[0_18px_50px_rgba(15,23,42,0.07)] ring-1 ring-white/90 backdrop-blur-xl dark:border-white/10 dark:bg-zinc-950/90 dark:text-zinc-100 dark:ring-white/5",',
            "sidebar surface",
        ),
        (
            'mobile ? "flex flex-col p-4" : "hidden lg:flex lg:flex-col",\n        collapsed && !mobile ? "p-3" : "p-4",',
            'mobile ? "flex flex-col p-3" : "hidden lg:flex lg:flex-col",\n        collapsed && !mobile ? "p-2.5" : "p-3",',
            "sidebar padding",
        ),
        (
            'collapsed && !mobile ? "pb-4" : "pb-5"',
            'collapsed && !mobile ? "pb-3" : "pb-4"',
            "sidebar header spacing",
        ),
        (
            '<LogoMark className={cn(collapsed && !mobile ? "h-14 w-14 rounded-3xl" : "h-24 w-24 rounded-[28px]")} />',
            '<LogoMark className={cn(collapsed && !mobile ? "h-11 w-11 rounded-2xl" : "h-16 w-16 rounded-[22px]")} />',
            "sidebar logo size",
        ),
        (
            '<p className="mt-3 max-w-full truncate text-sm font-black text-slate-950">{productName}</p>',
            '<p className="mt-2 max-w-full truncate text-sm font-black tracking-tight text-slate-950 dark:text-white">{productName}</p>',
            "sidebar product name",
        ),
        (
            '<p className="mt-1 max-w-full truncate text-xs font-bold text-slate-500">{productSubtitle}</p>',
            '<p className="mt-0.5 max-w-full truncate text-[11px] font-bold text-slate-500 dark:text-zinc-400">{productSubtitle}</p>',
            "sidebar product subtitle",
        ),
        (
            'className="tos-sidebar-scroll-region mt-5 min-h-0 min-w-0 max-w-full flex-1 overflow-y-auto overflow-x-hidden overscroll-y-contain [scrollbar-gutter:stable] [touch-action:pan-y]"',
            'className="tos-sidebar-scroll-region mt-3 min-h-0 min-w-0 max-w-full flex-1 overflow-y-auto overflow-x-hidden overscroll-y-contain pe-0.5 [scrollbar-gutter:stable] [touch-action:pan-y]"',
            "sidebar nav spacing",
        ),
        (
            '"group relative flex w-full items-center rounded-2xl text-sm font-black transition-all focus:outline-none focus:ring-2 focus:ring-amber-300/60",',
            '"group relative flex w-full items-center rounded-xl text-sm font-extrabold transition-all focus:outline-none focus:ring-2 focus:ring-amber-300/60",',
            "single nav shape",
        ),
        (
            'collapsedIconOnly ? "h-12 justify-center px-0" : "justify-start gap-3 px-3 py-3",',
            'collapsedIconOnly ? "h-11 justify-center px-0" : "justify-start gap-3 px-3 py-2.5",',
            "single nav density",
        ),
        (
            '"bg-white text-slate-950 shadow-sm ring-1 ring-amber-200/80 before:absolute before:inset-y-2 before:start-0 before:w-1 before:rounded-full before:bg-amber-500"',
            '"bg-amber-50/80 text-slate-950 ring-1 ring-amber-200/70 before:absolute before:inset-y-2 before:start-0 before:w-1 before:rounded-full before:bg-amber-500 dark:bg-amber-500/10 dark:text-white"',
            "primary nav active states",
        ),
        (
            '"relative w-full min-w-0 max-w-full rounded-[24px] border bg-white transition-all",',
            '"relative w-full min-w-0 max-w-full rounded-[18px] border bg-slate-50/60 transition-all dark:bg-white/[0.03]",',
            "group card shape",
        ),
        (
            '? "border-amber-200/90 shadow-[0_18px_36px_rgba(15,23,42,0.08)] before:absolute before:inset-y-4 before:start-0 before:w-1 before:rounded-full before:bg-amber-500"',
            '? "border-amber-200/80 bg-white shadow-sm before:absolute before:inset-y-3 before:start-0 before:w-1 before:rounded-full before:bg-amber-500 dark:bg-white/[0.05]"',
            "group open state",
        ),
        (
            ': "border-slate-200/80 shadow-sm shadow-slate-200/40"',
            ': "border-slate-200/70 shadow-none dark:border-white/10"',
            "group closed state",
        ),
        (
            '"sticky top-0 z-20 flex w-full min-w-0 items-center gap-3 bg-white px-3 py-3 text-start text-sm font-black transition focus:outline-none focus:ring-2 focus:ring-amber-300/60",',
            '"sticky top-0 z-20 flex w-full min-w-0 items-center gap-3 bg-transparent px-3 py-2.5 text-start text-sm font-extrabold transition focus:outline-none focus:ring-2 focus:ring-amber-300/60",',
            "group header density",
        ),
        (
            'isOpen ? "rounded-t-[23px]" : "rounded-[23px]",',
            'isOpen ? "rounded-t-[17px]" : "rounded-[17px]",',
            "group header radius",
        ),
        (
            'className="relative z-10 overflow-hidden rounded-b-[23px] border-t border-slate-100 bg-white/95 px-2 py-2"',
            'className="relative z-10 overflow-hidden rounded-b-[17px] border-t border-slate-100 bg-white/90 px-1.5 py-1.5 dark:border-white/10 dark:bg-zinc-950/40"',
            "subnav container",
        ),
        (
            '"group/sub relative flex w-full min-w-0 scroll-mt-14 items-center gap-2 rounded-2xl px-3 py-2.5 text-start text-xs font-black transition focus:outline-none focus:ring-2 focus:ring-amber-300/50",',
            '"group/sub relative flex w-full min-w-0 scroll-mt-14 items-center gap-2 rounded-xl px-3 py-2.5 text-start text-xs font-extrabold transition focus:outline-none focus:ring-2 focus:ring-amber-300/50",',
            "subnav shape",
        ),
        (
            '? "bg-white text-slate-950 shadow-sm ring-1 ring-amber-200/70 before:absolute before:inset-y-2 before:start-0 before:w-1 before:rounded-full before:bg-amber-500"',
            '? "bg-amber-50/80 text-slate-950 ring-1 ring-amber-200/60 before:absolute before:inset-y-2 before:start-0 before:w-1 before:rounded-full before:bg-amber-500 dark:bg-amber-500/10 dark:text-white"',
            "subnav active",
        ),
        (
            '"group relative grid h-12 w-full place-items-center rounded-2xl text-slate-500 transition-all focus:outline-none focus:ring-2 focus:ring-amber-300/60",',
            '"group relative grid h-11 w-full place-items-center rounded-xl text-slate-500 transition-all focus:outline-none focus:ring-2 focus:ring-amber-300/60",',
            "collapsed root density",
        ),
    ]
    for old, new, label in swaps:
        if label == "primary nav active states":
            text = replace_many(text, old, new, f"Sidebar {label}", minimum=2)
        else:
            text = replace_once(text, old, new, f"Sidebar {label}")
    path.write_text(text)

def patch_topbar(path):
    text = path.read_text()
    swaps = [
        (
            'import { Bell, Check, Menu, Moon, Plus, Sparkles, Sun, UserRound } from "lucide-react";',
            'import { Bell, Check, Menu, Moon, Plus, Sun, UserRound } from "lucide-react";',
            "Topbar icon import",
        ),
        (
            '<header className="tos-premium-topbar sticky top-0 z-30 flex min-h-[78px] items-center justify-between gap-4 border-b border-white/70 bg-white/75 px-4 backdrop-blur-2xl dark:border-white/10 dark:bg-zinc-950/65 sm:px-6">',
            '<header className="tos-premium-topbar sticky top-0 z-30 flex min-h-[72px] items-center justify-between gap-4 border-b border-zinc-200/70 bg-white/90 px-4 backdrop-blur-xl dark:border-white/10 dark:bg-zinc-950/85 sm:px-5 lg:px-6">',
            "Topbar shell",
        ),
        (
            '<h1 className="flex items-center gap-2 truncate text-xl font-black tracking-tight text-zinc-950 dark:text-white sm:text-2xl">\n            {title}\n            <Sparkles className="hidden fill-amber-400 text-amber-400 sm:block" size={18} />\n          </h1>',
            '<h1 className="truncate text-xl font-black tracking-[-0.02em] text-zinc-950 dark:text-white sm:text-2xl">\n            {title}\n          </h1>',
            "Topbar title",
        ),
        (
            '<div className="flex min-w-0 items-center gap-2">',
            '<div className="flex min-w-0 items-center gap-1.5 rounded-2xl border border-zinc-200/70 bg-zinc-50/80 p-1.5 shadow-sm dark:border-white/10 dark:bg-white/[0.04]">',
            "Topbar action cluster",
        ),
        (
            'className="tos-premium-user-chip hidden min-w-0 items-center gap-3 rounded-2xl border border-zinc-200 bg-white/80 px-3 py-2 text-right shadow-sm transition hover:-translate-y-0.5 hover:bg-amber-50 dark:border-white/10 dark:bg-zinc-900/70 dark:hover:bg-zinc-800 lg:flex"',
            'className="tos-premium-user-chip hidden min-w-0 items-center gap-3 rounded-xl border border-transparent bg-white px-3 py-1.5 text-right transition hover:border-amber-200 hover:bg-amber-50 dark:bg-zinc-900/70 dark:hover:bg-zinc-800 lg:flex"',
            "Topbar user chip",
        ),
        (
            'className="relative grid h-11 w-11 shrink-0 place-items-center rounded-2xl border border-zinc-200 bg-white text-zinc-600 shadow-sm transition hover:-translate-y-0.5 hover:bg-amber-50 dark:border-white/10 dark:bg-zinc-900 dark:text-zinc-300 dark:hover:bg-zinc-800"',
            'className="relative grid h-10 w-10 shrink-0 place-items-center rounded-xl border border-transparent bg-white text-zinc-600 transition hover:border-amber-200 hover:bg-amber-50 dark:bg-zinc-900 dark:text-zinc-300 dark:hover:bg-zinc-800"',
            "Topbar notifications button",
        ),
        (
            'className={`absolute left-0 top-12 z-50 w-[320px] overflow-hidden rounded-3xl border border-zinc-100 bg-white shadow-2xl dark:border-white/10 dark:bg-zinc-900 ${isEnglish ? "text-left" : "text-right"}`}',
            'className={`absolute left-0 top-11 z-50 w-[320px] overflow-hidden rounded-2xl border border-zinc-200/80 bg-white shadow-2xl dark:border-white/10 dark:bg-zinc-900 ${isEnglish ? "text-left" : "text-right"}`}',
            "Topbar notification popover",
        ),
        (
            'className="grid h-11 w-11 shrink-0 place-items-center rounded-2xl border border-zinc-200 bg-white text-zinc-600 shadow-sm transition hover:-translate-y-0.5 hover:bg-amber-50 dark:border-white/10 dark:bg-zinc-900 dark:text-amber-300 dark:hover:bg-zinc-800"',
            'className="grid h-10 w-10 shrink-0 place-items-center rounded-xl border border-transparent bg-white text-zinc-600 transition hover:border-amber-200 hover:bg-amber-50 dark:bg-zinc-900 dark:text-amber-300 dark:hover:bg-zinc-800"',
            "Topbar theme button",
        ),
        (
            'className="grid h-11 w-11 shrink-0 place-items-center rounded-2xl border border-zinc-200 bg-white text-xs font-black text-zinc-600 shadow-sm transition hover:-translate-y-0.5 hover:bg-amber-50 dark:border-white/10 dark:bg-zinc-900 dark:text-amber-300 dark:hover:bg-zinc-800"',
            'className="grid h-10 w-10 shrink-0 place-items-center rounded-xl border border-transparent bg-white text-xs font-black text-zinc-600 transition hover:border-amber-200 hover:bg-amber-50 dark:bg-zinc-900 dark:text-amber-300 dark:hover:bg-zinc-800"',
            "Topbar language button",
        ),
        (
            'className="grid h-11 w-11 place-items-center rounded-2xl border border-zinc-200 bg-white text-zinc-500 shadow-sm dark:border-white/10 dark:bg-zinc-900 dark:text-zinc-300 lg:hidden"',
            'className="grid h-10 w-10 place-items-center rounded-xl border border-transparent bg-white text-zinc-500 dark:bg-zinc-900 dark:text-zinc-300 lg:hidden"',
            "Topbar mobile profile",
        ),
    ]
    for old, new, label in swaps:
        text = replace_once(text, old, new, label)
    path.write_text(text)

def main():
    repo = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
    output = Path(sys.argv[2] if len(sys.argv) > 2 else "/var/tmp/TOS_UX_UI_PHASE01_GLOBAL_SHELL.patch").resolve()

    branch = run(["git", "branch", "--show-current"], repo).stdout.strip()
    head = run(["git", "rev-parse", "HEAD"], repo).stdout.strip()
    if branch != "main":
        raise RuntimeError(f"Expected branch main, found {branch}")
    if head != TARGET_BASE_HEAD:
        raise RuntimeError(f"Expected HEAD {TARGET_BASE_HEAD}, found {head}")

    for rel, expected_blob in EXPECTED_BLOBS.items():
        target = repo / rel
        if not target.is_file():
            raise RuntimeError(f"Missing target: {rel}")
        actual = run(["git", "hash-object", "--", rel], repo).stdout.strip()
        if actual != expected_blob:
            raise RuntimeError(f"Target drift for {rel}: expected {expected_blob}, found {actual}")

    temp_root = Path(tempfile.mkdtemp(prefix="tos-ux-ui-phase01-global-shell-"))
    worktree = temp_root / "worktree"
    try:
        run(["git", "worktree", "add", "--detach", str(worktree), TARGET_BASE_HEAD], repo)
        patch_app(worktree / "frontend/src/App.jsx")
        patch_sidebar(worktree / "frontend/src/components/layout/Sidebar.jsx")
        patch_topbar(worktree / "frontend/src/components/layout/Topbar.jsx")

        changed = sorted(
            run(["git", "diff", "--name-only", "--", *EXPECTED_PATHS], worktree)
            .stdout.strip().splitlines()
        )
        if changed != EXPECTED_PATHS:
            raise RuntimeError(f"Unexpected patch scope: {changed}; expected {EXPECTED_PATHS}")

        patch = run(["git", "diff", "--binary", "--", *EXPECTED_PATHS], worktree).stdout
        if not patch.strip():
            raise RuntimeError("Generated patch is empty")

        forbidden = ["backend/", "server/", "client/", "drizzle/", "prisma/"]
        for prefix in forbidden:
            if f"diff --git a/{prefix}" in patch:
                raise RuntimeError(f"Forbidden path entered patch: {prefix}")

        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(patch)

        apply_check = subprocess.run(
            ["git", "apply", "--check", str(output)],
            cwd=repo, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        if apply_check.returncode != 0:
            raise RuntimeError(f"git apply --check failed:\n{apply_check.stderr}")

        digest = hashlib.sha256(output.read_bytes()).hexdigest()
        print(f"PATCH={output}")
        print(f"SHA256={digest}")
        print(f"TARGET_BASE_HEAD={TARGET_BASE_HEAD}")
        print("PHASE=UI-01 GLOBAL SHELL")
        print("FILES=")
        for rel in EXPECTED_PATHS:
            print(rel)
    finally:
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(worktree)],
            cwd=repo, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        shutil.rmtree(temp_root, ignore_errors=True)

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
