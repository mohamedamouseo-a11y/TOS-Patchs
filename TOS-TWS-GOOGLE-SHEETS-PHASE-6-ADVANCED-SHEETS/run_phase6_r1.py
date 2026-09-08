#!/usr/bin/env python3
from pathlib import Path
import hashlib
import subprocess
import sys
import urllib.request

PATCH = "TOS-TWS-GOOGLE-SHEETS-PHASE-6-ADVANCED-SHEETS-R1"
REPO = Path("/var/www/TOS")
EXPECTED_HEAD = "0dde58e4ca91ac63f28efc0c3605fbc58895c5d8"
RUNNER_URL = "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-TWS-GOOGLE-SHEETS-PHASE-6-ADVANCED-SHEETS/run_phase6.py"
RUNNER_BLOB_SHA = "3ab01991089ea9e140aab44bc8b5e0af1b36df2f"

PHASE6_SCOPE = {
    "backend/src/services/workspace.service.js",
    "backend/src/utils/sheetCollabPhase5.js",
    "backend/src/utils/sheetAdvancedPhase6.js",
    "backend/src/utils/sheetAdvancedPhase6.test.js",
    "frontend/src/pages/tws/TSheetsEditor.jsx",
    "frontend/src/pages/tws/sheetCollabPhase5.js",
    "frontend/src/pages/tws/sheetAdvancedPhase6.js",
}

TRACKED_PHASE6 = {
    "backend/src/services/workspace.service.js",
    "backend/src/utils/sheetCollabPhase5.js",
    "frontend/src/pages/tws/TSheetsEditor.jsx",
    "frontend/src/pages/tws/sheetCollabPhase5.js",
}
NEW_PHASE6 = PHASE6_SCOPE - TRACKED_PHASE6


def git(*args, check=True):
    return subprocess.run(
        ["git", *args],
        cwd=REPO,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=check,
    )


def blob_sha(data):
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def status_paths():
    p = git("status", "--porcelain")
    result = set()
    for line in p.stdout.splitlines():
        if not line.strip():
            continue
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        result.add(path)
    return result


def fingerprint(rel):
    path = REPO / rel
    if not path.exists():
        return "MISSING"
    if path.is_file():
        return hashlib.sha256(path.read_bytes()).hexdigest()
    return "DIR"


def snapshot(paths):
    return {rel: fingerprint(rel) for rel in sorted(paths)}


def rollback_phase6_only():
    if TRACKED_PHASE6:
        subprocess.run(
            ["git", "checkout", "HEAD", "--", *sorted(TRACKED_PHASE6)],
            cwd=REPO,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
    for rel in NEW_PHASE6:
        path = REPO / rel
        if not path.exists():
            continue
        tracked = git("ls-files", "--error-unmatch", rel, check=False).returncode == 0
        if not tracked and path.is_file():
            path.unlink()


def replace_exact(source, old, new, label):
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return source.replace(old, new, 1)


def corrected_runner_source(source):
    source = replace_exact(
        source,
        '    "frontend/src/pages/tws/sheetAdvancedPhase6.js",\n]\n\n\ndef run(cmd, cwd=REPO, check=True):',
        '    "frontend/src/pages/tws/sheetAdvancedPhase6.js",\n]\n\nPREEXISTING_DIRTY = set()\n\n\ndef run(cmd, cwd=REPO, check=True):',
        "inject preexisting dirty state",
    )

    source = replace_exact(
        source,
        '''    actual = changed_paths()\n    if actual != EXPECTED_CHANGED:\n        raise RuntimeError(f"unexpected changed paths: {sorted(actual)}")\n    print(f"PATCH_FILE_COUNT={len(actual)}")\n''',
        '''    actual_all = changed_paths()\n    missing_preexisting = PREEXISTING_DIRTY - actual_all\n    if missing_preexisting:\n        raise RuntimeError(f"pre-existing dirty paths disappeared: {sorted(missing_preexisting)}")\n    actual = actual_all - PREEXISTING_DIRTY\n    if actual != EXPECTED_CHANGED:\n        raise RuntimeError(f"unexpected Phase 6 changed paths: {sorted(actual)}; all={sorted(actual_all)}")\n    print(f"PATCH_FILE_COUNT={len(actual)}")\n''',
        "relax final changed-path union",
    )

    source = replace_exact(
        source,
        '''    if changed_paths():\n        raise RuntimeError("PRECHECK_WORKTREE is not clean")\n    print("PRECHECK_WORKTREE=CLEAN")\n''',
        '''    global PREEXISTING_DIRTY\n    PREEXISTING_DIRTY = changed_paths()\n    phase6_scope = set(TRACKED) | set(NEW_FILES)\n    overlap = PREEXISTING_DIRTY & phase6_scope\n    if overlap:\n        raise RuntimeError(f"PREEXISTING_DIRTY_OVERLAPS_PHASE6_SCOPE: {sorted(overlap)}")\n    if PREEXISTING_DIRTY:\n        print("PRECHECK_WORKTREE=DIRTY_UNRELATED_ALLOWED")\n        print("PREEXISTING_DIRTY_PATHS=" + ",".join(sorted(PREEXISTING_DIRTY)))\n    else:\n        print("PRECHECK_WORKTREE=CLEAN")\n''',
        "allow unrelated dirty state",
    )

    source = replace_exact(
        source,
        '        print("PHASE_6_ROLLBACK=PASS" if not changed_paths() else "PHASE_6_ROLLBACK=FAIL")\n',
        '        print("PHASE_6_ROLLBACK=PASS" if changed_paths() == PREEXISTING_DIRTY else "PHASE_6_ROLLBACK=FAIL")\n',
        "rollback preservation check",
    )
    return source


def main():
    print(f"PATCH={PATCH}")
    if not REPO.exists():
        raise RuntimeError("repo not found")

    head = git("rev-parse", "HEAD").stdout.strip()
    print(f"HEAD={head}")
    if head != EXPECTED_HEAD:
        raise RuntimeError(f"unexpected HEAD: {head}; expected {EXPECTED_HEAD}")

    preexisting = status_paths()
    overlap = preexisting & PHASE6_SCOPE
    if overlap:
        raise RuntimeError(f"PREEXISTING_DIRTY_OVERLAPS_PHASE6_SCOPE: {sorted(overlap)}")
    pre_snapshot = snapshot(preexisting)
    if preexisting:
        print("R1_PREEXISTING_DIRTY_COUNT=" + str(len(preexisting)))
        print("R1_PREEXISTING_DIRTY_PATHS=" + ",".join(sorted(preexisting)))
    else:
        print("R1_PREEXISTING_DIRTY_COUNT=0")

    data = urllib.request.urlopen(RUNNER_URL, timeout=30).read()
    actual_blob = blob_sha(data)
    if actual_blob != RUNNER_BLOB_SHA:
        raise RuntimeError(f"base runner integrity mismatch: {actual_blob} != {RUNNER_BLOB_SHA}")
    source = data.decode("utf-8")
    corrected = corrected_runner_source(source)
    compile(corrected, "run_phase6_r1_corrected.py", "exec")
    print("R1_BASE_RUNNER_INTEGRITY=PASS")
    print("R1_CORRECTED_SOURCE_SYNTAX=PASS")
    print("R1_CORRECTED_SOURCE_SHA256=" + hashlib.sha256(corrected.encode()).hexdigest())

    try:
        exec(compile(corrected, "run_phase6_r1_corrected.py", "exec"), {"__name__": "__main__"})
    except SystemExit as exc:
        code = int(exc.code or 0)
        if code != 0:
            rollback_phase6_only()
            post_snapshot = snapshot(preexisting)
            print("R1_PREEXISTING_DIRTY_STATE_PRESERVED=YES" if post_snapshot == pre_snapshot else "R1_PREEXISTING_DIRTY_STATE_PRESERVED=NO")
        raise
    except BaseException:
        rollback_phase6_only()
        post_snapshot = snapshot(preexisting)
        print("R1_PREEXISTING_DIRTY_STATE_PRESERVED=YES" if post_snapshot == pre_snapshot else "R1_PREEXISTING_DIRTY_STATE_PRESERVED=NO")
        raise

    post_snapshot = snapshot(preexisting)
    if post_snapshot != pre_snapshot:
        rollback_phase6_only()
        raise RuntimeError("pre-existing dirty file contents changed during Phase 6")

    final_paths = status_paths()
    if not preexisting.issubset(final_paths):
        rollback_phase6_only()
        raise RuntimeError("pre-existing dirty paths were not preserved")
    phase6_paths = final_paths - preexisting
    if phase6_paths != PHASE6_SCOPE:
        rollback_phase6_only()
        raise RuntimeError(f"unexpected Phase 6 final paths: {sorted(phase6_paths)}")

    print("R1_PREEXISTING_DIRTY_STATE_PRESERVED=YES")
    print("R1_PHASE6_CHANGED_PATHS_EXACT=YES")
    print("R1_READY_FOR_GIT_PUSH=YES")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:
        rollback_phase6_only()
        print("PHASE_6_R1_RUN=FAIL")
        print(f"ERROR={exc}")
        print("READY_FOR_GIT_PUSH=NO")
        sys.exit(1)
