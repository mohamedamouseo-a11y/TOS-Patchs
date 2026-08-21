#!/usr/bin/env python3
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

EXPECTED_HEAD = "92540062f26ee04cbb67f2df9c1aba2f655a2522"
TARGET = "frontend/src/components/GithubAdvancedAdmin.jsx"
EXPECTED_BLOB = "2ec32123f8bfa50e0e635f1eeb826139328ef48c"

REPLACEMENTS = [
    (
'''              ["#github-overview", "نظرة عامة", GitBranch],
              ["#github-workflow", "المراجعة والـ Push", GitMerge],
              ["#github-changes", "الملفات والتغييرات", FileCode2],
              ["#github-connection", "إعدادات الاتصال", ShieldCheck],
              ["#github-console", "السجلات والتنفيذ", Terminal],''',
'''              ["#github-overview", ui("نظرة عامة", "Overview"), GitBranch],
              ["#github-workflow", ui("المراجعة والـ Push", "Review & Push"), GitMerge],
              ["#github-changes", ui("الملفات والتغييرات", "Files & Changes"), FileCode2],
              ["#github-connection", ui("إعدادات الاتصال", "Connection Settings"), ShieldCheck],
              ["#github-console", ui("السجلات والتنفيذ", "Logs & Execution"), Terminal],'''
    ),
    (
'''            <p className="text-[10px] font-black uppercase tracking-wide text-zinc-400">الحساب</p>''',
'''            <p className="text-[10px] font-black uppercase tracking-wide text-zinc-400">{ui("الحساب", "Account")}</p>'''
    ),
    (
'''          <section className="rounded-[28px] border border-zinc-200/70 bg-white p-5 shadow-[0_16px_45px_rgba(15,23,42,0.05)] dark:border-white/10 dark:bg-zinc-950"><div className="flex items-center justify-between gap-3"><h3 className="text-sm font-black">{ui("معلومات المستودع", "Repository Information")}</h3><Badge tone={status?.configured ? "success" : "warning"}>{status?.configured ? ui("مكتمل", "Complete") : ui("غير مكتمل", "Incomplete")}</Badge></div><div className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-6">{[["المستودع", premiumRepoName], ["الفرع", status?.branch || selectedBranch || "—"], ["آخر Commit", status?.shortSha || "—"], ["الصلاحية", status?.permission || "—"], ["Working Tree", status?.changedFiles ? `${status.changedFiles} ${isEnglish ? "files" : "ملف"}` : ui("نظيف", "Clean")], ["آخر مزامنة", formatUiDate(status?.lastSyncAt)]].map(([label, value]) => <div key={label} className="rounded-[16px] border border-zinc-100 bg-zinc-50/60 p-3 dark:border-white/10 dark:bg-white/[0.025]"><p className="text-[9px] font-black text-zinc-400">{label}</p><p className="mt-1.5 truncate text-[11px] font-black" dir="auto">{value}</p></div>)}</div></section>''',
'''          <section className="rounded-[28px] border border-zinc-200/70 bg-white p-5 shadow-[0_16px_45px_rgba(15,23,42,0.05)] dark:border-white/10 dark:bg-zinc-950"><div className="flex items-center justify-between gap-3"><h3 className="text-sm font-black">{ui("معلومات المستودع", "Repository Information")}</h3><Badge tone={status?.configured ? "success" : "warning"}>{status?.configured ? ui("مكتمل", "Complete") : ui("غير مكتمل", "Incomplete")}</Badge></div><div className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-6">{[[ui("المستودع", "Repository"), premiumRepoName], [ui("الفرع", "Branch"), status?.branch || selectedBranch || "—"], [ui("آخر Commit", "Last Commit"), status?.shortSha || "—"], [ui("الصلاحية", "Permission"), status?.permission || "—"], ["Working Tree", status?.changedFiles ? `${status.changedFiles} ${isEnglish ? "files" : "ملف"}` : ui("نظيف", "Clean")], [ui("آخر مزامنة", "Last sync"), formatUiDate(status?.lastSyncAt)]].map(([label, value]) => <div key={label} className="rounded-[16px] border border-zinc-100 bg-zinc-50/60 p-3 dark:border-white/10 dark:bg-white/[0.025]"><p className="text-[9px] font-black text-zinc-400">{label}</p><p className="mt-1.5 truncate text-[11px] font-black" dir="auto">{value}</p></div>)}</div></section>'''
    ),
    (
'''            <summary className="flex cursor-pointer list-none items-center justify-between gap-3"><div className="flex items-center gap-3"><ShieldCheck size={19} /><div><h3 className="text-sm font-black">{ui("إعدادات الاتصال", "Connection Settings")}</h3><p className="mt-1 text-[10px] font-bold text-zinc-400">Token، المسار المحلي، Repository والفرع.</p></div></div><Badge tone="zinc">{ui("إظهار / إخفاء", "Show / Hide")}</Badge></summary>''',
'''            <summary className="flex cursor-pointer list-none items-center justify-between gap-3"><div className="flex items-center gap-3"><ShieldCheck size={19} /><div><h3 className="text-sm font-black">{ui("إعدادات الاتصال", "Connection Settings")}</h3><p className="mt-1 text-[10px] font-bold text-zinc-400">{ui("Token، المسار المحلي، Repository والفرع.", "Token, local path, repository and branch.")}</p></div></div><Badge tone="zinc">{ui("إظهار / إخفاء", "Show / Hide")}</Badge></summary>'''
    ),
]


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
        die("usage: generate_batch2_1_from_live.py REPO_ROOT OUTPUT_PATCH", 2)

    root = Path(sys.argv[1]).resolve()
    output = Path(sys.argv[2]).resolve()
    target = root / TARGET

    if not (root / ".git").is_dir():
        die(f"not a git repository: {root}", 3)
    if not target.is_file():
        die(f"target missing: {TARGET}", 4)

    head = run(["git", "rev-parse", "HEAD"], root).stdout.strip()
    print(f"HEAD={head}")
    if head != EXPECTED_HEAD:
        die(f"HEAD mismatch expected={EXPECTED_HEAD} actual={head}", 5)

    blob = run(["git", "hash-object", TARGET], root).stdout.strip()
    print(f"SOURCE_BLOB={blob}")
    if blob != EXPECTED_BLOB:
        die(f"blob mismatch expected={EXPECTED_BLOB} actual={blob}", 6)

    diff = run(["git", "diff", "--", TARGET], root).stdout
    if diff.strip():
        die("target has tracked local modifications", 7)
    print("TARGET_CLEAN=YES")

    raw = target.read_bytes()
    if b"\r\n" in raw:
        die("CRLF source detected; explicit handling required", 8)
    had_terminal_newline = raw.endswith(b"\n")
    text = raw.decode("utf-8")

    for index, (old, new) in enumerate(REPLACEMENTS, start=1):
        count = text.count(old)
        print(f"REPLACEMENT_{index}_MATCHES={count}")
        if count != 1:
            die(f"replacement {index} expected one exact match, found {count}", 20 + index)
        text = text.replace(old, new, 1)

    tmp = Path(tempfile.mkdtemp(prefix="tos-batch2-1-"))
    try:
        run(["git", "init", "-q"], tmp)
        run(["git", "config", "user.email", "batch2-1@tos.local"], tmp)
        run(["git", "config", "user.name", "TOS Batch 2.1 Generator"], tmp)

        tmp_target = tmp / TARGET
        tmp_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(target, tmp_target)
        run(["git", "add", "--", TARGET], tmp)
        run(["git", "commit", "-qm", "exact live baseline"], tmp)

        encoded = text.encode("utf-8")
        if had_terminal_newline and not encoded.endswith(b"\n"):
            encoded += b"\n"
        elif not had_terminal_newline and encoded.endswith(b"\n"):
            encoded = encoded[:-1]
        tmp_target.write_bytes(encoded)

        proc = subprocess.run(
            ["git", "diff", "--binary", "--full-index", "--", TARGET],
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

        output.write_text(proc.stdout, encoding="utf-8", newline="\n")
        print(f"GENERATED_PATCH_SHA256={sha256(output)}")

        numstat = run(["git", "apply", "--numstat", str(output)], root).stdout.strip().splitlines()
        parsed_paths = {row.split("\t")[-1] for row in numstat if row.strip()}
        if parsed_paths != {TARGET}:
            die(f"unexpected patch paths: {sorted(parsed_paths)}", 42)
        print("PARSER=PASS")

        run(["git", "apply", "--check", str(output)], root)
        print("APPLY_CHECK=PASS")
        print("GENERATION_MODE=GIT_DIFF_FROM_EXACT_LIVE_SOURCE")
        print("BATCH2_1_GENERATOR=PASS")
        print(f"TARGET_PATH={TARGET}")
        print(f"OUTPUT={output}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
