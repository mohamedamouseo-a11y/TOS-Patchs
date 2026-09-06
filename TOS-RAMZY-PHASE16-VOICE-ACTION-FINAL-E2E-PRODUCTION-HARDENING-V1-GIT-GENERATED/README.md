# TOS Ramzy Phase 16 — Voice & Action Final E2E / Production Hardening V1

Baseline: `f7678ab1ab7b5b0261a9e3a3a78c43533999b66d`

This patch hardens the final browser/API boundary for Ramzy approvals and installs the Phase 16 acceptance matrix.

## Scope

- Adds `RAMZY_VOICE_ACTION_PRODUCTION_HARDENING_V1`.
- Adds a server-side Public Approval Boundary so browser/API/socket consumers receive only safe approval metadata, human-readable names/summaries, confirmation metadata, and safe execution outcomes.
- Keeps internal target IDs and raw execution records server-side for execution/audit only.
- Preserves approval/run control references required by the Ramzy UI without rendering target database IDs.
- Re-validates the final Phase 10–15 contracts in one acceptance matrix: multilingual identity/ambiguity, voice review-before-send, server-side RBAC, confirmation/revision guards, conversational draft safety, multi-step partial outcomes, evidence, audit and no raw target rendering.
- No Prisma/schema/package changes.
- No frontend source changes; frontend build is validation-only.
- No frontend deploy in this patch.

## Controlled real-action acceptance

The runner intentionally does **not** create a production task automatically. A true real-action E2E requires an explicit sandbox/test project selected by the user so Phase 16 does not leave unwanted production data. The runner reports:

`CONTROLLED_REAL_ACTION_E2E=READY_REQUIRES_EXPLICIT_SANDBOX_TARGET`

That final controlled acceptance should cover one typed/voice request through identity resolution → approval → confirm → actual execution → audit/result, plus one ambiguity/failure path.

## Run

```bash
cd /var/www/TOS-Patchs/TOS-RAMZY-PHASE16-VOICE-ACTION-FINAL-E2E-PRODUCTION-HARDENING-V1-GIT-GENERATED
bash run_phase16_voice_action_final_e2e_production_hardening_v1.sh
```

Do not commit, push, reset, clean, or discard unrelated work inside `/var/www/TOS`.
