#!/usr/bin/env python3
import hashlib
import sys
import urllib.request

PATCH = "TOS-TWS-TDOCS-PHASE-2-R3-JS-ESCAPE-BUILD-FIX"
UPSTREAM_URL = "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-TWS-TDOCS-PHASE-2-GOOGLE-DOCS-MENU-CORE-EDITING-PARITY/run_tdocs_phase2.py"
EXPECTED_UPSTREAM_BLOB = "000eb0db54ac80650a438af173a2422e0ecd53e4"

BROKEN_SYNTAX = b'        if (REPO / candidate in []:\n            pass\n'
OLD_BASELINE = b'BASELINE = "509c51eeab1a9b880d902aac5082aa6124996c9b"'
NEW_BASELINE = b'BASELINE = "db1efe2ccf30552ab7c65f7bc672861adf66cc05"'

SHORTCUT_OLD = br'    window.alert("T-Docs shortcuts\nCtrl+B Bold · Ctrl+I Italic · Ctrl+U Underline · Ctrl+H Find/Replace · Ctrl+K Link · Ctrl+Enter Page break · Ctrl+Shift+7 Numbered list · Ctrl+Shift+8 Bulleted list · Ctrl+S Save named version");'
SHORTCUT_NEW = br'    window.alert("T-Docs shortcuts\\nCtrl+B Bold · Ctrl+I Italic · Ctrl+U Underline · Ctrl+H Find/Replace · Ctrl+K Link · Ctrl+Enter Page break · Ctrl+Shift+7 Numbered list · Ctrl+Shift+8 Bulleted list · Ctrl+S Save named version");'

REGEX_OLD = br'    const escaped = query.replace(/[.*+?^${}()|[\\]\\\\]/g, "\\$&");'
REGEX_NEW = br'    const escaped = query.replace(/[.*+?^${}()|[\\]\\\\]/g, "\\\\$&");'


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "TOS-patch-runner-r3"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def replace_exact(data: bytes, old: bytes, new: bytes, label: str) -> bytes:
    count = data.count(old)
    if count != 1:
        raise RuntimeError(f"{label}_ANCHOR_COUNT:{count}")
    return data.replace(old, new, 1)


try:
    upstream = download(UPSTREAM_URL)
    actual = git_blob_sha(upstream)
    if actual != EXPECTED_UPSTREAM_BLOB:
        raise RuntimeError(f"UPSTREAM_INTEGRITY_MISMATCH:{actual}")

    fixed = replace_exact(upstream, BROKEN_SYNTAX, b"", "BROKEN_SYNTAX")
    fixed = replace_exact(fixed, OLD_BASELINE, NEW_BASELINE, "BASELINE")
    fixed = replace_exact(fixed, SHORTCUT_OLD, SHORTCUT_NEW, "SHORTCUT_ESCAPE")
    fixed = replace_exact(fixed, REGEX_OLD, REGEX_NEW, "REGEX_ESCAPE")

    code = compile(fixed.decode("utf-8"), "run_tdocs_phase2_r3_fixed.py", "exec")

    print(f"PATCH={PATCH}")
    print("UPSTREAM_INTEGRITY=PASS")
    print("RUNNER_SYNTAX_FIX=PASS")
    print("LATEST_BASELINE_REBASE=PASS")
    print("JS_SHORTCUT_ESCAPE_FIX=PASS")
    print("FIND_REPLACE_REGEX_ESCAPE_FIX=PASS")
    print("EXPECTED_HEAD=db1efe2ccf30552ab7c65f7bc672861adf66cc05")
    print("ORIGINAL_PHASE_RUNNER=EXECUTING")

    namespace = {
        "__name__": "__main__",
        "__file__": "run_tdocs_phase2_r3_fixed.py",
    }
    exec(code, namespace, namespace)
except SystemExit:
    raise
except Exception as exc:
    print(f"ERROR={exc}", file=sys.stderr)
    sys.exit(1)
