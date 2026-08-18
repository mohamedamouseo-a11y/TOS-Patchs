# Verification Contract — TOS Ramzy Message Renderer V2

Pass only if all applicable checks succeed:

- Raw Markdown markers are no longer visibly printed for normal assistant Markdown.
- Raw HTML execution remains disabled.
- Project/task GFM tables render as readable cards without changing returned values.
- Unknown table types remain readable through responsive table rendering.
- Arabic/English mixed text, project names, statuses, IDs, code, and URLs remain directionally readable.
- Messages body scrolls internally; no page-level horizontal overflow from long reply content.
- Existing scroll-to-latest behavior remains intact.
- Composer starts compact and grows only with content.
- Mic / speech-to-prompt behavior is unchanged.
- Send / Enter / Shift+Enter / streaming behavior is unchanged.
- Existing panel dimensions, header, launcher, history, minimize and drag behavior are unchanged.
- Dark mode and mobile remain readable/responsive.
- Frontend build succeeds from `/var/www/TOS/frontend` and writes `/var/www/TOS/frontend/dist`.
- No backend, DB, Prisma, env, provider, memory, system-intelligence, approval, audit or permission changes.

Required final marker:
`TOS_RAMZY_MESSAGE_RENDERER_V2_OK`
