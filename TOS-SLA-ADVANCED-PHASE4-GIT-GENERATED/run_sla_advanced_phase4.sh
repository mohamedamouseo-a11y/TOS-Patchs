#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-/var/www/TOS}"
OUTPUT="${2:-/var/tmp/TOS_SLA_ADVANCED_PHASE4.patch}"
GENERATOR_COMMIT="003a0154ee6b3d19bbcbe21a0324d29eb0dbf984"
GENERATOR_URL="https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/${GENERATOR_COMMIT}/TOS-SLA-ADVANCED-PHASE4-GIT-GENERATED/generate_sla_advanced_phase4.py"
TMP_GENERATOR="$(mktemp /var/tmp/tos-sla-advanced-phase4-generator.XXXXXX.py)"
trap 'rm -f "$TMP_GENERATOR"' EXIT

curl -fsSL "$GENERATOR_URL" -o "$TMP_GENERATOR"

python3 - "$TMP_GENERATOR" "$REPO" "$OUTPUT" <<'PY'
import importlib.util
import sys
from pathlib import Path

generator_path = Path(sys.argv[1]).resolve()
repo = sys.argv[2]
output = sys.argv[3]

spec = importlib.util.spec_from_file_location("tos_phase4_generator", generator_path)
if spec is None or spec.loader is None:
    raise SystemExit("ERROR: unable to load pinned Phase 4 generator")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

# Egypt/Cairo operational default: Sunday-Thursday (ISO weekdays 7,1,2,3,4).
old_days = "1,2,3,4,5"
new_days = "1,2,3,4,7"

advanced = mod.NEW_FILES["server/slaAdvanced.ts"]
if advanced.count(old_days) != 1:
    raise SystemExit(f"ERROR: expected one slaAdvanced default workweek, found {advanced.count(old_days)}")
mod.NEW_FILES["server/slaAdvanced.ts"] = advanced.replace(old_days, new_days, 1)

ui = mod.NEW_FILES["client/src/pages/SlaAdvancedPage.tsx"]
old_ui_days = "businessDays: [1, 2, 3, 4, 5],"
new_ui_days = "businessDays: [1, 2, 3, 4, 7],"
if ui.count(old_ui_days) != 1:
    raise SystemExit(f"ERROR: expected one Advanced SLA UI workweek default, found {ui.count(old_ui_days)}")
mod.NEW_FILES["client/src/pages/SlaAdvancedPage.tsx"] = ui.replace(old_ui_days, new_ui_days, 1)

migration = mod.NEW_FILES["drizzle/migrations/sla_advanced_001.sql"]
old_sql_days = "DEFAULT '1,2,3,4,5'"
new_sql_days = "DEFAULT '1,2,3,4,7'"
if migration.count(old_sql_days) != 1:
    raise SystemExit(f"ERROR: expected one migration workweek default, found {migration.count(old_sql_days)}")
mod.NEW_FILES["drizzle/migrations/sla_advanced_001.sql"] = migration.replace(old_sql_days, new_sql_days, 1)

schema_replacements = []
schema_hits = 0
for old, new in mod.SCHEMA_REPLACEMENTS:
    hits = new.count('.default("1,2,3,4,5")')
    schema_hits += hits
    new = new.replace('.default("1,2,3,4,5")', '.default("1,2,3,4,7")')
    schema_replacements.append((old, new))
if schema_hits != 1:
    raise SystemExit(f"ERROR: expected one schema workweek default, found {schema_hits}")
mod.SCHEMA_REPLACEMENTS = schema_replacements

advanced_test = mod.NEW_FILES["server/slaAdvanced.test.ts"]
if advanced_test.count(old_days) != 1:
    raise SystemExit(f"ERROR: expected one SLA Advanced test workweek fixture, found {advanced_test.count(old_days)}")
advanced_test = advanced_test.replace(old_days, new_days, 1)
old_open = 'new Date("2026-08-24T07:00:00Z")'
new_open = 'new Date("2026-08-23T07:00:00Z")'
old_closed = 'new Date("2026-08-23T09:00:00Z")'
new_closed = 'new Date("2026-08-28T07:00:00Z")'
if advanced_test.count(old_open) != 1 or advanced_test.count(old_closed) != 1:
    raise SystemExit("ERROR: expected SLA Advanced business-window test anchors")
advanced_test = advanced_test.replace(old_open, new_open, 1).replace(old_closed, new_closed, 1)
mod.NEW_FILES["server/slaAdvanced.test.ts"] = advanced_test

# Harden the generated migration executor: load .env and execute one SQL statement at a time.
mod.NEW_FILES["scripts/apply-sla-advanced-v1-migration.ts"] = '''import "dotenv/config";
import fs from "node:fs";
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

sys.argv = [str(generator_path), repo, output]
try:
    mod.main()
except Exception as exc:
    print(f"ERROR: {exc}", file=sys.stderr)
    raise SystemExit(1)
PY
