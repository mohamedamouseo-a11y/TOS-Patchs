#!/usr/bin/env python3
from pathlib import Path

PATCH = "TOS-TWS-TSHEETS-PERSISTENCE-RECENTS-DRIVE-V1"
ROOT = Path.cwd()
PARENT = ROOT/"frontend/src/pages/tws/TSheetsCasualLab.jsx"
API = ROOT/"frontend/src/lib/api.js"
AUTOSAVE = ROOT/"vendor/tsheets-casual-upstream/apps/web/src/autosave/useAutosave.ts"
APP = ROOT/"vendor/tsheets-casual-upstream/apps/web/src/App.tsx"
HOME = ROOT/"vendor/tsheets-casual-upstream/apps/web/src/home/HomeScreen.tsx"
ROUTES = ROOT/"backend/src/routes/workspace.routes.js"
SCHEMA = ROOT/"backend/prisma/schema.prisma"
MIGRATION = ROOT/"backend/prisma/migrations/20260926221000_tsheets_raw_workbook_drive_sync/migration.sql"

def fail(msg):
    raise SystemExit("ERROR: "+msg)

for p in [PARENT, API, AUTOSAVE, APP, HOME, ROUTES, SCHEMA]:
    if not p.exists(): fail("missing "+str(p))

PARENT.write_text("""// TOS_TWS_TSHEETS_PERSISTENCE_RECENTS_DRIVE_V1
import { useEffect, useRef } from "react";
import { api } from "../../lib/api";

const DRIVE_SYNC_INTERVAL_MS = 60_000;

export function TSheetsCasualLab({ documentId }) {
  const documentIdRef = useRef(documentId || null);
  const createPromiseRef = useRef(null);

  useEffect(() => {
    documentIdRef.current = documentId || null;
  }, [documentId]);

  useEffect(() => {
    let disposed = false;

    async function ensureDocument() {
      if (documentIdRef.current) return documentIdRef.current;
      if (!createPromiseRef.current) {
        createPromiseRef.current = api.tws.create({
          type: "TSHEET",
          title: "Untitled spreadsheet",
          visibility: "PRIVATE",
        }).then((doc) => {
          documentIdRef.current = doc.id;
          return doc.id;
        }).finally(() => {
          createPromiseRef.current = null;
        });
      }
      return createPromiseRef.current;
    }

    window.__TOS_TSHEETS_SAVE__ = async (requestedId, workbookData) => {
      const currentId = documentIdRef.current;
      const docId = currentId || requestedId || await ensureDocument();
      if (!docId || disposed) return null;
      await api.tws.putRawWorkbook(docId, workbookData);
      if (!documentId && !disposed) {
        window.history.replaceState(
          { ...(window.history.state || {}), tosPage: "tws" },
          "",
          "/tws/sheets-lab/" + encodeURIComponent(docId),
        );
        window.dispatchEvent(new Event("popstate"));
      }
      return docId;
    };

    window.__TOS_TSHEETS_LOAD__ = async (requestedId) => {
      const docId = requestedId || documentIdRef.current;
      if (!docId) return null;
      const result = await api.tws.getRawWorkbook(docId);
      return result?.rawWorkbookData ?? null;
    };

    window.__TOS_TSHEETS_RECENTS__ = async () => {
      const result = await api.tws.list({ type: "TSHEET", status: "ACTIVE", limit: 50 });
      return (result?.items || []).map((doc) => ({
        id: doc.id,
        name: doc.title || "Untitled spreadsheet",
        modifiedAt: doc.updatedAt ? new Date(doc.updatedAt).getTime() : Date.now(),
        size: 0,
      }));
    };

    window.__TOS_TSHEETS_OPEN__ = (docId) => {
      if (!docId) return;
      window.history.pushState(
        { ...(window.history.state || {}), tosPage: "tws" },
        "",
        "/tws/sheets-lab/" + encodeURIComponent(docId),
      );
      window.dispatchEvent(new Event("popstate"));
    };

    return () => {
      disposed = true;
      delete window.__TOS_TSHEETS_SAVE__;
      delete window.__TOS_TSHEETS_LOAD__;
      delete window.__TOS_TSHEETS_RECENTS__;
      delete window.__TOS_TSHEETS_OPEN__;
    };
  }, [documentId]);

  useEffect(() => {
    if (!documentId) return;
    let cancelled = false;
    const run = async () => {
      if (cancelled) return;
      try {
        await api.tws.syncRawWorkbookDrive(documentId);
      } catch (e) {
        console.warn("[TSheetsCasualLab] background Drive sync failed:", e);
      }
    };
    const timer = window.setInterval(() => void run(), DRIVE_SYNC_INTERVAL_MS);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [documentId]);

  const src = documentId
    ? "/tws-casual-runtime/?tosDocumentId=" + encodeURIComponent(documentId)
    : "/tws-casual-runtime/";

  return (
    <section
      data-tsheets-casual-lab="p03-v2-clean"
      data-tsheets-frame-fit="v2"
      data-tsheets-persistence="recents-drive-v1"
      className="relative h-full min-h-0 w-full overflow-hidden bg-white"
    >
      <iframe
        title="T-Sheets Lab"
        src={src}
        className="block h-full min-h-0 w-full border-0 bg-white"
        allow="clipboard-read; clipboard-write"
      />
    </section>
  );
}
""")

api = API.read_text()
needle = 'putRawWorkbook: (documentId, workbookData) => request(\`/api/tws/documents/__DOLLAR_LBRACE__documentId}/raw-workbook\`, { method: "PUT", body: JSON.stringify(workbookData) }),'.replace("__DOLLAR_LBRACE__", "$"+"{")
if needle not in api: fail("api raw workbook anchor missing")
api = api.replace(needle, needle + '\n    syncRawWorkbookDrive: (documentId) => request(\`/api/tws/documents/__DOLLAR_LBRACE__documentId}/raw-workbook/sync-drive\`, { method: "POST" }),'.replace("__DOLLAR_LBRACE__", "$"+"{"), 1)
API.write_text(api)

autosave = AUTOSAVE.read_text()
old = """        if (typeof window !== 'undefined' && window.parent && window.parent !== window) {
          const params = new URLSearchParams(window.location.search);
          const tosDocId = params.get('tosDocumentId');
          if (tosDocId) {
            const directSave = (window.parent as any).__TOS_TSHEETS_SAVE__;
            if (typeof directSave === 'function') {
              try { directSave(tosDocId, data); } catch {}
            }
          }
        }"""
new = """        if (typeof window !== 'undefined' && window.parent && window.parent !== window) {
          const params = new URLSearchParams(window.location.search);
          const tosDocId = params.get('tosDocumentId');
          const directSave = (window.parent as any).__TOS_TSHEETS_SAVE__;
          if (typeof directSave === 'function') {
            // TOS_PERSISTENCE_RECENTS_DRIVE_V1: null id creates the real TOS file.
            try { void directSave(tosDocId, data); } catch {}
          }
        }"""
if old not in autosave: fail("autosave bridge anchor missing")
AUTOSAVE.write_text(autosave.replace(old,new,1))

app = APP.read_text()
driver_anchor = "                                  <AutosaveDriver />\n                                  <DesktopRecoveryDriver />"
if driver_anchor not in app: fail("App driver anchor missing")
app = app.replace(driver_anchor, "                                  <TosWorkbookHydrator replaceWorkbook={replaceWorkbook} />\n"+driver_anchor, 1)
insert_anchor = "/** Effect-only — drives the IDB autosave loop. No-op in collab rooms. */\nfunction AutosaveDriver(): ReactNode {"
if insert_anchor not in app: fail("App AutosaveDriver anchor missing")
hydrator = """/** TOS embedded mode: hydrate the canonical raw workbook from TOS DB. */
function TosWorkbookHydrator({
  replaceWorkbook,
}: {
  replaceWorkbook: WorkbookCtxValue['replaceWorkbook'];
}): ReactNode {
  const loadedRef = useRef<string | null>(null);
  useEffect(() => {
    if (typeof window === 'undefined' || window.parent === window) return;
    const documentId = new URLSearchParams(window.location.search).get('tosDocumentId');
    if (!documentId || loadedRef.current === documentId) return;
    const load = (window.parent as any).__TOS_TSHEETS_LOAD__;
    if (typeof load !== 'function') return;
    let cancelled = false;
    void (async () => {
      try {
        const data = await load(documentId);
        if (cancelled) return;
        if (data) replaceWorkbook(data, null);
        loadedRef.current = documentId;
      } catch (err) {
        console.warn('[tos] raw workbook load failed', err);
      }
    })();
    return () => { cancelled = true; };
  }, [replaceWorkbook]);
  return null;
}

"""
APP.write_text(app.replace(insert_anchor, hydrator+insert_anchor,1))

home = HOME.read_text()
state_anchor = "  const [view, setView] = useState<HomeView>('home');\n  const [collapsed, setCollapsed] = useState(false);"
if state_anchor not in home: fail("Home state anchor missing")
home = home.replace(state_anchor, state_anchor+"\n  const [tosRecents, setTosRecents] = useState<RecentEntry[]>([]);",1)
visible_anchor = "  const visible = (forcedOpen || (!dismissed && isBlank)) && !inCollabRoom;"
if visible_anchor not in home: fail("Home visible anchor missing")
home = home.replace(visible_anchor, visible_anchor+"""

  useEffect(() => {
    if (!visible || typeof window === 'undefined' || window.parent === window) return;
    const list = (window.parent as any).__TOS_TSHEETS_RECENTS__;
    if (typeof list !== 'function') return;
    let cancelled = false;
    void list().then((items: Array<{ id: string; name: string; modifiedAt: number; size?: number }>) => {
      if (cancelled) return;
      setTosRecents((items || []).map((item) => ({
        id: 'tos:' + item.id,
        name: item.name,
        sourceFormat: null,
        size: item.size || 0,
        modifiedAt: item.modifiedAt || Date.now(),
      })));
    }).catch((err: unknown) => console.warn('[tos] recent list failed', err));
    return () => { cancelled = true; };
  }, [visible]);""",1)
open_anchor = """  const onOpenRecent = async (rec: RecentEntry) => {
    try {
      const opened = await fileSource.openRecent(rec.id);"""
if open_anchor not in home: fail("Home recent open anchor missing")
home = home.replace(open_anchor, """  const onOpenRecent = async (rec: RecentEntry) => {
    if (rec.id.startsWith('tos:') && typeof window !== 'undefined' && window.parent !== window) {
      const open = (window.parent as any).__TOS_TSHEETS_OPEN__;
      if (typeof open === 'function') {
        open(rec.id.slice(4));
        return;
      }
    }
    try {
      const opened = await fileSource.openRecent(rec.id);""",1)
delete_anchor = """  const onDeleteRecent = (rec: RecentEntry) => {
    void fileSource.forgetRecent(rec.id);
  };"""
if delete_anchor not in home: fail("Home recent delete anchor missing")
home = home.replace(delete_anchor, """  const onDeleteRecent = (rec: RecentEntry) => {
    if (rec.id.startsWith('tos:')) return;
    void fileSource.forgetRecent(rec.id);
  };

  const mergedRecents = useMemo(() => {
    const local = recents.filter((r) => !r.id.startsWith('tos:'));
    return [...tosRecents, ...local].sort((a, b) => b.modifiedAt - a.modifiedAt);
  }, [tosRecents, recents]);""",1)
home = home.replace("recents={recents} onOpen={onOpenRecent}", "recents={mergedRecents} onOpen={onOpenRecent}")
home = home.replace("{recents.length > 0 && (", "{mergedRecents.length > 0 && (")
home = home.replace("recents={recents.slice(0, 6)}", "recents={mergedRecents.slice(0, 6)}")
home = home.replace("{recents.length > 0 ? (", "{mergedRecents.length > 0 ? (")
home = home.replace("recents={recents}\n", "recents={mergedRecents}\n")
HOME.write_text(home)

routes = ROUTES.read_text()
if 'import { prisma } from "../prisma.js";' not in routes:
    routes = routes.replace('import { Router } from "express";', 'import { Router } from "express";\nimport { prisma } from "../prisma.js";', 1)
if 'uploadJsonViaGoogleDrivePool' not in routes:
    routes = routes.replace('import { emitRealtimeInvalidation } from "../services/realtimeState.service.js";',
      'import { emitRealtimeInvalidation } from "../services/realtimeState.service.js";\nimport { uploadJsonViaGoogleDrivePool } from "../services/googleDriveStoragePool.service.js";\nimport { updateJsonOnDrive } from "../services/googleDrive.service.js";',1)
old_put = """  const updated = await prisma.workspaceDocument.update({
    where: { id: documentId },
    data: { rawWorkbookData: req.body ?? null },
  });
  res.json({ rawWorkbookData: updated.rawWorkbookData, updatedAt: updated.updatedAt });
}));"""
new_put = """  const updated = await prisma.workspaceDocument.update({
    where: { id: documentId },
    data: {
      rawWorkbookData: req.body ?? null,
      rawWorkbookUpdatedAt: new Date(),
      lastEditedById: req.user.id,
    },
  });
  res.json({ rawWorkbookData: updated.rawWorkbookData, rawWorkbookUpdatedAt: updated.rawWorkbookUpdatedAt, updatedAt: updated.updatedAt });
}));

router.post("/documents/:id/raw-workbook/sync-drive", asyncHandler(async (req, res) => {
  const documentId = required(req.params.id, "id");
  const document = await prisma.workspaceDocument.findUniqueOrThrow({ where: { id: documentId } });
  await workspaceService.assertDocumentAccess(req.user, document, "EDIT");
  if (document.type !== "TSHEET") throw new AppError("Not a TSHEET document", 400);
  if (!document.rawWorkbookData) return res.json({ synced: false, skipped: true, reason: "no-raw-workbook" });
  if (document.rawWorkbookDriveSyncedAt && document.rawWorkbookUpdatedAt && document.rawWorkbookDriveSyncedAt >= document.rawWorkbookUpdatedAt) {
    return res.json({ synced: false, skipped: true, reason: "already-synced", syncedAt: document.rawWorkbookDriveSyncedAt });
  }

  const filename = String(document.title || "Untitled spreadsheet").replace(/[\\\\/:*?"<>|]+/g, "_") + ".casual-workbook.json";
  let driveFileId = document.rawWorkbookDriveFileId;
  let storageAccountId = document.rawWorkbookDriveStorageAccountId;

  if (driveFileId) {
    await updateJsonOnDrive({
      fileId: driveFileId,
      storageAccountId,
      filename,
      contentJson: document.rawWorkbookData,
      metadata: { system: "TOS", module: "TWS", kind: "CASUAL_RAW_WORKBOOK", documentId },
    });
  } else {
    const uploaded = await uploadJsonViaGoogleDrivePool({
      filename,
      contentJson: document.rawWorkbookData,
      context: { projectId: document.projectId, taskId: document.taskId, twsDocument: true, twsType: "TSHEET", rawWorkbook: true },
      metadata: { system: "TOS", module: "TWS", kind: "CASUAL_RAW_WORKBOOK", documentId, title: document.title },
    });
    driveFileId = uploaded.driveFileId;
    storageAccountId = uploaded.storageAccountId;
  }

  const syncedAt = new Date();
  await prisma.workspaceDocument.update({
    where: { id: documentId },
    data: { rawWorkbookDriveFileId: driveFileId, rawWorkbookDriveStorageAccountId: storageAccountId, rawWorkbookDriveSyncedAt: syncedAt },
  });
  res.json({ synced: true, skipped: false, driveFileId, storageAccountId, syncedAt });
}));"""
if old_put not in routes: fail("backend raw PUT anchor missing")
ROUTES.write_text(routes.replace(old_put,new_put,1))

schema = SCHEMA.read_text()
schema_anchor = "  rawWorkbookData Json?\n  plainText      String?"
if schema_anchor not in schema: fail("schema anchor missing")
schema = schema.replace(schema_anchor, """  rawWorkbookData                  Json?
  rawWorkbookUpdatedAt             DateTime?
  rawWorkbookDriveFileId           String?
  rawWorkbookDriveStorageAccountId String?
  rawWorkbookDriveSyncedAt         DateTime?
  plainText                        String?""",1)
SCHEMA.write_text(schema)

MIGRATION.parent.mkdir(parents=True, exist_ok=True)
MIGRATION.write_text("""ALTER TABLE "WorkspaceDocument"
  ADD COLUMN "rawWorkbookUpdatedAt" TIMESTAMP(3),
  ADD COLUMN "rawWorkbookDriveFileId" TEXT,
  ADD COLUMN "rawWorkbookDriveStorageAccountId" TEXT,
  ADD COLUMN "rawWorkbookDriveSyncedAt" TIMESTAMP(3);
""")

checks = {
 "parent": 'data-tsheets-persistence="recents-drive-v1"' in PARENT.read_text(),
 "interval": "DRIVE_SYNC_INTERVAL_MS = 60_000" in PARENT.read_text(),
 "api": "syncRawWorkbookDrive" in API.read_text(),
 "autosave": "null id creates the real TOS file" in AUTOSAVE.read_text(),
 "hydrate": "TosWorkbookHydrator" in APP.read_text(),
 "recents": "__TOS_TSHEETS_RECENTS__" in HOME.read_text(),
 "prisma": 'import { prisma } from "../prisma.js";' in ROUTES.read_text(),
 "syncroute": 'raw-workbook/sync-drive' in ROUTES.read_text(),
 "schema": "rawWorkbookDriveSyncedAt" in SCHEMA.read_text(),
 "migration": MIGRATION.exists(),
}
bad = [k for k,v in checks.items() if not v]
if bad: fail("verify failed: "+",".join(bad))

print("PATCH="+PATCH)
print("APPLY=PASS")
print("FIRST_REAL_AUTOSAVE_CREATES_TOS_DOCUMENT=YES")
print("TOS_RECENT_FILES_BRIDGE=YES")
print("SERVER_RAW_SAVE=YES")
print("SERVER_RAW_LOAD=YES")
print("DRIVE_BACKGROUND_INTERVAL_SECONDS=60")
print("DRIVE_SYNC_DIRTY_CHECK=SERVER_TIMESTAMP")
print("DRIVE_RAW_WORKBOOK_FORMAT=JSON_SIDECAR")
print("LEGACY_TSHEET_DRIVE_FILE_PRESERVED=YES")
print("BACK_HOME_V4_TOUCHED=NO")
print("FRAME_FIT_V2_TOUCHED=NO")
print("COMMIT=NO")
print("PUSH=NO")
