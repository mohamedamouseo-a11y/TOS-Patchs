#!/usr/bin/env python3
import hashlib
import sys
import urllib.request

PATCH = "TOS-TWS-TDOCS-PHASE-2-R2-LATEST-BASELINE-RUNNER-FIX"
UPSTREAM_URL = "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-TWS-TDOCS-PHASE-2-GOOGLE-DOCS-MENU-CORE-EDITING-PARITY/run_tdocs_phase2.py"
EXPECTED_UPSTREAM_BLOB = "000eb0db54ac80650a438af173a2422e0ecd53e4"

BROKEN = b'        if (REPO / candidate in []:\n            pass\n'
OLD_BASELINE = b'BASELINE = "509c51eeab1a9b880d902aac5082aa6124996c9b"'
NEW_BASELINE = b'BASELINE = "db1efe2ccf30552ab7c65f7bc672861adf66cc05"'


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "TOS-patch-runner-r2"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


try:
    upstream = download(UPSTREAM_URL)
    actual = git_blob_sha(upstream)
    if actual != EXPECTED_UPSTREAM_BLOB:
        raise RuntimeError(f"UPSTREAM_INTEGRITY_MISMATCH:{actual}")

    if upstream.count(BROKEN) != 1:
        raise RuntimeError(f"BROKEN_ANCHOR_COUNT:{upstream.count(BROKEN)}")
    if upstream.count(OLD_BASELINE) != 1:
        raise RuntimeError(f"BASELINE_ANCHOR_COUNT:{upstream.count(OLD_BASELINE)}")

    fixed = upstream.replace(BROKEN, b"", 1)
    fixed = fixed.replace(OLD_BASELINE, NEW_BASELINE, 1)

    code = compile(fixed.decode("utf-8"), "run_tdocs_phase2_r2_fixed.py", "exec")

    print(f"PATCH={PATCH}")
    print("UPSTREAM_INTEGRITY=PASS")
    print("RUNNER_SYNTAX_FIX=PASS")
    print("LATEST_BASELINE_REBASE=PASS")
    print("EXPECTED_HEAD=db1efe2ccf30552ab7c65f7bc672861adf66cc05")
    print("ORIGINAL_PHASE_RUNNER=EXECUTING")

    namespace = {
        "__name__": "__main__",
        "__file__": "run_tdocs_phase2_r2_fixed.py",
    }
    exec(code, namespace, namespace)
except SystemExit:
    raise
except Exception as exc:
    print(f"ERROR={exc}", file=sys.stderr)
    sys.exit(1)
