#!/usr/bin/env python3
from pathlib import Path
import hashlib
import subprocess
import sys
import urllib.request

PATCH = "TOS-TWS-GOOGLE-SHEETS-PHASE-5-COLLABORATION-R2"
REPO = Path("/var/www/TOS")
EXPECTED_HEAD = "db8fbbc311015e0a3acbebfb4b137c58d5f77114"
RUNNER_URL = "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-TWS-GOOGLE-SHEETS-PHASE-5-COLLABORATION/run_phase5.py"
RUNNER_BLOB_SHA = "f0453ea65b8f7b4ffd58e822b43ea843f23ab207"

TRACKED = [
    "backend/src/routes/workspace.routes.js",
    "backend/src/services/workspace.service.js",
    "backend/src/sockets.js",
    "frontend/src/lib/api.js",
    "frontend/src/pages/tws/TSheetsEditor.jsx",
    "frontend/src/pages/tws/useTwsPresence.js",
]
NEW_FILES = [
    "backend/src/utils/sheetCollabPhase5.js",
    "backend/src/utils/sheetCollabPhase5.test.js",
    "frontend/src/pages/tws/sheetCollabPhase5.js",
]

BAD_BLOCK = '''    if (REPO / "backend/src/utils/workspaceXlsx.phase3.test.js" in []:
        pass
'''
FIXED_BLOCK = ""


def blob_sha(data):
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def git(*args, check=True):
    return subprocess.run(
        ["git", *args],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=check,
    )


def clean_status():
    return git("status", "--porcelain").stdout.strip() == ""


def rollback():
    subprocess.run(
        ["git", "checkout", "HEAD", "--", *TRACKED],
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    for rel in NEW_FILES:
        path = REPO / rel
        if not path.exists():
            continue
        tracked = git("ls-files", "--error-unmatch", rel, check=False).returncode == 0
        if not tracked:
            path.unlink()


def main():
    print(f"PATCH={PATCH}")
    if not REPO.exists():
        raise RuntimeError("repo not found")

    head = git("rev-parse", "HEAD").stdout.strip()
    print(f"HEAD={head}")
    if head != EXPECTED_HEAD:
        raise RuntimeError(f"unexpected HEAD: {head}; expected {EXPECTED_HEAD}")
    if not clean_status():
        raise RuntimeError("PRECHECK_WORKTREE is not clean")
    print("PRECHECK_WORKTREE=CLEAN")

    data = urllib.request.urlopen(RUNNER_URL, timeout=30).read()
    actual = blob_sha(data)
    if actual != RUNNER_BLOB_SHA:
        raise RuntimeError(f"Phase 5 base runner integrity mismatch: {actual} != {RUNNER_BLOB_SHA}")

    source = data.decode("utf-8")
    count = source.count(BAD_BLOCK)
    if count != 1:
        raise RuntimeError(f"expected exactly one known syntax defect, found {count}")

    corrected = source.replace(BAD_BLOCK, FIXED_BLOCK, 1)
    compile(corrected, "run_phase5_r2_corrected.py", "exec")
    print("PHASE_5_R2_BASE_RUNNER_INTEGRITY=PASS")
    print("PHASE_5_R2_SYNTAX_CORRECTION=APPLIED")
    print("PHASE_5_R2_CORRECTED_SOURCE_SYNTAX=PASS")
    print(f"PHASE_5_R2_CORRECTED_SOURCE_SHA256={hashlib.sha256(corrected.encode()).hexdigest()}")

    try:
        exec(compile(corrected, "run_phase5_r2_corrected.py", "exec"), {"__name__": "__main__"})
    except SystemExit as exc:
        code = int(exc.code or 0)
        if code == 0:
            return
        rollback()
        print("PHASE_5_R2_ROLLBACK=PASS" if clean_status() else "PHASE_5_R2_ROLLBACK=FAIL")
        raise
    except BaseException:
        rollback()
        print("PHASE_5_R2_ROLLBACK=PASS" if clean_status() else "PHASE_5_R2_ROLLBACK=FAIL")
        raise


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:
        rollback()
        print("PHASE_5_R2_ROLLBACK=PASS" if clean_status() else "PHASE_5_R2_ROLLBACK=FAIL")
        print("PHASE_5_R2_RUN=FAIL")
        print(f"ERROR={exc}")
        print("READY_FOR_GIT_PUSH=NO")
        sys.exit(1)
