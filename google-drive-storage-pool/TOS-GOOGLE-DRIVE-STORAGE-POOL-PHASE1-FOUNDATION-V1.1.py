#!/usr/bin/env python3
from pathlib import Path

ROOT = Path.cwd()
SCHEMA = ROOT / "backend/prisma/schema.prisma"
MIGRATION = ROOT / "backend/prisma/migrations/20260919133000_google_drive_storage_pool_phase1_foundation/migration.sql"
TEST = ROOT / "backend/src/services/googleDriveStoragePoolPhase1.test.js"

if not SCHEMA.exists() or not MIGRATION.exists() or not TEST.exists():
    raise SystemExit("PATCH=FAIL\nREASON=Apply Phase1 V1 first and run this from TOS repository root")

def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"PATCH=FAIL\nREASON={label} expected once, found {count}")
    return text.replace(old, new, 1)

schema = SCHEMA.read_text(encoding="utf-8")
changed = []

old_account = """model GoogleDriveStorageAccount {
  id              String   @id @default(cuid())
  name            String
  settingsKey     String   @unique
  priority        Int      @default(1)
  isLegacyPrimary Boolean  @default(false)
  createdAt       DateTime @default(now())
  updatedAt       DateTime @updatedAt

  @@index([priority])
  @@index([isLegacyPrimary])
}

"""

new_account = """model GoogleDriveStorageAccount {
  id              String   @id @default(cuid())
  name            String
  settingsKey     String   @unique
  priority        Int      @default(1)
  isLegacyPrimary Boolean  @default(false)
  createdAt       DateTime @default(now())
  updatedAt       DateTime @updatedAt

  projectFolders GoogleDriveProjectFolder[]

  @@index([priority])
  @@index([isLegacyPrimary])
}

model GoogleDriveProjectFolder {
  storageAccountId        String
  projectId               String
  driveFolderId           String?
  driveTasksFolderId      String?
  driveClientFilesFolderId String?
  createdAt               DateTime @default(now())
  updatedAt               DateTime @updatedAt

  storageAccount GoogleDriveStorageAccount @relation(fields: [storageAccountId], references: [id], onDelete: Restrict)
  project        Project                   @relation(fields: [projectId], references: [id], onDelete: Cascade)

  @@id([storageAccountId, projectId])
  @@index([projectId])
}

"""

if "model GoogleDriveProjectFolder {" not in schema:
    schema = replace_once(schema, old_account, new_account, "GoogleDriveStorageAccount model")

if "driveFolderMappings GoogleDriveProjectFolder[]" not in schema:
    schema = replace_once(
        schema,
        """  workspaceDocuments WorkspaceDocument[]
  workspaceFolders   WorkspaceFolder[]

  tgwsDocuments TgwsDocument[]
""",
        """  workspaceDocuments WorkspaceDocument[]
  workspaceFolders   WorkspaceFolder[]
  driveFolderMappings GoogleDriveProjectFolder[]

  tgwsDocuments TgwsDocument[]
""",
        "Project relation list",
    )

schema = schema.replace(
    'storageAccountId    String?   @default("gdrive_legacy_primary")',
    'storageAccountId    String?'
)
schema = schema.replace(
    'storageAccountId String?             @default("gdrive_legacy_primary")',
    'storageAccountId String?'
)
schema = schema.replace(
    'storageAccountId String?   @default("gdrive_legacy_primary")',
    'storageAccountId String?'
)

if '@default("gdrive_legacy_primary")' in schema:
    raise SystemExit("PATCH=FAIL\nREASON=Unexpected legacy-primary default remains in schema")

if SCHEMA.read_text(encoding="utf-8") != schema:
    SCHEMA.write_text(schema, encoding="utf-8")
    changed.append(str(SCHEMA.relative_to(ROOT)))

migration_sql = """-- TOS Google Drive Storage Pool - Phase 1 foundation
-- Foundation only: no runtime pool selection, no OAuth behavior change.
-- Legacy null ownership remains valid and resolves to Drive #1 until exact-account runtime is enabled.

CREATE TABLE "GoogleDriveStorageAccount" (
  "id" TEXT NOT NULL,
  "name" TEXT NOT NULL,
  "settingsKey" TEXT NOT NULL,
  "priority" INTEGER NOT NULL DEFAULT 1,
  "isLegacyPrimary" BOOLEAN NOT NULL DEFAULT false,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL,
  CONSTRAINT "GoogleDriveStorageAccount_pkey" PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX "GoogleDriveStorageAccount_settingsKey_key"
  ON "GoogleDriveStorageAccount"("settingsKey");

CREATE INDEX "GoogleDriveStorageAccount_priority_idx"
  ON "GoogleDriveStorageAccount"("priority");

CREATE INDEX "GoogleDriveStorageAccount_isLegacyPrimary_idx"
  ON "GoogleDriveStorageAccount"("isLegacyPrimary");

CREATE UNIQUE INDEX "GoogleDriveStorageAccount_single_legacy_primary"
  ON "GoogleDriveStorageAccount"("isLegacyPrimary")
  WHERE "isLegacyPrimary" = true;

INSERT INTO "GoogleDriveStorageAccount"
  ("id", "name", "settingsKey", "priority", "isLegacyPrimary", "createdAt", "updatedAt")
VALUES
  ('gdrive_legacy_primary', 'Primary Google Drive', 'main', 1, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

-- Project folder IDs are Drive-account-specific. Preserve the legacy Project
-- columns for compatibility and seed an account-aware mapping for Phase 2.
CREATE TABLE "GoogleDriveProjectFolder" (
  "storageAccountId" TEXT NOT NULL,
  "projectId" TEXT NOT NULL,
  "driveFolderId" TEXT,
  "driveTasksFolderId" TEXT,
  "driveClientFilesFolderId" TEXT,
  "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT "GoogleDriveProjectFolder_pkey" PRIMARY KEY ("storageAccountId", "projectId")
);

CREATE INDEX "GoogleDriveProjectFolder_projectId_idx"
  ON "GoogleDriveProjectFolder"("projectId");

ALTER TABLE "GoogleDriveProjectFolder"
  ADD CONSTRAINT "GoogleDriveProjectFolder_storageAccountId_fkey"
  FOREIGN KEY ("storageAccountId") REFERENCES "GoogleDriveStorageAccount"("id")
  ON DELETE RESTRICT ON UPDATE CASCADE;

ALTER TABLE "GoogleDriveProjectFolder"
  ADD CONSTRAINT "GoogleDriveProjectFolder_projectId_fkey"
  FOREIGN KEY ("projectId") REFERENCES "Project"("id")
  ON DELETE CASCADE ON UPDATE CASCADE;

INSERT INTO "GoogleDriveProjectFolder"
  ("storageAccountId", "projectId", "driveFolderId", "driveTasksFolderId", "driveClientFilesFolderId", "createdAt", "updatedAt")
SELECT
  'gdrive_legacy_primary',
  "id",
  "driveFolderId",
  "driveTasksFolderId",
  "driveClientFilesFolderId",
  CURRENT_TIMESTAMP,
  CURRENT_TIMESTAMP
FROM "Project"
WHERE "driveFolderId" IS NOT NULL
   OR "driveTasksFolderId" IS NOT NULL
   OR "driveClientFilesFolderId" IS NOT NULL;

ALTER TABLE "File" ADD COLUMN "storageAccountId" TEXT;
ALTER TABLE "WorkspaceDocument" ADD COLUMN "storageAccountId" TEXT;
ALTER TABLE "WorkspaceVersion" ADD COLUMN "storageAccountId" TEXT;

-- Existing Drive-backed records belong to the current single Drive.
UPDATE "File"
SET "storageAccountId" = 'gdrive_legacy_primary'
WHERE "driveFileId" IS NOT NULL AND "storageAccountId" IS NULL;

UPDATE "WorkspaceDocument"
SET "storageAccountId" = 'gdrive_legacy_primary'
WHERE "driveFileId" IS NOT NULL AND "storageAccountId" IS NULL;

UPDATE "WorkspaceVersion"
SET "storageAccountId" = 'gdrive_legacy_primary'
WHERE "driveFileId" IS NOT NULL AND "storageAccountId" IS NULL;

CREATE INDEX "File_storageAccountId_idx" ON "File"("storageAccountId");
CREATE INDEX "WorkspaceDocument_storageAccountId_idx" ON "WorkspaceDocument"("storageAccountId");
CREATE INDEX "WorkspaceVersion_storageAccountId_idx" ON "WorkspaceVersion"("storageAccountId");

ALTER TABLE "File"
  ADD CONSTRAINT "File_storageAccountId_fkey"
  FOREIGN KEY ("storageAccountId") REFERENCES "GoogleDriveStorageAccount"("id")
  ON DELETE RESTRICT ON UPDATE CASCADE;

ALTER TABLE "WorkspaceDocument"
  ADD CONSTRAINT "WorkspaceDocument_storageAccountId_fkey"
  FOREIGN KEY ("storageAccountId") REFERENCES "GoogleDriveStorageAccount"("id")
  ON DELETE RESTRICT ON UPDATE CASCADE;

ALTER TABLE "WorkspaceVersion"
  ADD CONSTRAINT "WorkspaceVersion_storageAccountId_fkey"
  FOREIGN KEY ("storageAccountId") REFERENCES "GoogleDriveStorageAccount"("id")
  ON DELETE RESTRICT ON UPDATE CASCADE;
"""

if MIGRATION.read_text(encoding="utf-8") != migration_sql:
    MIGRATION.write_text(migration_sql, encoding="utf-8")
    changed.append(str(MIGRATION.relative_to(ROOT)))

test_js = r'''import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const repoRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../..");
const read = (relative) => readFile(path.join(repoRoot, relative), "utf8");

function modelBlock(schema, modelName) {
  const start = schema.indexOf("model " + modelName + " {");
  assert.notEqual(start, -1, modelName + " model missing");
  const rest = schema.slice(start);
  const next = rest.indexOf("\nmodel ", 1);
  return next === -1 ? rest : rest.slice(0, next);
}

test("Phase 1 adds the legacy-primary account while preserving current GoogleDriveSettings", async () => {
  const schema = await read("backend/prisma/schema.prisma");
  const account = modelBlock(schema, "GoogleDriveStorageAccount");
  const settings = modelBlock(schema, "GoogleDriveSettings");

  assert.match(account, /settingsKey\s+String\s+@unique/);
  assert.match(account, /priority\s+Int\s+@default\(1\)/);
  assert.match(account, /isLegacyPrimary\s+Boolean\s+@default\(false\)/);
  assert.match(settings, /id\s+String\s+@id/);
});

test("Phase 1 records optional exact-account ownership without mislabeling non-Drive rows", async () => {
  const schema = await read("backend/prisma/schema.prisma");
  for (const name of ["File", "WorkspaceDocument", "WorkspaceVersion"]) {
    const block = modelBlock(schema, name);
    assert.match(block, /storageAccountId\s+String\?/);
    assert.doesNotMatch(block, /storageAccountId[^\n]*@default/);
    assert.match(block, /@@index\(\[storageAccountId\]\)/);
  }
});

test("Phase 1 adds account-aware project folder mapping and preserves legacy Project folder columns", async () => {
  const schema = await read("backend/prisma/schema.prisma");
  const mapping = modelBlock(schema, "GoogleDriveProjectFolder");
  const project = modelBlock(schema, "Project");

  assert.match(mapping, /@@id\(\[storageAccountId, projectId\]\)/);
  assert.match(mapping, /driveFolderId\s+String\?/);
  assert.match(mapping, /driveTasksFolderId\s+String\?/);
  assert.match(mapping, /driveClientFilesFolderId\s+String\?/);
  assert.match(project, /driveFolderId\s+String\?/);
  assert.match(project, /driveFolderMappings\s+GoogleDriveProjectFolder\[\]/);
});

test("Phase 1 migration backfills only legacy Drive ownership and legacy project folder mappings", async () => {
  const migration = await read("backend/prisma/migrations/20260919133000_google_drive_storage_pool_phase1_foundation/migration.sql");

  assert.match(migration, /CREATE TABLE "GoogleDriveStorageAccount"/);
  assert.match(migration, /'gdrive_legacy_primary', 'Primary Google Drive', 'main', 1, true/);
  assert.match(migration, /GoogleDriveStorageAccount_single_legacy_primary/);
  assert.match(migration, /CREATE TABLE "GoogleDriveProjectFolder"/);
  assert.match(migration, /FROM "Project"[\s\S]*?"driveFolderId" IS NOT NULL/);
  assert.doesNotMatch(migration, /ALTER COLUMN "storageAccountId" SET DEFAULT/);

  for (const table of ["File", "WorkspaceDocument", "WorkspaceVersion"]) {
    assert.match(migration, new RegExp('UPDATE "' + table + '"[\\s\\S]*?"driveFileId" IS NOT NULL[\\s\\S]*?"storageAccountId" IS NULL'));
    assert.match(migration, new RegExp('"' + table + '_storageAccountId_fkey"'));
  }
});

test("Phase 1 leaves Google Drive runtime on the existing single-drive adapter", async () => {
  const driveService = await read("backend/src/services/googleDrive.service.js");
  assert.match(driveService, /const SETTINGS_ID = "main";/);
  assert.match(driveService, /export async function getDriveClient\(\)/);
  assert.doesNotMatch(driveService, /googleDriveStoragePool/i);
});
'''

if TEST.read_text(encoding="utf-8") != test_js:
    TEST.write_text(test_js, encoding="utf-8")
    changed.append(str(TEST.relative_to(ROOT)))

print("PATCH=PASS")
print(f"FILES_CHANGED={len(changed)}")
for item in changed:
    print(item)
