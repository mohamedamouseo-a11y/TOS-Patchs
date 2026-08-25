#!/usr/bin/env python3
import hashlib
import importlib.util
import sys
from pathlib import Path

EXPECTED_BASE = "d71a7ded2b0e2d6b0cb82d916f7649e88699e391"
EXPECTED_FILE = "frontend/src/pages/TeamPerformanceDashboard.jsx"
EXPECTED_TARGET_BLOB = "2639ab89d95361d2985d61b6a5e00fec18574a1b"
EXPECTED_V1_BLOB = "bee62a75fa08afe17d349e08c732fb2b2ae47aeb"
EXPECTED_V2_BLOB = "97fd934ddd7975ff32a5bf0f680ce00ecab90a45"
EXPECTED_V2_PATCH_SHA256 = "a38a0c42788ee1bf449d2b1a4edb4afce8a547a131688b75a33a60eee00f0614"


def git_blob(path):
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"IMPORT_FAILED={path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    if len(sys.argv) != 5:
        raise SystemExit("usage: recovery_v3.py <repo> <patch-output> <v1-generator> <v2-generator>")

    repo = Path(sys.argv[1]).resolve()
    final_patch = Path(sys.argv[2]).resolve()
    v1_path = Path(sys.argv[3]).resolve()
    v2_path = Path(sys.argv[4]).resolve()

    if not v1_path.is_file():
        raise SystemExit(f"V1_GENERATOR_MISSING={v1_path}")
    if not v2_path.is_file():
        raise SystemExit(f"V2_GENERATOR_MISSING={v2_path}")

    v1_blob = git_blob(v1_path)
    v2_blob = git_blob(v2_path)
    if v1_blob != EXPECTED_V1_BLOB:
        raise SystemExit(f"V1_GENERATOR_BLOB={v1_blob}; expected {EXPECTED_V1_BLOB}")
    if v2_blob != EXPECTED_V2_BLOB:
        raise SystemExit(f"V2_GENERATOR_BLOB={v2_blob}; expected {EXPECTED_V2_BLOB}")

    v2 = load_module("ui20_recovery_v2", v2_path)

    if getattr(v2, "EXPECTED_BASE", None) != EXPECTED_BASE:
        raise SystemExit("V2_BASE_MISMATCH")
    if getattr(v2, "EXPECTED_FILE", None) != EXPECTED_FILE:
        raise SystemExit("V2_TARGET_FILE_MISMATCH")
    if getattr(v2, "EXPECTED_TARGET_BLOB", None) != EXPECTED_TARGET_BLOB:
        raise SystemExit("V2_TARGET_BLOB_MISMATCH")
    if getattr(v2, "EXPECTED_V1_BLOB", None) != EXPECTED_V1_BLOB:
        raise SystemExit("V2_V1_BLOB_MISMATCH")

    raw_patch = final_patch.with_suffix(final_patch.suffix + ".v2-raw")
    if raw_patch.exists():
        raw_patch.unlink()
    if final_patch.exists():
        final_patch.unlink()

    original_argv = list(sys.argv)
    try:
        sys.argv = [str(v2_path), str(repo), str(raw_patch), str(v1_path)]
        v2.main()
    finally:
        sys.argv = original_argv

    if not raw_patch.is_file():
        raise SystemExit("V2_RAW_PATCH_MISSING")

    raw_bytes = raw_patch.read_bytes()
    raw_sha = sha256_bytes(raw_bytes)
    if raw_sha != EXPECTED_V2_PATCH_SHA256:
        raise SystemExit(f"V2_RAW_PATCH_SHA256={raw_sha}; expected {EXPECTED_V2_PATCH_SHA256}")

    raw_text = raw_bytes.decode("utf-8")
    expected_old_header = f"--- a/{EXPECTED_FILE}\n+++ b/{EXPECTED_FILE}\n"
    if not raw_text.startswith(expected_old_header):
        raise SystemExit("V2_UNIFIED_HEADER_MISMATCH")
    if raw_text.startswith("diff --git "):
        raise SystemExit("V2_ALREADY_HAS_GIT_HEADER")

    git_header = f"diff --git a/{EXPECTED_FILE} b/{EXPECTED_FILE}\n"
    final_text = git_header + raw_text
    final_patch.parent.mkdir(parents=True, exist_ok=True)
    final_patch.write_text(final_text, encoding="utf-8")

    scope_lines = [line for line in final_text.splitlines() if line.startswith("diff --git ")]
    expected_scope = f"diff --git a/{EXPECTED_FILE} b/{EXPECTED_FILE}"
    if scope_lines != [expected_scope]:
        raise SystemExit(f"FINAL_SCOPE_HEADER_MISMATCH={scope_lines!r}")

    final_sha = hashlib.sha256(final_text.encode("utf-8")).hexdigest()

    print("RECOVERY_V3=YES")
    print("RECOVERY_V3_REASON=PATCH_ENVELOPE_GIT_HEADER_MISSING")
    print("V1_GENERATOR_BLOB_VERIFIED=YES")
    print("V2_GENERATOR_BLOB_VERIFIED=YES")
    print("V2_RAW_PATCH_SHA256_VERIFIED=YES")
    print("V2_REPLACEMENTS_CHANGED=NO")
    print("V2_BEHAVIOR_GUARDS_CHANGED=NO")
    print("PATCH_CONTENT_HUNKS_CHANGED=NO")
    print("PATCH_GIT_HEADER_ADDED=YES")
    print("PATCH_SCOPE_HEADER_COUNT=1")
    print(f"PATCH_SCOPE_HEADER={expected_scope}")
    print(f"V2_RAW_PATCH_SHA256={raw_sha}")
    print(f"FINAL_PATCH_SHA256={final_sha}")
    print(f"FINAL_PATCH_PATH={final_patch}")


if __name__ == "__main__":
    main()
