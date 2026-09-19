#!/usr/bin/env python3
from pathlib import Path

ROOT = Path.cwd()
POOL = ROOT / "backend/src/services/googleDriveStoragePool.service.js"
PACKAGE = ROOT / "backend/package.json"
TEST = ROOT / "backend/src/services/googleDriveStoragePoolPhase4.test.js"
SMOKE = ROOT / "backend/scripts/google-drive-storage-pool-production-smoke.mjs"

for p in [POOL, PACKAGE]:
    if not p.exists():
        raise SystemExit(f"PATCH=FAIL\nREASON=Missing {p}")

def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"PATCH=FAIL\nREASON={label} expected once, found {count}")
    return text.replace(old, new, 1)

changed = []

# ------------------------------------------------------------------
# Runtime hardening: never mask a total quota-probe outage as capacity.
# Also honor enabled/drainMode for injected candidate lists.
# ------------------------------------------------------------------
pool = POOL.read_text(encoding="utf-8")

old_select = '''export async function selectGoogleDriveStorageAccountForUpload({
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
'''

new_select = '''export async function selectGoogleDriveStorageAccountForUpload({
  uploadBytes = 0,
  candidates = null,
  quotaLoader = getGoogleDriveStorageQuota,
} = {}) {
  const accounts = candidates
    ? sortGoogleDriveStorageAccounts(candidates).filter((account) => account?.enabled !== false && account?.drainMode !== true)
    : await loadPoolCandidates();
  let lastError = null;
  let successfulQuotaChecks = 0;

  for (const account of accounts) {
    try {
      const quota = await quotaLoader(account.settingsKey);
      successfulQuotaChecks += 1;
      const capacity = googleDriveQuotaCanAcceptUpload(quota, uploadBytes);
      if (capacity.eligible) return { account, quota, capacity };
    } catch (error) {
      lastError = error;
    }
  }

  if (lastError && successfulQuotaChecks === 0) throw lastError;
  throw new AppError("No Google Drive storage account has enough writable capacity", 507);
}
'''

if old_select in pool:
    pool = replace_once(pool, old_select, new_select, "Phase4 selection hardening")
elif "successfulQuotaChecks" not in pool:
    raise SystemExit("PATCH=FAIL\nREASON=selectGoogleDriveStorageAccountForUpload changed unexpectedly")

old_file_loop = '''  const candidates = await loadPoolCandidates();
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
'''
new_file_loop = '''  const candidates = await loadPoolCandidates();
  const uploadBytes = Number(fileInput?.size ?? fileInput.buffer.length ?? 0);
  let lastQuotaError = null;
  let successfulQuotaChecks = 0;

  for (const account of candidates) {
    let quota;
    try {
      quota = await getGoogleDriveStorageQuota(account.settingsKey);
      successfulQuotaChecks += 1;
    } catch (error) {
      // A broken/unreachable account should not prevent trying the next one.
      lastQuotaError = error;
      continue;
    }

    const capacity = googleDriveQuotaCanAcceptUpload(quota, uploadBytes);
'''
if old_file_loop in pool:
    pool = replace_once(pool, old_file_loop, new_file_loop, "Phase4 file quota probes")

old_file_tail = '''  if (lastQuotaError && candidates.length === 1) throw lastQuotaError;
  throw new AppError("No Google Drive storage account is available for this upload", 507);
}

export async function cleanupFreshGoogleDrivePoolUpload'''
new_file_tail = '''  if (lastQuotaError && successfulQuotaChecks === 0) throw lastQuotaError;
  throw new AppError("No Google Drive storage account is available for this upload", 507);
}

export async function cleanupFreshGoogleDrivePoolUpload'''
if old_file_tail in pool:
    pool = replace_once(pool, old_file_tail, new_file_tail, "Phase4 file error tail")

old_json_loop = '''  const candidates = await loadPoolCandidates();
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
'''
new_json_loop = '''  const candidates = await loadPoolCandidates();
  const uploadBytes = Buffer.byteLength(JSON.stringify(contentJson ?? {}), "utf8");
  let lastQuotaError = null;
  let successfulQuotaChecks = 0;

  for (const account of candidates) {
    let quota;
    try {
      quota = await getGoogleDriveStorageQuota(account.settingsKey);
      successfulQuotaChecks += 1;
    } catch (error) {
      lastQuotaError = error;
      continue;
    }

    const capacity = googleDriveQuotaCanAcceptUpload(quota, uploadBytes);
'''
if old_json_loop in pool:
    pool = replace_once(pool, old_json_loop, new_json_loop, "Phase4 JSON quota probes")

old_json_tail = '''  if (lastQuotaError && candidates.length === 1) throw lastQuotaError;
  throw new AppError("No Google Drive storage account is available for this TWS upload", 507);
}
'''
new_json_tail = '''  if (lastQuotaError && successfulQuotaChecks === 0) throw lastQuotaError;
  throw new AppError("No Google Drive storage account is available for this TWS upload", 507);
}
'''
if old_json_tail in pool:
    pool = replace_once(pool, old_json_tail, new_json_tail, "Phase4 JSON error tail")

if POOL.read_text(encoding="utf-8") != pool:
    POOL.write_text(pool, encoding="utf-8")
    changed.append(str(POOL.relative_to(ROOT)))

# ------------------------------------------------------------------
# Phase 4 tests
# ------------------------------------------------------------------
test_js = r'''import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  googleDriveQuotaCanAcceptUpload,
  selectGoogleDriveStorageAccountForUpload,
} from "./googleDriveStoragePool.service.js";
import {
  googleDriveStorageDeletePolicy,
} from "./googleDriveStoragePoolManagement.service.js";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../..");
const read = (relative) => readFile(path.join(repoRoot, relative), "utf8");

test("Phase 4 injected selection excludes disabled and draining accounts", async () => {
  const candidates = [
    { id: "disabled", settingsKey: "disabled", priority: 1, enabled: false, drainMode: false },
    { id: "draining", settingsKey: "draining", priority: 2, enabled: true, drainMode: true },
    { id: "active", settingsKey: "active", priority: 3, enabled: true, drainMode: false },
  ];
  const selected = await selectGoogleDriveStorageAccountForUpload({
    uploadBytes: 1,
    candidates,
    quotaLoader: async () => ({ limit: 1000, usage: 0 }),
  });
  assert.equal(selected.account.id, "active");
});

test("Phase 4 does not mask total quota probe outage as capacity exhaustion", async () => {
  const expected = new Error("quota backend unavailable");
  await assert.rejects(
    selectGoogleDriveStorageAccountForUpload({
      uploadBytes: 1,
      candidates: [
        { id: "a", settingsKey: "a", priority: 1 },
        { id: "b", settingsKey: "b", priority: 2 },
      ],
      quotaLoader: async () => { throw expected; },
    }),
    (error) => error === expected,
  );
});

test("Phase 4 still returns capacity error when probes work but reserve blocks writes", async () => {
  await assert.rejects(
    selectGoogleDriveStorageAccountForUpload({
      uploadBytes: 100,
      candidates: [
        { id: "a", settingsKey: "a", priority: 1 },
        { id: "b", settingsKey: "b", priority: 2 },
      ],
      quotaLoader: async () => ({ limit: 1000, usage: 900 }),
    }),
    (error) => Number(error?.status || error?.statusCode) === 507 || /capacity/i.test(String(error?.message || "")),
  );
  assert.equal(googleDriveQuotaCanAcceptUpload({ limit: 1000, usage: 900 }, 50).eligible, true);
  assert.equal(googleDriveQuotaCanAcceptUpload({ limit: 1000, usage: 900 }, 51).eligible, false);
});

test("Phase 4 safe delete protects primary and referenced accounts", () => {
  assert.deepEqual(googleDriveStorageDeletePolicy({ isLegacyPrimary: true, referenceCount: 0 }), { allowed: false, reason: "LEGACY_PRIMARY" });
  assert.deepEqual(googleDriveStorageDeletePolicy({ isLegacyPrimary: false, referenceCount: 1 }), { allowed: false, reason: "REFERENCED" });
  assert.deepEqual(googleDriveStorageDeletePolicy({ isLegacyPrimary: false, referenceCount: 0 }), { allowed: true, reason: null });
});

test("Phase 4 exact-account lifecycle remains wired for files and TWS", async () => {
  const files = await read("backend/src/routes/files.routes.js");
  const workspace = await read("backend/src/services/workspace.service.js");

  assert.match(files, /getGoogleDriveDownload\(file\.driveFileId, \{ storageAccountId: file\.storageAccountId \}\)/);
  assert.match(files, /deleteGoogleDriveFile\(file\.driveFileId, \{ storageAccountId: file\.storageAccountId \}\)/);
  assert.match(workspace, /readJsonFromDrive\(document\.driveFileId, document\.storageAccountId\)/);
  assert.match(workspace, /readJsonFromDrive\(version\.driveFileId, version\.storageAccountId\)/);
  assert.match(workspace, /storageAccountId:\s*uploaded\.storageAccountId/);
});

test("Phase 4 System Backup and TGWS stay pinned to legacy getDriveClient", async () => {
  const backup = await read("backend/src/services/systemBackup.service.js");
  const tgws = await read("backend/src/services/tgws.service.js");
  assert.match(backup, /getDriveClient/);
  assert.match(tgws, /getDriveClient/);
  assert.doesNotMatch(backup, /googleDriveStoragePool/);
  assert.doesNotMatch(tgws, /googleDriveStoragePool/);
});

test("Phase 4 dedicated database backup remains isolated from operational pool", async () => {
  const dbBackup = await read("backend/src/services/databaseBackup.service.js");
  assert.doesNotMatch(dbBackup, /googleDriveStoragePool/);
  assert.doesNotMatch(dbBackup, /from "\.\/googleDrive\.service\.js"/);
});

test("Phase 4 production smoke is gated and restores drain state in finally", async () => {
  const smoke = await read("backend/scripts/google-drive-storage-pool-production-smoke.mjs");
  assert.match(smoke, /TOS_GDRIVE_SMOKE_ALLOW_WRITE/);
  assert.match(smoke, /SECONDARY_REQUIRED=YES/);
  assert.match(smoke, /finally/);
  assert.match(smoke, /originalStates/);
  assert.match(smoke, /drainMode/);
  assert.match(smoke, /deleteGoogleDriveFile/);
});
'''

if TEST.exists():
    if TEST.read_text(encoding="utf-8") != test_js:
        raise SystemExit("PATCH=FAIL\nREASON=Phase4 test exists with different content")
else:
    TEST.write_text(test_js, encoding="utf-8")
    changed.append(str(TEST.relative_to(ROOT)))

# ------------------------------------------------------------------
# Production smoke: controlled temporary writes only, no user rows.
# ------------------------------------------------------------------
smoke_js = r'''import crypto from "crypto";
import { prisma } from "../src/prisma.js";
import {
  GOOGLE_DRIVE_POOL_RESERVE_RATIO,
  googleDriveQuotaCanAcceptUpload,
  sortGoogleDriveStorageAccounts,
  uploadFileViaGoogleDrivePool,
  uploadJsonViaGoogleDrivePool,
} from "../src/services/googleDriveStoragePool.service.js";
import {
  deleteGoogleDriveFile,
  getGoogleDriveDownload,
  getGoogleDriveStorageQuota,
  readJsonFromDrive,
  updateJsonOnDrive,
} from "../src/services/googleDrive.service.js";

const ALLOW_WRITE = process.env.TOS_GDRIVE_SMOKE_ALLOW_WRITE === "1";
const runId = `phase4-${Date.now()}-${crypto.randomBytes(4).toString("hex")}`;
const temporaryFiles = [];
const originalStates = new Map();

function fail(message) {
  throw new Error(message);
}

async function streamToBuffer(stream) {
  const chunks = [];
  for await (const chunk of stream) chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
  return Buffer.concat(chunks);
}

async function connectedWritableAccounts() {
  const accounts = sortGoogleDriveStorageAccounts(await prisma.googleDriveStorageAccount.findMany({
    where: { enabled: true, drainMode: false },
    orderBy: [{ priority: "asc" }, { createdAt: "asc" }],
  }));
  const settings = await prisma.googleDriveSettings.findMany({
    where: { id: { in: accounts.map((account) => account.settingsKey) } },
    select: { id: true, connected: true, refreshToken: true },
  });
  const byId = new Map(settings.map((row) => [row.id, row]));
  return accounts.filter((account) => {
    const row = byId.get(account.settingsKey);
    return Boolean(row?.connected && row?.refreshToken);
  });
}

async function eligibleAccounts(accounts, bytes) {
  const result = [];
  for (const account of accounts) {
    try {
      const quota = await getGoogleDriveStorageQuota(account.settingsKey);
      if (googleDriveQuotaCanAcceptUpload(quota, bytes, GOOGLE_DRIVE_POOL_RESERVE_RATIO).eligible) {
        result.push(account);
      }
    } catch (error) {
      console.log(`QUOTA_SKIP=${account.id}:${error?.message || error}`);
    }
  }
  return result;
}

async function remember(account) {
  if (originalStates.has(account.id)) return;
  originalStates.set(account.id, {
    enabled: account.enabled,
    drainMode: account.drainMode,
    priority: account.priority,
  });
}

async function setDrain(account, drainMode) {
  await remember(account);
  await prisma.googleDriveStorageAccount.update({
    where: { id: account.id },
    data: { drainMode },
  });
}

async function cleanupTemp(upload) {
  if (!upload?.driveFileId) return;
  const ok = await deleteGoogleDriveFile(upload.driveFileId, { storageAccountId: upload.storageAccountId });
  if (!ok) fail(`Temporary Drive cleanup failed for ${upload.driveFileId}`);
  const index = temporaryFiles.findIndex((item) => item.driveFileId === upload.driveFileId);
  if (index >= 0) temporaryFiles.splice(index, 1);
}

async function main() {
  if (!ALLOW_WRITE) {
    console.log("SMOKE=BLOCKED");
    console.log("WRITE_CONFIRMATION_REQUIRED=YES");
    console.log("Set TOS_GDRIVE_SMOKE_ALLOW_WRITE=1");
    return;
  }

  const candidates = await connectedWritableAccounts();
  const payload = Buffer.from(`TOS Google Drive Phase 4 production smoke ${runId}`, "utf8");
  const eligible = await eligibleAccounts(candidates, payload.length);

  if (eligible.length < 2) {
    console.log("SMOKE=BLOCKED");
    console.log("SECONDARY_REQUIRED=YES");
    console.log(`CONNECTED_WRITABLE_ELIGIBLE=${eligible.length}`);
    return;
  }

  const first = eligible[0];
  const second = eligible[1];
  console.log(`PRIMARY_CANDIDATE=${first.id}`);
  console.log(`FAILOVER_CANDIDATE=${second.id}`);

  // 1) Priority Fill + exact-account file read/delete.
  const normalUpload = await uploadFileViaGoogleDrivePool({
    buffer: payload,
    size: payload.length,
    originalname: `${runId}-priority.txt`,
    mimetype: "text/plain",
  }, {
    originalname: `${runId}-priority.txt`,
    mimetype: "text/plain",
  });
  temporaryFiles.push(normalUpload);
  if (normalUpload.storageAccountId !== first.id) {
    fail(`Priority Fill expected ${first.id} but used ${normalUpload.storageAccountId}`);
  }

  const normalDownload = await getGoogleDriveDownload(normalUpload.driveFileId, {
    storageAccountId: normalUpload.storageAccountId,
  });
  const downloaded = await streamToBuffer(normalDownload.stream);
  if (!downloaded.equals(payload)) fail("Exact-account file download content mismatch");
  await cleanupTemp(normalUpload);
  console.log("PRIORITY_FILL=PASS");
  console.log("EXACT_FILE_READ_DELETE=PASS");

  // 2) Drain first candidate and prove failover to second.
  await setDrain(first, true);
  const failoverUpload = await uploadFileViaGoogleDrivePool({
    buffer: payload,
    size: payload.length,
    originalname: `${runId}-failover.txt`,
    mimetype: "text/plain",
  }, {
    originalname: `${runId}-failover.txt`,
    mimetype: "text/plain",
  });
  temporaryFiles.push(failoverUpload);
  if (failoverUpload.storageAccountId !== second.id) {
    fail(`Drain failover expected ${second.id} but used ${failoverUpload.storageAccountId}`);
  }
  await cleanupTemp(failoverUpload);
  console.log("DRAIN_FAILOVER=PASS");

  // 3) TWS-style JSON write/read/update/delete on failover Drive.
  const initialJson = { smoke: runId, step: 1 };
  const jsonUpload = await uploadJsonViaGoogleDrivePool({
    filename: `${runId}-tws.json`,
    contentJson: initialJson,
    context: { twsDocument: true, twsType: "TDOC" },
    metadata: { phase: "4", smoke: true },
  });
  temporaryFiles.push(jsonUpload);
  if (jsonUpload.storageAccountId !== second.id) {
    fail(`TWS failover expected ${second.id} but used ${jsonUpload.storageAccountId}`);
  }

  const readOne = await readJsonFromDrive(jsonUpload.driveFileId, jsonUpload.storageAccountId);
  if (readOne?.smoke !== runId || readOne?.step !== 1) fail("Exact-account TWS read mismatch");

  await updateJsonOnDrive({
    fileId: jsonUpload.driveFileId,
    storageAccountId: jsonUpload.storageAccountId,
    contentJson: { smoke: runId, step: 2 },
    metadata: { phase: "4", updated: true },
  });
  const readTwo = await readJsonFromDrive(jsonUpload.driveFileId, jsonUpload.storageAccountId);
  if (readTwo?.smoke !== runId || readTwo?.step !== 2) fail("Exact-account TWS update/read mismatch");
  await cleanupTemp(jsonUpload);
  console.log("TWS_EXACT_LIFECYCLE=PASS");

  console.log("SMOKE=PASS");
}

try {
  await main();
} catch (error) {
  console.error("SMOKE=FAIL");
  console.error(`ERROR=${error?.message || error}`);
  process.exitCode = 1;
} finally {
  for (const upload of [...temporaryFiles]) {
    try {
      await deleteGoogleDriveFile(upload.driveFileId, { storageAccountId: upload.storageAccountId });
    } catch {}
  }

  for (const [id, state] of originalStates.entries()) {
    try {
      await prisma.googleDriveStorageAccount.update({
        where: { id },
        data: {
          enabled: state.enabled,
          drainMode: state.drainMode,
          priority: state.priority,
        },
      });
    } catch (error) {
      console.error(`RESTORE_STATE_FAILED=${id}:${error?.message || error}`);
      process.exitCode = 1;
    }
  }

  await prisma.$disconnect().catch(() => null);
}
'''

if SMOKE.exists():
    if SMOKE.read_text(encoding="utf-8") != smoke_js:
        raise SystemExit("PATCH=FAIL\nREASON=Production smoke script exists with different content")
else:
    SMOKE.parent.mkdir(parents=True, exist_ok=True)
    SMOKE.write_text(smoke_js, encoding="utf-8")
    changed.append(str(SMOKE.relative_to(ROOT)))

# ------------------------------------------------------------------
# Package scripts
# ------------------------------------------------------------------
package = PACKAGE.read_text(encoding="utf-8")
if '"test:google-drive-storage-pool-phase4"' not in package:
    package = replace_once(
        package,
        '    "test:google-drive-storage-pool-phase3": "node --test src/services/googleDriveStoragePoolPhase3.test.js"\n',
        '    "test:google-drive-storage-pool-phase3": "node --test src/services/googleDriveStoragePoolPhase3.test.js",\n'
        '    "test:google-drive-storage-pool-phase4": "node --test src/services/googleDriveStoragePoolPhase4.test.js",\n'
        '    "smoke:google-drive-storage-pool-production": "node scripts/google-drive-storage-pool-production-smoke.mjs"\n',
        "Phase4 package scripts",
    )

if PACKAGE.read_text(encoding="utf-8") != package:
    PACKAGE.write_text(package, encoding="utf-8")
    changed.append(str(PACKAGE.relative_to(ROOT)))

print("PATCH=PASS")
print(f"FILES_CHANGED={len(changed)}")
for item in changed:
    print(item)
