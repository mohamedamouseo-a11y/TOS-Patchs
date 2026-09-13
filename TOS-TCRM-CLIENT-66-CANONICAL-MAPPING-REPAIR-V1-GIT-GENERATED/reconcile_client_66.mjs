#!/usr/bin/env node
import process from "node:process";
import { pathToFileURL } from "node:url";

const PATCH = "TOS-TCRM-CLIENT-66-CANONICAL-MAPPING-REPAIR-V1-GIT-GENERATED";
const TOS_ROOT = process.env.TOS_REPO || "/var/www/TOS";
const BACKEND_DIR = `${TOS_ROOT}/backend`;
const PRISMA_MODULE = `${BACKEND_DIR}/src/prisma.js`;

const CRM_CLIENT_ID = "66";
const EXPECTED_NAME = "Modern House Furniture";
const CANONICAL_PROJECT_ID = "cmqgbwzwp0003iml9dtnuaafk";
const STALE_PROJECT_ID = "cmsusfbox007gmxl9y1lubgwe";

function fail(reason, extra = {}) {
  console.log(`PATCH=${PATCH}`);
  console.log("STATUS=ABORT");
  console.log(`REASON=${reason}`);
  for (const [key, value] of Object.entries(extra)) console.log(`${key}=${value}`);
  process.exitCode = 2;
}

process.chdir(BACKEND_DIR);
const { basePrisma: prisma } = await import(pathToFileURL(PRISMA_MODULE).href);

try {
  const projects = await prisma.project.findMany({
    where: { id: { in: [CANONICAL_PROJECT_ID, STALE_PROJECT_ID] } },
    select: { id: true, name: true, archivedAt: true },
  });
  const byId = new Map(projects.map((p) => [p.id, p]));
  const canonical = byId.get(CANONICAL_PROJECT_ID);
  const stale = byId.get(STALE_PROJECT_ID);

  if (!canonical || !stale) {
    fail("EXPECTED_PROJECT_NOT_FOUND", {
      CANONICAL_EXISTS: canonical ? "YES" : "NO",
      STALE_EXISTS: stale ? "YES" : "NO",
    });
  } else if (String(canonical.name || "").trim() !== EXPECTED_NAME || String(stale.name || "").trim() !== EXPECTED_NAME) {
    fail("PROJECT_NAME_MISMATCH", {
      CANONICAL_NAME_MATCH: String(canonical.name || "").trim() === EXPECTED_NAME ? "YES" : "NO",
      STALE_NAME_MATCH: String(stale.name || "").trim() === EXPECTED_NAME ? "YES" : "NO",
    });
  } else if (canonical.archivedAt) {
    fail("CANONICAL_PROJECT_ARCHIVED");
  } else {
    const beforeClient = await prisma.$queryRawUnsafe(
      `SELECT project_id, crm_client_id, crm_project_id, source_key FROM tos_crm_project_deliveries WHERE crm_client_id = $1 ORDER BY updated_at DESC`,
      CRM_CLIENT_ID,
    );
    const beforeCanonical = await prisma.$queryRawUnsafe(
      `SELECT project_id, crm_client_id FROM tos_crm_project_deliveries WHERE project_id = $1`,
      CANONICAL_PROJECT_ID,
    );

    if (beforeClient.length !== 1) {
      fail("CRM_CLIENT_MAPPING_COUNT_MISMATCH", { BEFORE_CLIENT_MAPPING_COUNT: beforeClient.length });
    } else if (String(beforeClient[0].project_id) !== STALE_PROJECT_ID) {
      fail("CRM_CLIENT_NOT_MAPPED_TO_EXPECTED_STALE_PROJECT", { CURRENT_PROJECT_ID: beforeClient[0].project_id });
    } else if (beforeCanonical.length !== 0) {
      fail("CANONICAL_PROJECT_ALREADY_HAS_MAPPING", { CANONICAL_MAPPING_COUNT: beforeCanonical.length });
    } else {
      const result = await prisma.$transaction(async (tx) => {
        const locked = await tx.$queryRawUnsafe(
          `SELECT project_id, crm_client_id FROM tos_crm_project_deliveries WHERE crm_client_id = $1 FOR UPDATE`,
          CRM_CLIENT_ID,
        );
        if (locked.length !== 1 || String(locked[0].project_id) !== STALE_PROJECT_ID) {
          throw new Error("MAPPING_CHANGED_DURING_REPAIR");
        }

        const targetRows = await tx.$queryRawUnsafe(
          `SELECT project_id, crm_client_id FROM tos_crm_project_deliveries WHERE project_id = $1 FOR UPDATE`,
          CANONICAL_PROJECT_ID,
        );
        if (targetRows.length !== 0) throw new Error("CANONICAL_MAPPING_APPEARED_DURING_REPAIR");

        const updated = await tx.$executeRawUnsafe(
          `UPDATE tos_crm_project_deliveries SET project_id = $1, updated_at = NOW() WHERE crm_client_id = $2 AND project_id = $3`,
          CANONICAL_PROJECT_ID,
          CRM_CLIENT_ID,
          STALE_PROJECT_ID,
        );
        if (updated !== 1) throw new Error(`UNEXPECTED_UPDATE_COUNT:${updated}`);

        const afterClient = await tx.$queryRawUnsafe(
          `SELECT project_id, crm_client_id, crm_project_id, source_key FROM tos_crm_project_deliveries WHERE crm_client_id = $1`,
          CRM_CLIENT_ID,
        );
        const afterStale = await tx.$queryRawUnsafe(
          `SELECT project_id, crm_client_id FROM tos_crm_project_deliveries WHERE project_id = $1`,
          STALE_PROJECT_ID,
        );
        if (afterClient.length !== 1 || String(afterClient[0].project_id) !== CANONICAL_PROJECT_ID) {
          throw new Error("POSTCHECK_CLIENT_MAPPING_FAILED");
        }
        if (afterStale.length !== 0) throw new Error("POSTCHECK_STALE_PROJECT_STILL_MAPPED");
        return { updated, afterClient };
      });

      console.log(`PATCH=${PATCH}`);
      console.log("STATUS=APPLIED");
      console.log(`CRM_CLIENT_ID=${CRM_CLIENT_ID}`);
      console.log(`CANONICAL_PROJECT_ID=${CANONICAL_PROJECT_ID}`);
      console.log(`STALE_PROJECT_ID=${STALE_PROJECT_ID}`);
      console.log(`ROWS_UPDATED=${result.updated}`);
      console.log("CLIENT_MAPPING_COUNT_AFTER=1");
      console.log(`CLIENT_MAPPED_PROJECT_ID_AFTER=${result.afterClient[0].project_id}`);
      console.log("STALE_PROJECT_MAPPING_COUNT_AFTER=0");
      console.log("PROJECT_ROWS_CHANGED=NO");
      console.log("STALE_PROJECT_ARCHIVED=NO");
      console.log("SOURCE_CODE_CHANGED=NO");
      console.log("STATUS_FINAL=PASS");
    }
  }
} catch (error) {
  if (!process.exitCode) {
    console.log(`PATCH=${PATCH}`);
    console.log("STATUS=ABORT");
    console.log(`REASON=${String(error?.message || error)}`);
    process.exitCode = 3;
  }
} finally {
  await prisma.$disconnect().catch(() => {});
}
