#!/usr/bin/env python3
import hashlib
import sys
import urllib.request

PATCH = "TOS-TWS-TDOCS-PHASE-2-1-R1-LATEST-BASELINE"
UPSTREAM_URL = "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-TWS-TDOCS-PHASE-2-1-FINAL-GOOGLE-TOOLBAR-MICRO-FIDELITY/run_tdocs_phase2_1.py"
EXPECTED_UPSTREAM_BLOB = "eec5ee24241f7737bed1c0d4ed63bd5eb5499ab5"
OLD_BASELINE = 'BASELINE = "048592147387e2b49382f605a04f8d2efd64f61c"'
NEW_BASELINE = 'BASELINE = "6d23d9f5ef56856cd87ea671d1b11e474e3a39b7"'
EXPECTED_TDOCS_BLOB = 'EDITOR_BLOB = "ed1c94e5faf7a7f2bb9a3ecf8cc94f9ce6eca18a"'


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "TOS-patch-runner-phase2-1-r1"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}_ANCHOR_COUNT:{count}")
    return text.replace(old, new, 1)


try:
    upstream_bytes = download(UPSTREAM_URL)
    actual_blob = git_blob_sha(upstream_bytes)
    if actual_blob != EXPECTED_UPSTREAM_BLOB:
        raise RuntimeError(f"UPSTREAM_INTEGRITY_MISMATCH:{actual_blob}")

    upstream = upstream_bytes.decode("utf-8")
    if upstream.count(EXPECTED_TDOCS_BLOB) != 1:
        raise RuntimeError("TDOCS_BLOB_GUARD_ANCHOR_MISSING")

    fixed = replace_once(upstream, OLD_BASELINE, NEW_BASELINE, "BASELINE")
    code = compile(fixed, "run_tdocs_phase2_1_r1_fixed.py", "exec")

    print(f"PATCH={PATCH}")
    print("UPSTREAM_INTEGRITY=PASS")
    print("LATEST_BASELINE_REBASE=PASS")
    print("TDOCS_EDITOR_BLOB_GUARD_PRESERVED=PASS")
    print("EXPECTED_HEAD=6d23d9f5ef56856cd87ea671d1b11e474e3a39b7")
    print("ORIGINAL_PHASE_2_1_RUNNER=EXECUTING")

    namespace = {
        "__name__": "__main__",
        "__file__": "run_tdocs_phase2_1_r1_fixed.py",
    }
    exec(code, namespace, namespace)
except SystemExit:
    raise
except Exception as exc:
    print(f"ERROR={exc}", file=sys.stderr)
    sys.exit(1)
