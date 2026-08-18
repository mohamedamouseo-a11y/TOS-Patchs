# TOS Ramzy Premium Chat + Voice V1

## Scope
Frontend-only guarded patch for Ramzy.

Modified files only:
- `frontend/src/components/RamzyAssistant.jsx`
- `frontend/src/index.css`

## UI target
- Desktop panel max width: 720px
- Desktop panel max height: 760px
- Premium navy header
- Larger avatar/identity
- Improved chat bubbles and typography
- Premium composer
- Mic + Send controls
- Existing mobile/RTL/dark-mode behavior preserved

## Voice target
Browser-native speech-to-text only using `SpeechRecognition` / `webkitSpeechRecognition`.

- Arabic: `ar-EG`
- English: `en-US`
- Dictation writes into the prompt textarea
- Existing typed text is preserved
- No automatic send
- No raw audio upload/storage
- No backend speech service

## Safety
Must not change:
- Agnes Primary / Gemini Fallback
- Ramzy Memory
- Ramzy System Intelligence
- Tools / approvals / permissions / audit
- DB / Prisma / environment
