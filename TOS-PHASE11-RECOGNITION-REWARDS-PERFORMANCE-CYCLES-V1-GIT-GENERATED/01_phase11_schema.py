#!/usr/bin/env python3
from pathlib import Path
import sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
schema = repo / "backend/prisma/schema.prisma"
text = schema.read_text()
marker = "model PerformanceReview {"
if "model RecognitionPerformanceCycle {" in text:
    raise SystemExit("Phase 11 schema already present")
if "model SuccessionCandidate {" not in text:
    raise SystemExit("Phase 10 baseline missing")

models = r'''model RecognitionPerformanceCycle {
  id              String   @id @default(cuid())
  name            String
  cycleType       String   @default("MONTHLY")
  department      String?
  startDate       DateTime
  endDate         DateTime
  nominationStart DateTime?
  nominationEnd   DateTime?
  status          String   @default("DRAFT")
  notes           String?
  isActive        Boolean  @default(true)
  openedAt        DateTime?
  closedAt        DateTime?
  createdById     String?
  updatedById     String?
  createdAt       DateTime @default(now())
  updatedAt       DateTime @updatedAt

  nominations RecognitionNomination[]
  awards      RecognitionAward[]

  @@index([status, isActive])
  @@index([cycleType, startDate, endDate])
  @@index([department, isActive])
  @@index([nominationStart, nominationEnd])
  @@index([createdById])
  @@index([updatedById])
}

model RecognitionCategory {
  id                       String   @id @default(cuid())
  name                     String
  categoryType             String   @default("RECOGNITION")
  description              String?
  rewardType               String   @default("NONE")
  defaultRewardDescription String?
  isActive                 Boolean  @default(true)
  createdById              String?
  updatedById              String?
  createdAt                DateTime @default(now())
  updatedAt                DateTime @updatedAt

  nominations RecognitionNomination[]
  awards      RecognitionAward[]

  @@index([categoryType, isActive])
  @@index([name])
  @@index([createdById])
  @@index([updatedById])
}

model RecognitionNomination {
  id                        String   @id @default(cuid())
  cycleId                   String
  categoryId                String
  nomineeEmployeeId         String
  nominatedById             String
  reason                    String
  status                    String   @default("PENDING")
  decisionNote              String?
  reviewedById              String?
  reviewedAt                DateTime?
  snapshotPerformanceScore  Float?
  snapshotPerformanceStatus String?
  snapshotTargetAchievement Float?
  createdAt                 DateTime @default(now())
  updatedAt                 DateTime @updatedAt

  cycle    RecognitionPerformanceCycle @relation(fields: [cycleId], references: [id], onDelete: Cascade)
  category RecognitionCategory         @relation(fields: [categoryId], references: [id], onDelete: Restrict)
  award    RecognitionAward?

  @@unique([cycleId, categoryId, nomineeEmployeeId])
  @@index([nomineeEmployeeId, status])
  @@index([nominatedById])
  @@index([reviewedById])
  @@index([cycleId, status])
}

model RecognitionAward {
  id                String   @id @default(cuid())
  cycleId           String
  categoryId        String
  employeeId        String
  nominationId      String?  @unique
  title             String
  message           String?
  rewardType        String   @default("NONE")
  rewardDescription String?
  issuedById        String
  issuedAt          DateTime @default(now())
  isPublished       Boolean  @default(false)
  publishedAt       DateTime?
  createdAt         DateTime @default(now())
  updatedAt         DateTime @updatedAt

  cycle      RecognitionPerformanceCycle @relation(fields: [cycleId], references: [id], onDelete: Cascade)
  category   RecognitionCategory         @relation(fields: [categoryId], references: [id], onDelete: Restrict)
  nomination RecognitionNomination?      @relation(fields: [nominationId], references: [id], onDelete: SetNull)

  @@index([employeeId, issuedAt])
  @@index([cycleId, isPublished])
  @@index([categoryId, issuedAt])
  @@index([issuedById])
  @@index([isPublished, publishedAt])
}

'''
if marker not in text:
    raise SystemExit("schema anchor missing")
schema.write_text(text.replace(marker, models + marker, 1))

migration_dir = repo / "backend/prisma/migrations/202609021430_phase11_recognition_rewards_performance_cycles"
migration_dir.mkdir(parents=True, exist_ok=True)
migration = migration_dir / "migration.sql"
migration.write_text(r'''CREATE TABLE "RecognitionPerformanceCycle" (
    "id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "cycleType" TEXT NOT NULL DEFAULT 'MONTHLY',
    "department" TEXT,
    "startDate" TIMESTAMP(3) NOT NULL,
    "endDate" TIMESTAMP(3) NOT NULL,
    "nominationStart" TIMESTAMP(3),
    "nominationEnd" TIMESTAMP(3),
    "status" TEXT NOT NULL DEFAULT 'DRAFT',
    "notes" TEXT,
    "isActive" BOOLEAN NOT NULL DEFAULT true,
    "openedAt" TIMESTAMP(3),
    "closedAt" TIMESTAMP(3),
    "createdById" TEXT,
    "updatedById" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    CONSTRAINT "RecognitionPerformanceCycle_pkey" PRIMARY KEY ("id")
);

CREATE TABLE "RecognitionCategory" (
    "id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "categoryType" TEXT NOT NULL DEFAULT 'RECOGNITION',
    "description" TEXT,
    "rewardType" TEXT NOT NULL DEFAULT 'NONE',
    "defaultRewardDescription" TEXT,
    "isActive" BOOLEAN NOT NULL DEFAULT true,
    "createdById" TEXT,
    "updatedById" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    CONSTRAINT "RecognitionCategory_pkey" PRIMARY KEY ("id")
);

CREATE TABLE "RecognitionNomination" (
    "id" TEXT NOT NULL,
    "cycleId" TEXT NOT NULL,
    "categoryId" TEXT NOT NULL,
    "nomineeEmployeeId" TEXT NOT NULL,
    "nominatedById" TEXT NOT NULL,
    "reason" TEXT NOT NULL,
    "status" TEXT NOT NULL DEFAULT 'PENDING',
    "decisionNote" TEXT,
    "reviewedById" TEXT,
    "reviewedAt" TIMESTAMP(3),
    "snapshotPerformanceScore" DOUBLE PRECISION,
    "snapshotPerformanceStatus" TEXT,
    "snapshotTargetAchievement" DOUBLE PRECISION,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    CONSTRAINT "RecognitionNomination_pkey" PRIMARY KEY ("id")
);

CREATE TABLE "RecognitionAward" (
    "id" TEXT NOT NULL,
    "cycleId" TEXT NOT NULL,
    "categoryId" TEXT NOT NULL,
    "employeeId" TEXT NOT NULL,
    "nominationId" TEXT,
    "title" TEXT NOT NULL,
    "message" TEXT,
    "rewardType" TEXT NOT NULL DEFAULT 'NONE',
    "rewardDescription" TEXT,
    "issuedById" TEXT NOT NULL,
    "issuedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "isPublished" BOOLEAN NOT NULL DEFAULT false,
    "publishedAt" TIMESTAMP(3),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    CONSTRAINT "RecognitionAward_pkey" PRIMARY KEY ("id")
);

CREATE INDEX "RecognitionPerformanceCycle_status_isActive_idx" ON "RecognitionPerformanceCycle"("status", "isActive");
CREATE INDEX "RecognitionPerformanceCycle_cycleType_startDate_endDate_idx" ON "RecognitionPerformanceCycle"("cycleType", "startDate", "endDate");
CREATE INDEX "RecognitionPerformanceCycle_department_isActive_idx" ON "RecognitionPerformanceCycle"("department", "isActive");
CREATE INDEX "RecognitionPerformanceCycle_nominationStart_nominationEnd_idx" ON "RecognitionPerformanceCycle"("nominationStart", "nominationEnd");
CREATE INDEX "RecognitionPerformanceCycle_createdById_idx" ON "RecognitionPerformanceCycle"("createdById");
CREATE INDEX "RecognitionPerformanceCycle_updatedById_idx" ON "RecognitionPerformanceCycle"("updatedById");
CREATE INDEX "RecognitionCategory_categoryType_isActive_idx" ON "RecognitionCategory"("categoryType", "isActive");
CREATE INDEX "RecognitionCategory_name_idx" ON "RecognitionCategory"("name");
CREATE INDEX "RecognitionCategory_createdById_idx" ON "RecognitionCategory"("createdById");
CREATE INDEX "RecognitionCategory_updatedById_idx" ON "RecognitionCategory"("updatedById");
CREATE UNIQUE INDEX "RecognitionNomination_cycleId_categoryId_nomineeEmployeeId_key" ON "RecognitionNomination"("cycleId", "categoryId", "nomineeEmployeeId");
CREATE INDEX "RecognitionNomination_nomineeEmployeeId_status_idx" ON "RecognitionNomination"("nomineeEmployeeId", "status");
CREATE INDEX "RecognitionNomination_nominatedById_idx" ON "RecognitionNomination"("nominatedById");
CREATE INDEX "RecognitionNomination_reviewedById_idx" ON "RecognitionNomination"("reviewedById");
CREATE INDEX "RecognitionNomination_cycleId_status_idx" ON "RecognitionNomination"("cycleId", "status");
CREATE UNIQUE INDEX "RecognitionAward_nominationId_key" ON "RecognitionAward"("nominationId");
CREATE INDEX "RecognitionAward_employeeId_issuedAt_idx" ON "RecognitionAward"("employeeId", "issuedAt");
CREATE INDEX "RecognitionAward_cycleId_isPublished_idx" ON "RecognitionAward"("cycleId", "isPublished");
CREATE INDEX "RecognitionAward_categoryId_issuedAt_idx" ON "RecognitionAward"("categoryId", "issuedAt");
CREATE INDEX "RecognitionAward_issuedById_idx" ON "RecognitionAward"("issuedById");
CREATE INDEX "RecognitionAward_isPublished_publishedAt_idx" ON "RecognitionAward"("isPublished", "publishedAt");

ALTER TABLE "RecognitionNomination" ADD CONSTRAINT "RecognitionNomination_cycleId_fkey" FOREIGN KEY ("cycleId") REFERENCES "RecognitionPerformanceCycle"("id") ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE "RecognitionNomination" ADD CONSTRAINT "RecognitionNomination_categoryId_fkey" FOREIGN KEY ("categoryId") REFERENCES "RecognitionCategory"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
ALTER TABLE "RecognitionAward" ADD CONSTRAINT "RecognitionAward_cycleId_fkey" FOREIGN KEY ("cycleId") REFERENCES "RecognitionPerformanceCycle"("id") ON DELETE CASCADE ON UPDATE CASCADE;
ALTER TABLE "RecognitionAward" ADD CONSTRAINT "RecognitionAward_categoryId_fkey" FOREIGN KEY ("categoryId") REFERENCES "RecognitionCategory"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
ALTER TABLE "RecognitionAward" ADD CONSTRAINT "RecognitionAward_nominationId_fkey" FOREIGN KEY ("nominationId") REFERENCES "RecognitionNomination"("id") ON DELETE SET NULL ON UPDATE CASCADE;
''')

print("PRISMA_RECOGNITION_MODELS=PASS")
print("PRISMA_RECOGNITION_MIGRATION=PASS")
