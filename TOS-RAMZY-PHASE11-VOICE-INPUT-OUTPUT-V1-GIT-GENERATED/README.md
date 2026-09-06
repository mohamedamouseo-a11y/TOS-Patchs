# TOS — Ramzy Phase 11: Voice Input & Voice Output V1

Baseline TOS main:

`7e98d03108b80c8d881fcf50e62217db42f3027f`

## Scope

Phase 11 adds voice I/O as a transport layer around the existing Ramzy conversation/runtime. It does **not** create task actions from voice yet and does not bypass Phase 8 RBAC, Phase 10 identity resolution, approvals, or existing TOS business services.

## What it adds

- Three user modes in Ramzy:
  - Text only
  - Voice input
  - Voice conversation
- API Speech-to-Text when a compatible server-side voice provider is configured.
- Browser SpeechRecognition fallback when API STT is unavailable.
- API Text-to-Speech when a compatible server-side voice provider is configured.
- Browser SpeechSynthesis fallback when API TTS is unavailable.
- Manual speaker control for assistant responses.
- Automatic spoken response only in Voice Conversation mode, after the final assistant message is received.
- Voice transcription fills the composer for review. **No auto-send in Phase 11.**
- Provider credentials remain on the backend; no API key is exposed to the browser.

## Provider behavior

The server uses an OpenAI-compatible audio interface only when one of these is true:

1. `RAMZY_VOICE_BASE_URL` + `RAMZY_VOICE_API_KEY` are configured, or
2. the primary Ramzy provider is `openai`, or
3. the primary provider is `agnes` and `RAMZY_VOICE_USE_PRIMARY_OPENAI_COMPATIBLE=true` is explicitly enabled.

Optional environment variables:

- `RAMZY_STT_MODEL` (default `whisper-1`)
- `RAMZY_TTS_MODEL` (default `tts-1`)
- `RAMZY_TTS_VOICE` (default `alloy`)

If API voice is not configured, the UI falls back to browser voice features where supported.

## Security / permissions

- `/api/agent/voice/*` remains behind the existing `auth` middleware.
- Every voice endpoint also calls `assertAgentEnabledForUser`.
- Voice I/O gives Ramzy no new business permissions.
- Audio transcription becomes ordinary user text and will pass through the same Phase 10 identity resolution and later action/RBAC flow.
- Phase 11 does not execute task creation/assignment from a transcript.

## Files changed

Exactly 6 TOS files:

- `backend/src/routes/agent.routes.js`
- `backend/src/agency-operator/services/ramzyVoice.service.js` (new)
- `backend/src/agency-operator/tests/ramzyVoicePhase11.static.test.js` (new)
- `frontend/src/lib/api.js`
- `frontend/src/components/RamzyAssistant.jsx`
- `frontend/src/components/ramzyVoicePhase11.css` (new)

No Prisma/schema/migration/package changes.

## Validation

The runner validates:

- voice API routes exist behind authentication;
- server-side API secrets never move into frontend code;
- API STT/TTS and browser fallbacks are wired;
- no-auto-send guard is present;
- full Ramzy backend test suite;
- frontend production build;
- `git diff --check`;
- production frontend deploy and PM2 reload;
- backend PM2 reload;
- `/health`, `/dashboard`, `/team-performance`, `/tasks` return 200;
- unauthenticated voice status/TTS endpoints return 401;
- deployed frontend dist is byte-for-byte equivalent to the source build;
- unrelated pre-existing working-tree changes are preserved.

## Run

```bash
cd /var/www/TOS-Patchs
git pull --ff-only origin main
cd TOS-RAMZY-PHASE11-VOICE-INPUT-OUTPUT-V1-GIT-GENERATED
bash run_phase11_voice_input_output_v1.sh
```

Do not commit or push `/var/www/TOS` from OpenHands. The owner pushes manually after review.
