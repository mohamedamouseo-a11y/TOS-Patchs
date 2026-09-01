#!/usr/bin/env python3
from pathlib import Path
import sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
schema_path = repo / "backend/prisma/schema.prisma"
schema = schema_path.read_text()
anchor = "model SlaPolicy {"
if schema.count(anchor) != 1:
    raise SystemExit(f"SCHEMA_ANCHOR=FAIL count={schema.count(anchor)}")
model = '''model PerformanceTarget {
  id                   String   @id @default(cuid())
  scopeType            String
  employeeId           String?
  department           String?
  periodType           String   @default("MONTHLY")
  effectiveFrom        DateTime
  effectiveTo          DateTime
  targetScore          Float?
  targetCompletionRate Float?
  targetCompletedTasks Int?
  targetLoggedHours    Float?
  maxOverdueTasks      Int?
  customTargets        Json?
  isActive             Boolean  @default(true)
  createdById          String?
  updatedById          String?
  createdAt            DateTime @default(now())
  updatedAt            DateTime @updatedAt

  @@index([scopeType, employeeId, effectiveFrom, effectiveTo])
  @@index([scopeType, department, effectiveFrom, effectiveTo])
  @@index([isActive, effectiveFrom, effectiveTo])
  @@index([createdById])
  @@index([updatedById])
}

'''
schema_path.write_text(schema.replace(anchor, model + anchor, 1))

migration = repo / "backend/prisma/migrations/202609011600_phase6_performance_targets/migration.sql"
migration.parent.mkdir(parents=True, exist_ok=True)
migration.write_text('''CREATE TABLE "PerformanceTarget" (
    "id" TEXT NOT NULL,
    "scopeType" TEXT NOT NULL,
    "employeeId" TEXT,
    "department" TEXT,
    "periodType" TEXT NOT NULL DEFAULT 'MONTHLY',
    "effectiveFrom" TIMESTAMP(3) NOT NULL,
    "effectiveTo" TIMESTAMP(3) NOT NULL,
    "targetScore" DOUBLE PRECISION,
    "targetCompletionRate" DOUBLE PRECISION,
    "targetCompletedTasks" INTEGER,
    "targetLoggedHours" DOUBLE PRECISION,
    "maxOverdueTasks" INTEGER,
    "customTargets" JSONB,
    "isActive" BOOLEAN NOT NULL DEFAULT true,
    "createdById" TEXT,
    "updatedById" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    CONSTRAINT "PerformanceTarget_pkey" PRIMARY KEY ("id")
);
CREATE INDEX "PerformanceTarget_scopeType_employeeId_effectiveFrom_effectiveTo_idx" ON "PerformanceTarget"("scopeType", "employeeId", "effectiveFrom", "effectiveTo");
CREATE INDEX "PerformanceTarget_scopeType_department_effectiveFrom_effectiveTo_idx" ON "PerformanceTarget"("scopeType", "department", "effectiveFrom", "effectiveTo");
CREATE INDEX "PerformanceTarget_isActive_effectiveFrom_effectiveTo_idx" ON "PerformanceTarget"("isActive", "effectiveFrom", "effectiveTo");
CREATE INDEX "PerformanceTarget_createdById_idx" ON "PerformanceTarget"("createdById");
CREATE INDEX "PerformanceTarget_updatedById_idx" ON "PerformanceTarget"("updatedById");
''')
print("PRISMA_TARGET_MODEL=PASS")
print("PRISMA_MIGRATION_CREATED=PASS")
