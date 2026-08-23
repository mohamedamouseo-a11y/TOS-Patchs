#!/usr/bin/env python3
import difflib
import hashlib
import subprocess
import sys
from pathlib import Path

TARGET = "server/slaAdvanced.test.ts"
EXPECTED_HEAD = "b37edc16ec9a4b10fad90349b489fd6ac123c064"
OLD = '    expect(getBusinessMinutesLate("2026-08-21", mondayNoonUtc, base)).toBe(180);\n'
NEW = '    expect(getBusinessMinutesLate("2026-08-21", mondayNoonUtc, base)).toBe(660);\n'


def run(cmd, cwd):
    return subprocess.run(cmd, cwd=cwd, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def main():
    repo = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    output = Path(sys.argv[2] if len(sys.argv) > 2 else "/var/tmp/TOS_SLA_ADVANCED_PHASE4_TESTFIX.patch").resolve()

    if not (repo / ".git").exists():
        raise RuntimeError(f"Not a git repository: {repo}")
    branch = run(["git", "branch", "--show-current"], repo).stdout.strip()
    if branch != "main":
        raise RuntimeError(f"Expected branch main, found {branch or '(detached)'}")
    head = run(["git", "rev-parse", "HEAD"], repo).stdout.strip()
    if head != EXPECTED_HEAD:
        raise RuntimeError(f"Expected HEAD {EXPECTED_HEAD}, found {head}")

    path = repo / TARGET
    if not path.exists():
        raise RuntimeError(f"Missing Phase 4 test file: {TARGET}")
    before = path.read_text()
    if before.count(OLD) != 1:
        raise RuntimeError(f"Expected exactly one stale Cairo business-minutes assertion in {TARGET}, found {before.count(OLD)}")
    if 'businessDays: "1,2,3,4,7"' not in before:
        raise RuntimeError("Sunday-Thursday fixture not found; refusing to alter expectation")

    after = before.replace(OLD, NEW, 1)
    patch = ''.join(difflib.unified_diff(
        before.splitlines(True),
        after.splitlines(True),
        fromfile=f"a/{TARGET}",
        tofile=f"b/{TARGET}",
    ))
    output.write_text(patch)

    check = subprocess.run(["git", "apply", "--check", str(output)], cwd=repo, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if check.returncode != 0:
        raise RuntimeError(f"git apply --check failed:\n{check.stderr}")

    print(f"PATCH={output}")
    print(f"SHA256={hashlib.sha256(output.read_bytes()).hexdigest()}")
    print(f"FILE={TARGET}")
    print("EXPECTED_BUSINESS_MINUTES=660")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
