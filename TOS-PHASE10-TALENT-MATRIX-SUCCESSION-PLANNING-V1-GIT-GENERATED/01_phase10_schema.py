#!/usr/bin/env python3
from pathlib import Path
import sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
schema_path = repo / "backend/prisma/schema.prisma"
text = schema_path.read_text()

marker = "model TalentAssessment {"
if marker in text:
    print("PRISMA_TALENT_MODELS=PASS already-present")
    raise SystemExit(0)

anchor = "model PerformanceReview {"
if anchor not in text:
    raise SystemExit("Phase 10 schema anchor not found")

models = r'''model TalentAssessment {
  id             String   @id @default(cuid())
  employeeId     String   @unique
  potentialLevel String
  evidence       String?
  managerNote    String?
  isActive       Boolean  @default(true)
  assessedById   String
  assessedAt     DateTime @default(now())
  updatedById    String?
  createdAt      DateTime @default(now())
  updatedAt      DateTime @updatedAt

  @@index([potentialLevel, isActive])
  @@index([assessedById])
  @@index([assessedAt])
  @@index([updatedById])
}

model SuccessionRole {
  id                  String   @id @default(cuid())
  title               String
  department          String?
  criticality         String   @default("NORMAL")
  incumbentEmployeeId String?
  description         String?
  isActive            Boolean  @default(true)
  createdById         String?
  updatedById         String?
  createdAt           DateTime @default(now())
  updatedAt           DateTime @updatedAt

  candidates SuccessionCandidate[]

  @@index([department, isActive])
  @@index([criticality, isActive])
  @@index([incumbentEmployeeId])
  @@index([title])
  @@index([createdById])
  @@index([updatedById])
}

model SuccessionCandidate {
  id                String   @id @default(cuid())
  roleId            String
  employeeId        String
  readiness         String   @default("DEVELOPING")
  priority          Int      @default(3)
  rationale         String?
  developmentPlanId String?
  isActive          Boolean  @default(true)
  nominatedById     String?
  updatedById       String?
  createdAt         DateTime @default(now())
  updatedAt         DateTime @updatedAt

  role SuccessionRole @relation(fields: [roleId], references: [id], onDelete: Cascade)

  @@unique([roleId, employeeId])
  @@index([employeeId, isActive])
  @@index([roleId, readiness, isActive])
  @@index([developmentPlanId])
  @@index([nominatedById])
  @@index([updatedById])
}

'''

text = text.replace(anchor, models + anchor, 1)
schema_path.write_text(text)

migration_dir = repo / "backend/prisma/migrations/202609021410_phase10_talent_matrix_succession_planning"
migration_dir.mkdir(parents=True, exist_ok=True)
migration_sql = r'''CREATE TABLE "TalentAssessment" (
    "id" TEXT NOT NULL,
    "employeeId" TEXT NOT NULL,
    "potentialLevel" TEXT NOT NULL,
    "evidence" TEXT,
    "managerNote" TEXT,
    "isActive" BOOLEAN NOT NULL DEFAULT true,
    "assessedById" TEXT NOT NULL,
    "assessedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedById" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    CONSTRAINT "TalentAssessment_pkey" PRIMARY KEY ("id")
);

CREATE TABLE "SuccessionRole" (
    "id" TEXT NOT NULL,
    "title" TEXT NOT NULL,
    "department" TEXT,
    "criticality" TEXT NOT NULL DEFAULT 'NORMAL',
    "incumbentEmployeeId" TEXT,
    "description" TEXT,
    "isActive" BOOLEAN NOT NULL DEFAULT true,
    "createdById" TEXT,
    "updatedById" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    CONSTRAINT "SuccessionRole_pkey" PRIMARY KEY ("id")
);

CREATE TABLE "SuccessionCandidate" (
    "id" TEXT NOT NULL,
    "roleId" TEXT NOT NULL,
    "employeeId" TEXT NOT NULL,
    "readiness" TEXT NOT NULL DEFAULT 'DEVELOPING',
    "priority" INTEGER NOT NULL DEFAULT 3,
    "rationale" TEXT,
    "developmentPlanId" TEXT,
    "isActive" BOOLEAN NOT NULL DEFAULT true,
    "nominatedById" TEXT,
    "updatedById" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    CONSTRAINT "SuccessionCandidate_pkey" PRIMARY KEY ("id")
);

CREATE UNIQUE INDEX "TalentAssessment_employeeId_key" ON "TalentAssessment"("employeeId");
CREATE INDEX "TalentAssessment_potentialLevel_isActive_idx" ON "TalentAssessment"("potentialLevel", "isActive");
CREATE INDEX "TalentAssessment_assessedById_idx" ON "TalentAssessment"("assessedById");
CREATE INDEX "TalentAssessment_assessedAt_idx" ON "TalentAssessment"("assessedAt");
CREATE INDEX "TalentAssessment_updatedById_idx" ON "TalentAssessment"("updatedById");

CREATE INDEX "SuccessionRole_department_isActive_idx" ON "SuccessionRole"("department", "isActive");
CREATE INDEX "SuccessionRole_criticality_isActive_idx" ON "SuccessionRole"("criticality", "isActive");
CREATE INDEX "SuccessionRole_incumbentEmployeeId_idx" ON "SuccessionRole"("incumbentEmployeeId");
CREATE INDEX "SuccessionRole_title_idx" ON "SuccessionRole"("title");
CREATE INDEX "SuccessionRole_createdById_idx" ON "SuccessionRole"("createdById");
CREATE INDEX "SuccessionRole_updatedById_idx" ON "SuccessionRole"("updatedById");

CREATE UNIQUE INDEX "SuccessionCandidate_roleId_employeeId_key" ON "SuccessionCandidate"("roleId", "employeeId");
CREATE INDEX "SuccessionCandidate_employeeId_isActive_idx" ON "SuccessionCandidate"("employeeId", "isActive");
CREATE INDEX "SuccessionCandidate_roleId_readiness_isActive_idx" ON "SuccessionCandidate"("roleId", "readiness", "isActive");
CREATE INDEX "SuccessionCandidate_developmentPlanId_idx" ON "SuccessionCandidate"("developmentPlanId");
CREATE INDEX "SuccessionCandidate_nominatedById_idx" ON "SuccessionCandidate"("nominatedById");
CREATE INDEX "SuccessionCandidate_updatedById_idx" ON "SuccessionCandidate"("updatedById");

ALTER TABLE "SuccessionCandidate"
ADD CONSTRAINT "SuccessionCandidate_roleId_fkey"
FOREIGN KEY ("roleId") REFERENCES "SuccessionRole"("id")
ON DELETE CASCADE ON UPDATE CASCADE;
'''
(migration_dir / "migration.sql").write_text(migration_sql)

print("PRISMA_TALENT_MODELS=PASS")
print("PRISMA_TALENT_MIGRATION=PASS")
