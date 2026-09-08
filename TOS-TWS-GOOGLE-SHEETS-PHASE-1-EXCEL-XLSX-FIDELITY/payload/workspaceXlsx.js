import ExcelJS from "exceljs";

const MAX_SHEETS = 20;
const MAX_ROWS = 500;
const MAX_COLS = 100;
const MAX_CELLS_PER_SHEET = 20000;

function clamp(value, min, max) {
  const number = Number(value);
  if (!Number.isFinite(number)) return min;
  return Math.min(max, Math.max(min, number));
}

function excelColorToHex(color) {
  if (!color || typeof color !== "object") return null;
  const argb = String(color.argb || "").replace(/[^0-9a-f]/gi, "").toUpperCase();
  if (/^[0-9A-F]{8}$/.test(argb)) return `#${argb.slice(2)}`;
  if (/^[0-9A-F]{6}$/.test(argb)) return `#${argb}`;
  return null;
}

function cellTextFromObject(value) {
  if (!value || typeof value !== "object") return "";
  if (Array.isArray(value.richText)) return value.richText.map((part) => part?.text || "").join("");
  if (typeof value.text === "string") return value.text;
  if (typeof value.hyperlink === "string") return value.text || value.hyperlink;
  if (typeof value.error === "string") return value.error;
  return "";
}

function dateText(date) {
  const iso = date.toISOString();
  const hasTime = date.getUTCHours() || date.getUTCMinutes() || date.getUTCSeconds() || date.getUTCMilliseconds();
  return hasTime ? iso.slice(0, 16).replace("T", " ") : iso.slice(0, 10);
}

function numberFormatCategory(cell) {
  const value = cell?.value;
  const format = String(cell?.numFmt || "").trim();
  if (value instanceof Date) {
    const hasTime = value.getUTCHours() || value.getUTCMinutes() || value.getUTCSeconds() || value.getUTCMilliseconds();
    return hasTime ? "datetime" : "date";
  }
  if (!format || /^general$/i.test(format)) return "general";
  if (/%/.test(format)) return "percent";
  if (/[$€£¥₹]|\b(?:SAR|USD|EUR|GBP|EGP|AED)\b|ر\.?س/i.test(format)) return "currency";
  if (/[ymd]/i.test(format)) return /[hs]/i.test(format) ? "datetime" : "date";
  if (/[0#]/.test(format)) return "number";
  return "general";
}

function borderHex(cell) {
  const border = cell?.border || {};
  for (const side of ["top", "right", "bottom", "left"]) {
    if (!border?.[side]?.style) continue;
    return excelColorToHex(border[side].color) || "#d1d5db";
  }
  return null;
}

function formatFromCell(cell) {
  const format = {};
  if (cell?.font?.bold) format.bold = true;
  if (Number.isFinite(Number(cell?.font?.size))) format.fontSize = Math.round(clamp(cell.font.size, 8, 72));
  const fontColor = excelColorToHex(cell?.font?.color);
  if (fontColor) format.color = fontColor;
  const horizontal = String(cell?.alignment?.horizontal || "").toLowerCase();
  if (["left", "center", "right"].includes(horizontal)) format.align = horizontal;
  const fillColor = excelColorToHex(cell?.fill?.fgColor);
  if (fillColor) format.bg = fillColor;
  const border = borderHex(cell);
  if (border) format.border = `1px solid ${border}`;
  const numberFormat = numberFormatCategory(cell);
  if (numberFormat !== "general") format.numberFormat = numberFormat;
  return format;
}

function rawCellValue(cell) {
  if (typeof cell?.formula === "string" && cell.formula.trim()) return `=${cell.formula}`;
  const value = cell?.value;
  if (value === undefined || value === null || value === "") return "";
  if (value instanceof Date) return dateText(value);
  if (typeof value === "boolean") return value ? "TRUE" : "FALSE";
  if (typeof value === "number" || typeof value === "string") return value;
  return cellTextFromObject(value);
}

function freezeFromWorksheet(worksheet) {
  const view = (worksheet?.views || []).find((item) => item?.state === "frozen") || null;
  return {
    rows: Math.round(clamp(view?.ySplit || 0, 0, 5)),
    cols: Math.round(clamp(view?.xSplit || 0, 0, 5)),
  };
}

function dimensionsFromWorksheet(worksheet) {
  const rowHeights = {};
  for (let rowIndex = 1; rowIndex <= Math.min(worksheet.rowCount || 0, MAX_ROWS); rowIndex += 1) {
    const heightPt = Number(worksheet.getRow(rowIndex).height);
    if (!Number.isFinite(heightPt) || heightPt <= 0) continue;
    rowHeights[String(rowIndex)] = Math.round(clamp(heightPt * (96 / 72), 24, 160));
  }

  const colWidths = {};
  for (let colIndex = 1; colIndex <= Math.min(worksheet.columnCount || 0, MAX_COLS); colIndex += 1) {
    const excelWidth = Number(worksheet.getColumn(colIndex).width);
    if (!Number.isFinite(excelWidth) || excelWidth <= 0) continue;
    colWidths[String(colIndex)] = Math.round(clamp(excelWidth * 7 + 5, 64, 260));
  }
  return { rowHeights, colWidths };
}

function uniqueSheetId(index) {
  return `sheet_${index + 1}`;
}

export async function parseTSheetXlsx(buffer) {
  if (!buffer || !Buffer.isBuffer(buffer) || buffer.length === 0) throw new Error("XLSX buffer is required");

  const workbook = new ExcelJS.Workbook();
  await workbook.xlsx.load(buffer);

  const workbookSheets = workbook.worksheets.slice(0, MAX_SHEETS);
  if (workbookSheets.length === 0) {
    return {
      activeSheetId: "sheet_1",
      sheets: [{ id: "sheet_1", name: "Sheet1", rows: 30, cols: 12, cells: {}, formats: {}, protectedRanges: [], freeze: { rows: 0, cols: 0 }, rowHeights: {}, colWidths: {} }],
    };
  }

  const sheets = workbookSheets.map((worksheet, sheetIndex) => {
    const cells = {};
    const formats = {};
    let cellCount = 0;
    let maxRow = 0;
    let maxCol = 0;

    worksheet.eachRow({ includeEmpty: false }, (row, rowNumber) => {
      if (rowNumber > MAX_ROWS || cellCount >= MAX_CELLS_PER_SHEET) return;
      row.eachCell({ includeEmpty: false }, (cell, colNumber) => {
        if (colNumber > MAX_COLS || cellCount >= MAX_CELLS_PER_SHEET) return;
        const raw = rawCellValue(cell);
        const format = formatFromCell(cell);
        const hasFormat = Object.keys(format).length > 0;
        if (raw === "" && !hasFormat) return;

        const ref = cell.address.toUpperCase();
        if (raw !== "") {
          cells[ref] = { v: raw };
          cellCount += 1;
        }
        if (hasFormat) formats[ref] = format;
        maxRow = Math.max(maxRow, rowNumber);
        maxCol = Math.max(maxCol, colNumber);
      });
    });

    const { rowHeights, colWidths } = dimensionsFromWorksheet(worksheet);
    const rows = Math.min(MAX_ROWS, Math.max(maxRow, Math.min(worksheet.actualRowCount || 0, MAX_ROWS), 10));
    const cols = Math.min(MAX_COLS, Math.max(maxCol, Math.min(worksheet.actualColumnCount || 0, MAX_COLS), 5));

    return {
      id: uniqueSheetId(sheetIndex),
      name: String(worksheet.name || `Sheet${sheetIndex + 1}`).slice(0, 80),
      rows,
      cols,
      cells,
      formats,
      protectedRanges: [],
      freeze: freezeFromWorksheet(worksheet),
      rowHeights,
      colWidths,
    };
  });

  const requestedActiveIndex = Number(workbook.views?.[0]?.activeTab);
  const activeIndex = Number.isInteger(requestedActiveIndex) && requestedActiveIndex >= 0 && requestedActiveIndex < sheets.length ? requestedActiveIndex : 0;
  return { activeSheetId: sheets[activeIndex].id, sheets };
}
