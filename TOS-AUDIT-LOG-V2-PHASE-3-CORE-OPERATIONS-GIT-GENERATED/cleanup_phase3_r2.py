#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys

EXPECTED_HEAD = "c2704bd55eea2bbb099dd409e20af1a4d27b06f3"
ACCIDENTAL_PATH = "run_phase3.py"
ACCIDENTAL_BLOB = "e4411edfcf2fe96d9fceaa3aae5ad551fe1f7aa6"
PHASE3_BLOBS = {
    "backend/src/app.js": "ceda57c18f14480a12da8b3f07e0f8d4c62b159b",
    "backend/src/middleware/auditV2CoreOperations.js": "39e1436d3efb02b74458ef991a4e7ae3d88fe6c6",
    "backend/src/middleware/auditV2CoreOperations.test.js": "e5d05a19f09bfbaa2bf949a658eda9d2c9bc9e43",
}


def git(repo, *args):
    result = subprocess.run(["git", *args], cwd=repo, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def main():
    repo = Path(git(Path.cwd(), "rev-parse", "--show-toplevel"))
    print(f"REPO={repo}")
    require(git(repo, "rev-parse", "HEAD") == EXPECTED_HEAD, f"HEAD must equal {EXPECTED_HEAD}")
    require(not git(repo, "status", "--porcelain"), "working tree must be clean before cleanup")

    target = repo / ACCIDENTAL_PATH
    require(target.is_file(), f"missing accidental file: {ACCIDENTAL_PATH}")
    require(git(repo, "hash-object", ACCIDENTAL_PATH) == ACCIDENTAL_BLOB, "run_phase3.py content mismatch; stop")

    for rel, expected_blob in PHASE3_BLOBS.items():
        require((repo / rel).is_file(), f"missing Phase 3 file: {rel}")
        actual = git(repo, "hash-object", rel)
        require(actual == expected_blob, f"Phase 3 blob mismatch for {rel}: {actual}")

    target.unlink()
    status = git(repo, "status", "--short")
    require(status == f"D {ACCIDENTAL_PATH}", f"unexpected cleanup diff: {status!r}")
    require(not git(repo, "diff", "--check"), "git diff --check reported an issue")

    print("PHASE_3_CLEANUP=PASS")
    print("ONLY_FILE_REMOVED=run_phase3.py")
    print("PHASE_3_IMPLEMENTATION_PRESERVED=YES")
    print("READY_FOR_GIT_PUSH=YES")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("PHASE_3_CLEANUP=FAIL")
        print(f"ERROR={exc}")
        print("READY_FOR_GIT_PUSH=NO")
        sys.exit(1)
