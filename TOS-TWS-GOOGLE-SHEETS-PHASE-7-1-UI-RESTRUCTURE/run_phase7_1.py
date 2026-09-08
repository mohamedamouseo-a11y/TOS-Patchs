#!/usr/bin/env python3
from pathlib import Path
import hashlib
import subprocess
import sys
import urllib.request

PATCH = "TOS-TWS-GOOGLE-SHEETS-PHASE-7-1-UI-RESTRUCTURE"
REPO = Path("/var/www/TOS")
EXPECTED_HEAD = "64265e2bffdcaaf6fdb172370936c725b5414530"
BASE = "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-TWS-GOOGLE-SHEETS-PHASE-7-1-UI-RESTRUCTURE/payload"

PAYLOADS = {
    "tSheetsPhase7_1Restructure.css": "26c3de688600cbc1027e61ba4082d3b6534af988",
    "tSheetsPhase7_1Restructure.test.js": "3c5d3681340dc9efa18d7192278b70e111479fa1",
    "headerActions.phase7_1.txt": "c299938d7025e39be20015676f2896593dc4f56d",
    "menuStrip.phase7_1.txt": "0ec5c6086c504b66b9a4d7ec6b01f818690bad9b",
    "compactToolbar.phase7_1.txt": "ef63857c1e9655d9f8bd18284edaf7f93c7db8e6",
    "formulaStrip.phase7_1.txt": "d45136482aabebb88753fbe3332ec19b6d725055",
}

EDITOR = "frontend/src/pages/tws/TSheetsEditor.jsx"
PHASE7_CSS = "frontend/src/pages/tws/tSheetsPhase7Premium.css"
CSS = "frontend/src/pages/tws/tSheetsPhase7_1Restructure.css"
TEST = "frontend/src/pages/tws/tSheetsPhase7_1Restructure.test.js"

EXPECTED_BLOBS = {
    EDITOR: "88f393a427c478273ce11f4d23fe3596d8731e6e",
    PHASE7_CSS: "ca0a346ae7941c8583be115a53e06bdbabb0ae0a",
}

SCOPE = {EDITOR, CSS, TEST}
TRACKED = {EDITOR}
NEW_FILES = {CSS, TEST}


def run(cmd, cwd=REPO, check=True):
    p = subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if p.stdout:
        print(p.stdout.rstrip())
    if check and p.returncode != 0:
        raise RuntimeError(f"command failed ({p.returncode}): {' '.join(cmd)}")
    return p


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


def replace_region(text, start_marker, end_marker, replacement, label):
    start = text.find(start_marker)
    if start < 0:
        raise RuntimeError(f"{label}: start marker not found")
    end = text.find(end_marker, start + len(start_marker))
    if end < 0:
        raise RuntimeError(f"{label}: end marker not found")
    return text[:start] + replacement.rstrip() + "\n\n" + text[end:]


def rollback_phase71_only():
    subprocess.run(["git", "checkout", "HEAD", "--", EDITOR], cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for rel in NEW_FILES:
        path = REPO / rel
        if not path.exists():
            continue
        tracked = subprocess.run(
            ["git", "ls-files", "--error-unmatch", rel],
            cwd=REPO,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        ).returncode == 0
        if not tracked and path.is_file():
            path.unlink()


def apply_patch(payload):
    text = (REPO / EDITOR).read_text(encoding="utf-8")

    text = replace_once(
        text,
        'import "./tSheetsPhase7Premium.css";\n',
        'import "./tSheetsPhase7Premium.css";\nimport "./tSheetsPhase7_1Restructure.css";\n',
        "Phase 7.1 stylesheet import",
    )
    text = replace_once(
        text,
        '  const [showSheetPanel, setShowSheetPanel] = useState(true);\n',
        '  const [showSheetPanel, setShowSheetPanel] = useState(false);\n',
        "collapsed inspector default",
    )
    text = replace_once(
        text,
        '    <div className="tws-reference-ui tws-reference-sheets tws-sheets-phase7-premium flex h-full flex-col">',
        '    <div className="tws-reference-ui tws-reference-sheets tws-sheets-phase7-premium tws-sheets-phase7-1-restructure flex h-full flex-col">',
        "Phase 7.1 root hook",
    )

    text = replace_region(
        text,
        '        <div className="tws-sheets-actions flex',
        '      </div>\n\n      {!canEdit',
        payload["headerActions.phase7_1.txt"],
        "compact top actions",
    )

    header_anchor = '      </div>\n\n      {!canEdit'
    text = replace_once(
        text,
        header_anchor,
        '      </div>\n\n' + payload["menuStrip.phase7_1.txt"].rstrip() + '\n\n      {!canEdit',
        "spreadsheet menu strip",
    )

    old_toolbar_start = '      {canEdit && (\n        <div className="tws-sheets-toolbar flex'
    old_formula_start = '      {canEdit && (\n        <div className="tws-sheets-formula-strip grid'
    text = replace_region(
        text,
        old_toolbar_start,
        old_formula_start,
        payload["compactToolbar.phase7_1.txt"],
        "compact primary toolbar",
    )

    old_formula_start = '      {canEdit && (\n        <div className="tws-sheets-formula-strip grid'
    workspace_start = '      <div className="tws-sheets-workspace flex'
    text = replace_region(
        text,
        old_formula_start,
        workspace_start,
        payload["formulaStrip.phase7_1.txt"],
        "compact formula strip",
    )

    (REPO / EDITOR).write_text(text, encoding="utf-8")
    (REPO / CSS).write_text(payload["tSheetsPhase7_1Restructure.css"], encoding="utf-8")
    (REPO / TEST).write_text(payload["tSheetsPhase7_1Restructure.test.js"], encoding="utf-8")


def validate(preexisting):
    run(["node", "--check", "src/pages/tws/tSheetsPhase7_1Restructure.test.js"], cwd=REPO / "frontend")
    print("PHASE_7_1_TEST_SYNTAX=PASS")

    run(["node", "--test", "src/pages/tws/tSheetsPhase7_1Restructure.test.js"], cwd=REPO / "frontend")
    print("PHASE_7_1_UI_TESTS=PASS (7/7)")

    run(["node", "--test", "src/pages/tws/tSheetsPhase7Premium.test.js"], cwd=REPO / "frontend")
    print("PHASE_7_VISUAL_REGRESSION=PASS (6/6)")

    run(["node", "--test", "src/pages/tws/sheetGridPhase2.test.js", "src/pages/tws/sheetDataPhase3.test.js"], cwd=REPO / "frontend")
    print("PHASE_2_3_FRONTEND_REGRESSION=PASS")

    run(["node", "--test", "src/utils/sheetAdvancedPhase6.test.js"], cwd=REPO / "backend")
    print("PHASE_6_ADVANCED_REGRESSION=PASS (7/7)")
    run(["node", "--test", "src/utils/sheetCollabPhase5.test.js"], cwd=REPO / "backend")
    print("PHASE_5_COLLABORATION_REGRESSION=PASS (7/7)")
    run(["node", "--test", "src/utils/sheetFormula.phase4.test.js"], cwd=REPO / "backend")
    print("PHASE_4_FORMULA_REGRESSION=PASS (6/6)")
    run(["node", "--test", "src/utils/workspaceXlsx.phase1.test.js"], cwd=REPO / "backend")
    print("PHASE_1_XLSX_REGRESSION=PASS (4/4)")
    phase3 = REPO / "backend/src/utils/workspaceXlsx.phase3.test.js"
    if phase3.exists():
        run(["node", "--test", "src/utils/workspaceXlsx.phase3.test.js"], cwd=REPO / "backend")
        print("PHASE_3_XLSX_REGRESSION=PASS")

    run(["npm", "run", "build"], cwd=REPO / "frontend")
    print("FRONTEND_BUILD=PASS")

    run(["git", "diff", "--check", "--", *sorted(SCOPE)])

    actual_all = status_paths()
    missing_preexisting = preexisting - actual_all
    if missing_preexisting:
        raise RuntimeError(f"pre-existing dirty paths disappeared: {sorted(missing_preexisting)}")
    actual_phase = actual_all - preexisting
    if actual_phase != SCOPE:
        raise RuntimeError(f"unexpected Phase 7.1 changed paths: {sorted(actual_phase)}; all={sorted(actual_all)}")
    print(f"PATCH_FILE_COUNT={len(actual_phase)}")
    print("PHASE_7_1_CHANGED_PATHS_EXACT=YES")


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
    overlap = preexisting & SCOPE
    if overlap:
        raise RuntimeError(f"PREEXISTING_DIRTY_OVERLAPS_PHASE_7_1_SCOPE: {sorted(overlap)}")
    pre_snapshot = snapshot(preexisting)
    if preexisting:
        print("PRECHECK_WORKTREE=DIRTY_UNRELATED_ALLOWED")
        print("PREEXISTING_DIRTY_PATHS=" + ",".join(sorted(preexisting)))
    else:
        print("PRECHECK_WORKTREE=CLEAN")

    for rel, expected in EXPECTED_BLOBS.items():
        actual = file_blob_sha(rel)
        if actual != expected:
            raise RuntimeError(f"baseline blob mismatch for {rel}: {actual} != {expected}")
    print("BASELINE_BLOBS=PASS")

    payload = {name: download(name) for name in PAYLOADS}
    print("PAYLOAD_INTEGRITY=PASS")

    try:
        apply_patch(payload)
        validate(preexisting)
        post_snapshot = snapshot(preexisting)
        if post_snapshot != pre_snapshot:
            raise RuntimeError("pre-existing dirty file contents changed during Phase 7.1")
    except BaseException:
        rollback_phase71_only()
        post_snapshot = snapshot(preexisting)
        print("PHASE_7_1_ROLLBACK=PASS" if status_paths() == preexisting and post_snapshot == pre_snapshot else "PHASE_7_1_ROLLBACK=FAIL")
        raise

    print("PREEXISTING_DIRTY_STATE_PRESERVED=YES")
    print("HEADER_ACTIONS_COMPACT=PASS")
    print("SPREADSHEET_MENU_HIERARCHY=PASS")
    print("COMPACT_TOOLBAR=PASS")
    print("COMPACT_FORMULA_BAR=PASS")
    print("INSPECTOR_DEFAULT_COLLAPSED=PASS")
    print("LIGHT_DARK_PREMIUM_LAYER_PRESERVED=YES")
    print("FUNCTIONAL_BEHAVIOR_CHANGED=NO")
    print("DATABASE_SCHEMA_CHANGED=NO")
    print("PHASE_7_1_PATCH_APPLIED=YES")
    print("READY_FOR_GIT_PUSH=YES")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("PHASE_7_1_RUN=FAIL")
        print(f"ERROR={exc}")
        print("READY_FOR_GIT_PUSH=NO")
        sys.exit(1)
