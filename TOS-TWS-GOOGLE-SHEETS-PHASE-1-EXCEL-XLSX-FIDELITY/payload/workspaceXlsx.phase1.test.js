import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import ExcelJS from "exceljs";
import { parseTSheetXlsx } from "./workspaceXlsx.js";
import { buildTSheetXlsx } from "./workspaceExport.js";

function internalSheetDocument() {
  return {
    id: "phase1-sheet",
    title: "Phase 1 Fidelity",
    type: "TSHEET",
    contentJson: {
      activeSheetId: "sheet_1",
      sheets: [
        {
          id: "sheet_1",
          name: "Main",
          rows: 20,
          cols: 8,
          cells: {
            A1: { v: 10 },
            A2: { v: 20 },
            A3: { v: "=SUM(A1:A2)" },
            B1: { v: "مرحبا" },
            C1: { v: "2026-09-08" },
            D1: { v: 0.25 },
          },
          formats: {
            A1: { bold: true, align: "center", bg: "#ffeeaa", color: "#112233", fontSize: 16, border: "1px solid #334455", numberFormat: "number" },
            C1: { numberFormat: "date" },
            D1: { numberFormat: "percent" },
          },
          protectedRanges: [],
          freeze: { rows: 1, cols: 1 },
          rowHeights: { "1": 32 },
          colWidths: { "1": 120 },
        },
        {
          id: "sheet_2",
          name: "Second",
          rows: 10,
          cols: 5,
          cells: { A1: { v: "Sheet 2" } },
          formats: {},
          protectedRanges: [],
          freeze: { rows: 0, cols: 0 },
          rowHeights: {},
          colWidths: {},
        },
      ],
    },
  };
}

test("XLSX export preserves formulas, types, formats, dimensions and freeze panes", async () => {
  const buffer = await buildTSheetXlsx(internalSheetDocument());
  assert.ok(buffer.byteLength > 1000);

  const workbook = new ExcelJS.Workbook();
  await workbook.xlsx.load(buffer);
  assert.equal(workbook.worksheets.length, 2);

  const main = workbook.getWorksheet("Main");
  assert.ok(main);
  assert.equal(main.getCell("A1").value, 10);
  assert.equal(main.getCell("A3").formula, "SUM(A1:A2)");
  assert.equal(main.getCell("A3").result, 30);
  assert.equal(main.getCell("B1").value, "مرحبا");
  assert.ok(main.getCell("C1").value instanceof Date);
  assert.equal(main.getCell("D1").value, 0.25);
  assert.match(String(main.getCell("D1").numFmt || ""), /%/);
  assert.equal(main.getCell("A1").font?.bold, true);
  assert.equal(main.getCell("A1").font?.size, 16);
  assert.equal(main.getCell("A1").alignment?.horizontal, "center");
  assert.equal(main.getCell("A1").fill?.fgColor?.argb?.slice(-6), "FFEEAA");
  assert.ok(main.views.some((view) => view.state === "frozen" && view.xSplit === 1 && view.ySplit === 1));
  assert.ok(Number(main.getRow(1).height) > 0);
  assert.ok(Number(main.getColumn(1).width) > 0);
});

test("XLSX import preserves formulas, dates, booleans, styles and multiple sheets", async () => {
  const workbook = new ExcelJS.Workbook();
  const main = workbook.addWorksheet("Imported");
  main.getCell("A1").value = 10;
  main.getCell("A2").value = 20;
  main.getCell("A3").value = { formula: "SUM(A1:A2)", result: 30 };
  main.getCell("B1").value = new Date("2026-09-08T00:00:00.000Z");
  main.getCell("B1").numFmt = "yyyy-mm-dd";
  main.getCell("C1").value = true;
  main.getCell("D1").value = "مرحبا";
  main.getCell("A1").font = { bold: true, size: 15, color: { argb: "FF123456" } };
  main.getCell("A1").alignment = { horizontal: "center" };
  main.getCell("A1").fill = { type: "pattern", pattern: "solid", fgColor: { argb: "FFFFEEAA" } };
  main.getCell("A1").border = { bottom: { style: "thin", color: { argb: "FF334455" } } };
  main.views = [{ state: "frozen", xSplit: 1, ySplit: 1 }];
  main.getRow(1).height = 24;
  main.getColumn(1).width = 18;
  workbook.addWorksheet("Second").getCell("A1").value = "Sheet 2";

  const buffer = Buffer.from(await workbook.xlsx.writeBuffer());
  const parsed = await parseTSheetXlsx(buffer);
  assert.equal(parsed.sheets.length, 2);
  assert.equal(parsed.sheets[0].cells.A1.v, 10);
  assert.equal(parsed.sheets[0].cells.A3.v, "=SUM(A1:A2)");
  assert.equal(parsed.sheets[0].cells.B1.v, "2026-09-08");
  assert.equal(parsed.sheets[0].cells.C1.v, "TRUE");
  assert.equal(parsed.sheets[0].cells.D1.v, "مرحبا");
  assert.equal(parsed.sheets[0].formats.A1.bold, true);
  assert.equal(parsed.sheets[0].formats.A1.align, "center");
  assert.equal(parsed.sheets[0].formats.A1.bg, "#FFEEAA");
  assert.equal(parsed.sheets[0].formats.A1.color, "#123456");
  assert.equal(parsed.sheets[0].formats.A1.fontSize, 15);
  assert.equal(parsed.sheets[0].formats.A1.border, "1px solid #334455");
  assert.equal(parsed.sheets[0].formats.B1.numberFormat, "date");
  assert.deepEqual(parsed.sheets[0].freeze, { rows: 1, cols: 1 });
  assert.ok(Number(parsed.sheets[0].rowHeights["1"]) >= 24);
  assert.ok(Number(parsed.sheets[0].colWidths["1"]) >= 64);
});

test("XLSX export-import round trip keeps the formula contract", async () => {
  const exported = await buildTSheetXlsx(internalSheetDocument());
  const parsed = await parseTSheetXlsx(Buffer.from(exported));
  const main = parsed.sheets.find((sheet) => sheet.name === "Main");
  assert.ok(main);
  assert.equal(main.cells.A1.v, 10);
  assert.equal(main.cells.A3.v, "=SUM(A1:A2)");
  assert.equal(main.cells.B1.v, "مرحبا");
  assert.equal(main.formats.C1.numberFormat, "date");
  assert.equal(main.formats.D1.numberFormat, "percent");
});

test("Phase 1 routes and frontend hooks coexist with CSV import", () => {
  const routes = fs.readFileSync(new URL("../routes/workspace.routes.js", import.meta.url), "utf8");
  const service = fs.readFileSync(new URL("../services/workspace.service.js", import.meta.url), "utf8");
  const api = fs.readFileSync(new URL("../../../frontend/src/lib/api.js", import.meta.url), "utf8");
  const editor = fs.readFileSync(new URL("../../../frontend/src/pages/tws/TSheetsEditor.jsx", import.meta.url), "utf8");

  assert.ok(routes.includes('/documents/:id/import/csv'));
  assert.ok(routes.includes('/documents/:id/import/xlsx'));
  assert.ok(routes.includes('xlsxUpload.single("file")'));
  assert.ok(service.includes("export async function importSheetCsv"));
  assert.ok(service.includes("export async function importSheetXlsx"));
  assert.ok(api.includes("importCsv:"));
  assert.ok(api.includes("importXlsx:"));
  assert.ok(editor.includes("handleImportCsv"));
  assert.ok(editor.includes("handleImportXlsx"));
  assert.ok(editor.includes(".xlsx"));
});
