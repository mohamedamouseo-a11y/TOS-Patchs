#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

PATCH = "TOS-RAMZY-CONTEXTUAL-SMART-TASK-V1-GIT-GENERATED"
REVISION = "R2"
REPO = Path("/var/www/TOS")
SOURCE = REPO / "frontend/src/components/RamzyAssistant.jsx"
CSS = REPO / "frontend/src/components/ramzySmartTaskComposerV1.css"
SOURCE_REL = "frontend/src/components/RamzyAssistant.jsx"
CSS_REL = "frontend/src/components/ramzySmartTaskComposerV1.css"
EXPECTED_HEAD = "6d23d9f5ef56856cd87ea671d1b11e474e3a39b7"
EXPECTED_SOURCE_BLOB = "f9210e68d6faa72112f7846a80dda3652dbdd60f"
EXPECTED_CSS_BLOB = "18ac594a6db8d5f919c39405e2ee4f5824056eeb"
OLD_HEAD = "048592147387e2b49382f605a04f8d2efd64f61c"
BASE_RUNNER_URL = "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-RAMZY-CONTEXTUAL-SMART-TASK-V1-GIT-GENERATED/run_ramzy_contextual_smart_task_v1.py"


def run(cmd, check=True):
    result = subprocess.run(cmd, text=True, capture_output=True)
    if check and result.returncode:
        raise RuntimeError(
            f"Command failed ({result.returncode}): {' '.join(cmd)}\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    return result


def blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def replace_once(source: str, old: str, new: str, label: str) -> str:
    count = source.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one anchor, found {count}")
    return source.replace(old, new, 1)


def main():
    print(f"PATCH={PATCH}")
    print(f"RUNNER_REVISION={REVISION}")

    head = run(["git", "-C", str(REPO), "rev-parse", "HEAD"]).stdout.strip()
    print(f"HEAD={head}")
    if head != EXPECTED_HEAD:
        raise RuntimeError(f"BASELINE_MISMATCH expected={EXPECTED_HEAD} actual={head}")

    if not SOURCE.exists() or not CSS.exists():
        raise RuntimeError("SMART_TASK_V1_FILES_MISSING")

    source_blob = blob_sha(SOURCE)
    css_blob = blob_sha(CSS)
    print(f"SOURCE_BLOB={source_blob}")
    print(f"SMART_TASK_CSS_BLOB={css_blob}")
    if source_blob != EXPECTED_SOURCE_BLOB:
        raise RuntimeError(f"SOURCE_BLOB_MISMATCH expected={EXPECTED_SOURCE_BLOB} actual={source_blob}")
    if css_blob != EXPECTED_CSS_BLOB:
        raise RuntimeError(f"SMART_TASK_CSS_STATE_MISMATCH expected={EXPECTED_CSS_BLOB} actual={css_blob}")

    source_status = run(["git", "-C", str(REPO), "status", "--porcelain", "--", SOURCE_REL]).stdout.strip()
    css_status = run(["git", "-C", str(REPO), "status", "--porcelain", "--", CSS_REL]).stdout.strip()
    if source_status or css_status:
        raise RuntimeError(
            "SMART_TASK_TARGETS_NOT_CLEAN "
            f"source_dirty={bool(source_status)} css_dirty={bool(css_status)}"
        )

    with urllib.request.urlopen(BASE_RUNNER_URL, timeout=30) as response:
        runner = response.read().decode("utf-8")

    runner = replace_once(
        runner,
        f'EXPECTED_HEAD = "{OLD_HEAD}"',
        f'EXPECTED_HEAD = "{EXPECTED_HEAD}"',
        "baseline",
    )

    old_pre = '''    pre_status = set(git("status", "--porcelain").stdout.splitlines())
    pre_names = status_paths()
    if SOURCE_REL not in pre_names or CSS_REL not in pre_names:
        raise RuntimeError(
            f"SMART_TASK_V1_DIRTY_STATE_MISSING source={SOURCE_REL in pre_names} css={CSS_REL in pre_names}"
        )
'''
    new_pre = '''    pre_status = set(git("status", "--porcelain").stdout.splitlines())
    pre_names = status_paths()
    if SOURCE_REL in pre_names or CSS_REL in pre_names:
        raise RuntimeError(
            f"SMART_TASK_TARGETS_NOT_CLEAN source={SOURCE_REL in pre_names} css={CSS_REL in pre_names}"
        )
'''
    runner = replace_once(runner, old_pre, new_pre, "clean target precheck")

    old_post = '''        post_names = status_paths()
        if post_names != pre_names:
            raise RuntimeError(
                f"DIRTY_PATH_SET_CHANGED before={sorted(pre_names)} after={sorted(post_names)}"
            )
        post_status = set(git("status", "--porcelain").stdout.splitlines())
'''
    new_post = '''        post_names = status_paths()
        expected_post_names = pre_names | {SOURCE_REL, CSS_REL}
        if post_names != expected_post_names:
            raise RuntimeError(
                f"DIRTY_PATH_SET_CHANGED expected={sorted(expected_post_names)} after={sorted(post_names)}"
            )
        post_status = set(git("status", "--porcelain").stdout.splitlines())
'''
    runner = replace_once(runner, old_post, new_post, "post-patch dirty set")

    compile(runner, "run_ramzy_contextual_smart_task_v1_r2_generated.py", "exec")

    temp = Path(tempfile.gettempdir()) / "run_ramzy_contextual_smart_task_v1_r2_generated.py"
    temp.write_text(runner, encoding="utf-8")
    result = run([sys.executable, str(temp)], check=False)

    if result.stdout:
        print(result.stdout, end="" if result.stdout.endswith("\n") else "\n")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="" if result.stderr.endswith("\n") else "\n")
    sys.exit(result.returncode)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("PASS_FAIL=FAIL")
        print(f"ERROR={exc}")
        sys.exit(1)
