# TOS-TCRM-CLIENT-IDENTITY-DUPLICATE-GUARD-V1-GIT-GENERATED

## Reviewed baseline

Latest GitHub `main` reviewed before patch creation:

`cd019d60434943d625fde9d2ea2ddee7e68d2028`

The TCRM integration route is unchanged from the previously audited baseline `b514d21ed3715e1d7545a2f009e0ce72634dbcb3`; the route file blob is still `d7159d5a1205b575d911953502b94c8fa4bd2112`.

## Confirmed current behavior

`handleTcrmProjectUpsert` currently:

1. builds identity from `crmProjectId`, `crmDealId`, `crmClientId`;
2. searches only `tos_crm_project_deliveries` using `source_key` with `crm_client_id` fallback;
3. updates the linked project when a delivery row exists;
4. otherwise immediately creates a new `Project` and delivery row;
5. does not reconcile a pre-existing manual/legacy project before create.

The `Project` Prisma model does not store CRM identity directly; CRM identity lives in the raw `tos_crm_project_deliveries` mapping table.

## V1 scope

This is intentionally a small prevention step.

- Require `crmClientId` on project sync.
- Preserve existing mapped-project update behavior.
- Before creating a new project, look for active unlinked legacy candidates by exact case-insensitive trimmed project/client name.
- If any candidate exists, return `409 TCRM_LEGACY_PROJECT_LINK_REQUIRED` and create nothing.
- Do not auto-adopt in V1.
- Do not change schema or existing project data.
- Do not clean existing duplicates.

## Why block instead of auto-adopt?

`crmClientId` is the agreed source of truth. Legacy projects do not yet carry that identity. Name/client-name matching can safely identify a *possible* legacy project, but it is not strong enough to silently establish identity. V1 therefore blocks duplicate creation and leaves the one-time adoption/link decision for the next supervised step.

## Files

- `apply_patch.py` — deterministic patch runner for the live TOS source.
- `OPENHANDS_PROMPT.md` — no-GitHub OpenHands instructions and verification contract.

## Next step after V1 verification

Design and implement the explicit legacy adoption/link step, then harden database idempotency/uniqueness after a dry-run confirms existing mapping rows are safe to constrain.
