#!/usr/bin/env python3
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

EXPECTED_HEAD = "a9be3b4b5daabbcd2505720c4df6eaf97a8fe82d"
TARGET = "frontend/src/pages/SettingsPage.jsx"
EXPECTED_BLOB = "ade8d2adca44d1821426ca020c6dc2ac5ba4a7f9"

IDENTITY_START = 'function SettingsIdentityAdmin({ user }) {'
IDENTITY_END = 'function normalizeProjectTypeImageForSettings(value = "") {'
THRS_START = 'function ThrsIntegrationAdmin({ user }) {'
THRS_END = 'function SystemBackupAdmin({ user }) {'

IDENTITY_REPLACEMENTS = [
    (
        '<Button type="button" variant="soft" onClick={exportDesignSystemDraft} disabled={busy}><DownloadCloud size={15} /> تصدير</Button>',
        '<Button type="button" variant="soft" onClick={exportDesignSystemDraft} disabled={busy}><DownloadCloud size={15} /> {identityLang === "en" ? "Export" : "تصدير"}</Button>',
    ),
    (
        '<Button type="button" variant="soft" onClick={() => designImportInputRef.current?.click()} disabled={busy}><UploadCloud size={15} /> استيراد</Button>',
        '<Button type="button" variant="soft" onClick={() => designImportInputRef.current?.click()} disabled={busy}><UploadCloud size={15} /> {identityLang === "en" ? "Import" : "استيراد"}</Button>',
    ),
]

THRS_REPLACEMENTS = [
    (
        '<Button type="button" variant="soft" onClick={loadStatus} disabled={loading}><RefreshCw size={17} className={loading ? "animate-spin" : ""} />{loading ? "جاري التحديث..." : "تحديث الحالة"}</Button>',
        '<Button type="button" variant="soft" onClick={loadStatus} disabled={loading}><RefreshCw size={17} className={loading ? "animate-spin" : ""} />{loading ? thrsText("جاري التحديث...", "Refreshing...") : thrsText("تحديث الحالة", "Refresh status")}</Button>',
    ),
]


def die(message, code=1):
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(code)


def run(args, cwd, check=True):
    p = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if p.stdout:
        print(p.stdout, end="")
    if p.stderr:
        print(p.stderr, end="", file=sys.stderr)
    if check and p.returncode:
        die(f"command failed rc={p.returncode}: {' '.join(args)}", 90)
    return p


def replace_region(text, name, start_marker, end_marker, replacements, index_start):
    start = text.find(start_marker)
    if start < 0:
        die(f"{name} start marker missing", 30)
    end = text.find(end_marker, start + len(start_marker))
    if end < 0:
        die(f"{name} end marker missing", 31)
    before = text[:start]
    region = text[start:end]
    after = text[end:]
    for offset, (old, new) in enumerate(replacements):
        idx = index_start + offset
        count = region.count(old)
        print(f"REPLACEMENT_{idx}_REGION={name}")
        print(f"REPLACEMENT_{idx}_MATCHES={count}")
        if count != 1:
            die(f"replacement {idx} in {name} expected exactly 1 match, found {count}", 40 + idx)
        region = region.replace(old, new, 1)
    return before + region + after


def main():
    if len(sys.argv) != 3:
        die("usage: generate_phase5_3_1b_settings_core_residual_v2.py REPO_ROOT OUTPUT_PATCH", 2)

    root = Path(sys.argv[1]).resolve()
    output = Path(sys.argv[2]).resolve()
    target = root / TARGET

    if not (root / ".git").is_dir():
        die("not a git repository", 3)
    if not target.is_file():
        die(f"missing target: {TARGET}", 4)

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

    raw = target.read_bytes()
    if b"\r\n" in raw:
        die("CRLF detected", 8)
    terminal_newline = raw.endswith(b"\n")
    text = raw.decode("utf-8")

    text = replace_region(text, "IDENTITY", IDENTITY_START, IDENTITY_END, IDENTITY_REPLACEMENTS, 1)
    text = replace_region(text, "THRS", THRS_START, THRS_END, THRS_REPLACEMENTS, 3)

    tmp = Path(tempfile.mkdtemp(prefix="tos-phase5-3-1b-v2-"))
    try:
        run(["git", "init", "-q"], tmp)
        run(["git", "config", "user.email", "phase5-3-1b-v2@tos.local"], tmp)
        run(["git", "config", "user.name", "TOS Phase 5.3.1b V2 Generator"], tmp)
        tmp_target = tmp / TARGET
        tmp_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(target, tmp_target)
        run(["git", "add", "--", TARGET], tmp)
        run(["git", "commit", "-qm", "exact post-5.3.1a baseline"], tmp)

        encoded = text.encode("utf-8")
        if terminal_newline and not encoded.endswith(b"\n"):
            encoded += b"\n"
        elif not terminal_newline and encoded.endswith(b"\n"):
            encoded = encoded[:-1]
        tmp_target.write_bytes(encoded)

        diff = subprocess.run(["git", "diff", "--binary", "--full-index", "--", TARGET], cwd=tmp, text=True, capture_output=True)
        if diff.returncode or not diff.stdout.strip():
            die("failed to generate patch", 60)
        output.write_text(diff.stdout, encoding="utf-8", newline="\n")
        print(f"GENERATED_PATCH_SHA256={hashlib.sha256(output.read_bytes()).hexdigest()}")

        numstat = run(["git", "apply", "--numstat", str(output)], root).stdout.strip().splitlines()
        paths = {row.split("\t")[-1] for row in numstat if row.strip()}
        if paths != {TARGET}:
            die(f"unexpected patch paths: {sorted(paths)}", 61)
        print("PARSER=PASS")
        run(["git", "apply", "--check", str(output)], root)
        print("APPLY_CHECK=PASS")
        print("GENERATION_MODE=REGION_SCOPED_FROM_EXACT_POST_5_3_1A_SOURCE")
        print("PHASE5_3_1B_SETTINGS_CORE_RESIDUAL_V2_GENERATOR=PASS")
        print(f"OUTPUT={output}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
