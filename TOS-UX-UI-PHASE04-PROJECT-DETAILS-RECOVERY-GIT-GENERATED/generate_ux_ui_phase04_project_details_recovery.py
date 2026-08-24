#!/usr/bin/env python3
import difflib
import hashlib
import subprocess
import sys
from pathlib import Path

TARGET_BASE_HEAD = "1a2f6ef9d5611d01f7d2bd777aab3df7f67b03a3"
TARGET_FILE = "frontend/src/pages/ProjectsPage.jsx"
EXPECTED_FAILED_PATCH_BLOB = "d38b085bc0bba0b1a1eaa21e5ab4fa2ecb0f3285"
BAD_LINE = '          <button key={id} type="button" onClick={() => setActiveTab(id)} className={cn("inline-flex min-w-[132px] items-center justify-center gap-2 rounded-[13px] px-3 py-2.5 text-xs font-black transition", activeTab === id ? "bg-white text-amber-800 shadow-sm ring-1 ring-amber-200 dark:bg-amber-300 dark:text-zinc-950 dark:ring-amber-300" : "text-zinc-500 hover:bg-white hover:text-zinc-900 dark:text-zinc-400 dark:hover:bg-white/5 dark:hover:text-white")}> '
GOOD_LINE = BAD_LINE.rstrip()


def run(cmd, cwd):
    return subprocess.check_output(cmd, cwd=cwd, text=True).strip()


def git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode()
    return hashlib.sha1(header + data).hexdigest()


def main():
    if len(sys.argv) != 3:
        print("Usage: generate_ux_ui_phase04_project_details_recovery.py <repo> <output.patch>", file=sys.stderr)
        return 2

    repo = Path(sys.argv[1]).resolve()
    output = Path(sys.argv[2]).resolve()
    target = repo / TARGET_FILE

    branch = run(["git", "branch", "--show-current"], repo)
    head = run(["git", "rev-parse", "HEAD"], repo)
    blob = run(["git", "hash-object", "--", TARGET_FILE], repo)

    if branch != "main":
        raise RuntimeError(f"BRANCH={branch}; expected main")
    if head != TARGET_BASE_HEAD:
        raise RuntimeError(f"HEAD={head}; expected {TARGET_BASE_HEAD}")
    if blob != EXPECTED_FAILED_PATCH_BLOB:
        raise RuntimeError(f"WORKTREE_BLOB={blob}; expected failed UI-04 blob {EXPECTED_FAILED_PATCH_BLOB}")

    original = target.read_text(encoding="utf-8")
    if original.count(BAD_LINE) != 1:
        raise RuntimeError(f"BAD_LINE_COUNT={original.count(BAD_LINE)}; expected 1")

    updated = original.replace(BAD_LINE, GOOD_LINE, 1)
    if updated == original:
        raise RuntimeError("NO_RECOVERY_CHANGE")

    new_blob = git_blob_sha(updated.encode("utf-8"))
    diff = list(difflib.unified_diff(
        original.splitlines(keepends=True),
        updated.splitlines(keepends=True),
        fromfile=f"a/{TARGET_FILE}",
        tofile=f"b/{TARGET_FILE}",
        n=3,
    ))
    patch = (
        f"diff --git a/{TARGET_FILE} b/{TARGET_FILE}\n"
        f"index {EXPECTED_FAILED_PATCH_BLOB[:7]}..{new_blob[:7]} 100644\n"
        + "".join(diff)
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(patch, encoding="utf-8")

    sha256 = hashlib.sha256(output.read_bytes()).hexdigest()
    print(f"TARGET_BASE_HEAD={TARGET_BASE_HEAD}")
    print(f"TARGET_FILE={TARGET_FILE}")
    print(f"EXPECTED_FAILED_PATCH_BLOB={EXPECTED_FAILED_PATCH_BLOB}")
    print(f"RECOVERED_BLOB={new_blob}")
    print("RECOVERY_SCOPE=TRAILING_WHITESPACE_ONLY")
    print("SOURCE_SCOPE=ONE_FILE")
    print("BUSINESS_LOGIC_CHANGED=NO")
    print(f"PATCH_SHA256={sha256}")
    print(f"PATCH_PATH={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
