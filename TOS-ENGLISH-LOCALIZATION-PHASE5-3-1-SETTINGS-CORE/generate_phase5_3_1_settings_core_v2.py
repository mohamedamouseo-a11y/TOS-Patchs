#!/usr/bin/env python3
import hashlib
import importlib.util
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BASE_GENERATOR = SCRIPT_DIR / "generate_phase5_3_1_settings_core.py"

spec = importlib.util.spec_from_file_location("phase531_base", BASE_GENERATOR)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

EXPECTED_HEAD = base.EXPECTED_HEAD
TARGET = base.TARGET
EXPECTED_BLOB = base.EXPECTED_BLOB
REPLACEMENTS = base.REPLACEMENTS

REGIONS = [
    (
        "GOOGLE_DRIVE",
        "function GoogleDriveAdmin({ user }) {",
        "function formatBackupBytes(value)",
        REPLACEMENTS[0:24],
    ),
    (
        "THRS",
        "function ThrsIntegrationAdmin({ user }) {",
        "function SystemBackupAdmin({ user }) {",
        REPLACEMENTS[24:49],
    ),
    (
        "IDENTITY",
        "function SettingsIdentityAdmin({ user }) {",
        "function normalizeProjectTypeImageForSettings(value = \"\") {",
        REPLACEMENTS[49:],
    ),
]


def die(message, code=1):
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(code)


def run(args, cwd, check=True):
    proc = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, end="", file=sys.stderr)
    if check and proc.returncode:
        die(f"command failed rc={proc.returncode}: {' '.join(args)}", 90)
    return proc


def sha256(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_in_region(text, region_name, start_marker, end_marker, replacements, start_index):
    start = text.find(start_marker)
    if start < 0:
        die(f"{region_name} start marker missing", 40)
    end = text.find(end_marker, start + len(start_marker))
    if end < 0:
        die(f"{region_name} end marker missing", 41)

    before = text[:start]
    region = text[start:end]
    after = text[end:]

    for offset, (old, new, expected_count) in enumerate(replacements):
        replacement_number = start_index + offset
        count = region.count(old)
        print(f"REPLACEMENT_{replacement_number}_REGION={region_name}")
        print(f"REPLACEMENT_{replacement_number}_MATCHES={count}")
        if count != expected_count:
            die(
                f"replacement {replacement_number} in {region_name} expected {expected_count} exact matches, found {count}",
                100 + replacement_number,
            )
        region = region.replace(old, new)

    return before + region + after


def main():
    if len(sys.argv) != 3:
        die("usage: generate_phase5_3_1_settings_core_v2.py REPO_ROOT OUTPUT_PATCH", 2)

    root = Path(sys.argv[1]).resolve()
    output = Path(sys.argv[2]).resolve()
    target = root / TARGET

    if not (root / ".git").is_dir():
        die(f"not a git repository: {root}", 3)
    if not target.is_file():
        die(f"target missing: {TARGET}", 4)

    head = run(["git", "rev-parse", "HEAD"], root).stdout.strip()
    print(f"HEAD={head}")
    if head != EXPECTED_HEAD:
        die(f"HEAD mismatch expected={EXPECTED_HEAD} actual={head}", 5)

    blob = run(["git", "hash-object", TARGET], root).stdout.strip()
    print(f"SOURCE_BLOB={blob}")
    if blob != EXPECTED_BLOB:
        die(f"blob mismatch expected={EXPECTED_BLOB} actual={blob}", 6)

    if run(["git", "diff", "--cached", "--", TARGET], root).stdout.strip():
        die("target has staged changes", 7)
    if run(["git", "diff", "--", TARGET], root).stdout.strip():
        die("target has tracked local changes", 8)
    print("TARGET_CLEAN=YES")

    raw = target.read_bytes()
    if b"\r\n" in raw:
        die("CRLF source detected", 9)
    terminal_newline = raw.endswith(b"\n")
    text = raw.decode("utf-8")

    next_index = 1
    for region_name, start_marker, end_marker, replacements in REGIONS:
        text = replace_in_region(text, region_name, start_marker, end_marker, replacements, next_index)
        next_index += len(replacements)

    if next_index - 1 != len(REPLACEMENTS):
        die(f"replacement partition mismatch applied={next_index - 1} total={len(REPLACEMENTS)}", 42)

    tmp = Path(tempfile.mkdtemp(prefix="tos-phase5-3-1-settings-core-v2-"))
    try:
        run(["git", "init", "-q"], tmp)
        run(["git", "config", "user.email", "phase5-3-1-v2@tos.local"], tmp)
        run(["git", "config", "user.name", "TOS Phase 5.3.1 V2 Generator"], tmp)
        tmp_target = tmp / TARGET
        tmp_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(target, tmp_target)
        run(["git", "add", "--", TARGET], tmp)
        run(["git", "commit", "-qm", "exact live baseline"], tmp)

        encoded = text.encode("utf-8")
        if terminal_newline and not encoded.endswith(b"\n"):
            encoded += b"\n"
        elif not terminal_newline and encoded.endswith(b"\n"):
            encoded = encoded[:-1]
        tmp_target.write_bytes(encoded)

        proc = subprocess.run(
            ["git", "diff", "--binary", "--full-index", "--", TARGET],
            cwd=tmp,
            text=True,
            capture_output=True,
        )
        if proc.returncode:
            die(f"git diff failed rc={proc.returncode}", 80)
        if not proc.stdout.strip():
            die("generated patch is empty", 81)
        output.write_text(proc.stdout, encoding="utf-8", newline="\n")
        print(f"GENERATED_PATCH_SHA256={sha256(output)}")

        numstat = run(["git", "apply", "--numstat", str(output)], root).stdout.strip().splitlines()
        paths = {row.split("\t")[-1] for row in numstat if row.strip()}
        if paths != {TARGET}:
            die(f"unexpected patch paths: {sorted(paths)}", 82)
        print("PARSER=PASS")
        run(["git", "apply", "--check", str(output)], root)
        print("APPLY_CHECK=PASS")
        print("GENERATION_MODE=REGION_SCOPED_GIT_DIFF_FROM_EXACT_LIVE_SOURCE")
        print("PHASE5_3_1_SETTINGS_CORE_V2_GENERATOR=PASS")
        print(f"OUTPUT={output}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
