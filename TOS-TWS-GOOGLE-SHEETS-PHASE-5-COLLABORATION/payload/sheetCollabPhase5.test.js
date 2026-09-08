import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";

import * as backend from "./sheetCollabPhase5.js";
import * as frontend from "../../../frontend/src/pages/tws/sheetCollabPhase5.js";

function baseContent() {
  return {
    activeSheetId: "sheet_1",
    namedRanges: [],
    sheets: [{
      id: "sheet_1",
      name: "Sheet1",
      rows: 30,
      cols: 12,
      cells: { A1: { v: 1 }, B1: { v: 2 }, C1: { v: 3 } },
      formats: { A1: { bold: true } },
      merges: [], dataValidations: [], conditionalFormats: [], filter: null,
      protectedRanges: [], freeze: { rows: 0, cols: 0 }, rowHeights: {}, colWidths: {},
    }],
  };
}

test("Phase 5 builds minimal cell/format deltas", () => {
  const before = baseContent().sheets[0];
  const after = { ...before, cells: { ...before.cells, A1: { v: 10 }, D1: { v: "=A1+B1" } }, formats: { ...before.formats, A1: { bold: true, bg: "#fff7ed" } } };
  const patch = backend.buildSheetCollabPatch(before, after, { mutationId: "m1" });
  assert.equal(patch.sheetId, "sheet_1");
  assert.deepEqual(patch.cells, { A1: { v: 10 }, D1: { v: "=A1+B1" } });
  assert.deepEqual(patch.formats, { A1: { bold: true, bg: "#fff7ed" } });
  assert.deepEqual(patch.replace, {});
});

test("Phase 5 patch merge preserves unrelated concurrent cells", () => {
  const current = baseContent();
  current.sheets[0].cells.Z1 = { v: "remote" };
  const patch = { sheetId: "sheet_1", mutationId: "m2", cells: { A1: { v: 99 }, B1: null } };
  const merged = backend.applySheetCollabPatch(current, patch);
  assert.equal(merged.sheets[0].cells.A1.v, 99);
  assert.equal(merged.sheets[0].cells.B1, undefined);
  assert.equal(merged.sheets[0].cells.Z1.v, "remote");
});

test("Phase 5 structural sheet fields replace independently", () => {
  const current = baseContent();
  const patch = { sheetId: "sheet_1", replace: { freeze: { rows: 2, cols: 1 }, rowHeights: { "1": 44 } } };
  const merged = backend.applySheetCollabPatch(current, patch);
  assert.deepEqual(merged.sheets[0].freeze, { rows: 2, cols: 1 });
  assert.deepEqual(merged.sheets[0].rowHeights, { "1": 44 });
  assert.equal(merged.sheets[0].cells.C1.v, 3);
});

test("Phase 5 normalizer rejects invalid refs and strips unknown replace fields", () => {
  const patch = backend.normalizeSheetCollabPatch({
    sheetId: "sheet_1",
    cells: { A1: { v: 1 }, "<script>": { v: 2 } },
    formats: { B2: { bold: true }, BAD0: { bg: "red" } },
    replace: { rows: 40, password: "nope" },
  });
  assert.deepEqual(patch.cells, { A1: { v: 1 } });
  assert.deepEqual(patch.formats, { B2: { bold: true } });
  assert.deepEqual(patch.replace, { rows: 40 });
});

test("Phase 5 remote selections identify ranges and stable peer colors", () => {
  assert.equal(backend.selectionContainsRef({ anchorRef: "B2", focusRef: "D4" }, "C3"), true);
  assert.equal(backend.selectionContainsRef({ anchorRef: "B2", focusRef: "D4" }, "A1"), false);
  assert.equal(backend.collaborationPeerColor("user-1"), backend.collaborationPeerColor("user-1"));
});

test("Phase 5 frontend/backend helper behavior stays identical", () => {
  const before = baseContent().sheets[0];
  const after = { ...before, cells: { ...before.cells, A2: { v: "hello" } }, cols: 20 };
  assert.deepEqual(frontend.buildSheetCollabPatch(before, after, { mutationId: "same" }), backend.buildSheetCollabPatch(before, after, { mutationId: "same" }));
  const patch = backend.buildSheetCollabPatch(before, after, { mutationId: "same" });
  assert.deepEqual(frontend.applySheetCollabPatch(baseContent(), patch), backend.applySheetCollabPatch(baseContent(), patch));
});

test("Phase 5 collaboration wiring exists across route, service, socket and editor", () => {
  const route = fs.readFileSync(new URL("../routes/workspace.routes.js", import.meta.url), "utf8");
  const service = fs.readFileSync(new URL("../services/workspace.service.js", import.meta.url), "utf8");
  const sockets = fs.readFileSync(new URL("../sockets.js", import.meta.url), "utf8");
  const api = fs.readFileSync(new URL("../../../frontend/src/lib/api.js", import.meta.url), "utf8");
  const presence = fs.readFileSync(new URL("../../../frontend/src/pages/tws/useTwsPresence.js", import.meta.url), "utf8");
  const editor = fs.readFileSync(new URL("../../../frontend/src/pages/tws/TSheetsEditor.jsx", import.meta.url), "utf8");
  assert.ok(route.includes('/documents/:id/sheets/patch'));
  assert.ok(route.includes('tws-doc:sheet-patch'));
  assert.ok(service.includes('patchSheetCollaboration'));
  assert.ok(service.includes('runSheetCollabSerialized'));
  assert.ok(sockets.includes('tws-doc:selection'));
  assert.ok(api.includes('patchSheet:'));
  assert.ok(presence.includes('peerSelections'));
  assert.ok(presence.includes('emitSelection'));
  assert.ok(editor.includes('buildSheetCollabPatch'));
  assert.ok(editor.includes('scheduleSheetCollabPatch'));
  assert.ok(editor.includes('remoteSelectionsForRef'));
});
