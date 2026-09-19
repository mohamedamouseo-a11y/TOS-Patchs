#!/usr/bin/env python3
from pathlib import Path

ROOT = Path.cwd()
DRIVE = ROOT / "backend/src/services/googleDrive.service.js"
POOL = ROOT / "backend/src/services/googleDriveStoragePool.service.js"
FILES = ROOT / "backend/src/routes/files.routes.js"
EMP = ROOT / "backend/src/routes/employeeWork.routes.js"
WS = ROOT / "backend/src/services/workspace.service.js"
TEST = ROOT / "backend/src/services/googleDriveStoragePoolPhase2_1.test.js"
PACKAGE = ROOT / "backend/package.json"

for p in [DRIVE, POOL, FILES, EMP, WS, PACKAGE]:
    if not p.exists():
        raise SystemExit(f"PATCH=FAIL\nREASON=Missing {p}")

def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"PATCH=FAIL\nREASON={label} expected once, found {count}")
    return text.replace(old, new, 1)

changed = []

# ============================================================
# googleDrive.service.js
# ============================================================
drive = DRIVE.read_text(encoding="utf-8")

old_client = '''export async function getDriveClientForSettingsKey(settingsKey = SETTINGS_ID) {
  const settings = await getEffectiveSettings(settingsKey);
  if (!settings.connected || !settings.refreshToken) throw new AppError("Google Drive is not connected", 400);
  const oauth2Client = await getOAuthClient(settings);
  oauth2Client.setCredentials({ refresh_token: decryptSecret(settings.refreshToken) });
  const google = await getGoogle();
  return { drive: google.drive({ version: "v3", auth: oauth2Client }), settings };
}

export async function getDriveClient() {
  return getDriveClientForSettingsKey(SETTINGS_ID);
}
'''

new_client = '''export async function getDriveClientForSettingsKey(settingsKey = SETTINGS_ID) {
  const settings = await getEffectiveSettings(settingsKey);
  if (!settings.connected || !settings.refreshToken) throw new AppError("Google Drive is not connected", 400);
  const oauth2Client = await getOAuthClient(settings);
  oauth2Client.setCredentials({ refresh_token: decryptSecret(settings.refreshToken) });
  const google = await getGoogle();
  const drive = google.drive({ version: "v3", auth: oauth2Client });
  Object.defineProperty(drive, "__tosGoogleDriveSettingsKey", {
    value: settingsKey,
    enumerable: false,
    configurable: false,
    writable: false,
  });
  return { drive, settings };
}

export async function getDriveClient() {
  return getDriveClientForSettingsKey(SETTINGS_ID);
}

export async function getDriveClientForStorageAccountId(storageAccountId = null) {
  const accountId = storageAccountId || LEGACY_PRIMARY_STORAGE_ACCOUNT_ID;
  if (accountId === LEGACY_PRIMARY_STORAGE_ACCOUNT_ID) {
    return getDriveClientForSettingsKey(SETTINGS_ID);
  }

  const account = await prisma.googleDriveStorageAccount.findUnique({
    where: { id: accountId },
    select: { settingsKey: true },
  });
  if (!account?.settingsKey) throw new AppError("Google Drive storage account not found", 404);
  return getDriveClientForSettingsKey(account.settingsKey);
}

async function getDriveClientForFileOptions(options = {}) {
  if (options?.settingsKey) return getDriveClientForSettingsKey(options.settingsKey);
  return getDriveClientForStorageAccountId(options?.storageAccountId ?? null);
}

function driveSettingsKey(drive) {
  return drive?.__tosGoogleDriveSettingsKey || SETTINGS_ID;
}
'''

if old_client in drive:
    drive = replace_once(drive, old_client, new_client, "exact account client")
elif "getDriveClientForStorageAccountId" not in drive:
    raise SystemExit("PATCH=FAIL\nREASON=getDriveClientForSettingsKey block changed unexpectedly")

for old, new, label in [
    (
        '  const r = await withRetry(() => drive.files.list({ q, fields: "files(id,name)", spaces: "drive", pageSize: 1, supportsAllDrives: true, includeItemsFromAllDrives: true }), 2, { action: "drive_find_folder" });\n',
        '  const r = await withRetry(() => drive.files.list({ q, fields: "files(id,name)", spaces: "drive", pageSize: 1, supportsAllDrives: true, includeItemsFromAllDrives: true }), 2, { action: "drive_find_folder", settingsKey: driveSettingsKey(drive) });\n',
        "folder lookup settings key",
    ),
    (
        '  }), 2, { action: "drive_create_folder" });\n',
        '  }), 2, { action: "drive_create_folder", settingsKey: driveSettingsKey(drive) });\n',
        "folder create settings key",
    ),
    (
        '    }), 2, { action: "drive_assert_root_folder" });\n',
        '    }), 2, { action: "drive_assert_root_folder", settingsKey: driveSettingsKey(drive) });\n',
        "folder assert settings key",
    ),
]:
    if old in drive:
        drive = replace_once(drive, old, new, label)

old_ops = '''export async function uploadJsonToDrive({ filename, contentJson, context = {}, metadata = {} }) {
  const { drive, settings } = await getDriveClient();
  const folderId = await resolveFolderForContext(drive, settings, { ...context, twsDocument: true });
  let response;
  try {
    response = await withRetry(() => drive.files.create({
      requestBody: {
        name: safeDriveName(filename || "tws-document.json", "tws-document.json"),
        parents: [folderId],
        mimeType: "application/json",
      },
      media: {
        mimeType: "application/json",
        body: Readable.from(jsonBuffer(driveJsonPayload(contentJson, metadata))),
      },
      fields: "id,name,webViewLink",
      supportsAllDrives: true,
    }), 1, { action: "drive_upload_tws_json" });
  } catch (err) {
    throw await normalizeGoogleDriveRuntimeError(err, { action: "drive_upload_tws_json" });
  }
  return { driveFileId: response.data.id, name: response.data.name, webViewLink: response.data.webViewLink || null, provider: "GOOGLE_DRIVE" };
}

export async function updateJsonOnDrive({ fileId, filename = null, contentJson, metadata = {} }) {
  if (!fileId) throw new AppError("Google Drive file id is required", 400);
  const requestBody = {};
  if (filename) requestBody.name = safeDriveName(filename, "tws-document.json");
  try {
    const response = await withRetry(() => driveUpdateJson(fileId, requestBody, contentJson, metadata), 1, { action: "drive_update_tws_json" });
    return { driveFileId: response.data.id, name: response.data.name, webViewLink: response.data.webViewLink || null, provider: "GOOGLE_DRIVE" };
  } catch (err) {
    throw await normalizeGoogleDriveRuntimeError(err, { action: "drive_update_tws_json" });
  }
}

async function driveUpdateJson(fileId, requestBody, contentJson, metadata) {
  const { drive } = await getDriveClient();
  return drive.files.update({
    fileId,
    requestBody,
    media: {
      mimeType: "application/json",
      body: Readable.from(jsonBuffer(driveJsonPayload(contentJson, metadata))),
    },
    fields: "id,name,webViewLink",
    supportsAllDrives: true,
  });
}

export async function readJsonFromDrive(fileId) {
  if (!fileId) throw new AppError("Google Drive file id is required", 400);
  try {
    const { stream } = await getGoogleDriveDownload(fileId);
    const chunks = [];
    for await (const chunk of stream) chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
    const parsed = JSON.parse(Buffer.concat(chunks).toString("utf8") || "{}");
    return parsed?.contentJson !== undefined ? parsed.contentJson : parsed;
  } catch (err) {
    if (err instanceof SyntaxError) throw new AppError("Stored TWS Google Drive JSON is corrupted", 500);
    throw await normalizeGoogleDriveRuntimeError(err, { action: "drive_read_tws_json" });
  }
}

export async function copyJsonFileOnDrive({ sourceFileId, filename, context = {}, metadata = {} }) {
  const contentJson = await readJsonFromDrive(sourceFileId);
  return uploadJsonToDrive({ filename, contentJson, context, metadata });
}

export async function getGoogleDriveDownload(fileId) {
  const { drive } = await getDriveClient();
  const metadata = await withRetry(() => drive.files.get({ fileId, fields: "id,name,mimeType,size", supportsAllDrives: true }), 2, { action: "drive_download_metadata" });
  const stream = await withRetry(() => drive.files.get({ fileId, alt: "media", supportsAllDrives: true }, { responseType: "stream" }), 2, { action: "drive_download_stream" });
  return { metadata: metadata.data, stream: stream.data };
}

export async function deleteGoogleDriveFile(fileId, options = {}) {
  if (!fileId) return false;
  const settingsKey = options.settingsKey || SETTINGS_ID;
  try {
    const { drive } = await getDriveClientForSettingsKey(settingsKey);
    await withRetry(() => drive.files.delete({ fileId, supportsAllDrives: true }), 1, { action: "drive_delete_file", settingsKey });
    return true;
  } catch (err) {
    console.error("GOOGLE_DRIVE_DELETE_FAILED", {
      fileId,
      status: err?.response?.status || err?.code,
      message: err?.message,
    });
    return false;
  }
}
'''

new_ops = '''export async function uploadJsonToDrive({ filename, contentJson, context = {}, metadata = {} }, options = {}) {
  const settingsKey = options.settingsKey || SETTINGS_ID;
  const storageAccountId = options.storageAccountId || (settingsKey === SETTINGS_ID ? LEGACY_PRIMARY_STORAGE_ACCOUNT_ID : null);
  const { drive, settings } = await getDriveClientForSettingsKey(settingsKey);
  const folderId = await resolveFolderForContext(
    drive,
    settings,
    { ...context, twsDocument: true },
    storageAccountId || LEGACY_PRIMARY_STORAGE_ACCOUNT_ID,
  );
  let response;
  try {
    response = await withRetry(() => drive.files.create({
      requestBody: {
        name: safeDriveName(filename || "tws-document.json", "tws-document.json"),
        parents: [folderId],
        mimeType: "application/json",
      },
      media: {
        mimeType: "application/json",
        body: Readable.from(jsonBuffer(driveJsonPayload(contentJson, metadata))),
      },
      fields: "id,name,webViewLink",
      supportsAllDrives: true,
    }), 1, { action: "drive_upload_tws_json", settingsKey });
  } catch (err) {
    throw await normalizeGoogleDriveRuntimeError(err, { action: "drive_upload_tws_json", settingsKey });
  }
  return {
    driveFileId: response.data.id,
    storageAccountId,
    name: response.data.name,
    webViewLink: response.data.webViewLink || null,
    provider: "GOOGLE_DRIVE",
  };
}

export async function updateJsonOnDrive({ fileId, filename = null, contentJson, metadata = {}, storageAccountId = null }) {
  if (!fileId) throw new AppError("Google Drive file id is required", 400);
  const requestBody = {};
  if (filename) requestBody.name = safeDriveName(filename, "tws-document.json");
  const { drive, settings } = await getDriveClientForStorageAccountId(storageAccountId);
  try {
    const response = await withRetry(
      () => drive.files.update({
        fileId,
        requestBody,
        media: {
          mimeType: "application/json",
          body: Readable.from(jsonBuffer(driveJsonPayload(contentJson, metadata))),
        },
        fields: "id,name,webViewLink",
        supportsAllDrives: true,
      }),
      1,
      { action: "drive_update_tws_json", settingsKey: settings.id },
    );
    return {
      driveFileId: response.data.id,
      storageAccountId: storageAccountId || LEGACY_PRIMARY_STORAGE_ACCOUNT_ID,
      name: response.data.name,
      webViewLink: response.data.webViewLink || null,
      provider: "GOOGLE_DRIVE",
    };
  } catch (err) {
    throw await normalizeGoogleDriveRuntimeError(err, { action: "drive_update_tws_json", settingsKey: settings.id });
  }
}

export async function readJsonFromDrive(fileId, storageAccountId = null) {
  if (!fileId) throw new AppError("Google Drive file id is required", 400);
  try {
    const { stream } = await getGoogleDriveDownload(fileId, { storageAccountId });
    const chunks = [];
    for await (const chunk of stream) chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
    const parsed = JSON.parse(Buffer.concat(chunks).toString("utf8") || "{}");
    return parsed?.contentJson !== undefined ? parsed.contentJson : parsed;
  } catch (err) {
    if (err instanceof SyntaxError) throw new AppError("Stored TWS Google Drive JSON is corrupted", 500);
    throw err;
  }
}

export async function copyJsonFileOnDrive({ sourceFileId, sourceStorageAccountId = null, filename, context = {}, metadata = {} }) {
  const contentJson = await readJsonFromDrive(sourceFileId, sourceStorageAccountId);
  return uploadJsonToDrive({ filename, contentJson, context, metadata });
}

export async function getGoogleDriveDownload(fileId, options = {}) {
  if (!fileId) throw new AppError("Google Drive file id is required", 400);
  const { drive, settings } = await getDriveClientForFileOptions(options);
  const metadata = await withRetry(
    () => drive.files.get({ fileId, fields: "id,name,mimeType,size", supportsAllDrives: true }),
    2,
    { action: "drive_download_metadata", settingsKey: settings.id },
  );
  const stream = await withRetry(
    () => drive.files.get({ fileId, alt: "media", supportsAllDrives: true }, { responseType: "stream" }),
    2,
    { action: "drive_download_stream", settingsKey: settings.id },
  );
  return { metadata: metadata.data, stream: stream.data };
}

export async function deleteGoogleDriveFile(fileId, options = {}) {
  if (!fileId) return false;
  try {
    const { drive, settings } = await getDriveClientForFileOptions(options);
    await withRetry(
      () => drive.files.delete({ fileId, supportsAllDrives: true }),
      1,
      { action: "drive_delete_file", settingsKey: settings.id },
    );
    return true;
  } catch (err) {
    console.error("GOOGLE_DRIVE_DELETE_FAILED", {
      fileId,
      storageAccountId: options?.storageAccountId || null,
      status: err?.response?.status || err?.code,
      message: err?.message,
    });
    return false;
  }
}
'''

if old_ops in drive:
    drive = replace_once(drive, old_ops, new_ops, "exact account file operations")
elif "getGoogleDriveDownload(fileId, options = {})" not in drive:
    raise SystemExit("PATCH=FAIL\nREASON=Drive operation block changed unexpectedly")

if DRIVE.read_text(encoding="utf-8") != drive:
    DRIVE.write_text(drive, encoding="utf-8")
    changed.append(str(DRIVE.relative_to(ROOT)))

# ============================================================
# googleDriveStoragePool.service.js
# ============================================================
pool = POOL.read_text(encoding="utf-8")

if "uploadJsonToDrive" not in pool.split('} from "./googleDrive.service.js";', 1)[0]:
    pool = replace_once(
        pool,
        '''  isGoogleDriveQuotaExceededError,
  uploadFileToDrive,
} from "./googleDrive.service.js";
''',
        '''  isGoogleDriveQuotaExceededError,
  uploadFileToDrive,
  uploadJsonToDrive,
} from "./googleDrive.service.js";
''',
        "pool JSON import",
    )

if "export async function uploadJsonViaGoogleDrivePool" not in pool:
    pool = pool.rstrip() + r'''

export async function uploadJsonViaGoogleDrivePool({ filename, contentJson, context = {}, metadata = {} }) {
  const candidates = await loadPoolCandidates();
  const uploadBytes = Buffer.byteLength(JSON.stringify(contentJson ?? {}), "utf8");
  let lastQuotaError = null;

  for (const account of candidates) {
    let quota;
    try {
      quota = await getGoogleDriveStorageQuota(account.settingsKey);
    } catch (error) {
      lastQuotaError = error;
      continue;
    }

    const capacity = googleDriveQuotaCanAcceptUpload(quota, uploadBytes);
    if (!capacity.eligible) continue;

    try {
      return await uploadJsonToDrive(
        { filename, contentJson, context, metadata },
        { settingsKey: account.settingsKey, storageAccountId: account.id },
      );
    } catch (error) {
      if (isGoogleDriveQuotaExceededError(error)) {
        lastQuotaError = error;
        continue;
      }
      throw error;
    }
  }

  if (lastQuotaError && candidates.length === 1) throw lastQuotaError;
  throw new AppError("No Google Drive storage account is available for this TWS upload", 507);
}
''' + "\n"

if POOL.read_text(encoding="utf-8") != pool:
    POOL.write_text(pool, encoding="utf-8")
    changed.append(str(POOL.relative_to(ROOT)))

# ============================================================
# files.routes.js
# ============================================================
files = FILES.read_text(encoding="utf-8")

if 'deleteGoogleDriveFile(file.driveFileId, { storageAccountId: file.storageAccountId })' not in files:
    files = replace_once(
        files,
        '  const deleted = await deleteGoogleDriveFile(file.driveFileId);\n',
        '  const deleted = await deleteGoogleDriveFile(file.driveFileId, { storageAccountId: file.storageAccountId });\n',
        "File exact delete",
    )

plain_download = 'const download = await getGoogleDriveDownload(file.driveFileId);'
exact_download = 'const download = await getGoogleDriveDownload(file.driveFileId, { storageAccountId: file.storageAccountId });'
plain_count = files.count(plain_download)
if plain_count:
    if plain_count != 2:
        raise SystemExit(f"PATCH=FAIL\nREASON=Expected 2 File download sites, found {plain_count}")
    files = files.replace(plain_download, exact_download)

if files.count(exact_download) != 2:
    raise SystemExit("PATCH=FAIL\nREASON=File exact download routing incomplete")

if FILES.read_text(encoding="utf-8") != files:
    FILES.write_text(files, encoding="utf-8")
    changed.append(str(FILES.relative_to(ROOT)))

# ============================================================
# employeeWork.routes.js
# ============================================================
emp = EMP.read_text(encoding="utf-8")
if 'getGoogleDriveDownload(file.driveFileId, { storageAccountId: file.storageAccountId })' not in emp:
    emp = replace_once(
        emp,
        '  const download = await getGoogleDriveDownload(file.driveFileId);\n',
        '  const download = await getGoogleDriveDownload(file.driveFileId, { storageAccountId: file.storageAccountId });\n',
        "Employee exact download",
    )

if EMP.read_text(encoding="utf-8") != emp:
    EMP.write_text(emp, encoding="utf-8")
    changed.append(str(EMP.relative_to(ROOT)))

# ============================================================
# workspace.service.js
# ============================================================
ws = WS.read_text(encoding="utf-8")

if 'uploadJsonViaGoogleDrivePool' not in ws:
    ws = replace_once(
        ws,
        'import { uploadJsonToDrive, updateJsonOnDrive, readJsonFromDrive, deleteGoogleDriveFile } from "./googleDrive.service.js";\n',
        'import { updateJsonOnDrive, readJsonFromDrive, deleteGoogleDriveFile } from "./googleDrive.service.js";\nimport { uploadJsonViaGoogleDrivePool } from "./googleDriveStoragePool.service.js";\n',
        "Workspace pool import",
    )

if 'readJsonFromDrive(document.driveFileId, document.storageAccountId)' not in ws:
    ws = replace_once(
        ws,
        '  if (document?.driveFileId) return normalizeContentForType(document.type, await readJsonFromDrive(document.driveFileId));\n',
        '  if (document?.driveFileId) return normalizeContentForType(document.type, await readJsonFromDrive(document.driveFileId, document.storageAccountId));\n',
        "Workspace exact read",
    )

plain_upload = 'const uploaded = await uploadJsonToDrive({'
pool_upload = 'const uploaded = await uploadJsonViaGoogleDrivePool({'
plain_upload_count = ws.count(plain_upload)
if plain_upload_count:
    if plain_upload_count != 4:
        raise SystemExit(f"PATCH=FAIL\nREASON=Expected 4 TWS upload sites, found {plain_upload_count}")
    ws = ws.replace(plain_upload, pool_upload)

if ws.count(pool_upload) != 4:
    raise SystemExit("PATCH=FAIL\nREASON=TWS pool upload routing incomplete")

# 1) ensureDriveBackedDocument
old = '''    data: {
      driveFileId: uploaded.driveFileId,
      driveProvider: "GOOGLE_DRIVE",
      storageMode: "GOOGLE_DRIVE",
      contentJson: metadataContentFor({ driveFileId: uploaded.driveFileId, type: document.type }),
      plainText: computePlainText(document.type, normalized),
      lastEditedById: user?.id || document.lastEditedById || document.ownerId,
    },
'''
new = '''    data: {
      driveFileId: uploaded.driveFileId,
      storageAccountId: uploaded.storageAccountId,
      driveProvider: "GOOGLE_DRIVE",
      storageMode: "GOOGLE_DRIVE",
      contentJson: metadataContentFor({ driveFileId: uploaded.driveFileId, type: document.type }),
      plainText: computePlainText(document.type, normalized),
      lastEditedById: user?.id || document.lastEditedById || document.ownerId,
    },
'''
if old in ws:
    ws = replace_once(ws, old, new, "ensureDriveBacked ownership")

# 2) WorkspaceVersion
old = '''        contentJson: metadataContentFor({ driveFileId: uploaded.driveFileId, type: document.type }),
        driveFileId: uploaded.driveFileId,
        driveProvider: "GOOGLE_DRIVE",
        createdById: user.id,
        changeSummary,
'''
new = '''        contentJson: metadataContentFor({ driveFileId: uploaded.driveFileId, type: document.type }),
        driveFileId: uploaded.driveFileId,
        storageAccountId: uploaded.storageAccountId,
        driveProvider: "GOOGLE_DRIVE",
        createdById: user.id,
        changeSummary,
'''
if old in ws:
    ws = replace_once(ws, old, new, "WorkspaceVersion ownership")

if 'deleteGoogleDriveFile(uploaded.driveFileId, { storageAccountId: uploaded.storageAccountId })' not in ws:
    ws = replace_once(
        ws,
        '      await deleteGoogleDriveFile(uploaded.driveFileId);\n',
        '      await deleteGoogleDriveFile(uploaded.driveFileId, { storageAccountId: uploaded.storageAccountId });\n',
        "Version cleanup exact account",
    )

# 3) createDocument
old = '''      plainText: computePlainText(type, contentJson),
      driveFileId: uploaded.driveFileId,
      driveProvider: "GOOGLE_DRIVE",
      storageMode: "GOOGLE_DRIVE",
      ownerId: user.id,
'''
new = '''      plainText: computePlainText(type, contentJson),
      driveFileId: uploaded.driveFileId,
      storageAccountId: uploaded.storageAccountId,
      driveProvider: "GOOGLE_DRIVE",
      storageMode: "GOOGLE_DRIVE",
      ownerId: user.id,
'''
if old in ws:
    ws = replace_once(ws, old, new, "createDocument ownership")

# 4) duplicateDocument
old = '''      plainText: computePlainText(document.type, sourceContent),
      driveFileId: uploaded.driveFileId,
      driveProvider: "GOOGLE_DRIVE",
      storageMode: "GOOGLE_DRIVE",
      ownerId: user.id,
      projectId: document.projectId,
'''
new = '''      plainText: computePlainText(document.type, sourceContent),
      driveFileId: uploaded.driveFileId,
      storageAccountId: uploaded.storageAccountId,
      driveProvider: "GOOGLE_DRIVE",
      storageMode: "GOOGLE_DRIVE",
      ownerId: user.id,
      projectId: document.projectId,
'''
if old in ws:
    ws = replace_once(ws, old, new, "duplicate ownership")

# Initial post-create update
old = '''  await updateJsonOnDrive({
    fileId: uploaded.driveFileId,
    filename: workspaceDriveFileName(document),
    contentJson,
    metadata: driveMetadataFor(document, { createdAt: document.createdAt }),
  });
'''
new = '''  await updateJsonOnDrive({
    fileId: uploaded.driveFileId,
    storageAccountId: uploaded.storageAccountId,
    filename: workspaceDriveFileName(document),
    contentJson,
    metadata: driveMetadataFor(document, { createdAt: document.createdAt }),
  });
'''
if old in ws:
    ws = replace_once(ws, old, new, "post-create exact update")

# Rename
old = '    await updateJsonOnDrive({ fileId: updated.driveFileId, filename: workspaceDriveFileName(updated), contentJson, metadata: driveMetadataFor(updated, { renamedAt: new Date().toISOString() }) });\n'
new = '    await updateJsonOnDrive({ fileId: updated.driveFileId, storageAccountId: updated.storageAccountId, filename: workspaceDriveFileName(updated), contentJson, metadata: driveMetadataFor(updated, { renamedAt: new Date().toISOString() }) });\n'
if old in ws:
    ws = replace_once(ws, old, new, "rename exact update")

# Main content save
old = '''  await updateJsonOnDrive({
    fileId: document.driveFileId,
    filename: workspaceDriveFileName(document),
    contentJson: normalized,
    metadata: driveMetadataFor(document, { savedById: user.id }),
  });
'''
new = '''  await updateJsonOnDrive({
    fileId: document.driveFileId,
    storageAccountId: document.storageAccountId,
    filename: workspaceDriveFileName(document),
    contentJson: normalized,
    metadata: driveMetadataFor(document, { savedById: user.id }),
  });
'''
if old in ws:
    ws = replace_once(ws, old, new, "content exact update")

# Permanent delete
if 'deleteGoogleDriveFile(document.driveFileId, { storageAccountId: document.storageAccountId })' not in ws:
    ws = replace_once(
        ws,
        '  if (document.driveFileId) await deleteGoogleDriveFile(document.driveFileId);\n',
        '  if (document.driveFileId) await deleteGoogleDriveFile(document.driveFileId, { storageAccountId: document.storageAccountId });\n',
        "document exact delete",
    )

# Version restore exact source
if 'readJsonFromDrive(version.driveFileId, version.storageAccountId)' not in ws:
    ws = replace_once(
        ws,
        '  const versionContent = normalizeContentForType(document.type, version.driveFileId ? await readJsonFromDrive(version.driveFileId) : version.contentJson);\n',
        '  const versionContent = normalizeContentForType(document.type, version.driveFileId ? await readJsonFromDrive(version.driveFileId, version.storageAccountId) : version.contentJson);\n',
        "version exact read",
    )

# Version restore destination
old = '''  await updateJsonOnDrive({
    fileId: document.driveFileId,
    filename: workspaceDriveFileName(document),
    contentJson: versionContent,
    metadata: driveMetadataFor(document, { restoredFromVersion: version.versionNumber }),
  });
'''
new = '''  await updateJsonOnDrive({
    fileId: document.driveFileId,
    storageAccountId: document.storageAccountId,
    filename: workspaceDriveFileName(document),
    contentJson: versionContent,
    metadata: driveMetadataFor(document, { restoredFromVersion: version.versionNumber }),
  });
'''
if old in ws:
    ws = replace_once(ws, old, new, "version restore exact update")

# CSV
old = '  await updateJsonOnDrive({ fileId: backed.document.driveFileId, filename: workspaceDriveFileName(backed.document), contentJson: normalized, metadata: driveMetadataFor(backed.document, { import: "CSV" }) });\n'
new = '  await updateJsonOnDrive({ fileId: backed.document.driveFileId, storageAccountId: backed.document.storageAccountId, filename: workspaceDriveFileName(backed.document), contentJson: normalized, metadata: driveMetadataFor(backed.document, { import: "CSV" }) });\n'
if old in ws:
    ws = replace_once(ws, old, new, "CSV exact update")

# XLSX
old = '''  await updateJsonOnDrive({
    fileId: backed.document.driveFileId,
    filename: workspaceDriveFileName(backed.document),
    contentJson: normalized,
    metadata: driveMetadataFor(backed.document, { import: "XLSX", originalName: safeOriginalName }),
  });
'''
new = '''  await updateJsonOnDrive({
    fileId: backed.document.driveFileId,
    storageAccountId: backed.document.storageAccountId,
    filename: workspaceDriveFileName(backed.document),
    contentJson: normalized,
    metadata: driveMetadataFor(backed.document, { import: "XLSX", originalName: safeOriginalName }),
  });
'''
if old in ws:
    ws = replace_once(ws, old, new, "XLSX exact update")

# Contract checks before writing.
required_workspace_markers = [
    "uploadJsonViaGoogleDrivePool",
    "readJsonFromDrive(document.driveFileId, document.storageAccountId)",
    "readJsonFromDrive(version.driveFileId, version.storageAccountId)",
    "storageAccountId: uploaded.storageAccountId",
    "deleteGoogleDriveFile(uploaded.driveFileId, { storageAccountId: uploaded.storageAccountId })",
    "deleteGoogleDriveFile(document.driveFileId, { storageAccountId: document.storageAccountId })",
    "storageAccountId: backed.document.storageAccountId",
]
for marker in required_workspace_markers:
    if marker not in ws:
        raise SystemExit(f"PATCH=FAIL\nREASON=Workspace marker missing: {marker}")

if WS.read_text(encoding="utf-8") != ws:
    WS.write_text(ws, encoding="utf-8")
    changed.append(str(WS.relative_to(ROOT)))

# ============================================================
# tests
# ============================================================
test_js = r'''import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../..");
const read = (relative) => readFile(path.join(repoRoot, relative), "utf8");

test("Phase 2.1 resolves exact account and legacy null only to primary", async () => {
  const service = await read("backend/src/services/googleDrive.service.js");
  assert.match(service, /getDriveClientForStorageAccountId\(storageAccountId = null\)/);
  assert.match(service, /const accountId = storageAccountId \|\| LEGACY_PRIMARY_STORAGE_ACCOUNT_ID/);
  assert.match(service, /accountId === LEGACY_PRIMARY_STORAGE_ACCOUNT_ID/);
  assert.match(service, /where: \{ id: accountId \}/);
  assert.doesNotMatch(service, /for\s*\([^)]*googleDriveStorageAccount[\s\S]{0,300}fileId/);
});

test("Phase 2.1 routes File download preview and delete by ownership", async () => {
  const route = await read("backend/src/routes/files.routes.js");
  assert.match(route, /deleteGoogleDriveFile\(file\.driveFileId, \{ storageAccountId: file\.storageAccountId \}\)/);
  const exactDownloads = route.match(/getGoogleDriveDownload\(file\.driveFileId, \{ storageAccountId: file\.storageAccountId \}\)/g) || [];
  assert.equal(exactDownloads.length, 2);
});

test("Phase 2.1 routes employee attachment reads by ownership", async () => {
  const route = await read("backend/src/routes/employeeWork.routes.js");
  assert.match(route, /getGoogleDriveDownload\(file\.driveFileId, \{ storageAccountId: file\.storageAccountId \}\)/);
});

test("Phase 2.1 pools TWS writes and persists document/version ownership", async () => {
  const workspace = await read("backend/src/services/workspace.service.js");
  assert.match(workspace, /uploadJsonViaGoogleDrivePool/);
  assert.match(workspace, /readJsonFromDrive\(document\.driveFileId, document\.storageAccountId\)/);
  assert.match(workspace, /readJsonFromDrive\(version\.driveFileId, version\.storageAccountId\)/);
  assert.match(workspace, /storageAccountId:\s*uploaded\.storageAccountId/);
});

test("Phase 2.1 routes TWS updates and deletes to the exact account", async () => {
  const workspace = await read("backend/src/services/workspace.service.js");
  assert.match(workspace, /deleteGoogleDriveFile\(uploaded\.driveFileId, \{ storageAccountId: uploaded\.storageAccountId \}\)/);
  assert.match(workspace, /deleteGoogleDriveFile\(document\.driveFileId, \{ storageAccountId: document\.storageAccountId \}\)/);
  assert.match(workspace, /storageAccountId:\s*document\.storageAccountId/);
  assert.match(workspace, /storageAccountId:\s*backed\.document\.storageAccountId/);
});

test("Phase 2.1 isolates secondary reconnect state during folder operations", async () => {
  const service = await read("backend/src/services/googleDrive.service.js");
  assert.match(service, /__tosGoogleDriveSettingsKey/);
  assert.match(service, /drive_find_folder", settingsKey: driveSettingsKey\(drive\)/);
  assert.match(service, /drive_create_folder", settingsKey: driveSettingsKey\(drive\)/);
  assert.match(service, /drive_assert_root_folder", settingsKey: driveSettingsKey\(drive\)/);
  assert.match(service, /const settingsKey = context\.settingsKey \|\| SETTINGS_ID/);
});

test("Phase 2.1 keeps TGWS and System Backup outside the pool", async () => {
  const backup = await read("backend/src/services/systemBackup.service.js");
  const tgws = await read("backend/src/services/tgws.service.js");
  assert.doesNotMatch(backup, /googleDriveStoragePool/);
  assert.doesNotMatch(tgws, /googleDriveStoragePool/);
  assert.match(backup, /getDriveClient/);
  assert.match(tgws, /getDriveClient/);
});
'''

if TEST.exists():
    if TEST.read_text(encoding="utf-8") != test_js:
        raise SystemExit("PATCH=FAIL\nREASON=Phase2.1 test exists with different content")
else:
    TEST.write_text(test_js, encoding="utf-8")
    changed.append(str(TEST.relative_to(ROOT)))

package = PACKAGE.read_text(encoding="utf-8")
script = '"test:google-drive-storage-pool-phase2-1": "node --test src/services/googleDriveStoragePoolPhase2_1.test.js"'
if script not in package:
    package = replace_once(
        package,
        '    "test:google-drive-storage-pool-phase2": "node --test src/services/googleDriveStoragePoolPhase2.test.js"\n',
        '    "test:google-drive-storage-pool-phase2": "node --test src/services/googleDriveStoragePoolPhase2.test.js",\n'
        '    "test:google-drive-storage-pool-phase2-1": "node --test src/services/googleDriveStoragePoolPhase2_1.test.js"\n',
        "Phase2.1 package script",
    )

if PACKAGE.read_text(encoding="utf-8") != package:
    PACKAGE.write_text(package, encoding="utf-8")
    changed.append(str(PACKAGE.relative_to(ROOT)))

print("PATCH=PASS")
print(f"FILES_CHANGED={len(changed)}")
for item in changed:
    print(item)
