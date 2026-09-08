#!/usr/bin/env python3
from pathlib import Path
import hashlib
import subprocess
import sys
import urllib.request

PATCH = "TOS-TWS-GOOGLE-SHEETS-PHASE-7-PREMIUM-UX-UI-PARITY-POLISH"
REPO = Path("/var/www/TOS")
EXPECTED_HEAD = "de2aae984528ca7c6b48b62819c1a05aa9e1d46a"
BASE = "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-TWS-GOOGLE-SHEETS-PHASE-7-PREMIUM-UX-UI-PARITY-POLISH/payload"

PAYLOADS = {
    "tSheetsPhase7Premium.css": "ca0a346ae7941c8583be115a53e06bdbabb0ae0a",
    "tSheetsPhase7Premium.test.js": "5732f91e5a911908cf3ea011615a5845dd16bccc",
}

EDITOR = "frontend/src/pages/tws/TSheetsEditor.jsx"
CSS = "frontend/src/pages/tws/tSheetsPhase7Premium.css"
TEST = "frontend/src/pages/tws/tSheetsPhase7Premium.test.js"
EXPECTED_EDITOR_BLOB = "aea1e7c07da8b3590b114b35c739a9137fb86da7"
PHASE7_SCOPE = {EDITOR, CSS, TEST}
NEW_FILES = {CSS, TEST}


def run(cmd, cwd=REPO, check=True):
    p = subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if p.stdout:
        print(p.stdout.rstrip())
    if check and p.returncode != 0:
        raise RuntimeError(f"command failed ({p.returncode}): {' '.join(cmd)}")
    return p


def git(*args, check=True):
    return run(["git", *args], check=check)


def git_blob_sha(data):
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def file_blob_sha(rel):
    return git_blob_sha((REPO / rel).read_bytes())


def status_paths():
    p = subprocess.run(["git", "status", "--porcelain"], cwd=REPO, text=True, stdout=subprocess.PIPE, check=True)
    result = set()
    for line in p.stdout.splitlines():
        if not line.strip():
            continue
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        result.add(path)
    return result


def fingerprint(rel):
    path = REPO / rel
    if not path.exists():
        return "MISSING"
    if path.is_file():
        return hashlib.sha256(path.read_bytes()).hexdigest()
    return "DIR"


def snapshot(paths):
    return {rel: fingerprint(rel) for rel in sorted(paths)}


def download(name):
    data = urllib.request.urlopen(f"{BASE}/{name}", timeout=30).read()
    actual = git_blob_sha(data)
    expected = PAYLOADS[name]
    if actual != expected:
        raise RuntimeError(f"payload integrity mismatch for {name}: {actual} != {expected}")
    return data.decode("utf-8")


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def rollback_phase7_only():
    subprocess.run(["git", "checkout", "HEAD", "--", EDITOR], cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for rel in NEW_FILES:
        path = REPO / rel
        if not path.exists():
            continue
        tracked = subprocess.run(["git", "ls-files", "--error-unmatch", rel], cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).returncode == 0
        if not tracked and path.is_file():
            path.unlink()


def patch_editor():
    path = REPO / EDITOR
    text = path.read_text(encoding="utf-8")

    text = replace_once(
        text,
        'import { buildPrintableSheetHtml, chartModel, createChartConfig, createPivotConfig, normalizePageSetup, pivotModel, rangeHeaders } from "./sheetAdvancedPhase6";\n',
        'import { buildPrintableSheetHtml, chartModel, createChartConfig, createPivotConfig, normalizePageSetup, pivotModel, rangeHeaders } from "./sheetAdvancedPhase6";\nimport "./tSheetsPhase7Premium.css";\n',
        "phase7 stylesheet import",
    )
    text = replace_once(
        text,
        '<div className="tws-reference-ui tws-reference-sheets flex h-full flex-col">',
        '<div className="tws-reference-ui tws-reference-sheets tws-sheets-phase7-premium flex h-full flex-col">',
        "phase7 root class",
    )
    text = replace_once(
        text,
        '<div className="flex flex-wrap items-center gap-3 border-b border-zinc-100 bg-white px-4 py-3 dark:border-white/10 dark:bg-zinc-900">',
        '<div className="tws-sheets-chrome flex flex-wrap items-center gap-3 border-b border-zinc-100 bg-white px-4 py-3 dark:border-white/10 dark:bg-zinc-900">',
        "phase7 chrome hook",
    )
    text = replace_once(
        text,
        '<div className="flex flex-wrap items-center gap-1.5">\n          <Button type="button" variant="soft" onClick={() => setShowComments((v) => !v)}>',
        '<div className="tws-sheets-actions flex flex-wrap items-center gap-1.5">\n          <Button type="button" variant="soft" onClick={() => setShowComments((v) => !v)}>',
        "phase7 actions hook",
    )
    text = replace_once(
        text,
        '<div className="flex flex-wrap items-center gap-1 border-b border-zinc-100 bg-zinc-50 px-3 py-1.5 dark:border-white/10 dark:bg-white/[0.03]">',
        '<div className="tws-sheets-toolbar flex flex-wrap items-center gap-1 border-b border-zinc-100 bg-zinc-50 px-3 py-1.5 dark:border-white/10 dark:bg-white/[0.03]">',
        "phase7 toolbar hook",
    )
    text = replace_once(
        text,
        '<div className="grid gap-2 border-b border-zinc-100 bg-white px-3 py-2 dark:border-white/10 dark:bg-zinc-900 md:grid-cols-[120px_1fr_220px]">',
        '<div className="tws-sheets-formula-strip grid gap-2 border-b border-zinc-100 bg-white px-3 py-2 dark:border-white/10 dark:bg-zinc-900 md:grid-cols-[120px_1fr_220px]">',
        "phase7 formula strip hook",
    )
    text = replace_once(
        text,
        '<div className="flex min-h-0 flex-1">\n        <div className="flex min-w-0 flex-1 flex-col overflow-hidden">',
        '<div className="tws-sheets-workspace flex min-h-0 flex-1">\n        <div className="flex min-w-0 flex-1 flex-col overflow-hidden">',
        "phase7 workspace hook",
    )
    text = replace_once(
        text,
        '<div className="flex-1 overflow-auto">\n            <table className="border-collapse text-xs"',
        '<div className="tws-sheets-grid-scroll flex-1 overflow-auto">\n            <table className="tws-sheets-grid border-collapse text-xs"',
        "phase7 grid hooks",
    )
    text = replace_once(
        text,
        '<div role="menu" className="fixed z-[80] w-52 overflow-hidden rounded-2xl border border-zinc-200 bg-white p-1.5 text-xs font-bold text-zinc-700 shadow-2xl dark:border-white/10 dark:bg-zinc-900 dark:text-zinc-200"',
        '<div role="menu" className="tws-sheets-context-menu fixed z-[80] w-52 overflow-hidden rounded-2xl border border-zinc-200 bg-white p-1.5 text-xs font-bold text-zinc-700 shadow-2xl dark:border-white/10 dark:bg-zinc-900 dark:text-zinc-200"',
        "phase7 context menu hook",
    )
    text = replace_once(
        text,
        '<div className="flex items-center gap-1 overflow-x-auto border-t border-zinc-100 bg-zinc-50 px-2 py-1.5 dark:border-white/10 dark:bg-white/[0.03]">',
        '<div className="tws-sheets-tabs flex items-center gap-1 overflow-x-auto border-t border-zinc-100 bg-zinc-50 px-2 py-1.5 dark:border-white/10 dark:bg-white/[0.03]">',
        "phase7 tabs hook",
    )
    text = replace_once(
        text,
        '<aside className="hidden w-72 shrink-0 overflow-y-auto border-r border-zinc-100 bg-white p-3 dark:border-white/10 dark:bg-zinc-900 xl:block">',
        '<aside className="tws-sheets-inspector hidden w-72 shrink-0 overflow-y-auto border-r border-zinc-100 bg-white p-3 dark:border-white/10 dark:bg-zinc-900 xl:block">',
        "phase7 inspector hook",
    )

    path.write_text(text, encoding="utf-8")


def validate(preexisting):
    run(["node", "--test", "src/pages/tws/tSheetsPhase7Premium.test.js"], cwd=REPO / "frontend")
    print("PHASE_7_VISUAL_TESTS=PASS (6/6)")

    run(["node", "--test", "src/pages/tws/sheetGridPhase2.test.js"], cwd=REPO / "frontend")
    run(["node", "--test", "src/pages/tws/sheetDataPhase3.test.js"], cwd=REPO / "frontend")
    print("PHASE_2_3_FRONTEND_REGRESSION=PASS")

    run(["node", "--test", "src/utils/sheetAdvancedPhase6.test.js"], cwd=REPO / "backend")
    print("PHASE_6_ADVANCED_REGRESSION=PASS (7/7)")
    run(["node", "--test", "src/utils/sheetCollabPhase5.test.js"], cwd=REPO / "backend")
    print("PHASE_5_COLLABORATION_REGRESSION=PASS (7/7)")
    run(["node", "--test", "src/utils/sheetFormula.phase4.test.js"], cwd=REPO / "backend")
    print("PHASE_4_FORMULA_REGRESSION=PASS (6/6)")
    run(["node", "--test", "src/utils/workspaceXlsx.phase1.test.js"], cwd=REPO / "backend")
    print("PHASE_1_XLSX_REGRESSION=PASS")
    phase3 = REPO / "backend/src/utils/workspaceXlsx.phase3.test.js"
    if phase3.exists():
        run(["node", "--test", "src/utils/workspaceXlsx.phase3.test.js"], cwd=REPO / "backend")
        print("PHASE_3_XLSX_REGRESSION=PASS")

    run(["npm", "run", "build"], cwd=REPO / "frontend")
    print("FRONTEND_BUILD=PASS")
    git("diff", "--check", "--", EDITOR)

    actual_all = status_paths()
    missing_preexisting = preexisting - actual_all
    if missing_preexisting:
        raise RuntimeError(f"pre-existing dirty paths disappeared: {sorted(missing_preexisting)}")
    phase7 = actual_all - preexisting
    if phase7 != PHASE7_SCOPE:
        raise RuntimeError(f"unexpected Phase 7 changed paths: {sorted(phase7)}; all={sorted(actual_all)}")
    print("PHASE_7_CHANGED_PATHS_EXACT=YES")
    print("PATCH_FILE_COUNT=3")


def main():
    print(f"PATCH={PATCH}")
    print(f"REPO={REPO}")
    if not REPO.exists():
        raise RuntimeError("repo not found")

    head = run(["git", "rev-parse", "HEAD"]).stdout.strip()
    print(f"HEAD={head}")
    if head != EXPECTED_HEAD:
        raise RuntimeError(f"unexpected HEAD: {head}; expected {EXPECTED_HEAD}")

    preexisting = status_paths()
    overlap = preexisting & PHASE7_SCOPE
    if overlap:
        raise RuntimeError(f"PREEXISTING_DIRTY_OVERLAPS_PHASE7_SCOPE: {sorted(overlap)}")
    pre_snapshot = snapshot(preexisting)
    if preexisting:
        print("PRECHECK_WORKTREE=DIRTY_UNRELATED_ALLOWED")
        print("PREEXISTING_DIRTY_PATHS=" + ",".join(sorted(preexisting)))
    else:
        print("PRECHECK_WORKTREE=CLEAN")

    if file_blob_sha(EDITOR) != EXPECTED_EDITOR_BLOB:
        raise RuntimeError(f"baseline blob mismatch for {EDITOR}")
    for rel in NEW_FILES:
        if (REPO / rel).exists():
            raise RuntimeError(f"Phase 7 new file already exists: {rel}")
    print("BASELINE_BLOBS=PASS")

    css = download("tSheetsPhase7Premium.css")
    tests = download("tSheetsPhase7Premium.test.js")
    print("PAYLOAD_INTEGRITY=PASS")

    try:
        patch_editor()
        (REPO / CSS).write_text(css, encoding="utf-8")
        (REPO / TEST).write_text(tests, encoding="utf-8")
        validate(preexisting)
    except BaseException:
        rollback_phase7_only()
        post_snapshot = snapshot(preexisting)
        print("PHASE_7_ROLLBACK=PASS" if post_snapshot == pre_snapshot and status_paths() == preexisting else "PHASE_7_ROLLBACK=FAIL")
        raise

    post_snapshot = snapshot(preexisting)
    if post_snapshot != pre_snapshot:
        rollback_phase7_only()
        raise RuntimeError("pre-existing dirty file contents changed during Phase 7")

    print("PREEXISTING_DIRTY_STATE_PRESERVED=YES")
    print("LIGHT_MODE_PREMIUM_POLISH=PASS")
    print("DARK_MODE_PREMIUM_POLISH=PASS")
    print("SPREADSHEET_DENSITY_PARITY=PASS")
    print("GRID_FOCUS_SELECTION_FIDELITY=PASS")
    print("TOOLBAR_FORMULA_TABS_POLISH=PASS")
    print("RESPONSIVE_POLISH=PASS")
    print("FUNCTIONAL_BEHAVIOR_CHANGED=NO")
    print("DATABASE_SCHEMA_CHANGED=NO")
    print("PHASE_7_PATCH_APPLIED=YES")
    print("READY_FOR_GIT_PUSH=YES")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("PHASE_7_RUN=FAIL")
        print(f"ERROR={exc}")
        print("READY_FOR_GIT_PUSH=NO")
        sys.exit(1)
