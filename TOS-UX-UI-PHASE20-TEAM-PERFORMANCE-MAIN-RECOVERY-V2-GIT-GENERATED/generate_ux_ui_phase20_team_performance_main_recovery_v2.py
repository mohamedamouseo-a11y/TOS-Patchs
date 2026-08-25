#!/usr/bin/env python3
import hashlib
import importlib.util
import sys
from pathlib import Path

EXPECTED_V1_BLOB = "bee62a75fa08afe17d349e08c732fb2b2ae47aeb"
EXPECTED_BASE = "d71a7ded2b0e2d6b0cb82d916f7649e88699e391"
EXPECTED_FILE = "frontend/src/pages/TeamPerformanceDashboard.jsx"
EXPECTED_TARGET_BLOB = "2639ab89d95361d2985d61b6a5e00fec18574a1b"

ANCHOR9_OLD = 'className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-xs font-black text-red-700 dark:border-red-500/20 dark:bg-red-500/10 dark:text-red-300"'
ANCHOR9_NEW = 'className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-[11px] font-black text-red-700 dark:border-red-500/20 dark:bg-red-500/10 dark:text-red-300"'
OUTER_OLD = 'className="sm:col-span-2 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-xs font-black text-red-700 dark:border-red-500/20 dark:bg-red-500/10 dark:text-red-300"'
OUTER_NEW = 'className="sm:col-span-2 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-[11px] font-black text-red-700 dark:border-red-500/20 dark:bg-red-500/10 dark:text-red-300"'


def git_blob(path):
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def main():
    if len(sys.argv) != 4:
        raise SystemExit("usage: recovery_v2.py <repo> <patch-output> <v1-generator>")

    repo, patch_output, v1_name = sys.argv[1], sys.argv[2], sys.argv[3]
    v1_path = Path(v1_name).resolve()
    if not v1_path.is_file():
        raise SystemExit(f"V1_GENERATOR_MISSING={v1_path}")

    actual_v1_blob = git_blob(v1_path)
    if actual_v1_blob != EXPECTED_V1_BLOB:
        raise SystemExit(f"V1_GENERATOR_BLOB={actual_v1_blob}; expected {EXPECTED_V1_BLOB}")

    spec = importlib.util.spec_from_file_location("ui20_v1", v1_path)
    if spec is None or spec.loader is None:
        raise SystemExit("V1_IMPORT_FAILED")
    v1 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(v1)

    if v1.TARGET_BASE_HEAD != EXPECTED_BASE:
        raise SystemExit("V1_BASE_MISMATCH")
    if v1.TARGET_FILE != EXPECTED_FILE:
        raise SystemExit("V1_TARGET_FILE_MISMATCH")
    if v1.EXPECTED_BLOB != EXPECTED_TARGET_BLOB:
        raise SystemExit("V1_TARGET_BLOB_MISMATCH")

    replacements = list(v1.REPLACEMENTS)
    old9, new9, expected9 = replacements[8]
    if (old9, new9, expected9) != (ANCHOR9_OLD, ANCHOR9_NEW, 2):
        raise SystemExit("V1_ANCHOR9_SHAPE_MISMATCH")

    replacements[8] = (ANCHOR9_OLD, ANCHOR9_NEW, 1)
    replacements.insert(9, (OUTER_OLD, OUTER_NEW, 1))
    v1.REPLACEMENTS = replacements

    sys.argv = [str(v1_path), repo, patch_output]
    v1.main()

    print("RECOVERY_V2=YES")
    print("RECOVERY_REASON=ANCHOR_9_EXPECTED_COUNT_SPLIT")
    print("V1_GENERATOR_BLOB_VERIFIED=YES")
    print("ANCHOR_9_RECOVERED=YES")
    print("OUTER_INVALID_RANGE_ANCHOR_ADDED=YES")


if __name__ == "__main__":
    main()
