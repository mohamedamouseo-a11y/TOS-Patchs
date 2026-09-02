#!/usr/bin/env python3
from pathlib import Path
import sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
schema_path = repo / "backend/prisma/schema.prisma"
migration_dir = repo / "backend/prisma/migrations/202609021130_phase9_skills_competencies_development"
migration_path = migration_dir / "migration.sql"

schema = schema_path.read_text()
if "model SkillDefinition {" in schema:
    raise SystemExit("PHASE9_SCHEMA_ALREADY_PRESENT")

anchor = "model PerformanceReview {"
if anchor not in schema:
    raise SystemExit("PHASE9_SCHEMA_ANCHOR_MISSING")

block = r'''model SkillDefinition {
  id          String   @id @default(cuid())
  name        String
  category    String   @default("General")
  description String?
  isActive    Boolean  @default(true)
  createdById String?
  updatedById String?
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt

  requirements       CompetencyRequirement[]
  assessments        EmployeeSkillAssessment[]
  developmentPlans   EmployeeDevelopmentPlan[]
  developmentActions EmployeeDevelopmentAction[]

  @@index([category, isActive])
  @@index([name])
  @@index([createdById])
  @@index([updatedById])
}

model CompetencyRequirement {
  id          String   @id @default(cuid())
  skillId     String
  scopeType   String
  department  String?
  jobTitle    String?
  employeeId  String?
  targetLevel Int
  importance  String   @default("CORE")
  isActive    Boolean  @default(true)
  createdById String?
  updatedById String?
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt

  skill SkillDefinition @relation(fields: [skillId], references: [id], onDelete: Cascade)

  @@index([skillId, isActive])
  @@index([scopeType, department, isActive])
  @@index([scopeType, jobTitle, isActive])
  @@index([scopeType, employeeId, isActive])
  @@index([createdById])
  @@index([updatedById])
}

model EmployeeSkillAssessment {
  id           String   @id @default(cuid())
  employeeId   String
  skillId      String
  currentLevel Int
  evidence     String?
  assessedById String
  assessedAt   DateTime @default(now())
  createdAt    DateTime @default(now())
  updatedAt    DateTime @updatedAt

  skill SkillDefinition @relation(fields: [skillId], references: [id], onDelete: Cascade)

  @@unique([employeeId, skillId])
  @@index([employeeId])
  @@index([skillId])
  @@index([assessedById])
  @@index([assessedAt])
}

model EmployeeDevelopmentPlan {
  id                   String   @id @default(cuid())
  employeeId           String
  skillId              String?
  sourceReviewId       String?
  title                String
  objective            String?
  status               String   @default("DRAFT")
  currentLevelSnapshot Int?
  targetLevel          Int?
  startDate            DateTime @default(now())
  targetDate           DateTime?
  completedAt          DateTime?
  createdById          String?
  updatedById          String?
  createdAt            DateTime @default(now())
  updatedAt            DateTime @updatedAt

  skill   SkillDefinition?           @relation(fields: [skillId], references: [id], onDelete: SetNull)
  actions EmployeeDevelopmentAction[]

  @@index([employeeId, status])
  @@index([skillId, status])
  @@index([sourceReviewId])
  @@index([targetDate, status])
  @@index([createdById])
  @@index([updatedById])
}

model EmployeeDevelopmentAction {
  id          String   @id @default(cuid())
  planId      String
  skillId     String?
  title       String
  description String?
  dueDate     DateTime?
  status      String   @default("TODO")
  completedAt DateTime?
  createdById String?
  updatedById String?
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt

  plan  EmployeeDevelopmentPlan @relation(fields: [planId], references: [id], onDelete: Cascade)
  skill SkillDefinition?        @relation(fields: [skillId], references: [id], onDelete: SetNull)

  @@index([planId, status])
  @@index([skillId])
  @@index([dueDate, status])
  @@index([createdById])
}

'''

schema = schema.replace(anchor, block + anchor, 1)
schema_path.write_text(schema)

migration_dir.mkdir(parents=True, exist_ok=False)
migration_path.write_text(r'''CREATE TABLE "SkillDefinition" (
    "id" TEXT NOT NULL,
    "name" TEXT NOT NULL,
    "category" TEXT NOT NULL DEFAULT 'General',
    "description" TEXT,
    "isActive" BOOLEAN NOT NULL DEFAULT true,
    "createdById" TEXT,
    "updatedById" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    CONSTRAINT "SkillDefinition_pkey" PRIMARY KEY ("id")
);

CREATE TABLE "CompetencyRequirement" (
    "id" TEXT NOT NULL,
    "skillId" TEXT NOT NULL,
    "scopeType" TEXT NOT NULL,
    "department" TEXT,
    "jobTitle" TEXT,
    "employeeId" TEXT,
    "targetLevel" INTEGER NOT NULL,
    "importance" TEXT NOT NULL DEFAULT 'CORE',
    "isActive" BOOLEAN NOT NULL DEFAULT true,
    "createdById" TEXT,
    "updatedById" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    CONSTRAINT "CompetencyRequirement_pkey" PRIMARY KEY ("id")
);

CREATE TABLE "EmployeeSkillAssessment" (
    "id" TEXT NOT NULL,
    "employeeId" TEXT NOT NULL,
    "skillId" TEXT NOT NULL,
    "currentLevel" INTEGER NOT NULL,
    "evidence" TEXT,
    "assessedById" TEXT NOT NULL,
    "assessedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    CONSTRAINT "EmployeeSkillAssessment_pkey" PRIMARY KEY ("id")
);

CREATE TABLE "EmployeeDevelopmentPlan" (
    "id" TEXT NOT NULL,
    "employeeId" TEXT NOT NULL,
    "skillId" TEXT,
    "sourceReviewId" TEXT,
    "title" TEXT NOT NULL,
    "objective" TEXT,
    "status" TEXT NOT NULL DEFAULT 'DRAFT',
    "currentLevelSnapshot" INTEGER,
    "targetLevel" INTEGER,
    "startDate" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "targetDate" TIMESTAMP(3),
    "completedAt" TIMESTAMP(3),
    "createdById" TEXT,
    "updatedById" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    CONSTRAINT "EmployeeDevelopmentPlan_pkey" PRIMARY KEY ("id")
);

CREATE TABLE "EmployeeDevelopmentAction" (
    "id" TEXT NOT NULL,
    "planId" TEXT NOT NULL,
    "skillId" TEXT,
    "title" TEXT NOT NULL,
    "description" TEXT,
    "dueDate" TIMESTAMP(3),
    "status" TEXT NOT NULL DEFAULT 'TODO',
    "completedAt" TIMESTAMP(3),
    "createdById" TEXT,
    "updatedById" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    CONSTRAINT "EmployeeDevelopmentAction_pkey" PRIMARY KEY ("id")
);

CREATE INDEX "SkillDefinition_category_isActive_idx" ON "SkillDefinition"("category", "isActive");
CREATE INDEX "SkillDefinition_name_idx" ON "SkillDefinition"("name");
CREATE INDEX "SkillDefinition_createdById_idx" ON "SkillDefinition"("createdById");
CREATE INDEX "SkillDefinition_updatedById_idx" ON "SkillDefinition"("updatedById");

CREATE INDEX "CompetencyRequirement_skillId_isActive_idx" ON "CompetencyRequirement"("skillId", "isActive");
CREATE INDEX "CompetencyRequirement_scopeType_department_isActive_idx" ON "CompetencyRequirement"("scopeType", "department", "isActive");
CREATE INDEX "CompetencyRequirement_scopeType_jobTitle_isActive_idx" ON "CompetencyRequirement"("scopeType", "jobTitle", "isActive");
CREATE INDEX "CompetencyRequirement_scopeType_employeeId_isActive_idx" ON "CompetencyRequirement"("scopeType", "employeeId", "isActive");
CREATE INDEX "CompetencyRequirement_createdById_idx" ON "CompetencyRequirement"("createdById");
CREATE INDEX "CompetencyRequirement_updatedById_idx" ON "CompetencyRequirement"("updatedById");

CREATE UNIQUE INDEX "EmployeeSkillAssessment_employeeId_skillId_key" ON "EmployeeSkillAssessment"("employeeId", "skillId");
CREATE INDEX "EmployeeSkillAssessment_employeeId_idx" ON "EmployeeSkillAssessment"("employeeId");
CREATE INDEX "EmployeeSkillAssessment_skillId_idx" ON "EmployeeSkillAssessment"("skillId");
CREATE INDEX "EmployeeSkillAssessment_assessedById_idx" ON "EmployeeSkillAssessment"("assessedById");
CREATE INDEX "EmployeeSkillAssessment_assessedAt_idx" ON "EmployeeSkillAssessment"("assessedAt");

CREATE INDEX "EmployeeDevelopmentPlan_employeeId_status_idx" ON "EmployeeDevelopmentPlan"("employeeId", "status");
CREATE INDEX "EmployeeDevelopmentPlan_skillId_status_idx" ON "EmployeeDevelopmentPlan"("skillId", "status");
CREATE INDEX "EmployeeDevelopmentPlan_sourceReviewId_idx" ON "EmployeeDevelopmentPlan"("sourceReviewId");
CREATE INDEX "EmployeeDevelopmentPlan_targetDate_status_idx" ON "EmployeeDevelopmentPlan"("targetDate", "status");
CREATE INDEX "EmployeeDevelopmentPlan_createdById_idx" ON "EmployeeDevelopmentPlan"("createdById");
CREATE INDEX "EmployeeDevelopmentPlan_updatedById_idx" ON "EmployeeDevelopmentPlan"("updatedById");

CREATE INDEX "EmployeeDevelopmentAction_planId_status_idx" ON "EmployeeDevelopmentAction"("planId", "status");
CREATE INDEX "EmployeeDevelopmentAction_skillId_idx" ON "EmployeeDevelopmentAction"("skillId");
CREATE INDEX "EmployeeDevelopmentAction_dueDate_status_idx" ON "EmployeeDevelopmentAction"("dueDate", "status");
CREATE INDEX "EmployeeDevelopmentAction_createdById_idx" ON "EmployeeDevelopmentAction"("createdById");

ALTER TABLE "CompetencyRequirement"
ADD CONSTRAINT "CompetencyRequirement_skillId_fkey"
FOREIGN KEY ("skillId") REFERENCES "SkillDefinition"("id")
ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE "EmployeeSkillAssessment"
ADD CONSTRAINT "EmployeeSkillAssessment_skillId_fkey"
FOREIGN KEY ("skillId") REFERENCES "SkillDefinition"("id")
ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE "EmployeeDevelopmentPlan"
ADD CONSTRAINT "EmployeeDevelopmentPlan_skillId_fkey"
FOREIGN KEY ("skillId") REFERENCES "SkillDefinition"("id")
ON DELETE SET NULL ON UPDATE CASCADE;

ALTER TABLE "EmployeeDevelopmentAction"
ADD CONSTRAINT "EmployeeDevelopmentAction_planId_fkey"
FOREIGN KEY ("planId") REFERENCES "EmployeeDevelopmentPlan"("id")
ON DELETE CASCADE ON UPDATE CASCADE;

ALTER TABLE "EmployeeDevelopmentAction"
ADD CONSTRAINT "EmployeeDevelopmentAction_skillId_fkey"
FOREIGN KEY ("skillId") REFERENCES "SkillDefinition"("id")
ON DELETE SET NULL ON UPDATE CASCADE;
''')

print("PRISMA_SKILLS_MODELS=PASS")
print("PRISMA_SKILLS_MIGRATION=PASS")
