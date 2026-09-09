import { execFileSync } from "node:child_process";
import { basePrisma as prisma } from "/var/www/TOS/backend/src/prisma.js";

const PATCH = "TOS-PROJECT-DUPLICATE-AUDIT-V2-RISK-SCORING-READ-ONLY";
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
    .replace(/ـ/g, "")
    .replace(/[^\p{L}\p{N}]+/gu, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function normalizeLoose(value = "") {
  return normalizeName(value);
}

function dateMs(value) {
  if (!value) return null;
  const ms = new Date(value).getTime();
  return Number.isFinite(ms) ? ms : null;
}

function dateOnly(value) {
  const ms = dateMs(value);
  return ms === null ? null : new Date(ms).toISOString().slice(0, 10);
}

function absoluteAgeDays(left, right) {
  const a = dateMs(left);
  const b = dateMs(right);
  if (a === null || b === null) return null;
  return Math.abs(a - b) / 86400000;
}

function absoluteAgeMinutes(left, right) {
  const a = dateMs(left);
  const b = dateMs(right);
  if (a === null || b === null) return null;
  return Math.abs(a - b) / 60000;
}

function setFrom(values = []) {
  return new Set(values.map((value) => String(value || "").trim()).filter(Boolean));
}

function intersects(left, right) {
  for (const value of left) if (right.has(value)) return true;
  return false;
}

function allDifferentWhenPresent(left, right) {
  return left.size > 0 && right.size > 0 && !intersects(left, right);
}

function jaccard(left, right) {
  if (!left.size || !right.size) return 0;
  let intersection = 0;
  for (const value of left) if (right.has(value)) intersection += 1;
  const union = new Set([...left, ...right]).size;
  return union ? intersection / union : 0;
}

function projectCounts(project) {
  return {
    tasks: Number(project._count?.tasks || 0),
    files: Number(project._count?.files || 0),
    members: Number(project._count?.members || 0),
    meetings: Number(project._count?.meetings || 0),
    boards: Number(project._count?.boards || 0),
  };
}

function substantiveWorkCount(project) {
  const counts = projectCounts(project);
  return counts.tasks + counts.files + counts.meetings + counts.boards;
}

function crmSets(projectId, crmByProject) {
  const rows = crmByProject.get(projectId) || [];
  return {
    crmProjectIds: setFrom(rows.map((row) => row.crmProjectId)),
    sourceKeys: setFrom(rows.map((row) => row.sourceKey)),
    crmDealIds: setFrom(rows.map((row) => row.crmDealId)),
    crmClientIds: setFrom(rows.map((row) => row.crmClientId)),
  };
}

function compactProject(project, crmByProject) {
  const crmRows = crmByProject.get(project.id) || [];
  return {
    id: project.id,
    name: project.name,
    normalizedName: normalizeName(project.name),
    code: project.code || null,
    type: project.type || null,
    clientId: project.clientId || null,
    clientName: project.client?.name || null,
    status: project.status || null,
    stage: project.stage || null,
    priority: project.priority || null,
    startDate: project.startDate || null,
    dueDate: project.dueDate || null,
    deliveryDate: project.deliveryDate || null,
    archivedAt: project.archivedAt || null,
    createdAt: project.createdAt || null,
    updatedAt: project.updatedAt || null,
    memberUserIds: (project.members || []).map((member) => member.userId).filter(Boolean),
    counts: projectCounts(project),
    substantiveWorkCount: substantiveWorkCount(project),
    tcrm: crmRows.map((row) => ({
      sourceKey: row.sourceKey || null,
      crmProjectId: row.crmProjectId || null,
      crmDealId: row.crmDealId || null,
      crmClientId: row.crmClientId || null,
      updatedAt: row.updatedAt || null,
    })),
  };
}

function scorePair(left, right, crmByProject) {
  let score = 0;
  const reasons = [];
  const counterSignals = [];
  const add = (points, reason) => {
    score += points;
    if (points >= 0) reasons.push(`+${points} ${reason}`);
    else counterSignals.push(`${points} ${reason}`);
  };

  const leftClientName = normalizeLoose(left.client?.name || "");
  const rightClientName = normalizeLoose(right.client?.name || "");
  if (left.clientId && right.clientId && left.clientId === right.clientId) {
    add(35, "same TOS clientId");
  } else if (leftClientName && rightClientName && leftClientName === rightClientName) {
    add(20, "same normalized client name despite different/missing clientId");
  } else if (left.clientId && right.clientId && leftClientName && rightClientName && leftClientName !== rightClientName) {
    add(-35, "different populated clients");
  } else if (!left.clientId || !right.clientId) {
    add(3, "one or both projects have no linked client");
  }

  const lc = crmSets(left.id, crmByProject);
  const rc = crmSets(right.id, crmByProject);
  if (intersects(lc.crmProjectIds, rc.crmProjectIds)) add(100, "same TCRM crmProjectId");
  else if (allDifferentWhenPresent(lc.crmProjectIds, rc.crmProjectIds)) add(-60, "different non-empty TCRM crmProjectId values");

  if (intersects(lc.sourceKeys, rc.sourceKeys)) add(100, "same TCRM sourceKey");
  else if (allDifferentWhenPresent(lc.sourceKeys, rc.sourceKeys)) add(-45, "different non-empty TCRM sourceKey values");

  if (intersects(lc.crmDealIds, rc.crmDealIds)) add(35, "same TCRM crmDealId");
  else if (allDifferentWhenPresent(lc.crmDealIds, rc.crmDealIds)) add(-20, "different non-empty TCRM crmDealId values");

  if (intersects(lc.crmClientIds, rc.crmClientIds)) add(20, "same TCRM crmClientId");
  else if (allDifferentWhenPresent(lc.crmClientIds, rc.crmClientIds)) add(-20, "different non-empty TCRM crmClientId values");

  const ageMinutes = absoluteAgeMinutes(left.createdAt, right.createdAt);
  const ageDays = absoluteAgeDays(left.createdAt, right.createdAt);
  if (ageMinutes !== null && ageMinutes <= 10) add(25, "created within 10 minutes");
  else if (ageDays !== null && ageDays <= 1) add(18, "created within 24 hours");
  else if (ageDays !== null && ageDays <= 7) add(10, "created within 7 days");
  else if (ageDays !== null && ageDays <= 30) add(4, "created within 30 days");
  else if (ageDays !== null && ageDays >= 180) add(-12, "created at least 180 days apart");

  if (left.type && right.type && normalizeLoose(left.type) === normalizeLoose(right.type)) add(5, "same project type");
  if (left.priority && right.priority && left.priority === right.priority) add(2, "same priority");
  if (dateOnly(left.startDate) && dateOnly(left.startDate) === dateOnly(right.startDate)) add(5, "same start date");
  if (dateOnly(left.dueDate) && dateOnly(left.dueDate) === dateOnly(right.dueDate)) add(5, "same due date");
  if (dateOnly(left.deliveryDate) && dateOnly(left.deliveryDate) === dateOnly(right.deliveryDate)) add(3, "same delivery date");

  const leftMembers = setFrom((left.members || []).map((member) => member.userId));
  const rightMembers = setFrom((right.members || []).map((member) => member.userId));
  const memberOverlap = jaccard(leftMembers, rightMembers);
  if (memberOverlap >= 0.75) add(10, "very high team overlap");
  else if (memberOverlap >= 0.5) add(7, "high team overlap");
  else if (memberOverlap >= 0.25) add(3, "some team overlap");

  const leftWork = substantiveWorkCount(left);
  const rightWork = substantiveWorkCount(right);
  if ((leftWork === 0 && rightWork > 0) || (rightWork === 0 && leftWork > 0)) {
    add(10, "one project is an empty shell while the other has work");
  } else if (leftWork > 0 && rightWork > 0 && ageDays !== null && ageDays >= 90) {
    add(-5, "both contain work and were created far apart");
  }

  if (String(left.name || "").trim().toLowerCase() === String(right.name || "").trim().toLowerCase()) {
    add(3, "raw project names also match exactly");
  }

  const bounded = Math.max(0, Math.min(100, score));
  const classification = bounded >= 70
    ? "VERY_LIKELY_DUPLICATE"
    : bounded >= 35
      ? "POSSIBLE_DUPLICATE"
      : "LIKELY_LEGITIMATE";

  return {
    leftProjectId: left.id,
    rightProjectId: right.id,
    score: bounded,
    classification,
    createdAtDifferenceDays: ageDays === null ? null : Number(ageDays.toFixed(3)),
    memberOverlap: Number(memberOverlap.toFixed(3)),
    reasons,
    counterSignals,
  };
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
        type: true,
        clientId: true,
        status: true,
        stage: true,
        priority: true,
        startDate: true,
        dueDate: true,
        deliveryDate: true,
        archivedAt: true,
        createdAt: true,
        updatedAt: true,
        client: { select: { id: true, name: true } },
        members: { select: { userId: true } },
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

  const crmByProject = new Map();
  for (const row of report.crmRows) {
    if (!crmByProject.has(row.projectId)) crmByProject.set(row.projectId, []);
    crmByProject.get(row.projectId).push(row);
  }

  const activeProjects = report.projects.filter((project) => !project.archivedAt);
  const groupsByName = new Map();
  for (const project of activeProjects) {
    const key = normalizeName(project.name);
    if (!key) continue;
    if (!groupsByName.has(key)) groupsByName.set(key, []);
    groupsByName.get(key).push(project);
  }

  const reviewGroups = [...groupsByName.entries()]
    .map(([key, projects]) => ({ key, projects }))
    .filter(({ projects }) => {
      if (projects.length < 2) return false;
      const clients = new Set(projects.map((project) => project.clientId || "NO_CLIENT"));
      return clients.size > 1 || projects.some((project) => !project.clientId);
    })
    .sort((a, b) => a.key.localeCompare(b.key, "ar"));

  const totals = {
    VERY_LIKELY_DUPLICATE: 0,
    POSSIBLE_DUPLICATE: 0,
    LIKELY_LEGITIMATE: 0,
  };
  let pairCount = 0;

  console.log(`TOTAL_PROJECTS=${report.projects.length}`);
  console.log(`ACTIVE_PROJECTS=${activeProjects.length}`);
  console.log(`ARCHIVED_PROJECTS=${report.projects.length - activeProjects.length}`);
  console.log(`TCRM_MAPPING_ROWS=${report.crmRows.length}`);
  console.log(`REVIEW_NAME_ONLY_GROUPS=${reviewGroups.length}`);

  reviewGroups.forEach((group, groupIndex) => {
    const pairResults = [];
    for (let i = 0; i < group.projects.length; i += 1) {
      for (let j = i + 1; j < group.projects.length; j += 1) {
        const result = scorePair(group.projects[i], group.projects[j], crmByProject);
        pairResults.push(result);
        totals[result.classification] += 1;
        pairCount += 1;
      }
    }
    pairResults.sort((a, b) => b.score - a.score || a.leftProjectId.localeCompare(b.leftProjectId));
    const groupClassification = pairResults[0]?.classification || "LIKELY_LEGITIMATE";
    const maxScore = pairResults[0]?.score ?? 0;

    console.log(`\n=== REVIEW_NAME_ONLY_V2 #${groupIndex + 1} ===`);
    console.log(`NORMALIZED_NAME=${group.key}`);
    console.log(`PROJECT_COUNT=${group.projects.length}`);
    console.log(`PAIR_COUNT=${pairResults.length}`);
    console.log(`GROUP_MAX_SCORE=${maxScore}`);
    console.log(`GROUP_CLASSIFICATION=${groupClassification}`);
    console.log("PROJECTS_BEGIN");
    for (const project of group.projects) console.log(JSON.stringify(compactProject(project, crmByProject)));
    console.log("PROJECTS_END");
    console.log("PAIR_SCORES_BEGIN");
    for (const pair of pairResults) console.log(JSON.stringify(pair));
    console.log("PAIR_SCORES_END");
  });

  console.log("\n=== V2_SUMMARY ===");
  console.log(`REVIEW_GROUP_COUNT=${reviewGroups.length}`);
  console.log(`PAIR_COUNT=${pairCount}`);
  console.log(`VERY_LIKELY_DUPLICATE_PAIRS=${totals.VERY_LIKELY_DUPLICATE}`);
  console.log(`POSSIBLE_DUPLICATE_PAIRS=${totals.POSSIBLE_DUPLICATE}`);
  console.log(`LIKELY_LEGITIMATE_PAIRS=${totals.LIKELY_LEGITIMATE}`);
  console.log("AUDIT_COMPLETE=YES");
  console.log("DATABASE_CHANGES=NONE");
  console.log("FILES_CHANGED=NONE");
  console.log("PUSH_PERFORMED=NO");
  console.log("AUTOMATIC_DELETE_ALLOWED=NO");
  console.log("READY_FOR_CLEANUP=NO");
  console.log("MANUAL_REVIEW_REQUIRED=YES");
  console.log("NEXT_STEP=REVIEW_VERY_LIKELY_AND_POSSIBLE_PAIRS_BEFORE_ANY_CLEANUP");
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
