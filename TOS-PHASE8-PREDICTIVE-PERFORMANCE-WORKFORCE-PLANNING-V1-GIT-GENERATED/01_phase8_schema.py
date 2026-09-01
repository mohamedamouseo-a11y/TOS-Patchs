#!/usr/bin/env python3
from pathlib import Path
import sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
schema_path = repo / "backend/prisma/schema.prisma"
schema = schema_path.read_text()
anchor = "model PerformanceReview {"
if schema.count(anchor) != 1:
    raise SystemExit(f"SCHEMA_ANCHOR=FAIL count={schema.count(anchor)}")
if "model WorkforceCapacityPlan {" in schema:
    raise SystemExit("WORKFORCE_CAPACITY_MODEL_ALREADY_PRESENT=FAIL")

model = '''model WorkforceCapacityPlan {
  id                  String   @id @default(cuid())
  employeeId          String
  weeklyCapacityHours Float
  effectiveFrom       DateTime
  effectiveTo         DateTime?
  note                String?
  isActive            Boolean  @default(true)
  createdById         String?
  updatedById         String?
  createdAt           DateTime @default(now())
  updatedAt           DateTime @updatedAt

  @@index([employeeId, effectiveFrom, effectiveTo])
  @@index([isActive, effectiveFrom, effectiveTo])
  @@index([createdById])
  @@index([updatedById])
}

'''
schema_path.write_text(schema.replace(anchor, model + anchor, 1))

migration = repo / "backend/prisma/migrations/202609020120_phase8_workforce_capacity_plans/migration.sql"
if migration.exists():
    raise SystemExit("WORKFORCE_CAPACITY_MIGRATION_ALREADY_PRESENT=FAIL")
migration.parent.mkdir(parents=True, exist_ok=True)
migration.write_text('''CREATE TABLE "WorkforceCapacityPlan" (
    "id" TEXT NOT NULL,
    "employeeId" TEXT NOT NULL,
    "weeklyCapacityHours" DOUBLE PRECISION NOT NULL,
    "effectiveFrom" TIMESTAMP(3) NOT NULL,
    "effectiveTo" TIMESTAMP(3),
    "note" TEXT,
    "isActive" BOOLEAN NOT NULL DEFAULT true,
    "createdById" TEXT,
    "updatedById" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    CONSTRAINT "WorkforceCapacityPlan_pkey" PRIMARY KEY ("id")
);

CREATE INDEX "WorkforceCapacityPlan_employeeId_effectiveFrom_effectiveTo_idx" ON "WorkforceCapacityPlan"("employeeId", "effectiveFrom", "effectiveTo");
CREATE INDEX "WorkforceCapacityPlan_isActive_effectiveFrom_effectiveTo_idx" ON "WorkforceCapacityPlan"("isActive", "effectiveFrom", "effectiveTo");
CREATE INDEX "WorkforceCapacityPlan_createdById_idx" ON "WorkforceCapacityPlan"("createdById");
CREATE INDEX "WorkforceCapacityPlan_updatedById_idx" ON "WorkforceCapacityPlan"("updatedById");
''')

print("PRISMA_WORKFORCE_CAPACITY_MODEL=PASS")
print("PRISMA_WORKFORCE_CAPACITY_MIGRATION=PASS")
