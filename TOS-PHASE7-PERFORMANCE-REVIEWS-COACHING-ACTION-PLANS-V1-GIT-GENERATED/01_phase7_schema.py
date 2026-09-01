#!/usr/bin/env python3
from pathlib import Path
import sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
schema_path = repo / "backend/prisma/schema.prisma"
schema = schema_path.read_text()
anchor = "model SlaPolicy {"
if schema.count(anchor) != 1:
    raise SystemExit(f"SCHEMA_ANCHOR=FAIL count={schema.count(anchor)}")
if "model PerformanceReview {" in schema or "model PerformanceActionItem {" in schema:
    raise SystemExit("PHASE7_SCHEMA_ALREADY_PRESENT=FAIL")

models = '''model PerformanceReview {
  id                        String   @id @default(cuid())
  employeeId                String
  reviewerId                String
  periodStart               DateTime
  periodEnd                 DateTime
  status                    String   @default("DRAFT")
  triggerType               String   @default("PERIODIC")
  triggerReference          String?
  title                     String?
  strengths                 String?
  improvementAreas          String?
  managerNotes              String?
  employeeComment           String?
  employeeAcknowledgedAt    DateTime?
  followUpAt                DateTime?
  sharedAt                  DateTime?
  completedAt               DateTime?
  snapshotScore             Float?
  snapshotStatus            String?
  snapshotTargetAchievement Float?
  snapshotTargetStatus      String?
  snapshotCompletedTasks    Int?
  snapshotTotalTasks        Int?
  snapshotOverdueTasks      Int?
  snapshotActualHours       Float?
  createdById               String?
  updatedById               String?
  createdAt                 DateTime @default(now())
  updatedAt                 DateTime @updatedAt

  actions PerformanceActionItem[]

  @@index([employeeId, periodStart, periodEnd])
  @@index([reviewerId, status])
  @@index([status, followUpAt])
  @@index([employeeId, status, updatedAt])
  @@index([createdAt])
}

model PerformanceActionItem {
  id          String   @id @default(cuid())
  reviewId    String
  title       String
  description String?
  dueDate     DateTime?
  status      String   @default("OPEN")
  priority    String   @default("MEDIUM")
  completedAt DateTime?
  createdById String?
  updatedById String?
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt

  review PerformanceReview @relation(fields: [reviewId], references: [id], onDelete: Cascade)

  @@index([reviewId, status])
  @@index([dueDate, status])
  @@index([createdById])
}

'''
schema_path.write_text(schema.replace(anchor, models + anchor, 1))

migration = repo / "backend/prisma/migrations/202609020030_phase7_performance_reviews/migration.sql"
if migration.exists():
    raise SystemExit("PHASE7_MIGRATION_ALREADY_EXISTS=FAIL")
migration.parent.mkdir(parents=True, exist_ok=True)
migration.write_text('''CREATE TABLE "PerformanceReview" (
    "id" TEXT NOT NULL,
    "employeeId" TEXT NOT NULL,
    "reviewerId" TEXT NOT NULL,
    "periodStart" TIMESTAMP(3) NOT NULL,
    "periodEnd" TIMESTAMP(3) NOT NULL,
    "status" TEXT NOT NULL DEFAULT 'DRAFT',
    "triggerType" TEXT NOT NULL DEFAULT 'PERIODIC',
    "triggerReference" TEXT,
    "title" TEXT,
    "strengths" TEXT,
    "improvementAreas" TEXT,
    "managerNotes" TEXT,
    "employeeComment" TEXT,
    "employeeAcknowledgedAt" TIMESTAMP(3),
    "followUpAt" TIMESTAMP(3),
    "sharedAt" TIMESTAMP(3),
    "completedAt" TIMESTAMP(3),
    "snapshotScore" DOUBLE PRECISION,
    "snapshotStatus" TEXT,
    "snapshotTargetAchievement" DOUBLE PRECISION,
    "snapshotTargetStatus" TEXT,
    "snapshotCompletedTasks" INTEGER,
    "snapshotTotalTasks" INTEGER,
    "snapshotOverdueTasks" INTEGER,
    "snapshotActualHours" DOUBLE PRECISION,
    "createdById" TEXT,
    "updatedById" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    CONSTRAINT "PerformanceReview_pkey" PRIMARY KEY ("id")
);

CREATE TABLE "PerformanceActionItem" (
    "id" TEXT NOT NULL,
    "reviewId" TEXT NOT NULL,
    "title" TEXT NOT NULL,
    "description" TEXT,
    "dueDate" TIMESTAMP(3),
    "status" TEXT NOT NULL DEFAULT 'OPEN',
    "priority" TEXT NOT NULL DEFAULT 'MEDIUM',
    "completedAt" TIMESTAMP(3),
    "createdById" TEXT,
    "updatedById" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    CONSTRAINT "PerformanceActionItem_pkey" PRIMARY KEY ("id")
);

CREATE INDEX "PerformanceReview_employeeId_periodStart_periodEnd_idx" ON "PerformanceReview"("employeeId", "periodStart", "periodEnd");
CREATE INDEX "PerformanceReview_reviewerId_status_idx" ON "PerformanceReview"("reviewerId", "status");
CREATE INDEX "PerformanceReview_status_followUpAt_idx" ON "PerformanceReview"("status", "followUpAt");
CREATE INDEX "PerformanceReview_employeeId_status_updatedAt_idx" ON "PerformanceReview"("employeeId", "status", "updatedAt");
CREATE INDEX "PerformanceReview_createdAt_idx" ON "PerformanceReview"("createdAt");
CREATE INDEX "PerformanceActionItem_reviewId_status_idx" ON "PerformanceActionItem"("reviewId", "status");
CREATE INDEX "PerformanceActionItem_dueDate_status_idx" ON "PerformanceActionItem"("dueDate", "status");
CREATE INDEX "PerformanceActionItem_createdById_idx" ON "PerformanceActionItem"("createdById");

ALTER TABLE "PerformanceActionItem"
ADD CONSTRAINT "PerformanceActionItem_reviewId_fkey"
FOREIGN KEY ("reviewId") REFERENCES "PerformanceReview"("id")
ON DELETE CASCADE ON UPDATE CASCADE;
''')

print("PRISMA_REVIEW_MODELS=PASS")
print("PRISMA_REVIEW_MIGRATION_CREATED=PASS")
