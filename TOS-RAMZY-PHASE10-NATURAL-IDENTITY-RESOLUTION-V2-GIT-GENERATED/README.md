# TOS — Ramzy Phase 10 V2: Natural Identity Resolution + Team Performance Bridge

Current reviewed TOS main when this patch was prepared:

`bdfb1dcd97dd0732034bf966235fd968616816d3`

The runner is intentionally lineage-aware rather than locked to that exact SHA: it requires the Phase 9 baseline to remain an ancestor and refuses to touch any already-dirty Phase 10 target file. Unrelated dirty work is preserved and verified unchanged.

## Why V2

The original Phase 10 patch strengthened Ramzy's shared multilingual identity resolver, but Team Performance still had its own older employee resolver using only exact / startsWith / contains matching. That meant a valid authorized employee stored as `Youssef`, `Yousef` or `Yusuf` could fail when the user asked for `يوسف`.

The Team Performance response then surfaced the generic `EMPLOYEE_NOT_VISIBLE` wording, which could look like an ADMIN permission problem even when the real failure was name resolution.

## What V2 does

V2 first applies the original Phase 10 identity layer, then bridges `ramzyTeamPerformance.service.js` to the same shared `resolveEntityCandidates` pipeline.

This provides:

- Arabic/English/transliteration/phonetic name resolution inside Team Performance.
- `يوسف / Youssef / Yousef / Yusuf` support.
- Shared confidence and ambiguity guard: multiple or low-confidence matches require clarification; Ramzy must not guess.
- The Team Performance candidate set remains the already-authorized ACTIVE dataset produced by the existing Team Performance builder.
- ADMIN remains `SELF + TEAM`, not company-wide ALL.
- `performance.view_all` remains separate and is not granted to ADMIN by this patch.
- No RBAC widening, no score changes, no Prisma/schema/package changes.

## Expected TOS changes

Exactly these Phase 10 target files are added/modified by V1 + V2:

- `backend/src/agency-operator/prompts/ramzyPrompt.js`
- `backend/src/agency-operator/services/entityAlias.service.js`
- `backend/src/agency-operator/services/entityResolution.service.js`
- `backend/src/agency-operator/services/identityNameMatching.service.js` (new)
- `backend/src/agency-operator/services/ramzySystemIntelligence.service.js`
- `backend/src/agency-operator/services/ramzyTeamPerformance.service.js`
- `backend/src/agency-operator/tests/ramzyIdentityResolutionPhase10.test.js` (new)
- `backend/src/agency-operator/tests/ramzyTeamPerformanceIdentityPhase10.test.js` (new)

## Validation

The runner:

- refuses to overwrite any already-dirty Phase 10 target file;
- preserves unrelated dirty work exactly;
- runs the complete Ramzy backend test suite;
- verifies Team Performance no longer uses the parallel startsWith/contains employee resolver;
- verifies current permission semantics remain server-side TEAM/ALL based;
- reloads the real backend PM2 process (`tamiyouz-system`, with compatibility fallback);
- smokes health, dashboard, team-performance and tasks;
- never commits or pushes TOS.

## Run

```bash
cd /var/www/TOS-Patchs
git pull --ff-only origin main

cd TOS-RAMZY-PHASE10-NATURAL-IDENTITY-RESOLUTION-V2-GIT-GENERATED
bash run_phase10_natural_identity_resolution_v2.sh
```

Do not commit or push TOS from OpenHands. Push manually only after reviewing the runner report.
