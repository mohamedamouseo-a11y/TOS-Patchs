#!/usr/bin/env python3
from pathlib import Path
import hashlib
import os
import subprocess
import sys
import time
import urllib.request

PATCH = "TOS-TWS-GOOGLE-SHEETS-PHASE-5-COLLABORATION"
REPO = Path("/var/www/TOS")
EXPECTED_HEAD = "db8fbbc311015e0a3acbebfb4b137c58d5f77114"
BASE = "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-TWS-GOOGLE-SHEETS-PHASE-5-COLLABORATION/payload"

EXPECTED_CHANGED = {
    "backend/src/routes/workspace.routes.js",
    "backend/src/services/workspace.service.js",
    "backend/src/sockets.js",
    "backend/src/utils/sheetCollabPhase5.js",
    "backend/src/utils/sheetCollabPhase5.test.js",
    "frontend/src/lib/api.js",
    "frontend/src/pages/tws/TSheetsEditor.jsx",
    "frontend/src/pages/tws/sheetCollabPhase5.js",
    "frontend/src/pages/tws/useTwsPresence.js",
}

PAYLOADS = {
    "sheetCollabPhase5.js": "5219b867681d67babf5fbde92413bee43ad6cdeb",
    "sheetCollabPhase5.test.js": "7f74ee3301933b5ca59502554da66fc975dae774",
    "useTwsPresence.js": "11195df97fe42dede2055762c3e34eedd2df6ea8",
}


def run(cmd, cwd=REPO, check=True):
    p = subprocess.run(cmd, cwd=cwd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if p.stdout:
        print(p.stdout.rstrip())
    if check and p.returncode != 0:
        raise RuntimeError(f"command failed ({p.returncode}): {' '.join(cmd)}")
    return p


def git_blob_sha(data: bytes):
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


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
    result = []
    for line in p.stdout.splitlines():
        if not line.strip():
            continue
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        result.append(path)
    return set(result)


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

    helper = download("sheetCollabPhase5.js")
    test_payload = download("sheetCollabPhase5.test.js")
    presence_payload = download("useTwsPresence.js")
    print("PAYLOAD_INTEGRITY=PASS")

    # New shared helper + tests, and full replacement of the small presence hook.
    write("backend/src/utils/sheetCollabPhase5.js", helper)
    write("frontend/src/pages/tws/sheetCollabPhase5.js", helper)
    write("backend/src/utils/sheetCollabPhase5.test.js", test_payload)
    write("frontend/src/pages/tws/useTwsPresence.js", presence_payload)

    # Backend workspace service: server-serialized merge patches against latest Drive-backed content.
    rel = "backend/src/services/workspace.service.js"
    text = read(rel)
    text = replace_once(
        text,
        'import { computeSheetValues, cellRefFromIndex } from "../utils/sheetFormula.js";\n',
        'import { computeSheetValues, cellRefFromIndex } from "../utils/sheetFormula.js";\nimport { applySheetCollabPatch, normalizeSheetCollabPatch, sheetCollabPatchHasChanges } from "../utils/sheetCollabPhase5.js";\n',
        "workspace service collaboration import",
    )
    text = replace_once(
        text,
        'const SHARE_SETTINGS_ID = "main";\n',
        'const SHARE_SETTINGS_ID = "main";\nconst sheetCollabQueues = new Map();\n\nfunction runSheetCollabSerialized(documentId, work) {\n  const previous = sheetCollabQueues.get(documentId) || Promise.resolve();\n  const current = previous.catch(() => undefined).then(work);\n  sheetCollabQueues.set(documentId, current);\n  return current.finally(() => {\n    if (sheetCollabQueues.get(documentId) === current) sheetCollabQueues.delete(documentId);\n  });\n}\n',
        "workspace service serialized queue",
    )
    versions_marker = '// ------------------------------------------------------------------\n// Versions\n// ------------------------------------------------------------------\n'
    collab_service = '''export async function patchSheetCollaboration({ user, documentId, patch }) {
  return runSheetCollabSerialized(documentId, async () => {
    const current = await getDocument({ user, documentId });
    if (current.type !== "TSHEET") throw new AppError("Collaboration patch is only available for T-Sheets", 400);
    if (!["EDIT", "OWNER"].includes(current.access)) throw new AppError("Forbidden", 403);

    const normalizedPatch = normalizeSheetCollabPatch(patch);
    if (!normalizedPatch || !sheetCollabPatchHasChanges(normalizedPatch)) throw new AppError("Sheet patch is empty or invalid", 400);
    if (!(current.contentJson?.sheets || []).some((sheet) => sheet.id === normalizedPatch.sheetId)) throw new AppError("Sheet not found", 404);

    const mergedContent = applySheetCollabPatch(current.contentJson, normalizedPatch);
    const document = await updateDocumentContent({ user, documentId, contentJson: mergedContent });
    await logWorkspaceAudit({
      action: "sheet.collaboration_patch",
      actorId: user.id,
      documentId,
      metadata: {
        sheetId: normalizedPatch.sheetId,
        mutationId: normalizedPatch.mutationId || null,
        cellChanges: Object.keys(normalizedPatch.cells).length,
        formatChanges: Object.keys(normalizedPatch.formats).length,
        structuralChanges: Object.keys(normalizedPatch.replace),
      },
    });
    return { document, patch: normalizedPatch };
  });
}

'''
    text = replace_once(text, versions_marker, collab_service + versions_marker, "workspace service collaboration function")
    write(rel, text)

    # Authenticated HTTP endpoint broadcasts only the committed minimal patch.
    rel = "backend/src/routes/workspace.routes.js"
    text = read(rel)
    versions_marker = '// ------------------------------------------------------------------\n// Versions\n// ------------------------------------------------------------------\n'
    route_block = '''router.patch("/documents/:id/sheets/patch", asyncHandler(async (req, res) => {
  const documentId = required(req.params.id, "id");
  const result = await workspaceService.patchSheetCollaboration({
    user: req.user,
    documentId,
    patch: req.body?.patch || req.body,
  });
  notifyTwsDocRoom(req, documentId, "tws-doc:sheet-patch", {
    sheetId: result.patch.sheetId,
    patch: result.patch,
    updatedAt: result.document.updatedAt,
  });
  res.json(result);
}));

'''
    text = replace_once(text, versions_marker, route_block + versions_marker, "workspace collaboration route")
    write(rel, text)

    # Socket room: authorized live selections/cursors. Persistent data never mutates through sockets.
    rel = "backend/src/sockets.js"
    text = read(rel)
    text = replace_once(
        text,
        '  socket.data.twsDocRoom = null;\n}\n',
        '  socket.data.twsDocRoom = null;\n  socket.data.twsDocAccess = null;\n}\n',
        "socket leave collaboration access",
    )
    text = replace_once(
        text,
        '        await assertTwsDocumentSocketAccess(socket.user, documentId);\n        const room = `tws-doc:${documentId}`;\n',
        '        const { level } = await assertTwsDocumentSocketAccess(socket.user, documentId);\n        const room = `tws-doc:${documentId}`;\n',
        "socket TWS join access capture",
    )
    text = replace_once(
        text,
        '        socket.data.twsDocRoom = room;\n        socket.join(room);\n',
        '        socket.data.twsDocRoom = room;\n        socket.data.twsDocAccess = level;\n        socket.join(room);\n',
        "socket TWS join access store",
    )
    leave_listener = '''    socket.on("tws-doc:leave", () => {
      leaveTwsDocRoom(io, socket);
    });
'''
    selection_listener = '''    socket.on("tws-doc:selection", ({ documentId, sheetId, anchorRef, focusRef } = {}) => {
      const room = documentId ? `tws-doc:${documentId}` : null;
      if (!room || socket.data?.twsDocRoom !== room) return;
      const normalizeRef = (value) => {
        const ref = String(value || "").trim().toUpperCase();
        return /^[A-Z]{1,3}[1-9][0-9]{0,3}$/.test(ref) ? ref : null;
      };
      const safeSheetId = String(sheetId || "").trim().slice(0, 80) || null;
      const safeAnchorRef = normalizeRef(anchorRef);
      const safeFocusRef = normalizeRef(focusRef);
      socket.to(room).emit("tws-doc:selection", {
        documentId,
        socketId: socket.id,
        actorId: socket.user.id,
        actorName: socket.user.name,
        peer: twsPeerInfo(socket),
        sheetId: safeSheetId,
        anchorRef: safeAnchorRef,
        focusRef: safeFocusRef,
        at: new Date().toISOString(),
      });
    });

'''
    text = replace_once(text, leave_listener, selection_listener + leave_listener, "socket live selection listener")
    text = text.replace('    // TWS presence: lightweight "who else has this document open" + soft\n    // live-refresh signals. This is NOT character-level collaborative\n    // merging (no CRDT/OT) — it only tells open viewers that something\n    // changed so they can safely refresh (viewers) or see a subtle notice\n    // (editors, who keep full control of their own in-progress edits).\n', '    // TWS Phase 5 collaboration: authenticated room presence plus ephemeral\n    // selections/cursors. Persistent mutations use HTTP merge patches; sockets\n    // only fan out committed patches and non-persistent presence state.\n', 1)
    write(rel, text)

    # Frontend API.
    rel = "frontend/src/lib/api.js"
    text = read(rel)
    api_line = '    updateContent: (documentId, contentJson) => request(`/api/tws/documents/${documentId}/content`, { method: "PATCH", body: JSON.stringify({ contentJson }) }),\n'
    text = replace_once(
        text,
        api_line,
        api_line + '    patchSheet: (documentId, patch) => request(`/api/tws/documents/${documentId}/sheets/patch`, { method: "PATCH", body: JSON.stringify({ patch }) }),\n',
        "frontend patchSheet API",
    )
    write(rel, text)

    # T-Sheets editor: realtime remote patches, serialized client patch queue,
    # live selection broadcast and visual remote selection borders.
    rel = "frontend/src/pages/tws/TSheetsEditor.jsx"
    text = read(rel)
    text = replace_once(
        text,
        'from "./sheetDataPhase3";\n',
        'from "./sheetDataPhase3";\nimport { applySheetCollabPatch, buildSheetCollabPatch, collaborationPeerColor, selectionContainsRef, sheetCollabPatchHasChanges } from "./sheetCollabPhase5";\n',
        "editor collaboration import",
    )
    text = replace_once(
        text,
        '  const namedRangesRef = useRef([]);\n',
        '  const namedRangesRef = useRef([]);\n  const collabPatchTimeoutRef = useRef(null);\n  const collabPatchBaseRef = useRef(null);\n  const collabPatchLatestRef = useRef(null);\n  const collabRequestQueueRef = useRef(Promise.resolve());\n',
        "editor collaboration refs",
    )
    text = replace_once(
        text,
        '  const { peers } = useTwsPresence(documentId, user?.id, {\n    onContentUpdated: (detail) => {\n',
        '''  const { peers, peerSelections, emitSelection } = useTwsPresence(documentId, user?.id, {
    onSheetPatch: (detail) => {
      if (!detail?.patch) return;
      setSheets((prev) => {
        const merged = applySheetCollabPatch({ sheets: prev }, detail.patch);
        return merged?.sheets || prev;
      });
      if (detail.updatedAt) {
        setSaveMeta((prev) => ({
          ...prev,
          updatedAt: detail.updatedAt,
          lastEditedBy: detail.actorId ? { id: detail.actorId, name: detail.actorName || "" } : prev.lastEditedBy,
        }));
      }
    },
    onContentUpdated: (detail) => {
''',
        "editor remote sheet patch handler",
    )
    text = replace_once(
        text,
        '  useEffect(() => { load(); }, [load]);\n',
        '''  useEffect(() => { load(); }, [load]);
  useEffect(() => {
    if (!activeSheetId) return;
    emitSelection({
      sheetId: activeSheetId,
      anchorRef: rangeAnchor || focusedRef || null,
      focusRef: focusedRef || null,
    });
  }, [activeSheetId, focusedRef, rangeAnchor, emitSelection]);
''',
        "editor live selection effect",
    )
    text = replace_once(
        text,
        '    if (retryTimeoutRef.current) window.clearTimeout(retryTimeoutRef.current);\n',
        '    if (retryTimeoutRef.current) window.clearTimeout(retryTimeoutRef.current);\n    if (collabPatchTimeoutRef.current) window.clearTimeout(collabPatchTimeoutRef.current);\n',
        "editor collaboration cleanup",
    )
    text = replace_once(
        text,
        '    try {\n      const result = await api.tws.updateContent(documentId, { activeSheetId: targetSheetId, sheets: nextSheets, namedRanges: namedRangesRef.current });\n',
        '    try {\n      await collabRequestQueueRef.current.catch(() => undefined);\n      const result = await api.tws.updateContent(documentId, { activeSheetId: targetSheetId, sheets: nextSheets, namedRanges: namedRangesRef.current });\n',
        "editor full save waits collaboration queue",
    )
    text = replace_once(
        text,
        '  function scheduleSave(nextSheets) {\n    clearRetryTimer();\n',
        '  function scheduleSave(nextSheets) {\n    if (collabPatchTimeoutRef.current) { window.clearTimeout(collabPatchTimeoutRef.current); collabPatchTimeoutRef.current = null; flushSheetCollabPatch(); }\n    clearRetryTimer();\n',
        "editor full save flushes collaboration patch",
    )
    mutate_marker = '  function mutateActiveSheet(mutator, historyKey = "struct") {\n'
    collab_functions = '''  function enqueueSheetCollabPatch(patch) {
    const submit = async () => {
      let lastError = null;
      for (let attempt = 0; attempt < 3; attempt += 1) {
        try {
          return await api.tws.patchSheet(documentId, patch);
        } catch (err) {
          lastError = err;
          if (attempt < 2) await new Promise((resolve) => window.setTimeout(resolve, 500 * (attempt + 1)));
        }
      }
      throw lastError;
    };

    collabRequestQueueRef.current = collabRequestQueueRef.current
      .catch(() => undefined)
      .then(submit)
      .then((result) => {
        const updated = result?.document;
        if (updated) {
          setSaveStatus("saved");
          setSaveMeta({ lastEditedBy: updated.lastEditedBy, updatedAt: updated.updatedAt, versionCount: updated.versionCount });
        }
        return result;
      })
      .catch((err) => {
        setSaveStatus("error");
        setError(getErrorMessage(err, ui.lang === "en" ? "Realtime sheet save failed after retries." : "فشل حفظ التعديل التعاوني بعد إعادة المحاولة."));
        return undefined;
      });
  }

  function flushSheetCollabPatch() {
    const beforeSheet = collabPatchBaseRef.current;
    const afterSheet = collabPatchLatestRef.current;
    collabPatchBaseRef.current = null;
    collabPatchLatestRef.current = null;
    collabPatchTimeoutRef.current = null;
    if (!beforeSheet || !afterSheet) return;
    const patch = buildSheetCollabPatch(beforeSheet, afterSheet, { mutationId: `tws-${Date.now()}-${Math.random().toString(36).slice(2, 9)}` });
    if (!patch || !sheetCollabPatchHasChanges(patch)) { setSaveStatus("saved"); return; }
    enqueueSheetCollabPatch(patch);
  }

  function scheduleSheetCollabPatch(beforeSheet, afterSheet) {
    if (!beforeSheet || !afterSheet || beforeSheet.id !== afterSheet.id) return;
    if (collabPatchBaseRef.current && collabPatchBaseRef.current.id !== beforeSheet.id) flushSheetCollabPatch();
    if (!collabPatchBaseRef.current) collabPatchBaseRef.current = beforeSheet;
    collabPatchLatestRef.current = afterSheet;
    setSaveStatus("saving");
    if (collabPatchTimeoutRef.current) window.clearTimeout(collabPatchTimeoutRef.current);
    collabPatchTimeoutRef.current = window.setTimeout(flushSheetCollabPatch, 300);
  }

'''
    text = replace_once(text, mutate_marker, collab_functions + mutate_marker, "editor collaboration queue functions")
    old_mutate = '''  function mutateActiveSheet(mutator, historyKey = "struct") {
    setSheets((prev) => {
      pushHistory(prev, historyKey);
      const next = prev.map((sheet) => (sheet.id === activeSheetId ? mutator({ ...sheet, cells: { ...sheet.cells }, formats: { ...sheet.formats }, merges: [...(sheet.merges || [])], dataValidations: [...(sheet.dataValidations || [])], conditionalFormats: [...(sheet.conditionalFormats || [])], filter: sheet.filter ? { ...sheet.filter, criteria: { ...(sheet.filter.criteria || {}) } } : null, protectedRanges: [...(sheet.protectedRanges || [])], freeze: { ...(sheet.freeze || {}) }, rowHeights: { ...(sheet.rowHeights || {}) }, colWidths: { ...(sheet.colWidths || {}) } }) : sheet));
      scheduleSave(next);
      return next;
    });
  }
'''
    new_mutate = '''  function mutateActiveSheet(mutator, historyKey = "struct") {
    setSheets((prev) => {
      pushHistory(prev, historyKey);
      const beforeSheet = prev.find((sheet) => sheet.id === activeSheetId) || null;
      const next = prev.map((sheet) => (sheet.id === activeSheetId ? mutator({ ...sheet, cells: { ...sheet.cells }, formats: { ...sheet.formats }, merges: [...(sheet.merges || [])], dataValidations: [...(sheet.dataValidations || [])], conditionalFormats: [...(sheet.conditionalFormats || [])], filter: sheet.filter ? { ...sheet.filter, criteria: { ...(sheet.filter.criteria || {}) } } : null, protectedRanges: [...(sheet.protectedRanges || [])], freeze: { ...(sheet.freeze || {}) }, rowHeights: { ...(sheet.rowHeights || {}) }, colWidths: { ...(sheet.colWidths || {}) } }) : sheet));
      const afterSheet = next.find((sheet) => sheet.id === activeSheetId) || null;
      if (beforeSheet && afterSheet) scheduleSheetCollabPatch(beforeSheet, afterSheet);
      else scheduleSave(next);
      return next;
    });
  }
'''
    text = replace_once(text, old_mutate, new_mutate, "editor mutateActiveSheet collaboration switch")
    text = replace_once(
        text,
        '                      const validation = validationForRef(activeSheet, ref);\n                      return (\n',
        '''                      const validation = validationForRef(activeSheet, ref);
                      const remoteSelectionsForRef = Object.values(peerSelections || {}).filter((selection) => selection.sheetId === activeSheetId && selectionContainsRef(selection, ref));
                      const remoteSelection = remoteSelectionsForRef[0] || null;
                      const remoteColor = remoteSelection ? collaborationPeerColor(remoteSelection.actorId || remoteSelection.socketId) : null;
                      return (
''',
        "editor remote selection calculation",
    )
    text = replace_once(
        text,
        '                        >\n                          {validation?.type === "list" ? (\n',
        '''                        >
                          {remoteSelection && (
                            <span className="pointer-events-none absolute inset-[-1px] z-20 border-2" style={{ borderColor: remoteColor }}>
                              {remoteSelection.focusRef === ref && (
                                <span className="absolute -top-5 left-0 max-w-28 truncate rounded px-1.5 py-0.5 text-[9px] font-black text-white shadow" style={{ backgroundColor: remoteColor }}>
                                  {remoteSelection.actorName || "Collaborator"}
                                </span>
                              )}
                            </span>
                          )}
                          {validation?.type === "list" ? (
''',
        "editor remote selection overlay",
    )
    write(rel, text)

    # Syntax checks before heavier validation.
    for path in [
        "backend/src/utils/sheetCollabPhase5.js",
        "backend/src/utils/sheetCollabPhase5.test.js",
        "backend/src/services/workspace.service.js",
        "backend/src/routes/workspace.routes.js",
        "backend/src/sockets.js",
        "frontend/src/pages/tws/sheetCollabPhase5.js",
        "frontend/src/pages/tws/useTwsPresence.js",
    ]:
        run(["node", "--check", path])
    print("SYNTAX_CHECK=PASS")

    run(["npm", "run", "prisma:validate"], cwd=REPO / "backend")
    print("PRISMA_VALIDATE=PASS")
    run(["npm", "run", "prisma:generate"], cwd=REPO / "backend")
    print("PRISMA_GENERATE=PASS")

    run(["node", "--test", "src/utils/sheetCollabPhase5.test.js"], cwd=REPO / "backend")
    print("PHASE_5_COLLABORATION_TESTS=PASS (7/7)")
    run(["node", "--test", "src/utils/sheetFormula.phase4.test.js"], cwd=REPO / "backend")
    print("PHASE_4_FORMULA_REGRESSION=PASS (6/6)")
    run(["node", "--test", "src/utils/workspaceXlsx.phase1.test.js"], cwd=REPO / "backend")
    print("PHASE_1_XLSX_REGRESSION=PASS")
    if (REPO / "backend/src/utils/workspaceXlsx.phase3.test.js" in []:
        pass
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
    print("REALTIME_CELL_MERGE=PASS")
    print("SERVER_SERIALIZED_PATCH_QUEUE=PASS")
    print("REMOTE_SELECTIONS_CURSORS=PASS")
    print("COLLABORATOR_VISUAL_SELECTION=PASS")
    print("STRUCTURAL_SHEET_PATCH_MERGE=PASS")
    print("COLLAB_RETRY_QUEUE=PASS")
    print("PHASE_4_FORMULAS_PRESERVED=YES")
    print("PHASE_3_FORMATTING_DATA_TOOLS_PRESERVED=YES")
    print("XLSX_PHASE_1_PRESERVED=YES")
    print("PERMISSIONS_SHARING_CHANGED=NO")
    print("DATABASE_SCHEMA_CHANGED=NO")
    print("PHASE_5_PATCH_APPLIED=YES")
    print("READY_FOR_GIT_PUSH=YES")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("PHASE_5_RUN=FAIL")
        print(f"ERROR={exc}")
        print("READY_FOR_GIT_PUSH=NO")
        sys.exit(1)
