#!/usr/bin/env python3
from pathlib import Path
import hashlib
import subprocess
import sys
import tempfile
import urllib.request

BASE_RUNNER = "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-TWS-GOOGLE-SHEETS-PHASE-1-EXCEL-XLSX-FIDELITY/run_phase1.py"
EXPECTED_HEAD = "a442ff075526235775013ca64f7f34543e43880e"
ALLOWED_DASHBOARD_DIRTY = {
    "frontend/src/pages/tws/TwsDashboard.jsx",
    "frontend/src/pages/tws/twsDashboardFlagshipV1_1DarkFidelity.css",
    "frontend/src/pages/tws/twsDashboardFlagshipV2LuxuryPolish.css",
}
PHASE1_PATHS = {
    "backend/src/routes/workspace.routes.js",
    "backend/src/services/workspace.service.js",
    "backend/src/utils/workspaceExport.js",
    "backend/src/utils/workspaceXlsx.js",
    "backend/src/utils/workspaceXlsx.phase1.test.js",
    "frontend/src/lib/api.js",
    "frontend/src/pages/tws/TSheetsEditor.jsx",
}


def run(cmd, cwd, *, check=True):
    p = subprocess.run(cmd, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    if check and p.returncode != 0:
        raise RuntimeError(f"command failed ({p.returncode}): {' '.join(cmd)}\n{p.stdout}")
    return p


def git(repo, *args, check=True):
    return run(["git", *args], repo, check=check)


def raw_status(repo):
    p = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
        cwd=repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if p.returncode != 0:
        raise RuntimeError(p.stdout.decode("utf-8", "replace"))
    records = []
    parts = p.stdout.split(b"\0")
    i = 0
    while i < len(parts):
        raw = parts[i]
        i += 1
        if not raw:
            continue
        text = raw.decode("utf-8", "replace")
        status = text[:2]
        path = text[3:]
        if "R" in status or "C" in status:
            raise RuntimeError(f"rename/copy working-tree state is not supported: {text}")
        records.append((status, path))
    return records


def file_sha256(path):
    if not path.is_file():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def allowed_snapshot(repo, records):
    out = {}
    for status, rel in records:
        if rel in ALLOWED_DASHBOARD_DIRTY:
            out[rel] = (status, file_sha256(repo / rel))
    return out


def main():
    repo = Path(git(Path.cwd(), "rev-parse", "--show-toplevel").stdout.strip())
    print("PATCH=TOS-TWS-GOOGLE-SHEETS-PHASE-1-EXCEL-XLSX-FIDELITY-R1")
    print(f"REPO={repo}")
    head = git(repo, "rev-parse", "HEAD").stdout.strip()
    print(f"HEAD={head}")
    if head != EXPECTED_HEAD:
        raise RuntimeError(f"HEAD must equal Phase 1 baseline {EXPECTED_HEAD}")

    before_records = raw_status(repo)
    before_paths = {path for _, path in before_records}
    unexpected = sorted(before_paths - ALLOWED_DASHBOARD_DIRTY)
    if unexpected:
        raise RuntimeError(f"unexpected pre-existing dirty paths: {unexpected}")
    if before_paths:
        print(f"PREEXISTING_DASHBOARD_DIRTY=YES ({len(before_paths)} paths)")
    else:
        print("PREEXISTING_DASHBOARD_DIRTY=NO")
    before_allowed = allowed_snapshot(repo, before_records)

    # Download the already-reviewed Phase 1 runner, then make two guard-only
    # corrections in a temporary copy. Product payload/transforms are unchanged.
    source = urllib.request.urlopen(BASE_RUNNER, timeout=30).read().decode("utf-8")

    anchor = "\n\n\ndef run(cmd, cwd, *, check=True, env=None):"
    injection = (
        "\n\nALLOWED_COEXISTING_DIRTY = {\n"
        + "".join(f"    {rel!r},\n" for rel in sorted(ALLOWED_DASHBOARD_DIRTY))
        + "}\n\n\ndef run(cmd, cwd, *, check=True, env=None):"
    )
    if source.count(anchor) != 1:
        raise RuntimeError("R1 could not locate base runner constant injection point")
    source = source.replace(anchor, injection, 1)

    old_return = "        records.append((status, path))\n    return records\n"
    new_return = (
        "        records.append((status, path))\n"
        "    return [(status, path) for status, path in records if path not in ALLOWED_COEXISTING_DIRTY]\n"
    )
    if source.count(old_return) != 1:
        raise RuntimeError("R1 could not locate status_records return")
    source = source.replace(old_return, new_return, 1)

    old_diff_check = '    diff_check = git(repo, "diff", "--check", check=False)\n'
    new_diff_check = '    diff_check = git(repo, "diff", "--check", "--", *sorted(EXPECTED_CHANGED), check=False)\n'
    if source.count(old_diff_check) != 1:
        raise RuntimeError("R1 could not locate scoped diff-check")
    source = source.replace(old_diff_check, new_diff_check, 1)

    with tempfile.TemporaryDirectory(prefix="tws-phase1-r1-") as tmp:
        runner = Path(tmp) / "run_phase1_r1_effective.py"
        runner.write_text(source, encoding="utf-8")
        result = run([sys.executable, str(runner)], repo, check=False)
        print(result.stdout.rstrip())

    after_records = raw_status(repo)
    after_allowed = allowed_snapshot(repo, after_records)
    if after_allowed != before_allowed:
        raise RuntimeError(f"pre-existing dashboard working tree changed: before={before_allowed}, after={after_allowed}")

    after_paths = {path for _, path in after_records}
    unexpected_after = sorted(after_paths - ALLOWED_DASHBOARD_DIRTY - PHASE1_PATHS)
    if unexpected_after:
        raise RuntimeError(f"unexpected post-run dirty paths: {unexpected_after}")

    print("DASHBOARD_DIRTY_STATE_PRESERVED=YES")
    print("DASHBOARD_FILES_TOUCHED_BY_PHASE1=NO")

    if result.returncode != 0:
        print("PHASE_1_R1_RUN=FAIL")
        print("READY_FOR_GIT_PUSH=NO")
        sys.exit(result.returncode)

    phase1_present = after_paths & PHASE1_PATHS
    if phase1_present != PHASE1_PATHS:
        raise RuntimeError(f"Phase 1 output path mismatch: {sorted(phase1_present)}")
    print("PHASE_1_R1_RUN=PASS")
    print("READY_FOR_GIT_PUSH=YES")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("PHASE_1_R1_RUN=FAIL")
        print(f"ERROR={exc}")
        print("READY_FOR_GIT_PUSH=NO")
        sys.exit(1)
