#!/usr/bin/env python3
from pathlib import Path
import hashlib
import subprocess
import sys
import urllib.request

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


def blob_sha(data):
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def git(*args, check=True):
    return subprocess.run(["git", *args], cwd=REPO, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=check)


def clean_status():
    return git("status", "--porcelain").stdout.strip() == ""


def rollback():
    subprocess.run(["git", "checkout", "HEAD", "--", *TRACKED], cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for rel in NEW_FILES:
        path = REPO / rel
        if path.exists() and not git("ls-files", "--error-unmatch", rel, check=False).returncode == 0:
            path.unlink()


def main():
    if not REPO.exists():
        raise RuntimeError("repo not found")
    head = git("rev-parse", "HEAD").stdout.strip()
    if head != EXPECTED_HEAD:
        raise RuntimeError(f"unexpected HEAD: {head}; expected {EXPECTED_HEAD}")
    if not clean_status():
        raise RuntimeError("PRECHECK_WORKTREE is not clean")

    data = urllib.request.urlopen(RUNNER_URL, timeout=30).read()
    actual = blob_sha(data)
    if actual != RUNNER_BLOB_SHA:
        raise RuntimeError(f"Phase 5 runner integrity mismatch: {actual} != {RUNNER_BLOB_SHA}")
    source = data.decode("utf-8")
    compile(source, "run_phase5.py", "exec")
    print("PHASE_5_R1_RUNNER_INTEGRITY=PASS")
    print("PHASE_5_R1_RUNNER_SYNTAX=PASS")

    try:
        exec(compile(source, "run_phase5.py", "exec"), {"__name__": "__main__"})
    except SystemExit as exc:
        if int(exc.code or 0) == 0:
            return
        rollback()
        print("PHASE_5_R1_ROLLBACK=PASS" if clean_status() else "PHASE_5_R1_ROLLBACK=FAIL")
        raise
    except BaseException:
        rollback()
        print("PHASE_5_R1_ROLLBACK=PASS" if clean_status() else "PHASE_5_R1_ROLLBACK=FAIL")
        raise


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:
        print("PHASE_5_R1_RUN=FAIL")
        print(f"ERROR={exc}")
        print("READY_FOR_GIT_PUSH=NO")
        sys.exit(1)
