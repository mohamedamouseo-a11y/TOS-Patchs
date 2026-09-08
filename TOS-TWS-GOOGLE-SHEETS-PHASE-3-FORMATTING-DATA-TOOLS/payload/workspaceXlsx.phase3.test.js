import test from "node:test";
import assert from "node:assert/strict";
import ExcelJS from "exceljs";
import { buildTSheetXlsx } from "./workspaceExport.js";
import { parseTSheetXlsx } from "./workspaceXlsx.js";

function phase3Document() {
  return {
    id: "phase3-sheet",
    title: "Phase 3",
    type: "TSHEET",
    contentJson: {
      activeSheetId: "sheet_1",
      sheets: [{
        id: "sheet_1", name: "Data Tools", rows: 12, cols: 6,
        cells: {
          A1: { v: "Merged title" },
          A2: { v: "Name" }, B2: { v: "Score" }, C2: { v: "Status" },
          A3: { v: "Ahmed" }, B3: { v: 90 }, C3: { v: "Done" },
          A4: { v: "Sara" }, B4: { v: 55 }, C4: { v: "Pending" },
        },
        formats: {
          A1: { bold: true, italic: true, underline: true, strike: true, wrap: true, vertical: "middle", align: "center", bg: "#fef3c7" },
        },
        merges: [{ id: "m1", start: "A1", end: "B1" }],
        dataValidations: [{ id: "v1", start: "C3", end: "C4", type: "list", values: ["Done", "Pending"], allowBlank: true }],
        conditionalFormats: [],
        filter: { start: "A2", end: "C4", criteria: {} },
        protectedRanges: [], freeze: { rows: 1, cols: 0 }, rowHeights: {}, colWidths: {},
      }],
    },
  };
}

test("Phase 3 XLSX export carries merge, rich formatting, validation and filter", async () => {
  const buffer = await buildTSheetXlsx(phase3Document());
  const workbook = new ExcelJS.Workbook();
  await workbook.xlsx.load(buffer);
  const ws = workbook.getWorksheet("Data Tools");
  assert.ok(ws);
  assert.equal(ws.getCell("A1").font?.italic, true);
  assert.ok(ws.getCell("A1").font?.underline);
  assert.equal(ws.getCell("A1").font?.strike, true);
  assert.equal(ws.getCell("A1").alignment?.wrapText, true);
  assert.equal(ws.getCell("A1").alignment?.vertical, "middle");
  assert.ok((ws.model?.merges || []).includes("A1:B1"));
  assert.equal(ws.getCell("C3").dataValidation?.type, "list");
  assert.match(String(ws.getCell("C3").dataValidation?.formulae?.[0] || ""), /Done/);
  assert.ok(ws.autoFilter);
});

test("Phase 3 XLSX import restores merge, rich formatting and inline list validation", async () => {
  const workbook = new ExcelJS.Workbook();
  const ws = workbook.addWorksheet("Import Tools");
  ws.getCell("A1").value = "Title";
  ws.getCell("A1").font = { bold: true, italic: true, underline: true, strike: true };
  ws.getCell("A1").alignment = { horizontal: "center", vertical: "middle", wrapText: true };
  ws.mergeCells("A1:B1");
  ws.getCell("C2").value = "Done";
  ws.getCell("C2").dataValidation = { type: "list", allowBlank: true, formulae: ['"Done,Pending"'] };
  ws.autoFilter = "A2:C5";

  const buffer = Buffer.from(await workbook.xlsx.writeBuffer());
  const parsed = await parseTSheetXlsx(buffer);
  const sheet = parsed.sheets[0];
  assert.equal(sheet.formats.A1.italic, true);
  assert.equal(sheet.formats.A1.underline, true);
  assert.equal(sheet.formats.A1.strike, true);
  assert.equal(sheet.formats.A1.wrap, true);
  assert.equal(sheet.formats.A1.vertical, "middle");
  assert.ok(sheet.merges.some((merge) => merge.start === "A1" && merge.end === "B1"));
  assert.ok(sheet.dataValidations.some((rule) => rule.start === "C2" && rule.values.includes("Pending")));
  assert.equal(sheet.filter?.start, "A2");
  assert.equal(sheet.filter?.end, "C5");
});
