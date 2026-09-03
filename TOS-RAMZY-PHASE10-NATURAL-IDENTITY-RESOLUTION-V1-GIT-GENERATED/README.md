# TOS — Ramzy Phase 10: Natural Language & Identity Resolution

Baseline TOS HEAD:

`ee59c7c8e47aadc4c489b17948649208ce2b041c`

## Purpose

Strengthen Ramzy's identity resolution before voice actions are introduced. This phase builds on the existing multilingual matcher, aliases, ambiguity guard and Phase 8 RBAC rather than creating a parallel identity system.

## Main changes

- Adds `RAMZY_IDENTITY_NAME_MATCHING_V1` as a safe name-specific layer over the existing multilingual/phonetic matcher.
- Supports Arabic/English spelling and pronunciation variants such as `يوسف / Youssef / Yousef / Yusuf`.
- Supports compound-name spacing/transliteration variants such as `عبد الرحمن / Abdelrahman`.
- Normalizes common Arabic/English honorifics before identity comparison.
- Prevents a multi-word identity from receiving a high-confidence match merely because one common token matched, e.g. `محمد حسن` must not silently resolve to `Mohamed Ali`.
- Keeps single first-name matching available; if multiple authorized people share that phonetic name, the existing ambiguity guard forces clarification.
- Makes saved aliases spelling/transliteration-aware while capping fuzzy alias confidence below the automatic ALIAS threshold. Fuzzy aliases may surface a candidate but cannot silently auto-resolve it.
- Keeps alias lookup strictly workspace-scoped and user/global-alias scoped.
- Keeps person/project candidate discovery inside the existing authorized TOS surface. No RBAC widening.
- Updates Ramzy prompt rules so the configured AI provider can understand natural phrasing, but cannot override Identity Resolver confidence, ambiguity decisions, or RBAC.
- Treats future Speech-to-Text output as normal untrusted user text that must pass the same identity + permission checks.

## Provider boundary

This phase intentionally makes **zero extra AI-provider calls for identity matching**. The configured provider continues to understand the user's natural-language request, while the final identity decision stays deterministic and server-controlled. This avoids an LLM guessing a person/project outside the authorized candidate set. Phase 11 can add the speech provider without changing this safety boundary.

## TOS files changed

Exactly 6 files:

- `backend/src/agency-operator/prompts/ramzyPrompt.js`
- `backend/src/agency-operator/services/entityAlias.service.js`
- `backend/src/agency-operator/services/entityResolution.service.js`
- `backend/src/agency-operator/services/identityNameMatching.service.js` (new)
- `backend/src/agency-operator/services/ramzySystemIntelligence.service.js`
- `backend/src/agency-operator/tests/ramzyIdentityResolutionPhase10.test.js` (new)

No Prisma/schema/migration/package/frontend changes. No Performance Score, permission defaults, action semantics, or approval execution rules are changed.

## Validation

The runner validates:

- Arabic/English name variants.
- Compound-name spacing/transliteration.
- Multi-word partial-match rejection.
- Duplicate phonetic names require clarification.
- Fuzzy aliases cannot silently auto-resolve.
- RBAC-first visible-user/project resolution remains present.
- Full Ramzy test suite.
- Backend reload using production `tamiyouz-system` with `tamiyouz-backend` fallback.
- Health/dashboard/team-performance/tasks HTTP smoke.

## Run

```bash
cd /var/www/TOS-Patchs
git pull --ff-only origin main
cd TOS-RAMZY-PHASE10-NATURAL-IDENTITY-RESOLUTION-V1-GIT-GENERATED
bash run_phase10_natural_identity_resolution_v1.sh
```

Do not commit or push TOS from OpenHands. The owner pushes manually after review.
