#!/usr/bin/env python3
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

EXPECTED_HEAD = "1d7770be875a8210eafee712a90dc56eb084367a"
TARGET = "frontend/src/components/GithubAdvancedAdmin.jsx"
EXPECTED_BLOB = "4bd8bce788523ad830519f5a2599d4deb85f9189"

OLD = '''<Field type={showToken ? "text" : "password"} name="tos_github_pat_input_premium" value={token} onChange={(event) => setToken(event.target.value)} placeholder={status?.hasToken ? ui("Token محفوظ — اترك الحقل فارغًا لإعادة التحقق", "Token saved — leave blank to verify the current token") : "github_pat_..."} dir="ltr" className="pl-12" autoComplete="off" data-lpignore="true" data-1p-ignore="true" /><button type="button" onClick={() => setShowToken((value) => !value)} className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-700">{showToken ? <EyeOff size={18} /> : <Eye size={18} />}</button></div><Button onClick={verifyAccount} disabled={Boolean(busy) || (!token.trim() && !status?.hasToken)}>{busy === "verify" ? <Loader2 size={17} className="animate-spin" /> : <ShieldCheck size={17} />} تحقق</Button>'''

NEW = '''<Field type={showToken ? "text" : "password"} name="tos_github_pat_input_premium" value={token} onChange={(event) => setToken(event.target.value)} placeholder={status?.hasToken ? ui("Token محفوظ — اترك الحقل فارغًا لإعادة التحقق", "Token saved — leave blank to verify the current token") : "github_pat_..."} dir="ltr" className="pl-12" autoComplete="off" data-lpignore="true" data-1p-ignore="true" /><button type="button" onClick={() => setShowToken((value) => !value)} className="absolute left-4 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-zinc-700">{showToken ? <EyeOff size={18} /> : <Eye size={18} />}</button></div><Button onClick={verifyAccount} disabled={Boolean(busy) || (!token.trim() && !status?.hasToken)}>{busy === "verify" ? <Loader2 size={17} className="animate-spin" /> : <ShieldCheck size={17} />} {ui("تحقق", "Verify")}</Button>'''


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
        die("usage: generate_batch2_2_from_live.py REPO_ROOT OUTPUT_PATCH", 2)

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

    matches = text.count(OLD)
    print(f"REPLACEMENT_MATCHES={matches}")
    if matches != 1:
        die(f"expected one exact premium Verify match, found {matches}", 20)
    updated = text.replace(OLD, NEW, 1)

    tmp = Path(tempfile.mkdtemp(prefix="tos-batch2-2-"))
    try:
        run(["git", "init", "-q"], tmp)
        run(["git", "config", "user.email", "batch2-2@tos.local"], tmp)
        run(["git", "config", "user.name", "TOS Batch 2.2 Generator"], tmp)

        tmp_target = tmp / TARGET
        tmp_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(target, tmp_target)
        run(["git", "add", "--", TARGET], tmp)
        run(["git", "commit", "-qm", "exact live baseline"], tmp)

        encoded = updated.encode("utf-8")
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
        print("BATCH2_2_GENERATOR=PASS")
        print(f"TARGET_PATH={TARGET}")
        print(f"OUTPUT={output}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
