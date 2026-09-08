-- TOS Audit Log V2 Phase 5 Hardening
-- Adds query indexes and enforces append-only semantics.
CREATE INDEX IF NOT EXISTS "AuditEventV2_entityType_entityId_occurredAt_idx"
  ON "AuditEventV2"("entityType", "entityId", "occurredAt");
CREATE INDEX IF NOT EXISTS "AuditEventV2_outcome_occurredAt_idx"
  ON "AuditEventV2"("outcome", "occurredAt");
CREATE INDEX IF NOT EXISTS "AuditEventV2_severity_occurredAt_idx"
  ON "AuditEventV2"("severity", "occurredAt");
CREATE INDEX IF NOT EXISTS "AuditEventV2_source_occurredAt_idx"
  ON "AuditEventV2"("source", "occurredAt");

CREATE OR REPLACE FUNCTION "audit_event_v2_append_only_guard"()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
  IF TG_OP = 'UPDATE' THEN
    RAISE EXCEPTION 'AuditEventV2 is append-only: UPDATE is not allowed';
  END IF;

  IF TG_OP = 'DELETE'
     AND COALESCE(current_setting('app.audit_v2_retention_purge', true), '') <> 'on'
  THEN
    RAISE EXCEPTION 'AuditEventV2 is append-only: DELETE is only allowed by controlled retention';
  END IF;

  RETURN OLD;
END;
$$;

DROP TRIGGER IF EXISTS "AuditEventV2_append_only_guard" ON "AuditEventV2";
CREATE TRIGGER "AuditEventV2_append_only_guard"
BEFORE UPDATE OR DELETE ON "AuditEventV2"
FOR EACH ROW
EXECUTE FUNCTION "audit_event_v2_append_only_guard"();
