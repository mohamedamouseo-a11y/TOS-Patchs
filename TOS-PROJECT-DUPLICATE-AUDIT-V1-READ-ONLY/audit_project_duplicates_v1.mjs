import { execFileSync } from "node:child_process";
import { basePrisma as prisma } from "/var/www/TOS/backend/src/prisma.js";

const PATCH = "TOS-PROJECT-DUPLICATE-AUDIT-V1-READ-ONLY";
const REPO = "/var/www/TOS";

function safeGitHead() {
  try {
    return execFileSync("git", ["-C", REPO, "rev-parse", "HEAD"], { encoding: "utf8" }).trim();
  } catch {
    return "UNKNOWN";
  }
}

function normalizeName(value = "") {
  return String(value || "")
    .normalize("NFKC")
    .toLowerCase()
    .replace(/[\u064B-\u065F\u0670]/g, "")
    .replace(/[إأآ]/g, "ا")
    .replace(/ة/g, "ه")
    .replace(/ى/g, "ي")
    .replace(/[ـ]/g, "")
    .replace(/[^\p{L}\p{N}]+/gu, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function addGroup(map, key, project) {
  if (!key) return;
  if (!map.has(key)) map.set(key, new Map());
  map.get(key).set(project.id, project);
}

function groupsFromMap(map) {
  return [...map.entries()]
    .map(([key, items]) => ({ key, projects: [...items.values()] }))
    .filter((group) => group.projects.length > 1);
}

function compactProject(project, crmByProject) {
  const crmRows = crmByProject.get(project.id) || [];
  return {
    id: project.id,
    name: project.name,
    normalizedName: normalizeName(project.name),
    code: project.code || null,
    clientId: project.clientId || null,
    clientName: project.client?.name || null,
    status: project.status || null,
    stage: project.stage || null,
    archivedAt: project.archivedAt || null,
    createdAt: project.createdAt || null,
    updatedAt: project.updatedAt || null,
    counts: {
      tasks: Number(project._count?.tasks || 0),
      files: Number(project._count?.files || 0),
      members: Number(project._count?.members || 0),
      meetings: Number(project._count?.meetings || 0),
      boards: Number(project._count?.boards || 0),
    },
    tcrm: crmRows.map((row) => ({
      sourceKey: row.sourceKey || null,
      crmProjectId: row.crmProjectId || null,
      crmDealId: row.crmDealId || null,
      crmClientId: row.crmClientId || null,
      updatedAt: row.updatedAt || null,
    })),
  };
}

function printGroup(kind, index, reason, projects) {
  console.log(`\n=== ${kind} #${index + 1} ===`);
  console.log(`REASON=${reason}`);
  console.log(`PROJECT_COUNT=${projects.length}`);
  for (const project of projects) {
    console.log(JSON.stringify(project));
  }
}

async function main() {
  console.log(`PATCH=${PATCH}`);
  console.log("AUDIT_MODE=READ_ONLY");
  console.log(`TOS_HEAD=${safeGitHead()}`);
  console.log("DELETE_ALLOWED=NO");
  console.log("ARCHIVE_ALLOWED=NO");
  console.log("MERGE_ALLOWED=NO");
  console.log("DATABASE_WRITE_ALLOWED=NO");

  const report = await prisma.$transaction(async (tx) => {
    await tx.$executeRawUnsafe("SET TRANSACTION READ ONLY");

    const projects = await tx.project.findMany({
      select: {
        id: true,
        name: true,
        code: true,
        clientId: true,
        status: true,
        stage: true,
        archivedAt: true,
        createdAt: true,
        updatedAt: true,
        client: { select: { id: true, name: true } },
        _count: {
          select: {
            tasks: true,
            files: true,
            members: true,
            meetings: true,
            boards: true,
          },
        },
      },
      orderBy: [{ createdAt: "asc" }, { id: "asc" }],
    });

    let crmRows = [];
    try {
      crmRows = await tx.$queryRawUnsafe(`
        SELECT
          project_id AS "projectId",
          source_key AS "sourceKey",
          crm_project_id AS "crmProjectId",
          crm_deal_id AS "crmDealId",
          crm_client_id AS "crmClientId",
          updated_at AS "updatedAt"
        FROM tos_crm_project_deliveries
        ORDER BY updated_at ASC
      `);
    } catch (error) {
      console.log(`TCRM_MAPPING_READ=UNAVAILABLE ${String(error?.message || error).replace(/\s+/g, " ").slice(0, 300)}`);
      crmRows = [];
    }

    return { projects, crmRows };
  }, { timeout: 30000 });

  const projectById = new Map(report.projects.map((project) => [project.id, project]));
  const crmByProject = new Map();
  for (const row of report.crmRows) {
    if (!crmByProject.has(row.projectId)) crmByProject.set(row.projectId, []);
    crmByProject.get(row.projectId).push(row);
  }

  const crmProjectMap = new Map();
  const sourceKeyMap = new Map();
  const clientNameMap = new Map();
  const nameOnlyMap = new Map();

  for (const row of report.crmRows) {
    const project = projectById.get(row.projectId);
    if (!project) continue;
    if (row.crmProjectId) addGroup(crmProjectMap, String(row.crmProjectId).trim(), project);
    if (row.sourceKey) addGroup(sourceKeyMap, String(row.sourceKey).trim(), project);
  }

  for (const project of report.projects) {
    if (project.archivedAt) continue;
    const normalizedName = normalizeName(project.name);
    if (!normalizedName) continue;
    addGroup(nameOnlyMap, normalizedName, project);
    if (project.clientId) addGroup(clientNameMap, `${project.clientId}::${normalizedName}`, project);
  }

  const confirmedExternal = groupsFromMap(crmProjectMap);
  const confirmedSource = groupsFromMap(sourceKeyMap).filter((group) => {
    const ids = new Set(group.projects.map((project) => project.id));
    return ids.size > 1;
  });
  const strongClientName = groupsFromMap(clientNameMap);
  const reviewNameOnly = groupsFromMap(nameOnlyMap).filter((group) => {
    const clients = new Set(group.projects.map((project) => project.clientId || "NO_CLIENT"));
    return clients.size > 1 || group.projects.some((project) => !project.clientId);
  });

  const confirmedProjectPairs = new Set();
  for (const group of [...confirmedExternal, ...confirmedSource]) {
    const ids = group.projects.map((project) => project.id).sort();
    for (let i = 0; i < ids.length; i += 1) {
      for (let j = i + 1; j < ids.length; j += 1) confirmedProjectPairs.add(`${ids[i]}::${ids[j]}`);
    }
  }

  console.log(`TOTAL_PROJECTS=${report.projects.length}`);
  console.log(`ACTIVE_PROJECTS=${report.projects.filter((project) => !project.archivedAt).length}`);
  console.log(`ARCHIVED_PROJECTS=${report.projects.filter((project) => project.archivedAt).length}`);
  console.log(`TCRM_MAPPING_ROWS=${report.crmRows.length}`);
  console.log(`CONFIRMED_EXTERNAL_ID_GROUPS=${confirmedExternal.length}`);
  console.log(`CONFIRMED_SOURCE_KEY_GROUPS=${confirmedSource.length}`);
  console.log(`STRONG_SAME_CLIENT_NAME_GROUPS=${strongClientName.length}`);
  console.log(`REVIEW_NAME_ONLY_GROUPS=${reviewNameOnly.length}`);

  confirmedExternal.forEach((group, index) => {
    printGroup(
      "CONFIRMED_EXTERNAL_ID",
      index,
      `Same non-empty TCRM crmProjectId=${group.key} points to multiple TOS Project IDs`,
      group.projects.map((project) => compactProject(project, crmByProject)),
    );
  });

  confirmedSource.forEach((group, index) => {
    printGroup(
      "CONFIRMED_SOURCE_KEY",
      index,
      `Same TCRM sourceKey=${group.key} points to multiple TOS Project IDs`,
      group.projects.map((project) => compactProject(project, crmByProject)),
    );
  });

  strongClientName.forEach((group, index) => {
    printGroup(
      "STRONG_SAME_CLIENT_NAME",
      index,
      `Same active clientId + normalized project name key=${group.key}`,
      group.projects.map((project) => compactProject(project, crmByProject)),
    );
  });

  reviewNameOnly.forEach((group, index) => {
    printGroup(
      "REVIEW_NAME_ONLY",
      index,
      `Same normalized active project name=${group.key}, but client identity is absent or differs`,
      group.projects.map((project) => compactProject(project, crmByProject)),
    );
  });

  console.log("\nAUDIT_COMPLETE=YES");
  console.log("DATABASE_CHANGES=NONE");
  console.log("FILES_CHANGED=NONE");
  console.log("PUSH_PERFORMED=NO");
  console.log(`CONFIRMED_DUPLICATE_PAIR_COUNT=${confirmedProjectPairs.size}`);
  console.log("READY_FOR_AUTOMATIC_CLEANUP=NO");
  console.log("NEXT_STEP=REVIEW_GROUPS_AND_BUILD_EXPLICIT_CLEANUP_PLAN");
}

try {
  await main();
} catch (error) {
  console.error("AUDIT_COMPLETE=NO");
  console.error(`ERROR=${String(error?.stack || error)}`);
  process.exitCode = 1;
} finally {
  await prisma.$disconnect().catch(() => {});
}
