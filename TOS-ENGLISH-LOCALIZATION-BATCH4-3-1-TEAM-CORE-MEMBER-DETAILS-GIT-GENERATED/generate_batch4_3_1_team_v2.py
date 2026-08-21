#!/usr/bin/env python3
import subprocess
import sys
import tempfile
from pathlib import Path

EXPECTED_ORIGINAL_BLOB = "fd08b7f4f55f452fb2f837261627324a77a33c41"
OLD = "    ('>القسم</div>', '>{teamText(\"القسم\", \"Department\", lang)}</div>', 2),"
NEW = "    ('>القسم</div>', '>{teamText(\"القسم\", \"Department\", lang)}</div>', 1),"


def die(message, code=1):
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(code)


def run(args, **kwargs):
    proc = subprocess.run(args, text=True, capture_output=True, **kwargs)
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)
    return proc


def main():
    if len(sys.argv) != 4:
        die("usage: generate_batch4_3_1_team_v2.py ORIGINAL_GENERATOR REPO_ROOT OUTPUT_PATCH", 2)

    original = Path(sys.argv[1]).resolve()
    root = Path(sys.argv[2]).resolve()
    patch = Path(sys.argv[3]).resolve()

    if not original.is_file():
        die(f"original generator missing: {original}", 3)

    blob = subprocess.run(["git", "hash-object", str(original)], text=True, capture_output=True)
    if blob.returncode:
        die("could not hash original generator", 4)
    actual_blob = blob.stdout.strip()
    print(f"ORIGINAL_GENERATOR_BLOB={actual_blob}")
    if actual_blob != EXPECTED_ORIGINAL_BLOB:
        die(f"original generator blob mismatch expected={EXPECTED_ORIGINAL_BLOB} actual={actual_blob}", 5)

    source = original.read_text(encoding="utf-8")
    count = source.count(OLD)
    print(f"V2_REPAIR_MATCHES={count}")
    if count != 1:
        die(f"expected exactly one replacement-11 expectation line, found {count}", 6)

    corrected = source.replace(OLD, NEW)
    tmp = Path(tempfile.mkdtemp(prefix="tos-batch4-3-1-v2-")) / "generate_batch4_3_1_team_corrected.py"
    tmp.write_text(corrected, encoding="utf-8", newline="\n")

    compile_proc = run([sys.executable, "-m", "py_compile", str(tmp)])
    if compile_proc.returncode:
        die("corrected generator compile failed", 7)
    print("CORRECTED_GENERATOR_COMPILE=PASS")
    print("GENERATOR_V2_REPAIR=PASS")

    proc = subprocess.run([sys.executable, str(tmp), str(root), str(patch)], text=True)
    raise SystemExit(proc.returncode)


if __name__ == "__main__":
    main()
