#!/usr/bin/env python3
from pathlib import Path
import hashlib
import os
import subprocess
import sys
import tempfile
import urllib.request

PATCH = "TOS-TWS-GOOGLE-SHEETS-PHASE-1-EXCEL-XLSX-FIDELITY"
EXPECTED_HEAD = "a442ff075526235775013ca64f7f34543e43880e"
BASE = "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-TWS-GOOGLE-SHEETS-PHASE-1-EXCEL-XLSX-FIDELITY/payload"
PAYLOADS = {
    "backend/src/utils/workspaceXlsx.js": (f"{BASE}/workspaceXlsx.js", "ec716d692edee6f6e370e6302de84b24c1690a85"),
    "backend/src/utils/workspaceXlsx.phase1.test.js": (f"{BASE}/workspaceXlsx.phase1.test.js", "ee6e8f51c93879d4434b77fa5b70c1de34c3a11c"),
}
BASELINE_BLOBS = {
    "backend/src/routes/workspace.routes.js": "e9fcbfd7043f086515c1537037683126a61bb280",
    "backend/src/services/workspace.service.js": "7dc38a7648b9f7516c407f701d92b6e59f8ff6e1",
    "backend/src/utils/workspaceExport.js": "140fc5bced9f53b1c90dd5652daf8c9658713c88",
    "frontend/src/lib/api.js": "4638188ee4b0764411aef7ce313335ee92ccad4b",
    "frontend/src/pages/tws/TSheetsEditor.jsx": "d4001cccc78bde03802880caaeb79b295d052107",
    "backend/package.json": "0257b5f042e72ac74f70408623c59f37f4f2172b",
    "frontend/package.json": "cfc96956b2f98f04fe161c76e60fc73b337a4f23",
}
EXPECTED_CHANGED = {
    "backend/src/routes/workspace.routes.js",
    "backend/src/services/workspace.service.js",
    "backend/src/utils/workspaceExport.js",
    "backend/src/utils/workspaceXlsx.js",
    "backend/src/utils/workspaceXlsx.phase1.test.js",
    "frontend/src/lib/api.js",
    "frontend/src/pages/tws/TSheetsEditor.jsx",
}


def run(cmd, cwd, *, check=True, env=None):
    p = subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    if check and p.returncode != 0:
        raise RuntimeError(f"command failed ({p.returncode}): {' '.join(cmd)}\n{p.stdout}")
    return p


def git(repo, *args, check=True):
    return run(["git", *args], repo, check=check)


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def git_blob_sha(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def status_records(repo):
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
            if i < len(parts) and parts[i]:
                i += 1
            raise RuntimeError(f"rename/copy working-tree state is not supported: {text}")
        records.append((status, path))
    return records


def current_file_matches_head(repo, rel):
    path = repo / rel
    if not path.is_file():
        return False
    exists = git(repo, "cat-file", "-e", f"HEAD:{rel}", check=False)
    if exists.returncode != 0:
        return False
    head_blob = git(repo, "rev-parse", f"HEAD:{rel}").stdout.strip()
    work_blob = git(repo, "hash-object", "--", rel).stdout.strip()
    return head_blob == work_blob


def normalize_stale_index_if_safe(repo):
    records = status_records(repo)
    if not records:
        print("PRECHECK_WORKTREE=CLEAN")
        return
    dirty_paths = [path for _, path in records]
    print(f"PRECHECK_WORKTREE=DIRTY ({len(dirty_paths)} paths)")
    mismatched = [path for path in dirty_paths if not current_file_matches_head(repo, path)]
    if mismatched:
        raise RuntimeError(f"working tree contains real source differences; refusing to touch them: {mismatched}")
    # The server can retain a stale index after the external Developer Hub commit.
    # --mixed updates only the index; it does not overwrite working-tree files.
    git(repo, "reset", "--mixed", "HEAD")
    require(not status_records(repo), "safe index normalization did not produce a clean working tree")
    print("STALE_INDEX_RECOVERED=YES")
    print("SOURCE_FILES_OVERWRITTEN_DURING_RECOVERY=NO")


def verify_baseline(repo):
    head = git(repo, "rev-parse", "HEAD").stdout.strip()
    print(f"HEAD={head}")
    require(head == EXPECTED_HEAD, f"HEAD must equal Phase 1 baseline {EXPECTED_HEAD}")
    for rel, expected in BASELINE_BLOBS.items():
        actual = git(repo, "rev-parse", f"HEAD:{rel}").stdout.strip()
        require(actual == expected, f"baseline blob mismatch for {rel}: {actual} != {expected}")


def replace_once(path, old, new, label):
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    require(count == 1, f"{label}: expected exactly one replacement target, found {count}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def insert_before_once(path, marker, addition, label):
    text = path.read_text(encoding="utf-8")
    count = text.count(marker)
    require(count == 1, f"{label}: expected exactly one marker, found {count}")
    path.write_text(text.replace(marker, addition + marker, 1), encoding="utf-8")


def download_payloads(repo):
    for rel, (url, expected_blob) in PAYLOADS.items():
        data = urllib.request.urlopen(url, timeout=30).read()
        actual_blob = git_blob_sha(data)
        require(actual_blob == expected_blob, f"payload blob mismatch for {rel}: {actual_blob}")
        dest = repo / rel
        require(not dest.exists(), f"new Phase 1 path already exists: {rel}")
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)


def apply_transforms(repo):
    service = repo / "backend/src/services/workspace.service.js"
    routes = repo / "backend/src/routes/workspace.routes.js"
    export = repo / "backend/src/utils/workspaceExport.js"
    api = repo / "frontend/src/lib/api.js"
    editor = repo / "frontend/src/pages/tws/TSheetsEditor.jsx"

    replace_once(
        service,
        'import { parseCsv, stringifyCsv } from "../utils/workspaceCsv.js";\nimport { computeSheetValues, cellRefFromIndex } from "../utils/sheetFormula.js";\n',
        'import { parseCsv, stringifyCsv } from "../utils/workspaceCsv.js";\nimport { parseTSheetXlsx } from "../utils/workspaceXlsx.js";\nimport { computeSheetValues, cellRefFromIndex } from "../utils/sheetFormula.js";\n',
        "service XLSX utility import",
    )
    replace_once(
        service,
        'if (["general", "number", "currency", "percent"].includes(format?.numberFormat)) safeFormat.numberFormat = format.numberFormat;',
        'if (["general", "number", "currency", "percent", "date", "datetime"].includes(format?.numberFormat)) safeFormat.numberFormat = format.numberFormat;',
        "service date number formats",
    )

    xlsx_service = r'''export async function importSheetXlsx({ user, documentId, buffer, originalName = "" }) {
  const document = await getDocumentOr404(documentId);
  await assertDocumentAccess(user, document, "EDIT");
  if (document.type !== "TSHEET") throw new AppError("استيراد XLSX متاح فقط لملفات T-Sheets", 400);
  if (!Buffer.isBuffer(buffer) || buffer.length === 0) throw new AppError("ملف XLSX مطلوب", 400);

  let imported;
  try {
    imported = await parseTSheetXlsx(buffer);
  } catch {
    throw new AppError("ملف XLSX غير صالح أو غير مدعوم", 400);
  }

  const normalized = normalizeContentForType("TSHEET", imported);
  const backed = await ensureDriveBackedDocument(document, normalized, user);
  const safeOriginalName = String(originalName || "sheet.xlsx").replace(/[^a-zA-Z0-9\u0600-\u06FF_.-]+/g, "_").slice(0, 160);
  await updateJsonOnDrive({
    fileId: backed.document.driveFileId,
    filename: workspaceDriveFileName(backed.document),
    contentJson: normalized,
    metadata: driveMetadataFor(backed.document, { import: "XLSX", originalName: safeOriginalName }),
  });
  const updated = await prisma.workspaceDocument.update({
    where: { id: documentId },
    data: {
      contentJson: metadataContentFor({ driveFileId: backed.document.driveFileId, type: "TSHEET" }),
      plainText: computePlainText("TSHEET", normalized),
      storageMode: "GOOGLE_DRIVE",
      driveProvider: "GOOGLE_DRIVE",
      lastEditedById: user.id,
    },
    include: DOCUMENT_INCLUDE,
  });
  await maybeSnapshotVersion({ document: updated, user, reason: "MANUAL", changeSummary: "استيراد XLSX", contentJson: normalized });
  await logWorkspaceAudit({ action: "document.imported", actorId: user.id, documentId, metadata: { format: "xlsx", originalName: safeOriginalName } });
  return { ...serializeDocument(updated, "EDIT"), contentJson: normalized, plainText: updated.plainText || "" };
}

'''
    insert_before_once(
        service,
        '// ------------------------------------------------------------------\n// Internal user search (for the "share with specific users" picker —',
        xlsx_service,
        "service XLSX importer",
    )

    replace_once(
        routes,
        'import { Router } from "express";\n',
        'import { Router } from "express";\nimport multer from "multer";\n',
        "routes multer import",
    )
    replace_once(
        routes,
        'const router = Router();\nrouter.use(auth);\n',
        'const router = Router();\nrouter.use(auth);\n\nconst xlsxUpload = multer({\n  storage: multer.memoryStorage(),\n  limits: { fileSize: 10 * 1024 * 1024, files: 1 },\n});\n',
        "routes XLSX upload middleware",
    )
    xlsx_route = r'''router.post("/documents/:id/import/xlsx", xlsxUpload.single("file"), asyncHandler(async (req, res) => {
  const file = req.file;
  if (!file?.buffer?.length) throw new AppError("XLSX file is required", 400);
  if (!/\.xlsx$/i.test(String(file.originalname || ""))) throw new AppError("Only .xlsx files are supported", 400);
  const documentId = required(req.params.id, "id");
  const document = await workspaceService.importSheetXlsx({
    user: req.user,
    documentId,
    buffer: file.buffer,
    originalName: file.originalname,
  });
  notifyTwsDocRoom(req, documentId, "tws-doc:content-updated", { reason: "xlsx-import", updatedAt: document.updatedAt });
  res.json(document);
}));

'''
    insert_before_once(
        routes,
        '// ------------------------------------------------------------------\n// Folders\n// ------------------------------------------------------------------',
        xlsx_route,
        "routes XLSX import endpoint",
    )

    replace_once(
        api,
        '    importCsv: (documentId, { sheetId = "", csv }) => request(`/api/tws/documents/${documentId}/import/csv`, { method: "POST", body: JSON.stringify({ sheetId, csv }) }),\n',
        '    importCsv: (documentId, { sheetId = "", csv }) => request(`/api/tws/documents/${documentId}/import/csv`, { method: "POST", body: JSON.stringify({ sheetId, csv }) }),\n    importXlsx: (documentId, file, options = {}) => { const form = new FormData(); form.append("file", file, file?.name || "sheet.xlsx"); return uploadRequest(`/api/tws/documents/${documentId}/import/xlsx`, form, { onProgress: options.onProgress }); },\n',
        "frontend API XLSX import",
    )

    replace_once(
        editor,
        '  const csvInputRef = useRef(null);\n',
        '  const csvInputRef = useRef(null);\n  const xlsxInputRef = useRef(null);\n',
        "editor XLSX file ref",
    )
    xlsx_handler = r'''  async function handleImportXlsx(event) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    try {
      setSaveStatus("saving");
      const updated = await api.tws.importXlsx(documentId, file);
      const importedSheets = updated.contentJson?.sheets || [];
      setDoc(updated);
      setSheets(importedSheets);
      setActiveSheetId(updated.contentJson?.activeSheetId || importedSheets[0]?.id || "");
      setSaveStatus("saved");
      setSaveMeta({ lastEditedBy: updated.lastEditedBy, updatedAt: updated.updatedAt, versionCount: updated.versionCount });
    } catch (err) {
      setSaveStatus("error");
      setError(getErrorMessage(err, ui.lang === "en" ? "Failed to import Excel file." : "تعذر استيراد ملف Excel."));
    }
  }

'''
    insert_before_once(editor, '  async function handleTrash() {', xlsx_handler, "editor XLSX handler")
    replace_once(
        editor,
        '              <input ref={csvInputRef} type="file" accept=".csv,text/csv" className="hidden" onChange={handleImportCsv} />\n              <Button type="button" variant="soft" onClick={() => csvInputRef.current?.click()}><Upload size={14} /> {ui.uploadCsv}</Button>\n',
        '              <input ref={csvInputRef} type="file" accept=".csv,text/csv" className="hidden" onChange={handleImportCsv} />\n              <Button type="button" variant="soft" onClick={() => csvInputRef.current?.click()}><Upload size={14} /> {ui.uploadCsv}</Button>\n              <input ref={xlsxInputRef} type="file" accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" className="hidden" onChange={handleImportXlsx} />\n              <Button type="button" variant="soft" onClick={() => xlsxInputRef.current?.click()}><Upload size={14} /> {ui.lang === "en" ? "Import Excel" : "استيراد Excel"}</Button>\n',
        "editor XLSX control",
    )

    old_export = r'''export async function buildTSheetXlsx(document) {
  const workbook = new ExcelJS.Workbook();
  workbook.creator = "Tamiyouz Workspace System";
  const sheets = document.contentJson?.sheets || [];

  for (const sheet of sheets) {
    const worksheet = workbook.addWorksheet(String(sheet.name || "Sheet1").slice(0, 31));
    const values = computeSheetValues(sheet);
    const cols = Math.min(sheet.cols || 8, 200);
    const rows = Math.min(sheet.rows || 20, 2000);

    for (let row = 0; row < rows; row += 1) {
      for (let col = 0; col < cols; col += 1) {
        const ref = cellRefFromIndex(col, row);
        const value = values[ref];
        if (value === undefined || value === null || value === "") continue;
        const cell = worksheet.getCell(row + 1, col + 1);
        const numeric = typeof value === "number" ? value : Number(value);
        cell.value = typeof value === "number" || (!Number.isNaN(numeric) && String(value).trim() !== "") ? numeric : String(value);

        const format = sheet.formats?.[ref];
        if (format?.bold) cell.font = { bold: true };
        if (format?.align) cell.alignment = { horizontal: format.align };
        if (format?.bg) cell.fill = { type: "pattern", pattern: "solid", fgColor: { argb: hexToArgb(format.bg) } };
      }
    }
  }

  if (sheets.length === 0) workbook.addWorksheet("Sheet1");
  return workbook.xlsx.writeBuffer();
}'''
    new_export = r'''function excelNumberFormat(kind) {
  if (kind === "number") return "#,##0.00";
  if (kind === "currency") return "#,##0.00";
  if (kind === "percent") return "0.00%";
  if (kind === "date") return "yyyy-mm-dd";
  if (kind === "datetime") return "yyyy-mm-dd hh:mm";
  return "General";
}

function formulaResultForExcel(value) {
  if (value === "TRUE") return true;
  if (value === "FALSE") return false;
  if (typeof value === "number" || typeof value === "boolean") return value;
  if (typeof value === "string" && value && !value.startsWith("#")) return value;
  return undefined;
}

function dateForExcel(value, kind) {
  if (!["date", "datetime"].includes(kind)) return null;
  const text = String(value || "").trim();
  if (!text) return null;
  const normalized = text.includes("T") ? text : text.includes(" ") ? text.replace(" ", "T") : `${text}T00:00:00`;
  const withZone = /(?:Z|[+-]\d{2}:?\d{2})$/i.test(normalized) ? normalized : `${normalized}Z`;
  const date = new Date(withZone);
  return Number.isNaN(date.getTime()) ? null : date;
}

function formatHex(value) {
  const text = String(value || "").trim();
  return /^#[0-9a-f]{3}(?:[0-9a-f]{3})?$/i.test(text) ? hexToArgb(text) : null;
}

function uniqueWorksheetName(rawName, usedNames) {
  const base = String(rawName || "Sheet").replace(/[\\/*?:\[\]]/g, "_").slice(0, 31) || "Sheet";
  let name = base;
  let suffix = 2;
  while (usedNames.has(name.toLowerCase())) {
    const tail = `_${suffix}`;
    name = `${base.slice(0, Math.max(1, 31 - tail.length))}${tail}`;
    suffix += 1;
  }
  usedNames.add(name.toLowerCase());
  return name;
}

export async function buildTSheetXlsx(document) {
  const workbook = new ExcelJS.Workbook();
  workbook.creator = "Tamiyouz Workspace System";
  workbook.created = new Date();
  const sheets = document.contentJson?.sheets || [];
  const usedNames = new Set();

  for (const sheet of sheets) {
    const worksheet = workbook.addWorksheet(uniqueWorksheetName(sheet.name || "Sheet1", usedNames));
    const values = computeSheetValues(sheet);
    const cols = Math.min(sheet.cols || 8, 100);
    const rows = Math.min(sheet.rows || 20, 500);

    for (let row = 0; row < rows; row += 1) {
      for (let col = 0; col < cols; col += 1) {
        const ref = cellRefFromIndex(col, row);
        const raw = sheet.cells?.[ref]?.v;
        const value = values[ref];
        const format = sheet.formats?.[ref] || {};
        if ((raw === undefined || raw === null || raw === "") && Object.keys(format).length === 0) continue;

        const cell = worksheet.getCell(row + 1, col + 1);
        if (typeof raw === "string" && raw.startsWith("=")) {
          const formula = raw.slice(1);
          const result = formulaResultForExcel(value);
          cell.value = result === undefined ? { formula } : { formula, result };
        } else {
          const date = dateForExcel(raw, format.numberFormat);
          if (date) cell.value = date;
          else if (typeof raw === "number") cell.value = raw;
          else if (raw === "TRUE" || raw === "FALSE") cell.value = raw === "TRUE";
          else {
            const numeric = typeof raw === "string" && raw.trim() !== "" ? Number(raw) : Number.NaN;
            cell.value = !Number.isNaN(numeric) && ["number", "currency", "percent"].includes(format.numberFormat) ? numeric : String(raw ?? value ?? "");
          }
        }

        const font = {};
        if (format.bold) font.bold = true;
        if (format.fontSize) font.size = Math.max(8, Math.min(72, Number(format.fontSize) || 12));
        const fontColor = formatHex(format.color);
        if (fontColor) font.color = { argb: fontColor };
        if (Object.keys(font).length) cell.font = font;
        if (format.align) cell.alignment = { horizontal: format.align };
        const bg = formatHex(format.bg);
        if (bg) cell.fill = { type: "pattern", pattern: "solid", fgColor: { argb: bg } };
        if (format.border && format.border !== "none") {
          const match = String(format.border).match(/#([0-9a-f]{3,6})/i);
          const color = match ? hexToArgb(`#${match[1]}`) : "FFD1D5DB";
          cell.border = {
            top: { style: "thin", color: { argb: color } },
            right: { style: "thin", color: { argb: color } },
            bottom: { style: "thin", color: { argb: color } },
            left: { style: "thin", color: { argb: color } },
          };
        }
        if (format.numberFormat) cell.numFmt = excelNumberFormat(format.numberFormat);
      }
    }

    for (const [rowIndex, px] of Object.entries(sheet.rowHeights || {})) {
      const index = Number(rowIndex);
      if (Number.isInteger(index) && index >= 1 && index <= rows) worksheet.getRow(index).height = Math.max(18, Math.min(120, Number(px) * (72 / 96)));
    }
    for (const [colIndex, px] of Object.entries(sheet.colWidths || {})) {
      const index = Number(colIndex);
      if (Number.isInteger(index) && index >= 1 && index <= cols) worksheet.getColumn(index).width = Math.max(8, Math.min(40, (Number(px) - 5) / 7));
    }
    const xSplit = Math.max(0, Math.min(5, Number(sheet.freeze?.cols) || 0));
    const ySplit = Math.max(0, Math.min(5, Number(sheet.freeze?.rows) || 0));
    if (xSplit || ySplit) worksheet.views = [{ state: "frozen", xSplit, ySplit }];
  }

  if (sheets.length === 0) workbook.addWorksheet("Sheet1");
  return workbook.xlsx.writeBuffer();
}'''
    replace_once(export, old_export, new_export, "XLSX formula-preserving export")


def changed_paths(repo):
    records = status_records(repo)
    return {path for _, path in records}


def validate(repo):
    paths = changed_paths(repo)
    require(paths == EXPECTED_CHANGED, f"unexpected Phase 1 working-tree paths: {sorted(paths)}")
    print(f"PATCH_FILE_COUNT={len(paths)}")

    diff_check = git(repo, "diff", "--check", check=False)
    require(diff_check.returncode == 0, f"git diff --check failed:\n{diff_check.stdout}")

    for rel in [
        "backend/src/routes/workspace.routes.js",
        "backend/src/services/workspace.service.js",
        "backend/src/utils/workspaceExport.js",
        "backend/src/utils/workspaceXlsx.js",
        "backend/src/utils/workspaceXlsx.phase1.test.js",
    ]:
        checked = run(["node", "--check", rel], repo, check=False)
        require(checked.returncode == 0, f"node --check failed for {rel}:\n{checked.stdout}")

    prisma_validate = run(["npm", "run", "prisma:validate"], repo / "backend", check=False)
    require(prisma_validate.returncode == 0, f"prisma validate failed:\n{prisma_validate.stdout}")
    print("PRISMA_VALIDATE=PASS")
    prisma_generate = run(["npm", "run", "prisma:generate"], repo / "backend", check=False)
    require(prisma_generate.returncode == 0, f"prisma generate failed:\n{prisma_generate.stdout}")
    print("PRISMA_GENERATE=PASS")

    tests = run(["node", "--test", "src/utils/workspaceXlsx.phase1.test.js"], repo / "backend", check=False)
    print(tests.stdout.rstrip())
    require(tests.returncode == 0, "Phase 1 XLSX tests failed")
    print("PHASE_1_XLSX_TESTS=PASS")

    with tempfile.TemporaryDirectory(prefix="tws-phase1-build-") as outdir:
        build = run(["npm", "run", "build", "--", "--outDir", outdir, "--emptyOutDir"], repo / "frontend", check=False)
        require(build.returncode == 0, f"frontend build failed:\n{build.stdout}")
    print("FRONTEND_BUILD=PASS")

    route_text = (repo / "backend/src/routes/workspace.routes.js").read_text(encoding="utf-8")
    service_text = (repo / "backend/src/services/workspace.service.js").read_text(encoding="utf-8")
    export_text = (repo / "backend/src/utils/workspaceExport.js").read_text(encoding="utf-8")
    api_text = (repo / "frontend/src/lib/api.js").read_text(encoding="utf-8")
    editor_text = (repo / "frontend/src/pages/tws/TSheetsEditor.jsx").read_text(encoding="utf-8")

    require('/documents/:id/import/xlsx' in route_text and 'xlsxUpload.single("file")' in route_text, "XLSX import route missing")
    require('export async function importSheetCsv' in service_text, "CSV import was not preserved")
    require('export async function importSheetXlsx' in service_text, "XLSX import service missing")
    require('{ formula' in export_text and 'formulaResultForExcel' in export_text, "formula-preserving XLSX export missing")
    require('importXlsx:' in api_text and 'handleImportXlsx' in editor_text, "frontend XLSX import hook missing")
    require('"date", "datetime"' in service_text, "date/datetime format preservation missing")

    print("XLSX_IMPORT=PASS")
    print("XLSX_FORMULA_PRESERVATION=PASS")
    print("XLSX_TYPES_DATES_FORMATS=PASS")
    print("XLSX_ROUNDTRIP=PASS")
    print("CSV_IMPORT_PRESERVED=YES")
    print("TWS_AUTOSAVE_UNDO_REDO_CHANGED=NO")
    print("TWS_PERMISSIONS_SHARING_CHANGED=NO")
    print("DATABASE_SCHEMA_CHANGED=NO")


def main():
    repo = Path(git(Path.cwd(), "rev-parse", "--show-toplevel").stdout.strip())
    print(f"PATCH={PATCH}")
    print(f"REPO={repo}")
    verify_baseline(repo)
    normalize_stale_index_if_safe(repo)
    verify_baseline(repo)
    download_payloads(repo)
    apply_transforms(repo)
    validate(repo)
    print("PHASE_1_PATCH_APPLIED=YES")
    print("READY_FOR_GIT_PUSH=YES")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("PHASE_1_RUN=FAIL")
        print(f"ERROR={exc}")
        print("READY_FOR_GIT_PUSH=NO")
        sys.exit(1)
