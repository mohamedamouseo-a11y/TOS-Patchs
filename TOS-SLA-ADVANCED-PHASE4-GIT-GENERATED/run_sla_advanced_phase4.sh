#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-/var/www/TOS}"
OUTPUT="${2:-/var/tmp/TOS_SLA_ADVANCED_PHASE4.patch}"
GENERATOR_COMMIT="003a0154ee6b3d19bbcbe21a0324d29eb0dbf984"
GENERATOR_URL="https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/${GENERATOR_COMMIT}/TOS-SLA-ADVANCED-PHASE4-GIT-GENERATED/generate_sla_advanced_phase4.py"
TMP_GENERATOR="$(mktemp /var/tmp/tos-sla-advanced-phase4-generator.XXXXXX.py)"
trap 'rm -f "$TMP_GENERATOR"' EXIT

curl -fsSL "$GENERATOR_URL" -o "$TMP_GENERATOR"

# Harden the generated DB migration runner: execute statements individually
# over the existing DATABASE_URL instead of enabling multipleStatements.
python3 - "$TMP_GENERATOR" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
source = path.read_text()
old = '''import fs from "node:fs";
import path from "node:path";
import mysql from "mysql2/promise";

const databaseUrl = process.env.DATABASE_URL;
if (!databaseUrl) {
  throw new Error("DATABASE_URL is required");
}

const sqlPath = path.resolve(process.cwd(), "drizzle/migrations/sla_advanced_001.sql");
const sql = fs.readFileSync(sqlPath, "utf8");
const connection = await mysql.createConnection({
  uri: databaseUrl,
  multipleStatements: true,
} as any);

try {
  await connection.query(sql);
  const [policyRows] = await connection.query("SHOW TABLES LIKE 'sla_policies'");
  const [historyRows] = await connection.query("SHOW TABLES LIKE 'sla_breach_events'");
  if (!Array.isArray(policyRows) || policyRows.length !== 1) {
    throw new Error("sla_policies table verification failed");
  }
  if (!Array.isArray(historyRows) || historyRows.length !== 1) {
    throw new Error("sla_breach_events table verification failed");
  }
  console.log("SLA_ADVANCED_MIGRATION=PASS");
  console.log("SLA_POLICIES_TABLE=YES");
  console.log("SLA_BREACH_EVENTS_TABLE=YES");
} finally {
  await connection.end();
}
'''
new = '''import fs from "node:fs";
import path from "node:path";
import mysql from "mysql2/promise";

const databaseUrl = process.env.DATABASE_URL;
if (!databaseUrl) {
  throw new Error("DATABASE_URL is required");
}

const sqlPath = path.resolve(process.cwd(), "drizzle/migrations/sla_advanced_001.sql");
const sql = fs.readFileSync(sqlPath, "utf8");
const statements = sql
  .split(/;\\s*(?:\\r?\\n|$)/)
  .map(statement => statement.trim())
  .filter(Boolean);

const connection = await mysql.createConnection(databaseUrl);

try {
  for (const statement of statements) {
    await connection.query(statement);
  }

  const [policyRows] = await connection.query("SHOW TABLES LIKE 'sla_policies'");
  const [historyRows] = await connection.query("SHOW TABLES LIKE 'sla_breach_events'");
  if (!Array.isArray(policyRows) || policyRows.length !== 1) {
    throw new Error("sla_policies table verification failed");
  }
  if (!Array.isArray(historyRows) || historyRows.length !== 1) {
    throw new Error("sla_breach_events table verification failed");
  }
  console.log("SLA_ADVANCED_MIGRATION=PASS");
  console.log("SLA_POLICIES_TABLE=YES");
  console.log("SLA_BREACH_EVENTS_TABLE=YES");
} finally {
  await connection.end();
}
'''
needle = repr(old)
replacement = repr(new)
count = source.count(needle)
if count != 1:
    raise SystemExit(f"ERROR: expected exactly one Phase 4 migration-script payload, found {count}")
path.write_text(source.replace(needle, replacement, 1))
PY

python3 "$TMP_GENERATOR" "$REPO" "$OUTPUT"
