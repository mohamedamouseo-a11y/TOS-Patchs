# TOS-PROJECT-NAME-DUPLICATE-GUARD-V1

## Reviewed baseline

TOS GitHub `main` reviewed before patch creation:

- HEAD: `16e14cd7b6d71f9508fe0e066c08aa48005eb8a2`
- Target: `backend/src/routes/projects.routes.js`
- Target blob: `8c230713151be4d40224f9ce49482f83020f232b`

## Problem

The normal Projects API creates a project directly with `tx.project.create()`. The Prisma `Project.name` field is not unique and there is no normalized-name duplicate check.

This allowed active projects such as:

- `وقف مؤمنة`
- `وقف مؤمنه`
- `وقف مومنة`

to exist as separate rows even though they represent the same normalized Arabic name.

## V1 behavior

The patch adds one backend guard used by project lifecycle operations.

Normalization includes:

- Unicode NFKC
- lowercase
- Arabic diacritic removal
- `أ / إ / آ / ٱ -> ا`
- `ؤ -> و`
- `ئ / ى -> ي`
- `ة -> ه`
- tatweel removal
- punctuation/separator collapse
- whitespace collapse

The guard blocks an operation with HTTP 409 when another ACTIVE/non-archived project has the same normalized name.

Covered paths:

1. Project create
2. Project rename/update when `name` is supplied
3. Project restore from archive

Archived projects do not block new active projects. However, restoring an archived project is blocked if an active normalized-name match exists.

## Concurrency

The guard takes a PostgreSQL transaction advisory lock derived from the normalized project name before checking active projects. This serializes simultaneous create/rename/restore operations targeting the same normalized name and closes the normal application-level race condition.

## Scope

- Backend source only
- No Prisma schema change
- No migration
- No cleanup/archive/delete of existing projects
- No TCRM data modification
- No service restart performed by the patch runner
- No git push performed by the patch runner

## Files

- `apply_patch.py` — deterministic, anchor-guarded patch runner.
- `OPENHANDS_PROMPT.md` — minimal live-server application and verification instructions.
