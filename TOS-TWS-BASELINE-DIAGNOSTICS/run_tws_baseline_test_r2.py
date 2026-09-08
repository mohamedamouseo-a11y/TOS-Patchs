#!/usr/bin/env python3
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import textwrap

EXPECTED_HEAD = "a442ff075526235775013ca64f7f34543e43880e"


def run(cmd, cwd, *, input_text=None, check=True, text=True):
    p = subprocess.run(
        cmd,
        cwd=cwd,
        text=text,
        input=input_text,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if check and p.returncode != 0:
        out = p.stdout if text else (p.stdout or b"").decode("utf-8", "replace")
        raise RuntimeError(f"command failed ({p.returncode}): {' '.join(cmd)}\n{out}")
    return p


def git(repo, *args):
    return run(["git", *args], repo).stdout.strip()


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def main():
    repo = Path(git(Path.cwd(), "rev-parse", "--show-toplevel"))
    print("TWS_BASELINE_TEST_R2=START")
    print(f"REPO={repo}")

    head = git(repo, "rev-parse", "HEAD")
    print(f"HEAD={head}")
    require(head == EXPECTED_HEAD, f"HEAD must equal baseline {EXPECTED_HEAD}")

    status_before = git(repo, "status", "--porcelain=v1", "--untracked-files=all")
    print(f"SERVER_WORKTREE_DIRTY={'YES' if status_before else 'NO'}")
    print("TEST_SOURCE=ISOLATED_GIT_HEAD_ARCHIVE")

    required_paths = [
        "backend/package.json",
        "backend/src/routes/workspace.routes.js",
        "backend/src/services/workspace.service.js",
        "backend/src/utils/workspaceCsv.js",
        "backend/src/utils/workspaceExport.js",
        "backend/src/utils/sheetFormula.js",
        "frontend/src/pages/tws/TSheetsEditor.jsx",
        "frontend/src/pages/tws/sheetFormula.js",
    ]

    with tempfile.TemporaryDirectory(prefix="tws-baseline-r2-") as tmp_name:
        tmp = Path(tmp_name)
        archive_path = tmp / "head.tar"
        snapshot = tmp / "snapshot"
        snapshot.mkdir()

        run(["git", "archive", "--format=tar", "-o", str(archive_path), head], repo)
        with tarfile.open(archive_path, "r") as tf:
            tf.extractall(snapshot)

        for rel in required_paths:
            require((snapshot / rel).is_file(), f"missing required TWS file in HEAD snapshot: {rel}")

        source_node_modules = repo / "backend" / "node_modules"
        require(source_node_modules.is_dir(), "backend/node_modules is required on server for isolated baseline test")
        target_node_modules = snapshot / "backend" / "node_modules"
        if target_node_modules.exists() or target_node_modules.is_symlink():
            if target_node_modules.is_dir() and not target_node_modules.is_symlink():
                shutil.rmtree(target_node_modules)
            else:
                target_node_modules.unlink()
        os.symlink(source_node_modules, target_node_modules, target_is_directory=True)

        backend = snapshot / "backend"

        js = textwrap.dedent(r'''
            import assert from 'node:assert/strict';
            import ExcelJS from 'exceljs';
            import { computeSheetValues as computeBackend } from './src/utils/sheetFormula.js';
            import { computeSheetValues as computeFrontend } from '../frontend/src/pages/tws/sheetFormula.js';
            import { parseCsv, stringifyCsv } from './src/utils/workspaceCsv.js';
            import { buildTSheetXlsx } from './src/utils/workspaceExport.js';
            import fs from 'node:fs';

            const results = [];
            const pass = (name, detail='PASS') => { results.push([name, true, detail]); console.log(`${name}=PASS${detail && detail !== 'PASS' ? ` (${detail})` : ''}`); };
            const fail = (name, err) => { results.push([name, false, String(err?.message || err)]); console.log(`${name}=FAIL (${String(err?.message || err)})`); };
            const check = async (name, fn) => { try { await fn(); pass(name); } catch (e) { fail(name, e); } };

            const formulaSheet = {
              id: 'sheet_1', name: 'Formula Matrix', rows: 30, cols: 12,
              cells: {
                A1:{v:10}, A2:{v:20}, A3:{v:30},
                B1:{v:'=SUM(A1:A3)'},
                B2:{v:'=AVERAGE(A1:A3)'},
                B3:{v:'=MIN(A1:A3)'},
                B4:{v:'=MAX(A1:A3)'},
                B5:{v:'=COUNT(A1:A3)'},
                C1:{v:'=IF(A1<15,"YES","NO")'},
                C2:{v:'=CONCAT("T","WS")'},
                C3:{v:'=ROUND(10/3,2)'},
                C4:{v:'=ABS(-7)'},
                C5:{v:'=AND(A1=10,A2=20)'},
                C6:{v:'=OR(A1=99,A2=20)'},
                D1:{v:'K1'}, D2:{v:'K2'}, E1:{v:111}, E2:{v:222},
                F1:{v:'=VLOOKUP("K2",D1:E2,2)'},
                G1:{v:'=A1+A2*2'},
                H1:{v:'=A1>=10'},
                I1:{v:'=I2'}, I2:{v:'=I1'},
              }, formats:{}, freeze:{rows:0,cols:0}, protectedRanges:[], rowHeights:{}, colWidths:{}
            };

            await check('FORMULA_ENGINE_CORE', () => {
              const v = computeBackend(formulaSheet);
              assert.equal(v.B1, 60);
              assert.equal(v.B2, 20);
              assert.equal(v.B3, 10);
              assert.equal(v.B4, 30);
              assert.equal(v.B5, 3);
              assert.equal(v.C1, 'YES');
              assert.equal(v.C2, 'TWS');
              assert.equal(v.C3, 3.33);
              assert.equal(v.C4, 7);
              assert.equal(v.C5, true);
              assert.equal(v.C6, true);
              assert.equal(v.F1, 222);
              assert.equal(v.G1, 50);
              assert.equal(v.H1, true);
            });

            await check('FORMULA_FRONTEND_BACKEND_PARITY', () => {
              const a = computeBackend(formulaSheet);
              const b = computeFrontend(formulaSheet);
              for (const ref of ['B1','B2','B3','B4','B5','C1','C2','C3','C4','C5','C6','F1','G1','H1']) {
                assert.deepEqual(b[ref], a[ref], `formula mismatch at ${ref}`);
              }
            });

            await check('FORMULA_CIRCULAR_GUARD', () => {
              const v = computeBackend(formulaSheet);
              assert.ok(String(v.I1).includes('#') || String(v.I2).includes('#'), 'circular reference not surfaced');
            });

            await check('CSV_ROUNDTRIP', () => {
              const rows = [
                ['Name','Note','Arabic'],
                ['Ahmed','hello, world','مرحبا'],
                ['Quoted','He said "Hi"','سطر 1\nسطر 2'],
              ];
              const csv = stringifyCsv(rows);
              assert.deepEqual(parseCsv(csv), rows);
            });

            const exportDoc = {
              id:'baseline-sheet', title:'TWS Baseline', type:'TSHEET', status:'ACTIVE', visibility:'PRIVATE',
              contentJson:{ activeSheetId:'s1', sheets:[
                { id:'s1', name:'Main', rows:10, cols:6,
                  cells:{A1:{v:10},A2:{v:20},A3:{v:'=SUM(A1:A2)'},B1:{v:'مرحبا'}},
                  formats:{A1:{bold:true,bg:'#ffeeaa',align:'center'}}, freeze:{rows:1,cols:0}, protectedRanges:[], rowHeights:{}, colWidths:{} },
                { id:'s2', name:'Second', rows:5, cols:5, cells:{A1:{v:'Sheet 2'}}, formats:{}, freeze:{rows:0,cols:0}, protectedRanges:[], rowHeights:{}, colWidths:{} }
              ]}
            };

            let formulaPreserved = false;
            await check('XLSX_EXPORT_ROUNDTRIP', async () => {
              const buffer = await buildTSheetXlsx(exportDoc);
              assert.ok(buffer.byteLength > 1000, 'xlsx buffer unexpectedly small');
              const wb = new ExcelJS.Workbook();
              await wb.xlsx.load(buffer);
              assert.equal(wb.worksheets.length, 2);
              assert.equal(wb.getWorksheet('Main').getCell('A1').value, 10);
              assert.equal(wb.getWorksheet('Main').getCell('A3').value, 30);
              assert.equal(wb.getWorksheet('Main').getCell('B1').value, 'مرحبا');
              assert.equal(wb.getWorksheet('Second').getCell('A1').value, 'Sheet 2');
              assert.equal(wb.getWorksheet('Main').getCell('A1').font?.bold, true);
              assert.equal(wb.getWorksheet('Main').getCell('A1').alignment?.horizontal, 'center');
              const exportedFormulaCell = wb.getWorksheet('Main').getCell('A3').value;
              formulaPreserved = Boolean(exportedFormulaCell && typeof exportedFormulaCell === 'object' && exportedFormulaCell.formula);
            });
            console.log(`XLSX_FORMULA_PRESERVATION=${formulaPreserved ? 'YES' : 'NO'}`);

            await check('TSHEETS_EDITOR_BASELINE_FEATURES', () => {
              const src = fs.readFileSync('../frontend/src/pages/tws/TSheetsEditor.jsx','utf8');
              const mustHave = [
                'AUTOSAVE_DEBOUNCE_MS', 'AUTOSAVE_MAX_ATTEMPTS', 'function undo()', 'function redo()',
                'history.past.length > 50', 'sortSelection', 'protectedRanges', 'freeze', 'VersionHistoryModal',
                'PermissionsModal', 'ShareLinkModal', 'useTwsPresence'
              ];
              for (const needle of mustHave) assert.ok(src.includes(needle), `missing editor capability marker: ${needle}`);
            });

            let xlsxImport = false;
            await check('TWS_DOCUMENT_LIFECYCLE_ROUTES', () => {
              const src = fs.readFileSync('./src/routes/workspace.routes.js','utf8');
              for (const needle of [
                '/documents/:id/restore', '/documents/:id/permanent', '/documents/:id/versions/:versionId/restore',
                '/documents/:id/import/csv', '/documents/:id/export/:format'
              ]) assert.ok(src.includes(needle), `missing route: ${needle}`);
              xlsxImport = src.includes('/documents/:id/import/xlsx');
            });
            console.log(`XLSX_IMPORT=${xlsxImport ? 'YES' : 'NO'}`);

            const failures = results.filter(([, ok]) => !ok);
            console.log(`BASELINE_TESTS_TOTAL=${results.length}`);
            console.log(`BASELINE_TESTS_PASSED=${results.length - failures.length}`);
            console.log(`BASELINE_TESTS_FAILED=${failures.length}`);
            console.log('NO_PRODUCTION_DB_WRITES=YES');
            console.log('NO_TWS_DATA_MUTATION=YES');
            console.log(`CURRENT_GAP_XLSX_FORMULAS=${formulaPreserved ? 'NO' : 'YES'}`);
            console.log(`CURRENT_GAP_XLSX_IMPORT=${xlsxImport ? 'NO' : 'YES'}`);
            if (failures.length) process.exit(1);
        ''')

        node = run(["node", "--input-type=module", "-"], backend, input_text=js, check=False)
        print(node.stdout.rstrip())

    status_after = git(repo, "status", "--porcelain=v1", "--untracked-files=all")
    require(status_after == status_before, "server working tree changed during isolated baseline test")
    print("SERVER_WORKTREE_PRESERVED=YES")

    if node.returncode != 0:
        print("TWS_BASELINE_TEST_R2=FAIL")
        print("READY_FOR_UPDATE=NO")
        sys.exit(node.returncode)

    print("TWS_BASELINE_TEST_R2=PASS")
    print("READY_FOR_UPDATE=YES")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("TWS_BASELINE_TEST_R2=FAIL")
        print(f"ERROR={exc}")
        print("READY_FOR_UPDATE=NO")
        sys.exit(1)
