# PATCH REPORT — TOS Ramzy Gemini Primary / Agnes Fallback V1

## Status

- Patch package: **UPLOADED** to `mohamedamouseo-a11y/TOS-Patchs`.
- Source repository modified: **NO**.
- Production server modified: **NO**.
- Database modified/migrated: **NO**.
- Runtime deployment test: **NOT RUN**.

## Source inspected

Reference repository:

`mohamedamouseo-a11y/TOS` — branch `main`

The current GitHub source does not expose enough of the newer/live Ramzy implementation to safely write exact replacement files. In particular, searches did not locate the live-source signatures used by the Ramzy settings/runtime shown in the current environment, including:

- `AGENT_SETTINGS_ENCRYPTION_KEY`
- `OpenAI API key is not configured`
- `gpt-4.1-mini`
- `Mastra Agency Operator`

Because of that mismatch, this package is intentionally **fail-closed** rather than modifying unrelated/older AI code.

## Files in this patch

- `README.md` — scope, configuration, fallback rules, apply instructions.
- `RAMZY_PROVIDER_SPEC.md` — exact provider/failover behavior contract.
- `apply.mjs` — read-only source signature verifier; never modifies application files.
- `REPLIT_APPLY_PROMPT.txt` — minimal guarded integration/deployment prompt.
- `PATCH_REPORT.md` — this report.

## Required behavior after integration

- Primary provider: Gemini.
- Primary credential: `GEMINI_API_KEY`.
- Fallback provider: Agnes.
- Fallback credential: `AGNES_API_KEY`.
- Agnes base URL: `https://apihub.agnes-ai.com/v1`.
- Agnes default model: `agnes-2.0-flash`.
- Fallback happens only during model generation and before tool/action side effects begin.
- Existing Ramzy permissions, tools, approval gates, memory, limits, roles/workspaces and audit behavior stay unchanged.

## Guard behavior

Run:

```bash
node apply.mjs /var/www/TOS
```

Possible outcomes:

### `PATCH_BASE_MATCH`
The live source contains enough expected Ramzy signatures to continue. The verifier prints candidate integration files. Only those matched provider/model files should be changed according to `RAMZY_PROVIDER_SPEC.md`.

### `PATCH_BASE_MISMATCH`
Stop immediately. Do not guess filenames or apply changes to older/unrelated AI code. No application file is modified by the verifier.

## Smoke-test checklist after successful integration

1. Production build/check completes with no new errors.
2. Existing TOS process restarts successfully.
3. Ramzy settings page loads normally.
4. A normal Ramzy request succeeds through Gemini.
5. Audit identifies Gemini as provider for normal traffic.
6. A safe simulated Gemini unavailable/429/timeout case reaches Agnes before side effects.
7. Audit records fallback source and reason.
8. Gemini 401/403 remains visible as an auth failure in audit.
9. No fallback occurs after a tool/action side effect has started.
10. No API key or authorization header appears in logs, UI, source, or this public repository.

## Rollback rule

If integration/build fails, restore only the files changed during the Ramzy provider integration. Do not roll back or modify unrelated TOS files.
