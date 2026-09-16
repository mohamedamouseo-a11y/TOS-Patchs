# TOS Central Chat R31 — Native Video Playback

VERSION=TOS_CENTRAL_CHAT_R31
PATCH=TOS-CENTRAL-CHAT-R31-NATIVE-VIDEO-PLAYBACK
BASE_TOS_COMMIT_REVIEWED=cced65cb5ad09d36054bff7f70c8ab990693808c
TARGET=frontend/src/components/ChatPanel.jsx

## Goal
Make MP4/WebM attachments playable inline inside Central Chat as real native video players, not static previews.

## Required behavior
- Native `<video controls>` playback inside the message attachment card.
- Play / Pause / seek timeline / volume / fullscreen exposed by the browser's video controls.
- `preload="metadata"` only.
- `playsInline` enabled.
- NO autoplay.
- Keep the existing file download action.
- Keep image preview and audio playback behavior.
- Distinguish `video/webm` from `audio/webm` by MIME type so voice notes remain audio players.

## Scope
Frontend only. No backend/API/database/storage/permission changes.
Uses the existing authenticated `/api/files/:id/preview` media URL.

## Safety
- Installer uses guarded exact transformations.
- No git commands inside `/var/www/TOS`.
- No source push.
- On installer/build/deploy failure, restore source/live build and STOP.
