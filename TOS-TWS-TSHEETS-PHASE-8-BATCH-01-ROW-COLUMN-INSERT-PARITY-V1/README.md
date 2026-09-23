# TOS TSheets — Phase 8 / Batch 01 / V1

**Patch ID:** `TOS-TWS-TSHEETS-PHASE-8-BATCH-01-ROW-COLUMN-INSERT-PARITY-V1`

## End-user feature
The user can insert a row **above/below the currently selected cell** or a column **left/right of the current selection**, like Google Sheets. Existing data shifts to make room instead of only increasing the sheet size at the end.

## Included in V1
- Insert 1 row above.
- Insert 1 row below.
- Insert 1 column left.
- Insert 1 column right.
- Existing cell values shift with the structure.
- Formatting, merged ranges, validation, conditional formatting, protected ranges, filters, charts and pivot source ranges shift/expand with the insertion.
- Named ranges on the active sheet shift/expand.
- Common same-sheet formula references shift with inserted rows/columns.
- Undo/redo history and autosave remain wired through the current TSheets flow.
- Existing 500-row / 100-column safety limits are intentionally preserved in this batch.

## Deferred to next batches
- Delete selected rows/columns.
- Insert multiple selected rows/columns in one action.
- Row/column header right-click menus.
- Hide/unhide, move, group/ungroup, fit-to-data.
- Large-grid scaling beyond the current 500 x 100 limit.
- Full cross-sheet structural formula reference rewriting.

## Verification contract
1. Structural helper unit tests pass.
2. Frontend build passes.
3. Live bundle matches built bundle.
4. Browser smoke must verify row-above, row-below, column-left and column-right behavior with real cells.
5. Do not commit or push the live TOS working tree. User handles commit/push after browser verification.
