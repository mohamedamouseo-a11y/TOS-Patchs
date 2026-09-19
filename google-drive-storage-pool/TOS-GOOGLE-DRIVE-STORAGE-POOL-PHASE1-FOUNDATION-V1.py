#!/usr/bin/env python3
from pathlib import Path

ROOT = Path.cwd()
SCHEMA = ROOT / "backend/prisma/schema.prisma"
PACKAGE = ROOT / "backend/package.json"
MIGRATION = ROOT / "backend/prisma/migrations/20260919133000_google_drive_storage_pool_phase1_foundation/migration.sql"
TEST = ROOT / "backend/src/services/googleDriveStoragePoolPhase1.test.js"

if not SCHEMA.exists() or not PACKAGE.exists():
    raise SystemExit("PATCH=FAIL\nREASON=Run from TOS repository root")

def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"PATCH=FAIL\nREASON={label} expected once, found {count}")
    return text.replace(old, new, 1)

schema = SCHEMA.read_text(encoding="utf-8")
package = PACKAGE.read_text(encoding="utf-8")
changed = []

account_model = """model GoogleDriveStorageAccount {
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

if "model GoogleDriveStorageAccount {" not in schema:
    marker = """model GoogleDriveSettings {
  id           String   @id
  connected    Boolean  @default(false)
  rootFolderId String?
  clientId     String?
  clientSecret String?
  redirectUri  String?
  scope        String?
  refreshToken String?
  createdAt    DateTime @default(now())
  updatedAt    DateTime @updatedAt
}

"""
    schema = replace_once(schema, marker, marker + account_model, "GoogleDriveSettings model")

if 'storageAccountId    String?   @default("gdrive_legacy_primary")' not in schema:
    schema = replace_once(
        schema,
        """  driveFileId         String?
  hiddenDriveUrl      String?
""",
        """  driveFileId         String?
  storageAccountId    String?   @default("gdrive_legacy_primary")
  hiddenDriveUrl      String?
""",
        "File driveFileId field",
    )
    schema = replace_once(
        schema,
        """  @@index([deletedAt])
  @@index([driveDeleteFailedAt])
}
""",
        """  @@index([deletedAt])
  @@index([driveDeleteFailedAt])
  @@index([storageAccountId])
}
""",
        "File indexes",
    )

if 'driveFileId    String?             @unique\n  storageAccountId String?             @default("gdrive_legacy_primary")' not in schema:
    schema = replace_once(
        schema,
        """  driveFileId    String?             @unique
  driveProvider  String?
""",
        """  driveFileId    String?             @unique
  storageAccountId String?             @default("gdrive_legacy_primary")
  driveProvider  String?
""",
        "WorkspaceDocument driveFileId field",
    )
    schema = replace_once(
        schema,
        """  @@index([storageMode])
  @@index([driveProvider])
  @@index([deletedAt])
""",
        """  @@index([storageMode])
  @@index([driveProvider])
  @@index([storageAccountId])
  @@index([deletedAt])
""",
        "WorkspaceDocument indexes",
    )

if 'driveFileId   String?\n  storageAccountId String?   @default("gdrive_legacy_primary")' not in schema:
    schema = replace_once(
        schema,
        """  driveFileId   String?
  driveProvider String?
""",
        """  driveFileId   String?
  storageAccountId String?   @default("gdrive_legacy_primary")
  driveProvider String?
""",
        "WorkspaceVersion driveFileId field",
    )
    schema = replace_once(
        schema,
        """  @@index([documentId])
  @@index([driveFileId])
  @@index([createdById])
}
""",
        """  @@index([documentId])
  @@index([driveFileId])
  @@index([storageAccountId])
  @@index([createdById])
}
""",
        "WorkspaceVersion indexes",
    )

if SCHEMA.read_text(encoding="utf-8") != schema:
    SCHEMA.write_text(schema, encoding="utf-8")
    changed.append(str(SCHEMA.relative_to(ROOT)))

test_script_line = '"test:google-drive-storage-pool-phase1": "node --test src/services/googleDriveStoragePoolPhase1.test.js"'
if test_script_line not in package:
    package = replace_once(
        package,
        '    "test:ramzy": "node --test src/agency-operator/tests/*.test.js"\n',
        '    "test:ramzy": "node --test src/agency-operator/tests/*.test.js",\n'
        '    "test:google-drive-storage-pool-phase1": "node --test src/services/googleDriveStoragePoolPhase1.test.js"\n',
        "backend package test script",
    )
if PACKAGE.read_text(encoding="utf-8") != package:
    PACKAGE.write_text(package, encoding="utf-8")
    changed.append(str(PACKAGE.relative_to(ROOT)))

migration_sql = """-- TOS Google Drive Storage Pool - Phase 1 foundation
-- Foundation only: no runtime pool selection, no OAuth behavior change.

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

ALTER TABLE "File" ADD COLUMN "storageAccountId" TEXT;
ALTER TABLE "WorkspaceDocument" ADD COLUMN "storageAccountId" TEXT;
ALTER TABLE "WorkspaceVersion" ADD COLUMN "storageAccountId" TEXT;

UPDATE "File"
SET "storageAccountId" = 'gdrive_legacy_primary'
WHERE "driveFileId" IS NOT NULL AND "storageAccountId" IS NULL;

UPDATE "WorkspaceDocument"
SET "storageAccountId" = 'gdrive_legacy_primary'
WHERE "driveFileId" IS NOT NULL AND "storageAccountId" IS NULL;

UPDATE "WorkspaceVersion"
SET "storageAccountId" = 'gdrive_legacy_primary'
WHERE "driveFileId" IS NOT NULL AND "storageAccountId" IS NULL;

ALTER TABLE "File"
  ALTER COLUMN "storageAccountId" SET DEFAULT 'gdrive_legacy_primary';

ALTER TABLE "WorkspaceDocument"
  ALTER COLUMN "storageAccountId" SET DEFAULT 'gdrive_legacy_primary';

ALTER TABLE "WorkspaceVersion"
  ALTER COLUMN "storageAccountId" SET DEFAULT 'gdrive_legacy_primary';

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

MIGRATION.parent.mkdir(parents=True, exist_ok=True)
if MIGRATION.exists():
    existing = MIGRATION.read_text(encoding="utf-8")
    if existing != migration_sql:
        raise SystemExit("PATCH=FAIL\nREASON=Phase1 migration already exists with different content")
else:
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

test("Phase 1 adds a legacy-primary storage account without changing the existing settings key", async () => {
  const schema = await read("backend/prisma/schema.prisma");
  const account = modelBlock(schema, "GoogleDriveStorageAccount");
  const settings = modelBlock(schema, "GoogleDriveSettings");

  assert.match(account, /settingsKey\s+String\s+@unique/);
  assert.match(account, /priority\s+Int\s+@default\(1\)/);
  assert.match(account, /isLegacyPrimary\s+Boolean\s+@default\(false\)/);
  assert.match(settings, /id\s+String\s+@id/);
});

test("Phase 1 records Drive ownership for File, TWS document, and TWS version rows", async () => {
  const schema = await read("backend/prisma/schema.prisma");
  for (const name of ["File", "WorkspaceDocument", "WorkspaceVersion"]) {
    const block = modelBlock(schema, name);
    assert.match(block, /storageAccountId\s+String\?\s+@default\("gdrive_legacy_primary"\)/);
    assert.match(block, /@@index\(\[storageAccountId\]\)/);
  }
});

test("Phase 1 migration backfills only existing Drive-backed rows and protects the legacy primary", async () => {
  const migration = await read("backend/prisma/migrations/20260919133000_google_drive_storage_pool_phase1_foundation/migration.sql");

  assert.match(migration, /CREATE TABLE "GoogleDriveStorageAccount"/);
  assert.match(migration, /'gdrive_legacy_primary', 'Primary Google Drive', 'main', 1, true/);
  assert.match(migration, /GoogleDriveStorageAccount_single_legacy_primary/);

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

TEST.parent.mkdir(parents=True, exist_ok=True)
if TEST.exists():
    existing = TEST.read_text(encoding="utf-8")
    if existing != test_js:
        raise SystemExit("PATCH=FAIL\nREASON=Phase1 test already exists with different content")
else:
    TEST.write_text(test_js, encoding="utf-8")
    changed.append(str(TEST.relative_to(ROOT)))

print("PATCH=PASS")
print(f"FILES_CHANGED={len(changed)}")
for item in changed:
    print(item)
