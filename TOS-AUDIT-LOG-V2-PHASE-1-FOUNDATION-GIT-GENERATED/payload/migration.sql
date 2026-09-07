-- TOS Audit Log V2 Phase 1 Foundation
-- Additive only: legacy audit/activity tables are intentionally untouched.
CREATE TABLE "AuditEventV2" (
    "id" TEXT NOT NULL,
    "occurredAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "action" TEXT NOT NULL,
    "category" TEXT,
    "entityType" TEXT,
    "entityId" TEXT,
    "actorId" TEXT,
    "actorType" TEXT NOT NULL DEFAULT 'USER',
    "actorName" TEXT,
    "actorEmail" TEXT,
    "actorRole" TEXT,
    "outcome" TEXT NOT NULL DEFAULT 'SUCCESS',
    "severity" TEXT NOT NULL DEFAULT 'INFO',
    "source" TEXT NOT NULL DEFAULT 'TOS',
    "requestId" TEXT,
    "ipAddress" TEXT,
    "userAgent" TEXT,
    "httpMethod" TEXT,
    "route" TEXT,
    "legacySource" TEXT,
    "legacyId" TEXT,
    "metadata" JSONB,
    "beforeState" JSONB,
    "afterState" JSONB,
    "errorCode" TEXT,
    "errorMessage" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT "AuditEventV2_pkey" PRIMARY KEY ("id")
);

CREATE INDEX "AuditEventV2_occurredAt_idx" ON "AuditEventV2"("occurredAt");
CREATE INDEX "AuditEventV2_actorId_occurredAt_idx" ON "AuditEventV2"("actorId", "occurredAt");
CREATE INDEX "AuditEventV2_action_occurredAt_idx" ON "AuditEventV2"("action", "occurredAt");
CREATE INDEX "AuditEventV2_category_occurredAt_idx" ON "AuditEventV2"("category", "occurredAt");
CREATE INDEX "AuditEventV2_entityType_entityId_idx" ON "AuditEventV2"("entityType", "entityId");
CREATE INDEX "AuditEventV2_requestId_idx" ON "AuditEventV2"("requestId");
CREATE INDEX "AuditEventV2_legacySource_legacyId_idx" ON "AuditEventV2"("legacySource", "legacyId");
