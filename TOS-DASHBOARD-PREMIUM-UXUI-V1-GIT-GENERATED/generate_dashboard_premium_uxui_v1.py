#!/usr/bin/env python3
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

EXPECTED_HEAD = "0ad2cc04392dae067dc4c84d9cc206148870dd2d"
MAIN_TARGET = "frontend/src/main.jsx"
CSS_TARGET = "frontend/src/dashboard-premium.css"
EXPECTED_MAIN_BLOB = "0035c796b14f106b276d53421b8ba4bf1ae99514"
IMPORT_ANCHOR = 'import "./index.css";\n'
IMPORT_LINE = 'import "./dashboard-premium.css";\n'

CSS = r'''/* TOS_EXECUTIVE_DASHBOARD_PREMIUM_V1_START
   Scoped visual polish for frontend/src/pages/Dashboard.jsx.
   Matches the premium GitHub Sync design DNA without changing dashboard logic. */

:root {
  --tos-dash-gold: #c8922f;
  --tos-dash-gold-soft: #e7bf6b;
  --tos-dash-ink: #1d170d;
  --tos-dash-muted: #786b56;
  --tos-dash-line: rgba(186, 141, 55, 0.22);
  --tos-dash-surface: #fffdf8;
  --tos-dash-surface-2: #faf4e8;
}

/* The dashboard is the only direct page child using max-w-[1560px]. */
.tos-premium-page-viewport > .mx-auto.w-full.max-w-\[1560px\] {
  position: relative;
  isolation: isolate;
}

.tos-premium-page-viewport > .mx-auto.w-full.max-w-\[1560px\]::before {
  content: "";
  position: absolute;
  inset: 0;
  z-index: -1;
  pointer-events: none;
  background:
    radial-gradient(circle at 8% 0%, rgba(202, 146, 47, 0.085), transparent 23%),
    radial-gradient(circle at 92% 4%, rgba(35, 94, 133, 0.045), transparent 20%);
}

/* Executive hero */
.tos-premium-page-viewport > .mx-auto.w-full.max-w-\[1560px\] > section:first-child {
  border-color: rgba(200, 146, 47, 0.28) !important;
  background:
    radial-gradient(circle at 84% -24%, rgba(231, 191, 107, 0.28), transparent 35%),
    linear-gradient(135deg, #fffefb 0%, #fbf5e8 58%, #fffdfa 100%) !important;
  box-shadow:
    0 24px 70px rgba(91, 64, 20, 0.105),
    inset 0 1px 0 rgba(255, 255, 255, 0.9) !important;
  border-radius: 30px !important;
}

.tos-premium-page-viewport > .mx-auto.w-full.max-w-\[1560px\] > section:first-child::after {
  content: "";
  position: absolute;
  width: 260px;
  height: 260px;
  inset-inline-end: -72px;
  top: -150px;
  border: 1px solid rgba(200, 146, 47, 0.13);
  border-radius: 999px;
  pointer-events: none;
}

.tos-premium-page-viewport > .mx-auto.w-full.max-w-\[1560px\] > section:first-child > div:last-child > div:last-child {
  border-color: rgba(200, 146, 47, 0.22) !important;
  background: rgba(255, 255, 255, 0.72) !important;
  box-shadow: 0 12px 34px rgba(91, 64, 20, 0.08), inset 0 1px 0 rgba(255,255,255,.72) !important;
  backdrop-filter: blur(10px);
}

/* Date range strip */
.tos-premium-page-viewport > .mx-auto.w-full.max-w-\[1560px\] > .relative.z-20.rounded-2xl {
  border-color: rgba(200, 146, 47, 0.19) !important;
  background: linear-gradient(180deg, rgba(255,255,255,.96), rgba(252,248,239,.94)) !important;
  box-shadow: 0 12px 36px rgba(91, 64, 20, 0.07), inset 0 1px 0 rgba(255,255,255,.8) !important;
  border-radius: 22px !important;
}

/* KPI cards */
.tos-premium-page-viewport > .mx-auto.w-full.max-w-\[1560px\] > .grid > div.rounded-2xl {
  border-color: rgba(200, 146, 47, 0.19) !important;
  background: linear-gradient(180deg, rgba(255,255,255,.99), rgba(253,249,241,.95)) !important;
  box-shadow: 0 15px 42px rgba(91, 64, 20, 0.075), inset 0 1px 0 rgba(255,255,255,.85) !important;
  transition: transform .2s ease, box-shadow .2s ease, border-color .2s ease;
}

.tos-premium-page-viewport > .mx-auto.w-full.max-w-\[1560px\] > .grid > div.rounded-2xl:hover {
  transform: translateY(-2px);
  border-color: rgba(200, 146, 47, 0.34) !important;
  box-shadow: 0 20px 54px rgba(91, 64, 20, 0.11), inset 0 1px 0 rgba(255,255,255,.9) !important;
}

/* Main dashboard cards */
.tos-premium-page-viewport > .mx-auto.w-full.max-w-\[1560px\] [class*="rounded-[22px]"] {
  border-color: rgba(200, 146, 47, 0.18) !important;
  background:
    radial-gradient(circle at 94% -28%, rgba(231,191,107,.10), transparent 30%),
    linear-gradient(180deg, rgba(255,255,255,.99), rgba(252,248,240,.96)) !important;
  box-shadow: 0 18px 52px rgba(91, 64, 20, 0.075), inset 0 1px 0 rgba(255,255,255,.82) !important;
  border-radius: 26px !important;
}

/* Project and activity rows */
.tos-premium-page-viewport > .mx-auto.w-full.max-w-\[1560px\] [class*="rounded-2xl"][class*="border-zinc-200/60"],
.tos-premium-page-viewport > .mx-auto.w-full.max-w-\[1560px\] [class*="rounded-3xl"][class*="border-zinc-100"] {
  border-color: rgba(200, 146, 47, 0.13) !important;
  background: linear-gradient(180deg, rgba(255,255,255,.88), rgba(250,246,237,.78)) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.65) !important;
}

.tos-premium-page-viewport > .mx-auto.w-full.max-w-\[1560px\] [class*="rounded-2xl"][class*="border-zinc-200/60"]:hover,
.tos-premium-page-viewport > .mx-auto.w-full.max-w-\[1560px\] [class*="rounded-3xl"][class*="border-zinc-100"]:hover {
  border-color: rgba(200, 146, 47, 0.28) !important;
  background: #fffefb !important;
}

/* Quick actions become workflow-like premium controls. */
.tos-premium-page-viewport > .mx-auto.w-full.max-w-\[1560px\] button.group.rounded-2xl {
  border-color: rgba(200, 146, 47, 0.16) !important;
  background: linear-gradient(90deg, rgba(255,255,255,.96), rgba(251,246,235,.90)) !important;
  box-shadow: 0 8px 24px rgba(91,64,20,.055) !important;
}

.tos-premium-page-viewport > .mx-auto.w-full.max-w-\[1560px\] button.group.rounded-2xl:hover {
  border-color: rgba(200, 146, 47, 0.36) !important;
  box-shadow: 0 13px 34px rgba(91,64,20,.10) !important;
}

/* Progress visual hierarchy */
.tos-premium-page-viewport > .mx-auto.w-full.max-w-\[1560px\] [style*="conic-gradient"] {
  box-shadow: 0 18px 46px rgba(120, 83, 22, .12), 0 0 0 1px rgba(200,146,47,.14) !important;
}

.tos-premium-page-viewport > .mx-auto.w-full.max-w-\[1560px\] [style*="conic-gradient"] > div {
  box-shadow: inset 0 1px 0 rgba(255,255,255,.8), inset 0 0 28px rgba(126,95,42,.035) !important;
}

/* Dropdown */
.tos-premium-page-viewport > .mx-auto.w-full.max-w-\[1560px\] .absolute.end-0.top-full {
  border-color: rgba(200,146,47,.24) !important;
  background: rgba(255,253,248,.98) !important;
  box-shadow: 0 24px 70px rgba(70,49,17,.18) !important;
  backdrop-filter: blur(16px);
}

/* ---------- DARK MODE: Midnight Navy + restrained gold ---------- */
html.dark .tos-premium-page-viewport:has(> .mx-auto.w-full.max-w-\[1560px\]) {
  background:
    radial-gradient(circle at 2% 0%, rgba(198,143,35,.055), transparent 24%),
    linear-gradient(180deg,#050D16 0%,#06111B 52%,#050C14 100%) !important;
}

html.dark body:has(.tos-premium-page-viewport > .mx-auto.w-full.max-w-\[1560px\]) .tos-premium-sidebar {
  background:
    radial-gradient(circle at 22% 5%, rgba(210,158,48,.052), transparent 25%),
    linear-gradient(180deg,#050D16 0%,#07121D 48%,#050C14 100%) !important;
  border-color: rgba(102,136,165,.16) !important;
  box-shadow: 0 24px 64px rgba(0,0,0,.31), inset 0 1px 0 rgba(255,255,255,.024) !important;
}

html.dark .tos-premium-page-viewport > .mx-auto.w-full.max-w-\[1560px\]::before {
  background:
    radial-gradient(circle at 8% 0%, rgba(200,146,47,.065), transparent 23%),
    radial-gradient(circle at 92% 4%, rgba(48,112,160,.055), transparent 20%);
}

html.dark .tos-premium-page-viewport > .mx-auto.w-full.max-w-\[1560px\] > section:first-child {
  border-color: rgba(214,163,60,.24) !important;
  background:
    radial-gradient(circle at 84% -18%, rgba(196,143,38,.16), transparent 34%),
    radial-gradient(circle at 12% 0%, rgba(39,83,119,.11), transparent 28%),
    linear-gradient(135deg,#071522 0%,#091A28 56%,#07131F 100%) !important;
  box-shadow: 0 28px 84px rgba(0,0,0,.34), inset 0 1px 0 rgba(255,255,255,.026) !important;
}

html.dark .tos-premium-page-viewport > .mx-auto.w-full.max-w-\[1560px\] > section:first-child > div:last-child > div:last-child {
  border-color: rgba(110,145,174,.16) !important;
  background: linear-gradient(180deg,#0B1C2B 0%,#091824 100%) !important;
  box-shadow: 0 14px 38px rgba(0,0,0,.22), inset 0 1px 0 rgba(255,255,255,.024) !important;
}

html.dark .tos-premium-page-viewport > .mx-auto.w-full.max-w-\[1560px\] > .relative.z-20.rounded-2xl {
  border-color: rgba(101,136,165,.15) !important;
  background: linear-gradient(180deg,#081725 0%,#06131F 100%) !important;
  box-shadow: 0 15px 38px rgba(0,0,0,.20), inset 0 1px 0 rgba(255,255,255,.022) !important;
}

html.dark .tos-premium-page-viewport > .mx-auto.w-full.max-w-\[1560px\] > .grid > div.rounded-2xl {
  border-color: rgba(101,136,165,.15) !important;
  background:
    radial-gradient(circle at 88% -40%, rgba(36,81,119,.11), transparent 34%),
    linear-gradient(180deg,#091A29 0%,#071521 100%) !important;
  box-shadow: 0 16px 40px rgba(0,0,0,.20), inset 0 1px 0 rgba(255,255,255,.022) !important;
}

html.dark .tos-premium-page-viewport > .mx-auto.w-full.max-w-\[1560px\] > .grid > div.rounded-2xl:hover {
  border-color: rgba(203,155,58,.26) !important;
  box-shadow: 0 21px 52px rgba(0,0,0,.27), inset 0 1px 0 rgba(255,255,255,.026) !important;
}

html.dark .tos-premium-page-viewport > .mx-auto.w-full.max-w-\[1560px\] [class*="rounded-[22px]"] {
  border-color: rgba(101,136,165,.15) !important;
  background:
    radial-gradient(circle at 94% -32%, rgba(39,87,128,.10), transparent 31%),
    linear-gradient(180deg,#081827 0%,#071420 100%) !important;
  box-shadow: 0 17px 44px rgba(0,0,0,.22), inset 0 1px 0 rgba(255,255,255,.022) !important;
}

html.dark .tos-premium-page-viewport > .mx-auto.w-full.max-w-\[1560px\] [class*="rounded-2xl"][class*="border-zinc-200/60"],
html.dark .tos-premium-page-viewport > .mx-auto.w-full.max-w-\[1560px\] [class*="rounded-3xl"][class*="border-zinc-100"] {
  border-color: rgba(101,136,165,.11) !important;
  background: linear-gradient(90deg,rgba(10,27,42,.88),rgba(8,23,36,.88)) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.018) !important;
}

html.dark .tos-premium-page-viewport > .mx-auto.w-full.max-w-\[1560px\] [class*="rounded-2xl"][class*="border-zinc-200/60"]:hover,
html.dark .tos-premium-page-viewport > .mx-auto.w-full.max-w-\[1560px\] [class*="rounded-3xl"][class*="border-zinc-100"]:hover {
  border-color: rgba(199,151,55,.24) !important;
  background: linear-gradient(90deg,#0B1D2C,#091926) !important;
}

html.dark .tos-premium-page-viewport > .mx-auto.w-full.max-w-\[1560px\] button.group.rounded-2xl {
  border-color: rgba(105,140,169,.13) !important;
  background: linear-gradient(90deg,#0A1B2A 0%,#081724 100%) !important;
  box-shadow: 0 9px 26px rgba(0,0,0,.16), inset 0 1px 0 rgba(255,255,255,.018) !important;
}

html.dark .tos-premium-page-viewport > .mx-auto.w-full.max-w-\[1560px\] button.group.rounded-2xl:hover {
  border-color: rgba(205,156,59,.27) !important;
  background: linear-gradient(90deg,#0C2031 0%,#0A1A28 100%) !important;
  box-shadow: 0 14px 36px rgba(0,0,0,.23) !important;
}

/* Replace harsh white/gray text and surfaces only inside this dashboard. */
html.dark .tos-premium-page-viewport > .mx-auto.w-full.max-w-\[1560px\] [class*="text-zinc-950"],
html.dark .tos-premium-page-viewport > .mx-auto.w-full.max-w-\[1560px\] [class*="text-zinc-900"] {
  color: #EEF3F7 !important;
}

html.dark .tos-premium-page-viewport > .mx-auto.w-full.max-w-\[1560px\] [class*="text-zinc-800"] {
  color: #DCE5ED !important;
}

html.dark .tos-premium-page-viewport > .mx-auto.w-full.max-w-\[1560px\] [class*="text-zinc-500"] {
  color: #AEBCC8 !important;
}

html.dark .tos-premium-page-viewport > .mx-auto.w-full.max-w-\[1560px\] [class*="text-zinc-400"] {
  color: #91A3B2 !important;
}

html.dark .tos-premium-page-viewport > .mx-auto.w-full.max-w-\[1560px\] [class*="text-zinc-300"] {
  color: #C9D4DD !important;
}

html.dark .tos-premium-page-viewport > .mx-auto.w-full.max-w-\[1560px\] [class*="bg-white"] {
  border-color: rgba(101,136,165,.13);
}

html.dark .tos-premium-page-viewport > .mx-auto.w-full.max-w-\[1560px\] [style*="conic-gradient"] {
  background-color: #344B5F !important;
  background-blend-mode: multiply !important;
  box-shadow: 0 0 0 1px rgba(112,145,173,.13), 0 18px 42px rgba(0,0,0,.20) !important;
}

html.dark .tos-premium-page-viewport > .mx-auto.w-full.max-w-\[1560px\] [style*="conic-gradient"] > div {
  background: radial-gradient(circle at 38% 32%,#0C1E2E 0%,#081623 72%) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.025), inset 0 0 28px rgba(0,0,0,.20) !important;
}

html.dark .tos-premium-page-viewport > .mx-auto.w-full.max-w-\[1560px\] .h-3.overflow-hidden.rounded-full {
  background: #0A1A28 !important;
  box-shadow: inset 0 1px 3px rgba(0,0,0,.28) !important;
}

html.dark .tos-premium-page-viewport > .mx-auto.w-full.max-w-\[1560px\] .absolute.end-0.top-full {
  border-color: rgba(111,146,175,.17) !important;
  background: rgba(7,20,32,.98) !important;
  box-shadow: 0 24px 74px rgba(0,0,0,.42) !important;
}

/* Subtle dashboard scrollbar, consistent with GitHub Sync. */
html.dark .tos-premium-page-viewport:has(> .mx-auto.w-full.max-w-\[1560px\]) {
  scrollbar-color: rgba(181,133,41,.46) #06111B !important;
  scrollbar-width: thin !important;
}

html.dark .tos-premium-page-viewport:has(> .mx-auto.w-full.max-w-\[1560px\])::-webkit-scrollbar { width: 8px; }
html.dark .tos-premium-page-viewport:has(> .mx-auto.w-full.max-w-\[1560px\])::-webkit-scrollbar-track { background: #06111B; }
html.dark .tos-premium-page-viewport:has(> .mx-auto.w-full.max-w-\[1560px\])::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg,rgba(178,129,37,.42),rgba(134,96,29,.34));
  border: 2px solid #06111B;
  border-radius: 999px;
}

@media (max-width: 1023px) {
  .tos-premium-page-viewport > .mx-auto.w-full.max-w-\[1560px\] > section:first-child {
    border-radius: 24px !important;
  }
  .tos-premium-page-viewport > .mx-auto.w-full.max-w-\[1560px\] [class*="rounded-[22px]"] {
    border-radius: 22px !important;
  }
}

@media (prefers-reduced-motion: reduce) {
  .tos-premium-page-viewport > .mx-auto.w-full.max-w-\[1560px\] * {
    transition-duration: 0.01ms !important;
    animation-duration: 0.01ms !important;
  }
}

/* TOS_EXECUTIVE_DASHBOARD_PREMIUM_V1_END */
'''


def die(message, code=1):
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(code)


def run(args, cwd, check=True):
    proc = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)
    if check and proc.returncode:
        die(f"command failed rc={proc.returncode}: {' '.join(args)}", 90)
    return proc


def sha256(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if len(sys.argv) != 3:
        die("usage: generate_dashboard_premium_uxui_v1.py REPO_ROOT OUTPUT_PATCH", 2)

    root = Path(sys.argv[1]).resolve()
    output = Path(sys.argv[2]).resolve()
    main_target = root / MAIN_TARGET
    css_target = root / CSS_TARGET

    if not (root / ".git").is_dir():
        die(f"not a git repository: {root}", 3)
    if not main_target.is_file():
        die(f"target missing: {MAIN_TARGET}", 4)
    if css_target.exists():
        die(f"target already exists: {CSS_TARGET}; patch appears already applied or conflicts with local work", 5)

    head = run(["git", "rev-parse", "HEAD"], root).stdout.strip()
    print(f"HEAD={head}")
    if head != EXPECTED_HEAD:
        die(f"HEAD mismatch expected={EXPECTED_HEAD} actual={head}", 6)

    blob = run(["git", "hash-object", MAIN_TARGET], root).stdout.strip()
    print(f"MAIN_SOURCE_BLOB={blob}")
    if blob != EXPECTED_MAIN_BLOB:
        die(f"main.jsx blob mismatch expected={EXPECTED_MAIN_BLOB} actual={blob}", 7)

    if run(["git", "diff", "--cached", "--", MAIN_TARGET], root).stdout.strip():
        die("main.jsx has staged changes", 8)
    if run(["git", "diff", "--", MAIN_TARGET], root).stdout.strip():
        die("main.jsx has tracked local changes", 9)

    source = main_target.read_text(encoding="utf-8")
    if IMPORT_LINE in source:
        die("premium dashboard import already present", 10)
    if source.count(IMPORT_ANCHOR) != 1:
        die(f"expected one import anchor, found {source.count(IMPORT_ANCHOR)}", 11)
    patched_main = source.replace(IMPORT_ANCHOR, IMPORT_ANCHOR + IMPORT_LINE, 1)

    tmp = Path(tempfile.mkdtemp(prefix="tos-dashboard-premium-v1-"))
    try:
        run(["git", "init", "-q"], tmp)
        run(["git", "config", "user.email", "dashboard-patch@tos.local"], tmp)
        run(["git", "config", "user.name", "TOS Dashboard Premium Patch Generator"], tmp)

        tmp_main = tmp / MAIN_TARGET
        tmp_main.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(main_target, tmp_main)
        run(["git", "add", "--", MAIN_TARGET], tmp)
        run(["git", "commit", "-qm", "exact live baseline"], tmp)

        tmp_main.write_text(patched_main, encoding="utf-8", newline="\n")
        tmp_css = tmp / CSS_TARGET
        tmp_css.parent.mkdir(parents=True, exist_ok=True)
        tmp_css.write_text(CSS, encoding="utf-8", newline="\n")
        run(["git", "add", "-N", "--", CSS_TARGET], tmp)

        proc = subprocess.run(
            ["git", "diff", "--binary", "--full-index", "--", MAIN_TARGET, CSS_TARGET],
            cwd=tmp,
            text=True,
            capture_output=True,
        )
        if proc.returncode:
            if proc.stderr:
                print(proc.stderr, end="", file=sys.stderr)
            die(f"git diff failed rc={proc.returncode}", 40)
        if not proc.stdout.strip():
            die("generated patch is empty", 41)

        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(proc.stdout, encoding="utf-8", newline="\n")
        print(f"GENERATED_PATCH_SHA256={sha256(output)}")

        numstat = run(["git", "apply", "--numstat", str(output)], root).stdout.strip().splitlines()
        parsed_paths = {row.split("\t")[-1] for row in numstat if row.strip()}
        expected_paths = {MAIN_TARGET, CSS_TARGET}
        if parsed_paths != expected_paths:
            die(f"unexpected patch paths: {sorted(parsed_paths)}", 42)
        print("PARSER=PASS")

        run(["git", "apply", "--check", str(output)], root)
        print("APPLY_CHECK=PASS")
        print("GENERATION_MODE=GIT_DIFF_FROM_EXACT_LIVE_SOURCE")
        print("DASHBOARD_PREMIUM_UXUI_V1_GENERATOR=PASS")
        print(f"TARGETS={MAIN_TARGET},{CSS_TARGET}")
        print(f"OUTPUT={output}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
