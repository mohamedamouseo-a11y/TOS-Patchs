#!/usr/bin/env python3
from pathlib import Path

ROOT = Path.cwd()
DRIVE = ROOT / "backend/src/services/googleDrive.service.js"
POOL = ROOT / "backend/src/services/googleDriveStoragePool.service.js"
FILES = ROOT / "backend/src/routes/files.routes.js"
EMP = ROOT / "backend/src/routes/employeeWork.routes.js"
TEST = ROOT / "backend/src/services/googleDriveStoragePoolPhase2.test.js"
PACKAGE = ROOT / "backend/package.json"

for p in [DRIVE, FILES, EMP, PACKAGE]:
    if not p.exists():
        raise SystemExit(f"PATCH=FAIL\nREASON=Missing {p}")

def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"PATCH=FAIL\nREASON={label} expected once, found {n}")
    return text.replace(old, new, 1)

changed = []

drive = DRIVE.read_text(encoding="utf-8")

if 'const LEGACY_PRIMARY_STORAGE_ACCOUNT_ID = "gdrive_legacy_primary";' not in drive:
    drive = replace_once(
        drive,
        'const SETTINGS_ID = "main";\n',
        'const SETTINGS_ID = "main";\nconst LEGACY_PRIMARY_STORAGE_ACCOUNT_ID = "gdrive_legacy_primary";\n',
        "drive legacy account constant",
    )

drive = replace_once(
    drive,
    '''async function markGoogleDriveReconnectRequired(err, context = {}) {
  if (!isExpiredOrRevokedGoogleDriveTokenError(err)) return null;
  await prisma.googleDriveSettings.update({
    where: { id: SETTINGS_ID },
    data: { connected: false, refreshToken: null },
  }).catch(() => null);
''',
    '''async function markGoogleDriveReconnectRequired(err, context = {}) {
  if (!isExpiredOrRevokedGoogleDriveTokenError(err)) return null;
  const settingsKey = context.settingsKey || SETTINGS_ID;
  await prisma.googleDriveSettings.update({
    where: { id: settingsKey },
    data: { connected: false, refreshToken: null },
  }).catch(() => null);
''',
    "account-aware reconnect marker",
)

drive = replace_once(
    drive,
    '''async function getStoredSettings() {
  return prisma.googleDriveSettings.findUnique({ where: { id: SETTINGS_ID } });
}

function mergeSettings(settings = null) {
  return {
    id: SETTINGS_ID,
''',
    '''async function getStoredSettings(settingsKey = SETTINGS_ID) {
  return prisma.googleDriveSettings.findUnique({ where: { id: settingsKey } });
}

function mergeSettings(settings = null, settingsKey = SETTINGS_ID) {
  return {
    id: settingsKey,
''',
    "settings key support",
)

drive = replace_once(
    drive,
    '''async function getEffectiveSettings() {
  return mergeSettings(await getStoredSettings());
}
''',
    '''async function getEffectiveSettings(settingsKey = SETTINGS_ID) {
  return mergeSettings(await getStoredSettings(settingsKey), settingsKey);
}
''',
    "effective settings key support",
)

drive = replace_once(
    drive,
    '''export async function getDriveClient() {
  const settings = await getEffectiveSettings();
  if (!settings.connected || !settings.refreshToken) throw new AppError("Google Drive is not connected", 400);
  const oauth2Client = await getOAuthClient(settings);
  oauth2Client.setCredentials({ refresh_token: decryptSecret(settings.refreshToken) });
  const google = await getGoogle();
  return { drive: google.drive({ version: "v3", auth: oauth2Client }), settings };
}
''',
    '''export async function getDriveClientForSettingsKey(settingsKey = SETTINGS_ID) {
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

export async function getGoogleDriveStorageQuota(settingsKey = SETTINGS_ID) {
  const { drive } = await getDriveClientForSettingsKey(settingsKey);
  const response = await withRetry(
    () => drive.about.get({ fields: "storageQuota" }),
    2,
    { action: "drive_storage_quota", settingsKey },
  );
  const quota = response.data?.storageQuota || {};
  const numberOrNull = (value) => {
    if (value === null || value === undefined || value === "") return null;
    const parsed = Number(value);
    return Number.isFinite(parsed) && parsed >= 0 ? parsed : null;
  };
  return {
    limit: numberOrNull(quota.limit),
    usage: numberOrNull(quota.usage) || 0,
    usageInDrive: numberOrNull(quota.usageInDrive) || 0,
  };
}

export function isGoogleDriveQuotaExceededError(err) {
  const text = googleDriveErrorText(err);
  return text.includes("storagequotaexceeded")
    || text.includes("storage quota exceeded")
    || text.includes("storage quota has been exceeded")
    || text.includes("insufficient storage");
}
''',
    "drive client settings-key + quota support",
)

old_project = '''async function ensureProjectDriveFoldersForUpload(drive, settings, project) {
  if (!project) return null;
  let rootId = await resolveDriveRootFolder(drive, settings);
  rootId = await ensureFolder(drive, "Clients", rootId);
  rootId = await ensureFolder(drive, project.clientName || project.client?.name || "General", rootId);

  const projectFolderId = await resolveExistingFolderOrNull(drive, project.driveFolderId, "project.driveFolderId")
    || await ensureFolder(drive, project.name || "Project", rootId);
  const tasksFolderId = await resolveExistingFolderOrNull(drive, project.driveTasksFolderId, "project.driveTasksFolderId")
    || await ensureFolder(drive, "Tasks", projectFolderId);
  const clientFilesFolderId = await resolveExistingFolderOrNull(drive, project.driveClientFilesFolderId, "project.driveClientFilesFolderId")
    || await ensureFolder(drive, "Client Files", projectFolderId);

  if (project.driveFolderId !== projectFolderId || project.driveTasksFolderId !== tasksFolderId || project.driveClientFilesFolderId !== clientFilesFolderId) {
    await prisma.project.update({
      where: { id: project.id },
      data: { driveFolderId: projectFolderId, driveTasksFolderId: tasksFolderId, driveClientFilesFolderId: clientFilesFolderId },
    }).catch((err) => console.warn("GOOGLE_DRIVE_PROJECT_FOLDER_IDS_UPDATE_FAILED", { projectId: project.id, message: err?.message }));
  }

  return { projectFolderId, tasksFolderId, clientFilesFolderId };
}
'''

new_project = '''async function ensureProjectDriveFoldersForUpload(drive, settings, project, storageAccountId = LEGACY_PRIMARY_STORAGE_ACCOUNT_ID) {
  if (!project) return null;
  let rootId = await resolveDriveRootFolder(drive, settings);
  rootId = await ensureFolder(drive, "Clients", rootId);
  rootId = await ensureFolder(drive, project.clientName || project.client?.name || "General", rootId);

  const accountId = storageAccountId || LEGACY_PRIMARY_STORAGE_ACCOUNT_ID;
  const mapping = await prisma.googleDriveProjectFolder.findUnique({
    where: { storageAccountId_projectId: { storageAccountId: accountId, projectId: project.id } },
  }).catch(() => null);
  const isLegacyPrimary = accountId === LEGACY_PRIMARY_STORAGE_ACCOUNT_ID;
  const storedProjectFolderId = mapping?.driveFolderId || (isLegacyPrimary ? project.driveFolderId : null);
  const storedTasksFolderId = mapping?.driveTasksFolderId || (isLegacyPrimary ? project.driveTasksFolderId : null);
  const storedClientFilesFolderId = mapping?.driveClientFilesFolderId || (isLegacyPrimary ? project.driveClientFilesFolderId : null);

  const projectFolderId = await resolveExistingFolderOrNull(drive, storedProjectFolderId, "googleDriveProjectFolder.driveFolderId")
    || await ensureFolder(drive, project.name || "Project", rootId);
  const tasksFolderId = await resolveExistingFolderOrNull(drive, storedTasksFolderId, "googleDriveProjectFolder.driveTasksFolderId")
    || await ensureFolder(drive, "Tasks", projectFolderId);
  const clientFilesFolderId = await resolveExistingFolderOrNull(drive, storedClientFilesFolderId, "googleDriveProjectFolder.driveClientFilesFolderId")
    || await ensureFolder(drive, "Client Files", projectFolderId);

  await prisma.googleDriveProjectFolder.upsert({
    where: { storageAccountId_projectId: { storageAccountId: accountId, projectId: project.id } },
    update: { driveFolderId: projectFolderId, driveTasksFolderId: tasksFolderId, driveClientFilesFolderId: clientFilesFolderId },
    create: {
      storageAccountId: accountId,
      projectId: project.id,
      driveFolderId: projectFolderId,
      driveTasksFolderId: tasksFolderId,
      driveClientFilesFolderId: clientFilesFolderId,
    },
  }).catch((err) => console.warn("GOOGLE_DRIVE_PROJECT_FOLDER_MAPPING_UPDATE_FAILED", { projectId: project.id, storageAccountId: accountId, message: err?.message }));

  if (isLegacyPrimary && (project.driveFolderId !== projectFolderId || project.driveTasksFolderId !== tasksFolderId || project.driveClientFilesFolderId !== clientFilesFolderId)) {
    await prisma.project.update({
      where: { id: project.id },
      data: { driveFolderId: projectFolderId, driveTasksFolderId: tasksFolderId, driveClientFilesFolderId: clientFilesFolderId },
    }).catch((err) => console.warn("GOOGLE_DRIVE_PROJECT_FOLDER_IDS_UPDATE_FAILED", { projectId: project.id, message: err?.message }));
  }

  return { projectFolderId, tasksFolderId, clientFilesFolderId };
}
'''

if old_project in drive:
    drive = replace_once(drive, old_project, new_project, "account-aware project folder mapping")
elif new_project not in drive:
    raise SystemExit("PATCH=FAIL\nREASON=project folder function shape changed")

drive = replace_once(
    drive,
    '''async function resolveFolderForContext(drive, settings, context) {
''',
    '''async function resolveFolderForContext(drive, settings, context, storageAccountId = LEGACY_PRIMARY_STORAGE_ACCOUNT_ID) {
''',
    "folder context storage account parameter",
)

drive = replace_once(
    drive,
    '''    const folders = await ensureProjectDriveFoldersForUpload(drive, settings, project);
''',
    '''    const folders = await ensureProjectDriveFoldersForUpload(drive, settings, project, storageAccountId);
''',
    "folder context account mapping call",
)

drive = replace_once(
    drive,
    '''  const { drive, settings } = await getDriveClient();
  return ensureProjectDriveFoldersForUpload(drive, settings, project);
}
''',
    '''  const { drive, settings } = await getDriveClient();
  return ensureProjectDriveFoldersForUpload(drive, settings, project, LEGACY_PRIMARY_STORAGE_ACCOUNT_ID);
}
''',
    "legacy ensureProjectDriveFolders",
)

old_upload = '''export async function uploadFileToDrive(fileInput, context = {}) {
  const { drive, settings } = await getDriveClient();
  const folderId = await resolveFolderForContext(drive, settings, context);
  // Do not retry a streamed upload automatically: a stream cannot be safely reused after failure.
  let response;
  try {
    response = await drive.files.create({
      requestBody: {
        name: safeDriveName(context.originalname || fileInput?.originalname || "uploaded-file", "uploaded-file"),
        parents: [folderId],
      },
      media: {
        mimeType: context.mimetype || fileInput?.mimetype || "application/octet-stream",
        body: resolveUploadBody(fileInput),
      },
      fields: "id,name,webViewLink",
      supportsAllDrives: true,
    });
  } catch (err) {
    throw await normalizeGoogleDriveRuntimeError(err, { action: "drive_upload_file" });
  }
  return {
    driveFileId: response.data.id,
    hiddenDriveUrl: "hidden-from-team",
    webViewLink: response.data.webViewLink || null,
    provider: "GOOGLE_DRIVE",
  };
}
'''

new_upload = '''export async function uploadFileToDrive(fileInput, context = {}, options = {}) {
  const settingsKey = options.settingsKey || SETTINGS_ID;
  const storageAccountId = options.storageAccountId || (settingsKey === SETTINGS_ID ? LEGACY_PRIMARY_STORAGE_ACCOUNT_ID : null);
  const { drive, settings } = await getDriveClientForSettingsKey(settingsKey);
  const folderId = await resolveFolderForContext(drive, settings, context, storageAccountId || LEGACY_PRIMARY_STORAGE_ACCOUNT_ID);
  // Pool failover is only safe for replayable buffered uploads. This adapter
  // itself still performs one upload attempt and never blindly retries a stream.
  let response;
  try {
    response = await drive.files.create({
      requestBody: {
        name: safeDriveName(context.originalname || fileInput?.originalname || "uploaded-file", "uploaded-file"),
        parents: [folderId],
      },
      media: {
        mimeType: context.mimetype || fileInput?.mimetype || "application/octet-stream",
        body: resolveUploadBody(fileInput),
      },
      fields: "id,name,webViewLink",
      supportsAllDrives: true,
    });
  } catch (err) {
    throw await normalizeGoogleDriveRuntimeError(err, { action: "drive_upload_file", settingsKey });
  }
  return {
    driveFileId: response.data.id,
    storageAccountId,
    hiddenDriveUrl: "hidden-from-team",
    webViewLink: response.data.webViewLink || null,
    provider: "GOOGLE_DRIVE",
  };
}
'''

if old_upload in drive:
    drive = replace_once(drive, old_upload, new_upload, "account-aware upload adapter")
elif new_upload not in drive:
    raise SystemExit("PATCH=FAIL\nREASON=uploadFileToDrive shape changed")

drive = replace_once(
    drive,
    '''export async function deleteGoogleDriveFile(fileId) {
  if (!fileId) return false;
  try {
    const { drive } = await getDriveClient();
    await withRetry(() => drive.files.delete({ fileId, supportsAllDrives: true }), 1, { action: "drive_delete_file" });
''',
    '''export async function deleteGoogleDriveFile(fileId, options = {}) {
  if (!fileId) return false;
  const settingsKey = options.settingsKey || SETTINGS_ID;
  try {
    const { drive } = await getDriveClientForSettingsKey(settingsKey);
    await withRetry(() => drive.files.delete({ fileId, supportsAllDrives: true }), 1, { action: "drive_delete_file", settingsKey });
''',
    "account-aware cleanup delete",
)

if DRIVE.read_text(encoding="utf-8") != drive:
    DRIVE.write_text(drive, encoding="utf-8")
    changed.append(str(DRIVE.relative_to(ROOT)))

pool_js = r'''import { prisma } from "../prisma.js";
import { AppError } from "../middleware/errors.js";
import {
  deleteGoogleDriveFile,
  getGoogleDriveStorageQuota,
  isGoogleDriveQuotaExceededError,
  uploadFileToDrive,
} from "./googleDrive.service.js";

export const LEGACY_PRIMARY_STORAGE_ACCOUNT_ID = "gdrive_legacy_primary";
export const GOOGLE_DRIVE_POOL_RESERVE_RATIO = 0.05;

export function sortGoogleDriveStorageAccounts(accounts = []) {
  return [...accounts].sort((a, b) => {
    const priorityDiff = Number(a?.priority || 0) - Number(b?.priority || 0);
    if (priorityDiff) return priorityDiff;
    if (Boolean(a?.isLegacyPrimary) !== Boolean(b?.isLegacyPrimary)) return a?.isLegacyPrimary ? -1 : 1;
    return String(a?.id || "").localeCompare(String(b?.id || ""));
  });
}

export function googleDriveQuotaCanAcceptUpload(quota = {}, uploadBytes = 0, reserveRatio = GOOGLE_DRIVE_POOL_RESERVE_RATIO) {
  const requested = Math.max(0, Number(uploadBytes) || 0);
  const usage = Math.max(0, Number(quota?.usage) || 0);
  const limit = quota?.limit === null || quota?.limit === undefined ? null : Number(quota.limit);

  // Google can omit limit for effectively-unlimited storage. In that case the
  // account stays eligible and the upload API remains the final authority.
  if (!Number.isFinite(limit) || limit <= 0) {
    return { eligible: true, limit: null, usage, reserveBytes: 0, freeBytes: null };
  }

  const reserveBytes = Math.ceil(limit * Math.max(0, Number(reserveRatio) || 0));
  const freeBytes = Math.max(0, limit - usage);
  return {
    eligible: usage + requested <= limit - reserveBytes,
    limit,
    usage,
    reserveBytes,
    freeBytes,
  };
}

async function loadPoolCandidates() {
  const accounts = sortGoogleDriveStorageAccounts(await prisma.googleDriveStorageAccount.findMany({
    orderBy: [{ priority: "asc" }, { createdAt: "asc" }],
  }));
  if (!accounts.length) throw new AppError("Google Drive storage pool has no configured accounts", 503);

  const settingsRows = await prisma.googleDriveSettings.findMany({
    where: { id: { in: accounts.map((account) => account.settingsKey) } },
    select: { id: true, connected: true, refreshToken: true },
  });
  const settingsById = new Map(settingsRows.map((row) => [row.id, row]));

  return accounts.filter((account) => {
    const settings = settingsById.get(account.settingsKey);
    return Boolean(settings?.connected && settings?.refreshToken);
  });
}

export async function selectGoogleDriveStorageAccountForUpload({
  uploadBytes = 0,
  candidates = null,
  quotaLoader = getGoogleDriveStorageQuota,
} = {}) {
  const accounts = candidates ? sortGoogleDriveStorageAccounts(candidates) : await loadPoolCandidates();
  let lastError = null;

  for (const account of accounts) {
    try {
      const quota = await quotaLoader(account.settingsKey);
      const capacity = googleDriveQuotaCanAcceptUpload(quota, uploadBytes);
      if (capacity.eligible) return { account, quota, capacity };
    } catch (error) {
      lastError = error;
    }
  }

  if (lastError && !accounts.length) throw lastError;
  throw new AppError("No Google Drive storage account has enough writable capacity", 507);
}

export async function uploadFileViaGoogleDrivePool(fileInput, context = {}) {
  if (!Buffer.isBuffer(fileInput?.buffer)) {
    throw new AppError("Google Drive storage pool uploads require a replayable buffered file", 400);
  }

  const candidates = await loadPoolCandidates();
  const uploadBytes = Number(fileInput?.size ?? fileInput.buffer.length ?? 0);
  let lastQuotaError = null;

  for (const account of candidates) {
    let quota;
    try {
      quota = await getGoogleDriveStorageQuota(account.settingsKey);
    } catch (error) {
      // A broken/unreachable account should not prevent trying the next one.
      lastQuotaError = error;
      continue;
    }

    const capacity = googleDriveQuotaCanAcceptUpload(quota, uploadBytes);
    if (!capacity.eligible) continue;

    try {
      return await uploadFileToDrive(fileInput, context, {
        settingsKey: account.settingsKey,
        storageAccountId: account.id,
      });
    } catch (error) {
      if (isGoogleDriveQuotaExceededError(error)) {
        lastQuotaError = error;
        continue;
      }
      throw error;
    }
  }

  if (lastQuotaError && candidates.length === 1) throw lastQuotaError;
  throw new AppError("No Google Drive storage account is available for this upload", 507);
}

export async function cleanupFreshGoogleDrivePoolUpload(uploadResult) {
  if (!uploadResult?.driveFileId) return false;
  const storageAccountId = uploadResult.storageAccountId || LEGACY_PRIMARY_STORAGE_ACCOUNT_ID;
  const account = await prisma.googleDriveStorageAccount.findUnique({ where: { id: storageAccountId } });
  if (!account) return false;
  return deleteGoogleDriveFile(uploadResult.driveFileId, { settingsKey: account.settingsKey });
}
'''

if POOL.exists():
    if POOL.read_text(encoding="utf-8") != pool_js:
        raise SystemExit("PATCH=FAIL\nREASON=Phase2 pool service already exists with different content")
else:
    POOL.write_text(pool_js, encoding="utf-8")
    changed.append(str(POOL.relative_to(ROOT)))

files = FILES.read_text(encoding="utf-8")
files = replace_once(
    files,
    'import { uploadToGoogleDrive, getGoogleDriveDownload, deleteGoogleDriveFile } from "../services/googleDrive.service.js";\n',
    'import { getGoogleDriveDownload, deleteGoogleDriveFile } from "../services/googleDrive.service.js";\nimport { cleanupFreshGoogleDrivePoolUpload, uploadFileViaGoogleDrivePool } from "../services/googleDriveStoragePool.service.js";\n',
    "files route pool imports",
)
files = replace_once(
    files,
    '      drive = await uploadToGoogleDrive({ ...req.file, originalname: displayName }, {\n',
    '      drive = await uploadFileViaGoogleDrivePool({ ...req.file, originalname: displayName }, {\n',
    "files route pool upload",
)
files = replace_once(
    files,
    '''          driveFileId: drive.driveFileId,
          hiddenDriveUrl: drive.hiddenDriveUrl,
''',
    '''          driveFileId: drive.driveFileId,
          storageAccountId: drive.storageAccountId,
          hiddenDriveUrl: drive.hiddenDriveUrl,
''',
    "files route ownership persistence",
)
files = replace_once(
    files,
    '      const deleted = await deleteGoogleDriveFile(drive.driveFileId);\n',
    '      const deleted = await cleanupFreshGoogleDrivePoolUpload(drive);\n',
    "files route exact rollback cleanup",
)
if FILES.read_text(encoding="utf-8") != files:
    FILES.write_text(files, encoding="utf-8")
    changed.append(str(FILES.relative_to(ROOT)))

emp = EMP.read_text(encoding="utf-8")
emp = replace_once(
    emp,
    'import { uploadFileToDrive, deleteGoogleDriveFile, getGoogleDriveDownload } from "../services/googleDrive.service.js";\n',
    'import { deleteGoogleDriveFile, getGoogleDriveDownload } from "../services/googleDrive.service.js";\nimport { cleanupFreshGoogleDrivePoolUpload, uploadFileViaGoogleDrivePool } from "../services/googleDriveStoragePool.service.js";\n',
    "employee work pool imports",
)
emp = emp.replace('drive = await uploadFileToDrive(req.file, {', 'drive = await uploadFileViaGoogleDrivePool(req.file, {')
if emp.count('drive = await uploadFileViaGoogleDrivePool(req.file, {') != 2:
    raise SystemExit("PATCH=FAIL\nREASON=employee work expected 2 pool upload sites")
emp = emp.replace(
    '''        driveFileId: drive.driveFileId,
        hiddenDriveUrl: drive.hiddenDriveUrl,
''',
    '''        driveFileId: drive.driveFileId,
        storageAccountId: drive.storageAccountId,
        hiddenDriveUrl: drive.hiddenDriveUrl,
'''
)
if emp.count('storageAccountId: drive.storageAccountId,') != 2:
    raise SystemExit("PATCH=FAIL\nREASON=employee work expected 2 ownership persistence sites")
emp = emp.replace(
    'if (drive?.driveFileId) await deleteGoogleDriveFile(drive.driveFileId);',
    'if (drive?.driveFileId) await cleanupFreshGoogleDrivePoolUpload(drive);'
)
if emp.count('cleanupFreshGoogleDrivePoolUpload(drive)') != 2:
    raise SystemExit("PATCH=FAIL\nREASON=employee work expected 2 exact rollback cleanup sites")
if EMP.read_text(encoding="utf-8") != emp:
    EMP.write_text(emp, encoding="utf-8")
    changed.append(str(EMP.relative_to(ROOT)))

test_js = r'''import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  GOOGLE_DRIVE_POOL_RESERVE_RATIO,
  googleDriveQuotaCanAcceptUpload,
  selectGoogleDriveStorageAccountForUpload,
  sortGoogleDriveStorageAccounts,
} from "./googleDriveStoragePool.service.js";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../..");
const read = (relative) => readFile(path.join(repoRoot, relative), "utf8");

test("Phase 2 uses Priority Fill ordering", () => {
  const sorted = sortGoogleDriveStorageAccounts([
    { id: "b", priority: 2, isLegacyPrimary: false },
    { id: "a", priority: 1, isLegacyPrimary: true },
    { id: "c", priority: 3, isLegacyPrimary: false },
  ]);
  assert.deepEqual(sorted.map((row) => row.id), ["a", "b", "c"]);
});

test("Phase 2 keeps a 5 percent reserve", () => {
  assert.equal(GOOGLE_DRIVE_POOL_RESERVE_RATIO, 0.05);
  const limit = 1000;
  assert.equal(googleDriveQuotaCanAcceptUpload({ limit, usage: 900 }, 49).eligible, true);
  assert.equal(googleDriveQuotaCanAcceptUpload({ limit, usage: 900 }, 51).eligible, false);
});

test("Phase 2 skips a full primary and selects the next Drive", async () => {
  const candidates = [
    { id: "primary", settingsKey: "main", priority: 1, isLegacyPrimary: true },
    { id: "secondary", settingsKey: "drive-2", priority: 2, isLegacyPrimary: false },
  ];
  const quotas = {
    main: { limit: 1000, usage: 960 },
    "drive-2": { limit: 1000, usage: 100 },
  };
  const selected = await selectGoogleDriveStorageAccountForUpload({
    uploadBytes: 20,
    candidates,
    quotaLoader: async (settingsKey) => quotas[settingsKey],
  });
  assert.equal(selected.account.id, "secondary");
});

test("Phase 2 persists storageAccountId on operational File uploads", async () => {
  const filesRoute = await read("backend/src/routes/files.routes.js");
  const employeeRoute = await read("backend/src/routes/employeeWork.routes.js");

  assert.match(filesRoute, /uploadFileViaGoogleDrivePool/);
  assert.match(filesRoute, /storageAccountId:\s*drive\.storageAccountId/);
  assert.match(filesRoute, /cleanupFreshGoogleDrivePoolUpload\(drive\)/);

  assert.match(employeeRoute, /uploadFileViaGoogleDrivePool/);
  assert.match(employeeRoute, /storageAccountId:\s*drive\.storageAccountId/);
  assert.match(employeeRoute, /cleanupFreshGoogleDrivePoolUpload\(drive\)/);
});

test("Phase 2 keeps TGWS and System Backup pinned to legacy getDriveClient", async () => {
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
        raise SystemExit("PATCH=FAIL\nREASON=Phase2 test already exists with different content")
else:
    TEST.write_text(test_js, encoding="utf-8")
    changed.append(str(TEST.relative_to(ROOT)))

package = PACKAGE.read_text(encoding="utf-8")
script = '"test:google-drive-storage-pool-phase2": "node --test src/services/googleDriveStoragePoolPhase2.test.js"'
if script not in package:
    package = replace_once(
        package,
        '    "test:google-drive-storage-pool-phase1": "node --test src/services/googleDriveStoragePoolPhase1.test.js"\n',
        '    "test:google-drive-storage-pool-phase1": "node --test src/services/googleDriveStoragePoolPhase1.test.js",\n'
        '    "test:google-drive-storage-pool-phase2": "node --test src/services/googleDriveStoragePoolPhase2.test.js"\n',
        "Phase2 package script",
    )
if PACKAGE.read_text(encoding="utf-8") != package:
    PACKAGE.write_text(package, encoding="utf-8")
    changed.append(str(PACKAGE.relative_to(ROOT)))

print("PATCH=PASS")
print(f"FILES_CHANGED={len(changed)}")
for item in changed:
    print(item)
