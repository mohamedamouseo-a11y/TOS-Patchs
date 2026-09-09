#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

PATCH = "TOS-RAMZY-SMART-TASK-COMPOSER-V1-GIT-GENERATED"
REVISION = "R2"
REPO = Path("/var/www/TOS")
TARGET = REPO / "frontend/src/components/RamzyAssistant.jsx"
EXPECTED_HEAD = "048592147387e2b49382f605a04f8d2efd64f61c"
EXPECTED_TARGET_BLOB = "509c40b4f283d39fb50e7e2dc146797392d6d1ca"
OLD_BASELINE = "db1efe2ccf30552ab7c65f7bc672861adf66cc05"
BASE_RUNNER_URL = "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-RAMZY-SMART-TASK-COMPOSER-V1-GIT-GENERATED/run_ramzy_smart_task_composer_v1.py"


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


def main():
    print(f"PATCH={PATCH}")
    print(f"RUNNER_REVISION={REVISION}")

    head = run(["git", "-C", str(REPO), "rev-parse", "HEAD"]).stdout.strip()
    print(f"HEAD={head}")
    if head != EXPECTED_HEAD:
        raise RuntimeError(f"BASELINE_MISMATCH expected={EXPECTED_HEAD} actual={head}")

    if not TARGET.exists():
        raise RuntimeError(f"TARGET_MISSING={TARGET}")
    current_blob = blob_sha(TARGET)
    print(f"TARGET_BLOB={current_blob}")
    if current_blob != EXPECTED_TARGET_BLOB:
        raise RuntimeError(
            f"TARGET_BLOB_MISMATCH expected={EXPECTED_TARGET_BLOB} actual={current_blob}"
        )

    with urllib.request.urlopen(BASE_RUNNER_URL, timeout=30) as response:
        source = response.read().decode("utf-8")

    count = source.count(OLD_BASELINE)
    if count != 1:
        raise RuntimeError(f"BASE_RUNNER_BASELINE_ANCHOR_COUNT={count}")
    source = source.replace(OLD_BASELINE, EXPECTED_HEAD, 1)

    compile(source, "run_ramzy_smart_task_composer_v1_r2_generated.py", "exec")

    tmp = Path(tempfile.gettempdir()) / "run_ramzy_smart_task_composer_v1_r2_generated.py"
    tmp.write_text(source, encoding="utf-8")
    result = run([sys.executable, str(tmp)], check=False)

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
