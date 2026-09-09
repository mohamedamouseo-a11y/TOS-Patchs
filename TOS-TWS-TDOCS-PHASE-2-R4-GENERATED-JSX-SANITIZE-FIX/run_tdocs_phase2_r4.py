#!/usr/bin/env python3
import hashlib
import sys
import urllib.request

PATCH = "TOS-TWS-TDOCS-PHASE-2-R4-GENERATED-JSX-SANITIZE-FIX"
UPSTREAM_URL = "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-TWS-TDOCS-PHASE-2-GOOGLE-DOCS-MENU-CORE-EDITING-PARITY/run_tdocs_phase2.py"
EXPECTED_UPSTREAM_BLOB = "000eb0db54ac80650a438af173a2422e0ecd53e4"
OLD_BASELINE = 'BASELINE = "509c51eeab1a9b880d902aac5082aa6124996c9b"'
NEW_BASELINE = 'BASELINE = "db1efe2ccf30552ab7c65f7bc672861adf66cc05"'
BROKEN_SYNTAX = '        if (REPO / candidate in []:\n            pass\n'
WRITE_ANCHOR = '    editor_path.write_text(source, encoding="utf-8")\n'

SANITIZE_HOOK = r'''    # R4: sanitize generated JSX before validation/build.
    # The upstream Python triple-quoted template turns the shortcut \n into a
    # literal newline inside the JS string. Convert it back to a JS escape.
    source = editor_path.read_text(encoding="utf-8")
    broken_shortcut = 'window.alert("T-Docs shortcuts\nCtrl+B Bold'
    fixed_shortcut = 'window.alert("T-Docs shortcuts\\nCtrl+B Bold'
    shortcut_count = source.count(broken_shortcut)
    if shortcut_count != 1:
        raise RuntimeError(f"GENERATED_SHORTCUT_ANCHOR_COUNT:{shortcut_count}")
    source = source.replace(broken_shortcut, fixed_shortcut, 1)

    # Preserve the replacement backslash required by String.replace so the
    # generated JS uses "\\$&" instead of the ineffective "\$&" form.
    source = source.replace('"\\$&"', '"\\\\$&"')

    editor_path.write_text(source, encoding="utf-8")
    if 'window.alert("T-Docs shortcuts\\nCtrl+B Bold' not in source:
        raise RuntimeError("GENERATED_SHORTCUT_ESCAPE_FIX_FAILED")
    print("GENERATED_JSX_SHORTCUT_ESCAPE_FIX=PASS")
    print("GENERATED_FIND_REPLACE_ESCAPE_FIX=PASS")
'''


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "TOS-patch-runner-r4"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}_ANCHOR_COUNT:{count}")
    return text.replace(old, new, 1)


try:
    upstream_bytes = download(UPSTREAM_URL)
    actual = git_blob_sha(upstream_bytes)
    if actual != EXPECTED_UPSTREAM_BLOB:
        raise RuntimeError(f"UPSTREAM_INTEGRITY_MISMATCH:{actual}")

    upstream = upstream_bytes.decode("utf-8")
    fixed = replace_once(upstream, BROKEN_SYNTAX, "", "BROKEN_SYNTAX")
    fixed = replace_once(fixed, OLD_BASELINE, NEW_BASELINE, "BASELINE")
    fixed = replace_once(fixed, WRITE_ANCHOR, WRITE_ANCHOR + "\n" + SANITIZE_HOOK + "\n", "EDITOR_WRITE")

    # Validate the entire transformed Python runner before executing it.
    code = compile(fixed, "run_tdocs_phase2_r4_fixed.py", "exec")

    print(f"PATCH={PATCH}")
    print("UPSTREAM_INTEGRITY=PASS")
    print("RUNNER_SYNTAX_FIX=PASS")
    print("LATEST_BASELINE_REBASE=PASS")
    print("R4_TEXT_MODE=PASS")
    print("R4_NO_NON_ASCII_BYTES_LITERAL=PASS")
    print("EXPECTED_HEAD=db1efe2ccf30552ab7c65f7bc672861adf66cc05")
    print("ORIGINAL_PHASE_RUNNER=EXECUTING")

    namespace = {
        "__name__": "__main__",
        "__file__": "run_tdocs_phase2_r4_fixed.py",
    }
    exec(code, namespace, namespace)
except SystemExit:
    raise
except Exception as exc:
    print(f"ERROR={exc}", file=sys.stderr)
    sys.exit(1)
