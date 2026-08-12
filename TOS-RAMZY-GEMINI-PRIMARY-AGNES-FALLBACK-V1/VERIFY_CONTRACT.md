# Verification contract

The patch is accepted only when all of the following are true:

- Live Ramzy source was positively identified before editing.
- Primary provider is Gemini.
- Automatic fallback provider is Agnes AI.
- Agnes uses `https://apihub.agnes-ai.com/v1` and a valid configured model (default `agnes-2.0-flash`).
- Gemini and Agnes credentials are stored server-side and are never returned plaintext.
- Existing Ramzy secret encryption remains active when `AGENT_SETTINGS_ENCRYPTION_KEY` is present.
- Existing approval/proposal/read-only/tool/memory/workspace/role/limit behavior remains intact.
- Provider fallback occurs before tool side effects.
- Existing audit/error logging records primary-provider failures; successful provider identity is recorded where the existing audit model supports it.
- Production build succeeds.
- Only the existing TOS process is restarted.
- Ramzy AI settings page loads after deployment.
- No API keys, `.env` files, database dumps, or production secrets are committed to this public repository.

If the live source does not match the required anchors, the correct outcome is `SOURCE_MISMATCH` with zero production edits.
