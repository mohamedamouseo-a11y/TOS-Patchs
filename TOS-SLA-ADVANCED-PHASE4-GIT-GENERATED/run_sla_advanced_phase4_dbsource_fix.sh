#!/usr/bin/env bash
set -euo pipefail

REPO="${1:-/var/www/TOS}"
OUTPUT="${2:-/var/tmp/TOS_SLA_ADVANCED_PHASE4_DBSOURCE_FIX.patch}"
TARGET="scripts/apply-sla-advanced-v1-migration.ts"

cd "$REPO"

python3 - "$TARGET" "$OUTPUT" <<'PY'
from pathlib import Path
import difflib
import sys

target = Path(sys.argv[1])
output = Path(sys.argv[2])

if not target.exists():
    raise SystemExit(f"ERROR: missing expected Phase 4 migration runner: {target}")

old = target.read_text()
old_import = 'import "dotenv/config";\nimport fs from "node:fs";\nimport path from "node:path";\nimport mysql from "mysql2/promise";\n\nconst databaseUrl = process.env.DATABASE_URL;\nif (!databaseUrl) {\n  throw new Error("DATABASE_URL is required");\n}\n'
new_import = 'import fs from "node:fs";\nimport path from "node:path";\nimport mysql from "mysql2/promise";\nimport { config as loadEnv } from "dotenv";\n\nif (!process.env.DATABASE_URL) {\n  for (const candidate of [\n    path.resolve(process.cwd(), ".env"),\n    path.resolve(process.cwd(), "backend/.env"),\n  ]) {\n    if (!fs.existsSync(candidate)) continue;\n    loadEnv({ path: candidate, override: false });\n    if (process.env.DATABASE_URL) break;\n  }\n}\n\nconst databaseUrl = process.env.DATABASE_URL;\nif (!databaseUrl) {\n  throw new Error("DATABASE_URL is required; checked shell, .env, and backend/.env");\n}\n'

count = old.count(old_import)
if count != 1:
    raise SystemExit(f"ERROR: expected exactly one Phase 4 migration env block, found {count}")

new = old.replace(old_import, new_import, 1)
patch = ''.join(difflib.unified_diff(
    old.splitlines(True),
    new.splitlines(True),
    fromfile=f'a/{target.as_posix()}',
    tofile=f'b/{target.as_posix()}',
))
if not patch.strip():
    raise SystemExit("ERROR: generated DB source fix patch is empty")

output.write_text(patch)
print(f"PATCH={output}")
PY

git apply --check "$OUTPUT"
sha256sum "$OUTPUT"
