# TOS-RAMZY-GEMINI-PRIMARY-AGNES-FALLBACK-V1

## Goal
Change **Ramzy AI** provider order in the live TOS source so that:

1. **Gemini** is the primary provider.
2. **Agnes AI** is the automatic fallback provider.
3. OpenAI is no longer required as Ramzy's default model provider.

## Important baseline guard
The current `mohamedamouseo-a11y/TOS` GitHub `main` branch does not contain the same Ramzy implementation visible in the live TOS UI (the live UI contains Ramzy AI / Mastra Agency Operator / OpenAI `gpt-4.1-mini` settings and `AGENT_SETTINGS_ENCRYPTION_KEY`).

Therefore this patch MUST be applied only after locating the actual live Ramzy source under `/var/www/TOS`. Do not fabricate replacement paths and do not overwrite files if the required anchors are absent.

Expected live-source anchors include at least two of:
- `Ramzy` or `رمزي`
- `Mastra Agency Operator`
- `gpt-4.1-mini`
- `AGENT_SETTINGS_ENCRYPTION_KEY`
- `AI_API_KEY`
- `/api/agent`
- existing provider/model settings for the agent

If the live source cannot be identified unambiguously, STOP without changing production.

## Required provider configuration
### Gemini — primary
- Keep the API key server-side only.
- Prefer existing encrypted DB/settings storage when Ramzy already stores provider secrets there.
- Support `GEMINI_API_KEY` as environment fallback when the existing architecture supports environment secrets.
- Preserve the Gemini model already supported by the installed code/library. Do not invent a model identifier when the project already has a supported/default Gemini model.

### Agnes AI — fallback
- API base URL: `https://apihub.agnes-ai.com/v1`
- Chat endpoint: `/chat/completions` relative to that base URL.
- Default text model: `agnes-2.0-flash`
- Authentication: Bearer token from a server-side `AGNES_API_KEY` or the project's existing encrypted provider-key storage.
- Never expose or serialize the key to the browser.

## Failover contract
Provider order must be:

`Gemini -> Agnes`

Fallback is allowed when Gemini cannot produce the model response because of:
- missing/unconfigured Gemini key
- timeout/network failure
- HTTP 429
- HTTP 5xx
- provider unavailable/transient failure

For authentication/configuration failures, record the Gemini failure in the existing Ramzy audit/error log before attempting Agnes so the configuration problem is not hidden.

Fallback must happen at the **model generation boundary before tool side effects**. Do not execute Ramzy tools/actions twice because of provider fallback.

## Preserve existing Ramzy behavior
Do not change or remove:
- approval flow
- proposal/read-only mode
- tool/function calling contract
- memory behavior
- workspace restrictions
- allowed-role restrictions
- daily request limits
- tool-call limits
- current audit logging
- secret encryption via `AGENT_SETTINGS_ENCRYPTION_KEY` when present

Where practical, add `providerUsed` / equivalent audit metadata so successful calls show whether Gemini or Agnes served the request.

## UI/settings requirements
In Settings -> Ramzy AI:
- Primary provider must show **Gemini**.
- Fallback provider must show **Agnes AI**.
- Gemini and Agnes must have separate API-key/model configuration.
- Saved secrets must be masked and never returned in plaintext.
- Existing non-provider Ramzy settings must remain unchanged.

## Security
Never commit or print:
- API keys
- `.env`
- decrypted provider secrets
- production database content
- session/JWT secrets

This public patch repository must remain secret-free.

## Scope
Touch only files directly required for Ramzy provider settings/execution and, only if required by the current schema, the smallest migration/config change needed to store Agnes/Gemini settings.

No unrelated refactor. No full-project replacement. No changes to the private `TOS` GitHub repository from this patch workflow.
