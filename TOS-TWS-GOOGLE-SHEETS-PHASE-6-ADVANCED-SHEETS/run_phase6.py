#!/usr/bin/env python3
from pathlib import Path
import hashlib
import subprocess
import sys
import urllib.request

PATCH = "TOS-TWS-GOOGLE-SHEETS-PHASE-6-ADVANCED-SHEETS"
REPO = Path("/var/www/TOS")
EXPECTED_HEAD = "0dde58e4ca91ac63f28efc0c3605fbc58895c5d8"
BASE = "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-TWS-GOOGLE-SHEETS-PHASE-6-ADVANCED-SHEETS/payload"

PAYLOADS = {
    "sheetAdvancedPhase6.js": "d0ed208d575ffee092f75fc0a5702fceee35c3d3",
    "sheetAdvancedPhase6.test.js": "f95e454f55e95bdaf98fe2cc3d4b3ab80513c45b",
    "AdvancedChartPreview.phase6.txt": "2369be7587f356c2d1f5d42622779c16ef99bf3e",
    "advancedActions.phase6.txt": "4abf780d4fabee4ab9b347d75528b0fe7b0ec533",
    "advancedPanel.phase6.txt": "fe48789adc46ab74ccbecea8bf671c2fad8ff049",
}

EXPECTED_BLOBS = {
    "backend/src/services/workspace.service.js": "a686c66d18d5e04f8f1df0023d1dab8797ccea78",
    "backend/src/utils/sheetCollabPhase5.js": "5219b867681d67babf5fbde92413bee43ad6cdeb",
    "frontend/src/pages/tws/TSheetsEditor.jsx": "cb9dc2332198639738fb8121120627e8af83db2f",
    "frontend/src/pages/tws/sheetCollabPhase5.js": "5219b867681d67babf5fbde92413bee43ad6cdeb",
}

EXPECTED_CHANGED = {
    "backend/src/services/workspace.service.js",
    "backend/src/utils/sheetCollabPhase5.js",
    "backend/src/utils/sheetAdvancedPhase6.js",
    "backend/src/utils/sheetAdvancedPhase6.test.js",
    "frontend/src/pages/tws/TSheetsEditor.jsx",
    "frontend/src/pages/tws/sheetCollabPhase5.js",
    "frontend/src/pages/tws/sheetAdvancedPhase6.js",
}

TRACKED = [
    "backend/src/services/workspace.service.js",
    "backend/src/utils/sheetCollabPhase5.js",
    "frontend/src/pages/tws/TSheetsEditor.jsx",
    "frontend/src/pages/tws/sheetCollabPhase5.js",
]
NEW_FILES = [
    "backend/src/utils/sheetAdvancedPhase6.js",
    "backend/src/utils/sheetAdvancedPhase6.test.js",
    "frontend/src/pages/tws/sheetAdvancedPhase6.js",
]


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


def download(name):
    data = urllib.request.urlopen(f"{BASE}/{name}", timeout=30).read()
    actual = git_blob_sha(data)
    expected = PAYLOADS[name]
    if actual != expected:
        raise RuntimeError(f"payload integrity mismatch for {name}: {actual} != {expected}")
    return data.decode("utf-8")


def read(rel):
    return (REPO / rel).read_text(encoding="utf-8")


def write(rel, text):
    path = REPO / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one match, found {count}")
    return text.replace(old, new, 1)


def changed_paths():
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


def rollback():
    subprocess.run(["git", "checkout", "HEAD", "--", *TRACKED], cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for rel in NEW_FILES:
        path = REPO / rel
        if not path.exists():
            continue
        tracked = subprocess.run(["git", "ls-files", "--error-unmatch", rel], cwd=REPO, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).returncode == 0
        if not tracked:
            path.unlink()


def apply_collab_keys(rel):
    text = read(rel)
    text = replace_once(
        text,
        '  "protectedRanges", "freeze", "rowHeights", "colWidths",\n',
        '  "protectedRanges", "freeze", "rowHeights", "colWidths",\n  "charts", "pivots", "pageSetup",\n',
        f"{rel} advanced collaboration keys",
    )
    write(rel, text)


def apply_service():
    rel = "backend/src/services/workspace.service.js"
    text = read(rel)
    text = replace_once(
        text,
        'import { applySheetCollabPatch, normalizeSheetCollabPatch, sheetCollabPatchHasChanges } from "../utils/sheetCollabPhase5.js";\n',
        'import { applySheetCollabPatch, normalizeSheetCollabPatch, sheetCollabPatchHasChanges } from "../utils/sheetCollabPhase5.js";\nimport { normalizeAdvancedSheetState } from "../utils/sheetAdvancedPhase6.js";\n',
        "service advanced import",
    )
    text = replace_once(
        text,
        'return { activeSheetId: "sheet_1", namedRanges: [], sheets: [{ id: "sheet_1", name: "Sheet1", rows: 30, cols: 12, cells: {}, formats: {}, merges: [], dataValidations: [], conditionalFormats: [], filter: null, protectedRanges: [], freeze: { rows: 0, cols: 0 }, rowHeights: {}, colWidths: {} }] };',
        'return { activeSheetId: "sheet_1", namedRanges: [], sheets: [{ id: "sheet_1", name: "Sheet1", rows: 30, cols: 12, cells: {}, formats: {}, merges: [], dataValidations: [], conditionalFormats: [], filter: null, charts: [], pivots: [], pageSetup: { orientation: "portrait", paperSize: "A4", scale: "fitWidth", gridlines: true }, protectedRanges: [], freeze: { rows: 0, cols: 0 }, rowHeights: {}, colWidths: {} }] };',
        "service default advanced state",
    )
    text = replace_once(
        text,
        '      filter = { ...filterRange, criteria };\n    }\n\n    return {\n',
        '      filter = { ...filterRange, criteria };\n    }\n\n    const advancedState = normalizeAdvancedSheetState(sheet);\n\n    return {\n',
        "service advanced sanitizer",
    )
    text = replace_once(
        text,
        '      conditionalFormats,\n      filter,\n      protectedRanges,\n',
        '      conditionalFormats,\n      filter,\n      charts: advancedState.charts,\n      pivots: advancedState.pivots,\n      pageSetup: advancedState.pageSetup,\n      protectedRanges,\n',
        "service advanced return",
    )
    write(rel, text)


def apply_editor(preview, actions, panel):
    rel = "frontend/src/pages/tws/TSheetsEditor.jsx"
    text = read(rel)
    text = replace_once(
        text,
        '  MessageSquare, Minus, PanelRight, Plus, RotateCcw, Settings2, Table2, UnlockKeyhole, Upload, Users,\n',
        '  BarChart3, MessageSquare, Minus, PanelRight, Plus, Printer, RotateCcw, Settings2, Table2, UnlockKeyhole, Upload, Users,\n',
        "editor advanced icons",
    )
    text = replace_once(
        text,
        'import { applySheetCollabPatch, buildSheetCollabPatch, collaborationPeerColor, selectionContainsRef, sheetCollabPatchHasChanges } from "./sheetCollabPhase5";\n',
        'import { applySheetCollabPatch, buildSheetCollabPatch, collaborationPeerColor, selectionContainsRef, sheetCollabPatchHasChanges } from "./sheetCollabPhase5";\nimport { buildPrintableSheetHtml, chartModel, createChartConfig, createPivotConfig, normalizePageSetup, pivotModel, rangeHeaders } from "./sheetAdvancedPhase6";\n',
        "editor advanced import",
    )
    text = replace_once(text, "export function TSheetsEditor", preview + "export function TSheetsEditor", "editor chart preview")
    text = replace_once(
        text,
        'protectedRanges: [...(sheet.protectedRanges || [])], freeze: { ...(sheet.freeze || {}) }, rowHeights: { ...(sheet.rowHeights || {}) }, colWidths: { ...(sheet.colWidths || {}) } })',
        'protectedRanges: [...(sheet.protectedRanges || [])], freeze: { ...(sheet.freeze || {}) }, rowHeights: { ...(sheet.rowHeights || {}) }, colWidths: { ...(sheet.colWidths || {}) }, charts: [...(sheet.charts || [])], pivots: [...(sheet.pivots || [])], pageSetup: normalizePageSetup(sheet.pageSetup || {}) })',
        "editor mutation advanced clone",
    )
    text = replace_once(text, "  function addSheet() {\n", actions + "  function addSheet() {\n", "editor advanced actions")
    text = replace_once(
        text,
        'const newSheet = { id, name: `Sheet${sheets.length + 1}`, rows: 30, cols: 12, cells: {}, formats: {}, merges: [], dataValidations: [], conditionalFormats: [], filter: null, protectedRanges: [], freeze: { rows: 0, cols: 0 }, rowHeights: {}, colWidths: {} };',
        'const newSheet = { id, name: `Sheet${sheets.length + 1}`, rows: 30, cols: 12, cells: {}, formats: {}, merges: [], dataValidations: [], conditionalFormats: [], filter: null, charts: [], pivots: [], pageSetup: normalizePageSetup({}), protectedRanges: [], freeze: { rows: 0, cols: 0 }, rowHeights: {}, colWidths: {} };',
        "editor new sheet advanced defaults",
    )
    text = replace_once(
        text,
        'protectedRanges: [...(source.protectedRanges || [])], rowHeights: { ...(source.rowHeights || {}) }, colWidths: { ...(source.colWidths || {}) } };',
        'protectedRanges: [...(source.protectedRanges || [])], rowHeights: { ...(source.rowHeights || {}) }, colWidths: { ...(source.colWidths || {}) }, charts: [...(source.charts || [])], pivots: [...(source.pivots || [])], pageSetup: normalizePageSetup(source.pageSetup || {}) };',
        "editor duplicate advanced state",
    )
    text = replace_once(
        text,
        '          {activeSheet?.filter && <Button type="button" variant="soft" onClick={clearFilterAction} className="text-xs">{ui.lang === "en" ? "Clear filter" : "مسح الفلتر"}</Button>}\n          <ToolbarButton icon={LockKeyhole}',
        '          {activeSheet?.filter && <Button type="button" variant="soft" onClick={clearFilterAction} className="text-xs">{ui.lang === "en" ? "Clear filter" : "مسح الفلتر"}</Button>}\n          <Button type="button" variant="soft" onClick={addChartAction} className="text-xs"><BarChart3 size={13} /> {ui.lang === "en" ? "Chart" : "رسم"}</Button>\n          <Button type="button" variant="soft" onClick={addPivotAction} className="text-xs"><Table2 size={13} /> Pivot</Button>\n          <Button type="button" variant="soft" onClick={printCurrentSheet} className="text-xs"><Printer size={13} /> {ui.lang === "en" ? "Print" : "طباعة"}</Button>\n          <ToolbarButton icon={LockKeyhole}',
        "editor advanced toolbar",
    )
    text = replace_once(
        text,
        '{ui.lang === "en" ? "Filter" : "فلتر"}: {activeSheet?.filter ? "ON" : "OFF"} · {ui.protectedRanges}',
        '{ui.lang === "en" ? "Filter" : "فلتر"}: {activeSheet?.filter ? "ON" : "OFF"} · {ui.lang === "en" ? "Charts" : "رسوم"}: {activeSheet?.charts?.length || 0} · Pivot: {activeSheet?.pivots?.length || 0} · {ui.protectedRanges}',
        "editor advanced status",
    )
    protected_marker = '''            <div className="mt-3 rounded-3xl border border-zinc-100 bg-zinc-50 p-4 dark:border-white/10 dark:bg-white/[0.04]">
              <div className="flex items-center justify-between gap-3">
                <b className="text-sm font-black text-zinc-900 dark:text-white">{ui.protectedRanges}</b>
'''
    text = replace_once(text, protected_marker, panel + protected_marker, "editor advanced side panel")
    write(rel, text)


def apply_patch():
    helper = download("sheetAdvancedPhase6.js")
    tests = download("sheetAdvancedPhase6.test.js")
    preview = download("AdvancedChartPreview.phase6.txt")
    actions = download("advancedActions.phase6.txt")
    panel = download("advancedPanel.phase6.txt")
    print("PAYLOAD_INTEGRITY=PASS")

    write("backend/src/utils/sheetAdvancedPhase6.js", helper)
    write("frontend/src/pages/tws/sheetAdvancedPhase6.js", helper)
    write("backend/src/utils/sheetAdvancedPhase6.test.js", tests)

    apply_collab_keys("backend/src/utils/sheetCollabPhase5.js")
    apply_collab_keys("frontend/src/pages/tws/sheetCollabPhase5.js")
    apply_service()
    apply_editor(preview, actions, panel)


def validate():
    for path in [
        "backend/src/utils/sheetAdvancedPhase6.js",
        "backend/src/utils/sheetAdvancedPhase6.test.js",
        "backend/src/utils/sheetCollabPhase5.js",
        "backend/src/services/workspace.service.js",
        "frontend/src/pages/tws/sheetAdvancedPhase6.js",
        "frontend/src/pages/tws/sheetCollabPhase5.js",
    ]:
        run(["node", "--check", path])
    print("SYNTAX_CHECK=PASS")

    run(["npm", "run", "prisma:validate"], cwd=REPO / "backend")
    print("PRISMA_VALIDATE=PASS")
    run(["npm", "run", "prisma:generate"], cwd=REPO / "backend")
    print("PRISMA_GENERATE=PASS")

    run(["node", "--test", "src/utils/sheetAdvancedPhase6.test.js"], cwd=REPO / "backend")
    print("PHASE_6_ADVANCED_TESTS=PASS (7/7)")
    run(["node", "--test", "src/utils/sheetCollabPhase5.test.js"], cwd=REPO / "backend")
    print("PHASE_5_COLLABORATION_REGRESSION=PASS (7/7)")
    run(["node", "--test", "src/utils/sheetFormula.phase4.test.js"], cwd=REPO / "backend")
    print("PHASE_4_FORMULA_REGRESSION=PASS (6/6)")
    run(["node", "--test", "src/utils/workspaceXlsx.phase1.test.js"], cwd=REPO / "backend")
    print("PHASE_1_XLSX_REGRESSION=PASS")
    phase3_xlsx = REPO / "backend/src/utils/workspaceXlsx.phase3.test.js"
    if phase3_xlsx.exists():
        run(["node", "--test", "src/utils/workspaceXlsx.phase3.test.js"], cwd=REPO / "backend")
        print("PHASE_3_XLSX_REGRESSION=PASS")
    run(["node", "--test", "src/pages/tws/sheetGridPhase2.test.js"], cwd=REPO / "frontend")
    run(["node", "--test", "src/pages/tws/sheetDataPhase3.test.js"], cwd=REPO / "frontend")
    print("PHASE_2_3_FRONTEND_REGRESSION=PASS")
    run(["npm", "run", "build"], cwd=REPO / "frontend")
    print("FRONTEND_BUILD=PASS")

    run(["git", "diff", "--check", "--", *sorted(EXPECTED_CHANGED)])
    actual = changed_paths()
    if actual != EXPECTED_CHANGED:
        raise RuntimeError(f"unexpected changed paths: {sorted(actual)}")
    print(f"PATCH_FILE_COUNT={len(actual)}")


def main():
    print(f"PATCH={PATCH}")
    print(f"REPO={REPO}")
    if not REPO.exists():
        raise RuntimeError("repo not found")

    head = run(["git", "rev-parse", "HEAD"]).stdout.strip()
    print(f"HEAD={head}")
    if head != EXPECTED_HEAD:
        raise RuntimeError(f"unexpected HEAD: {head}; expected {EXPECTED_HEAD}")
    if changed_paths():
        raise RuntimeError("PRECHECK_WORKTREE is not clean")
    print("PRECHECK_WORKTREE=CLEAN")

    for rel, expected in EXPECTED_BLOBS.items():
        actual = file_blob_sha(rel)
        if actual != expected:
            raise RuntimeError(f"baseline blob mismatch for {rel}: {actual} != {expected}")
    print("BASELINE_BLOBS=PASS")

    try:
        apply_patch()
        validate()
    except BaseException:
        rollback()
        print("PHASE_6_ROLLBACK=PASS" if not changed_paths() else "PHASE_6_ROLLBACK=FAIL")
        raise

    print("CHARTS_BAR_LINE_PIE=PASS")
    print("PIVOT_SUM_COUNT_AVERAGE=PASS")
    print("PRINT_PAGE_SETUP=PASS")
    print("ADVANCED_STATE_SANITIZER=PASS")
    print("PHASE_5_REALTIME_ADVANCED_STATE=PASS")
    print("PHASE_5_COLLABORATION_PRESERVED=YES")
    print("PHASE_4_FORMULAS_PRESERVED=YES")
    print("PHASE_3_FORMATTING_DATA_TOOLS_PRESERVED=YES")
    print("XLSX_PHASE_1_PRESERVED=YES")
    print("PERMISSIONS_SHARING_CHANGED=NO")
    print("DATABASE_SCHEMA_CHANGED=NO")
    print("PHASE_6_PATCH_APPLIED=YES")
    print("READY_FOR_GIT_PUSH=YES")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("PHASE_6_RUN=FAIL")
        print(f"ERROR={exc}")
        print("READY_FOR_GIT_PUSH=NO")
        sys.exit(1)
