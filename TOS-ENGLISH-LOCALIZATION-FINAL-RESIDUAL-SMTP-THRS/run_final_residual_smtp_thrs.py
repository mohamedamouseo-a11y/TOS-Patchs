#!/usr/bin/env python3
from __future__ import annotations

import py_compile
import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
    patch_out = Path(sys.argv[2] if len(sys.argv) > 2 else "/var/tmp/TOS_FINAL_RESIDUAL_SMTP_THRS.patch").resolve()
    generator = Path(__file__).with_name("generate_final_residual_smtp_thrs.py")

    py_compile.compile(str(generator), doraise=True)
    print("FINAL_SMTP_THRS_GENERATOR_COMPILE=PASS")

    subprocess.run([sys.executable, str(generator), str(repo), str(patch_out)], check=True)
    subprocess.run(["git", "-C", str(repo), "apply", "--check", str(patch_out)], check=True)
    print("FINAL_SMTP_THRS_RUNNER=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
