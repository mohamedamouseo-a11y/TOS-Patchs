#!/usr/bin/env python3
import hashlib
import subprocess
import sys
import urllib.request
from pathlib import Path

TARGET_BASE_HEAD = "4dba25831fe42efbb0ac0e8f5feeb1e313c113fb"
TARGET_FILE = "frontend/src/pages/ProjectsPage.jsx"
EXPECTED_BLOB = "422db477233617b335698574f161ccb5c262c0f5"
ORIGINAL_BASE_HEAD = "2ecd378d422726d45299e4353b4a9fc30e983207"
PINNED_SOURCE_URL = "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/4acd19ffea1a3a92152b35992a704cc4f9a00be8/TOS-UX-UI-PHASE05-PROJECT-CREATE-GIT-GENERATED/generate_ux_ui_phase05_project_create.py"


def run(cmd, cwd):
    return subprocess.check_output(cmd, cwd=cwd, text=True).strip()


def main():
    if len(sys.argv) != 3:
        print("Usage: generate_ux_ui_phase05_project_create_rebased.py <repo> <output.patch>", file=sys.stderr)
        return 2

    repo = Path(sys.argv[1]).resolve()
    output = Path(sys.argv[2]).resolve()

    branch = run(["git", "branch", "--show-current"], repo)
    head = run(["git", "rev-parse", "HEAD"], repo)
    blob = run(["git", "hash-object", "--", TARGET_FILE], repo)

    if branch != "main":
        raise RuntimeError(f"BRANCH={branch}; expected main")
    if head != TARGET_BASE_HEAD:
        raise RuntimeError(f"HEAD={head}; expected {TARGET_BASE_HEAD}")
    if blob != EXPECTED_BLOB:
        raise RuntimeError(f"BLOB={blob}; expected {EXPECTED_BLOB}")

    with urllib.request.urlopen(PINNED_SOURCE_URL, timeout=30) as response:
        source = response.read().decode("utf-8")

    old_line = f'TARGET_BASE_HEAD = "{ORIGINAL_BASE_HEAD}"'
    new_line = f'TARGET_BASE_HEAD = "{TARGET_BASE_HEAD}"'
    if source.count(old_line) != 1:
        raise RuntimeError(f"PINNED_BASE_ANCHOR_COUNT={source.count(old_line)}; expected 1")

    rebased = source.replace(old_line, new_line, 1)
    if rebased.count(EXPECTED_BLOB) < 1:
        raise RuntimeError("EXPECTED_BLOB_NOT_PRESENT_IN_PINNED_GENERATOR")

    tmp = Path("/var/tmp/tos_ui05_rebased_inner_generator.py")
    tmp.write_text(rebased, encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, str(tmp), str(repo), str(output)],
        text=True,
        capture_output=True,
    )
    if completed.stdout:
        print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, file=sys.stderr, end="")
    if completed.returncode != 0:
        return completed.returncode

    if not output.is_file() or output.stat().st_size == 0:
        raise RuntimeError("PATCH_NOT_CREATED")

    patch_text = output.read_text(encoding="utf-8")
    expected_diff = f"diff --git a/{TARGET_FILE} b/{TARGET_FILE}"
    if patch_text.count(expected_diff) != 1:
        raise RuntimeError("PATCH_SCOPE_INVALID")
    if patch_text.count("diff --git ") != 1:
        raise RuntimeError("PATCH_HAS_MULTIPLE_FILES")

    for line_no, line in enumerate(patch_text.splitlines(), start=1):
        if line.rstrip() != line:
            raise RuntimeError(f"PATCH_TRAILING_WHITESPACE_LINE={line_no}")

    sha256 = hashlib.sha256(output.read_bytes()).hexdigest()
    print(f"REBASED_FROM_BASE_HEAD={ORIGINAL_BASE_HEAD}")
    print(f"TARGET_BASE_HEAD={TARGET_BASE_HEAD}")
    print(f"TARGET_FILE={TARGET_FILE}")
    print(f"EXPECTED_BLOB={EXPECTED_BLOB}")
    print("REBASE_REASON=PROFILE_HOTFIX_CHANGED_HEAD_ONLY")
    print("PROJECTS_SOURCE_CHANGED_BY_HOTFIX=NO")
    print("SOURCE_SCOPE=ONE_FILE")
    print("CREATE_SCOPE=PROJECT_CREATE_WIZARD_ONLY")
    print("BUSINESS_LOGIC_CHANGED=NO")
    print("API_CALLS_CHANGED=NO")
    print("ROUTES_CHANGED=NO")
    print(f"PATCH_SHA256={sha256}")
    print(f"PATCH_PATH={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
