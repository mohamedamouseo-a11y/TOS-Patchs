# TOS Ramzy Message Renderer V2

## Goal
Improve ONLY the Ramzy chat message presentation shown in production.

Observed issue:
- Markdown markers such as `**`, `#`, and pipe tables are visible as raw text.
- Arabic + English mixed content is hard to scan.
- project/task result tables wrap badly.
- the message body needs better scrolling.
- the composer is taller than necessary.

## Scope
Primary production files:
- `frontend/src/components/RamzyAssistant.jsx`
- `frontend/src/index.css`

Dependency files may be changed ONLY if the live frontend has no existing safe Markdown/GFM renderer:
- `frontend/package.json`
- the existing frontend lockfile only

No backend, Prisma, DB, env, provider, memory, intelligence, tool, approval, audit, permission, workspace, streaming, launcher, or voice behavior changes.

## Required implementation

### 1. Safe Markdown / GFM rendering
Assistant messages must render Markdown instead of printing it literally.

First inspect `frontend/package.json` and the existing component imports.
- Reuse an existing Markdown/GFM renderer if already installed.
- If none exists, add the minimum frontend-only dependency required for safe React Markdown rendering and GFM tables.
- Do not enable raw HTML rendering.
- Do not use `dangerouslySetInnerHTML`.
- Do not add `rehype-raw`.

Support at minimum:
- bold / italic
- headings
- paragraphs
- ordered/unordered lists
- inline code and fenced code
- links
- GFM tables
- line breaks compatible with the existing Ramzy response format

Links opened externally must use safe rel attributes.

### 2. RTL / LTR isolation
Mixed Arabic/English replies must remain readable.

Requirements:
- message prose uses `dir="auto"` where appropriate.
- use `unicode-bidi: plaintext` for natural mixed-direction text blocks.
- code, IDs, URLs, status values, and technical tokens remain isolated LTR where needed.
- never force the whole assistant reply to LTR.
- Arabic UI remains RTL.

### 3. Project / Task results as cards
When an assistant reply contains a valid GFM table whose headers indicate project/task operational data, do not show a cramped desktop table.

Detect data tables containing headers such as Arabic/English equivalents of:
- project / المشروع
- task / المهمة
- status / الحالة
- overdue / التأخير
- assignee / المسؤول

Render each data row as a compact `.ramzy-result-card` with label/value fields.

Rules:
- preserve the exact returned values; do not invent or rewrite data.
- unknown table types may render as a normal responsive Markdown table.
- status values such as `PLANNING`, `DELIVERY`, `IN_REVIEW`, `BLOCKED`, `DEVELOPMENT`, `CANCELLED`, `COMPLETED` may receive visual badges only; text/value must remain unchanged.
- technical IDs must wrap safely and must not overflow.
- if parsing fails, fall back to normal Markdown rendering; never drop the message.

### 4. Message body scrolling
The panel dimensions and launcher behavior stay unchanged.

Make the conversation body the only primary vertical scroll region:
- header stays fixed in the panel layout.
- composer stays fixed at the bottom of the panel layout.
- messages area uses `min-height: 0`, `overflow-y: auto`, and contained overscroll.
- preserve existing scroll-to-latest behavior.
- long code, IDs, and tables must not create page-level horizontal overflow.

### 5. Compact composer
Keep the current Mic and Send controls and all voice behavior.

Reduce only the excessive empty height:
- textarea starts compact, approximately 48-56px visual height.
- auto-grow only as the user types, with a sensible max around 120px.
- preserve Enter-to-send and Shift+Enter newline behavior.
- preserve focus, disabled, streaming, and microphone states.

### 6. Styling
Add scoped Ramzy-only CSS.

Required classes may include:
- `.ramzy-markdown`
- `.ramzy-markdown-table-wrap`
- `.ramzy-result-cards`
- `.ramzy-result-card`
- `.ramzy-result-field`
- `.ramzy-status-badge`

Style goals:
- clean readable spacing
- clear hierarchy
- subtle cards/borders matching the existing premium Ramzy UI
- no global typography regressions
- dark mode remains readable
- mobile remains responsive

## Production safety
Before changes, verify live anchors in `RamzyAssistant.jsx` still include the current Ramzy panel, message rendering loop, composer, send flow, streaming flow, and microphone controls.

If the source is materially different, STOP with `SOURCE_MISMATCH=YES` and do not overwrite the component wholesale.

Build from the actual served frontend only:
`/var/www/TOS/frontend`

The expected served output is:
`/var/www/TOS/frontend/dist`

Do NOT run the root build that writes `/var/www/TOS/dist/public`.
Do NOT modify Nginx.
Do NOT restart Nginx.
Do NOT restart backend/PM2 for this frontend-only patch unless the existing frontend deployment script explicitly requires it.
