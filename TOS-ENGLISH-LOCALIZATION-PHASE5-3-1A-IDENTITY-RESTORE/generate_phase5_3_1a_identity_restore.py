#!/usr/bin/env python3
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

EXPECTED_HEAD = "a9be3b4b5daabbcd2505720c4df6eaf97a8fe82d"
TARGET = "frontend/src/pages/SettingsPage.jsx"
EXPECTED_BLOB = "ee6081797a7e4942c707b979a6e18254a14624fb"
OLD = "استعادة التبويب الحالي"
NEW = '{identityLang === "en" ? "Restore current tab" : "استعادة التبويب الحالي"}'


def die(message, code=1):
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(code)


def run(args, cwd, check=True):
    p = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if p.stdout:
        print(p.stdout, end="")
    if p.stderr:
        print(p.stderr, end="", file=sys.stderr)
    if check and p.returncode:
        die(f"command failed rc={p.returncode}: {' '.join(args)}", 90)
    return p


def main():
    if len(sys.argv) != 3:
        die("usage: generate_phase5_3_1a_identity_restore.py REPO_ROOT OUTPUT_PATCH", 2)
    root = Path(sys.argv[1]).resolve()
    output = Path(sys.argv[2]).resolve()
    target = root / TARGET
    if not (root / ".git").is_dir():
        die("not a git repo", 3)
    head = run(["git", "rev-parse", "HEAD"], root).stdout.strip()
    print(f"HEAD={head}")
    if head != EXPECTED_HEAD:
        die(f"HEAD mismatch expected={EXPECTED_HEAD} actual={head}", 4)
    blob = run(["git", "hash-object", TARGET], root).stdout.strip()
    print(f"SOURCE_BLOB={blob}")
    if blob != EXPECTED_BLOB:
        die(f"blob mismatch expected={EXPECTED_BLOB} actual={blob}", 5)
    if run(["git", "diff", "--cached", "--", TARGET], root).stdout.strip():
        die("target has staged changes", 6)
    # V3 is intentionally an existing unstaged diff versus HEAD; exact blob pins it.
    raw = target.read_bytes()
    if b"\r\n" in raw:
        die("CRLF detected", 7)
    text = raw.decode("utf-8")
    count = text.count(OLD)
    print(f"RESTORE_LABEL_MATCHES={count}")
    if count != 1:
        die(f"expected exactly 1 restore label, found {count}", 8)
    text = text.replace(OLD, NEW, 1)

    tmp = Path(tempfile.mkdtemp(prefix="tos-phase5-3-1a-"))
    try:
        run(["git", "init", "-q"], tmp)
        run(["git", "config", "user.email", "phase5-3-1a@tos.local"], tmp)
        run(["git", "config", "user.name", "TOS Phase 5.3.1a Generator"], tmp)
        t = tmp / TARGET
        t.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(target, t)
        run(["git", "add", "--", TARGET], tmp)
        run(["git", "commit", "-qm", "exact post-v3 baseline"], tmp)
        t.write_text(text, encoding="utf-8", newline="\n")
        diff = subprocess.run(["git", "diff", "--binary", "--full-index", "--", TARGET], cwd=tmp, text=True, capture_output=True)
        if diff.returncode or not diff.stdout.strip():
            die("failed to generate patch", 9)
        output.write_text(diff.stdout, encoding="utf-8", newline="\n")
        print(f"GENERATED_PATCH_SHA256={hashlib.sha256(output.read_bytes()).hexdigest()}")
        numstat = run(["git", "apply", "--numstat", str(output)], root).stdout.strip().splitlines()
        paths = {row.split("\t")[-1] for row in numstat if row.strip()}
        if paths != {TARGET}:
            die(f"unexpected patch paths: {sorted(paths)}", 10)
        print("PARSER=PASS")
        run(["git", "apply", "--check", str(output)], root)
        print("APPLY_CHECK=PASS")
        print("PHASE5_3_1A_IDENTITY_RESTORE_GENERATOR=PASS")
        print(f"OUTPUT={output}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
