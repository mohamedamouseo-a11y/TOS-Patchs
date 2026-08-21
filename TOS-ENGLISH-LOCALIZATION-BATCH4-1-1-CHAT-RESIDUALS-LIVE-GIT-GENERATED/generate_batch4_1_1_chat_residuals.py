#!/usr/bin/env python3
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

EXPECTED_HEAD = "e022b2071363010a5113e56478c6dbed71e44a2e"
TARGET = "frontend/src/components/ChatPanel.jsx"
EXPECTED_LIVE_BLOB = "321afc1db7599f93d6650eaeb660f5250b61b5a0"

REPLACEMENTS = [
    (
        '  [/^(\\d+) جديد$/u, "$1 new"],\n',
        '  [/^(\\d+) جديد$/u, "$1 new"],\n'
        '  [/^1\\s+نتيجة$/u, "1 result"],\n'
        '  [/^(\\d+)\\s+نتيجة$/u, "$1 results"],\n'
    ),
    (
        '  "عرض بيانات المستخدم": "View user profile",\n',
        '  "بدء": "Start",\n'
        '  "كل المستخدمين": "All users",\n'
        '  "ملفات": "Files",\n'
        '  "مثبت": "Pinned",\n'
        '  "نتيجة": "Result",\n'
        '  "تبويبات الشات للموبايل": "Mobile chat tabs",\n'
        '  "عرض بيانات المستخدم": "View user profile",\n'
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
        die("usage: generate_batch4_1_1_chat_residuals.py REPO_ROOT OUTPUT_PATCH", 2)

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

    live_blob = run(["git", "hash-object", TARGET], root).stdout.strip()
    print(f"LIVE_BLOB={live_blob}")
    if live_blob != EXPECTED_LIVE_BLOB:
        die(f"live blob mismatch expected={EXPECTED_LIVE_BLOB} actual={live_blob}", 6)

    staged = run(["git", "diff", "--cached", "--", TARGET], root).stdout
    if staged.strip():
        die("target has staged changes", 7)
    print("TARGET_STAGED=NO")

    tracked_diff = run(["git", "diff", "--", TARGET], root).stdout
    print(f"TARGET_TRACKED_DIRTY={'YES' if tracked_diff.strip() else 'NO'}")
    print("TARGET_STATE_POLICY=EXACT_LIVE_BLOB_ALLOWED_EVEN_IF_TRACKED_DIRTY")

    raw = target.read_bytes()
    if b"\r\n" in raw:
        die("CRLF source detected", 8)
    terminal_newline = raw.endswith(b"\n")
    text = raw.decode("utf-8")

    for index, (old, new) in enumerate(REPLACEMENTS, start=1):
        count = text.count(old)
        print(f"REPLACEMENT_{index}_MATCHES={count}")
        if count != 1:
            die(f"replacement {index} expected 1 exact match, found {count}", 20 + index)
        text = text.replace(old, new, 1)

    tmp = Path(tempfile.mkdtemp(prefix="tos-batch4-1-1-chat-"))
    try:
        run(["git", "init", "-q"], tmp)
        run(["git", "config", "user.email", "batch4-1-1@tos.local"], tmp)
        run(["git", "config", "user.name", "TOS Batch 4.1.1 Generator"], tmp)

        tmp_target = tmp / TARGET
        tmp_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(target, tmp_target)
        run(["git", "add", "--", TARGET], tmp)
        run(["git", "commit", "-qm", "exact live baseline"], tmp)

        encoded = text.encode("utf-8")
        if terminal_newline and not encoded.endswith(b"\n"):
            encoded += b"\n"
        elif not terminal_newline and encoded.endswith(b"\n"):
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
        print("BATCH4_1_1_CHAT_RESIDUALS_GENERATOR=PASS")
        print(f"OUTPUT={output}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
