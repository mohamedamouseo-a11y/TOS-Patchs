# Manus — TCS V6 Feature & Workflow Audit / Completion

## Mission
Complete the next real TCS product step without rebuilding existing capabilities and without another cosmetic-only redesign.

TCS is already a mature chat system with a draggable/resizable desktop window, floating launcher, realtime unread, direct/group/project conversations, channels, reactions, replies/threads, mentions, edit/delete, files/Drive, voice, meetings, Huddles/WebRTC, search, task conversion, pins/decisions, notifications, presence, templates/commands, moderation/insights, delivery/read receipts, and responsive desktop-window UX.

V6 must first prove what exists, what is partial, and what is truly missing, then implement only the highest-value missing/partial daily workflows.

---

## Repositories and runtime

Prompt repository ONLY:
- `mohamedamouseo-a11y/TOS-Patchs`
- This repository stores instructions only. DO NOT push implementation code here.

Implementation:
- Working copy: `/var/www/TOS`
- Repository: `mohamedamouseo-a11y/TOS`
- Branch: `main`
- Required starting remote SHA: `1adcddb782e80c2233460916e0e9b6815aab830d`

Before editing, verify local/remote lineage and preserve all TCS/TNC/Ramzy work already on main.

---

# Phase A — Evidence-first TCS capability audit

Audit the canonical production TCS code before changing anything:

Frontend:
- `frontend/src/components/ChatPanel.jsx`
- `frontend/src/components/TcsDesktopWindow.jsx`
- `frontend/src/components/TcsFloatingLauncher.jsx`
- `frontend/src/hooks/useChat.js`
- `frontend/src/hooks/useGlobalTcsUnread.js`
- `frontend/src/lib/api.js`
- relevant realtime/socket helpers
- relevant TCS CSS only where needed

Backend:
- `backend/src/routes/chat.routes.js`
- `backend/src/routes/centralChatNative.routes.js`
- chat services/helpers
- `backend/prisma/schema.prisma`
- existing migrations relevant to chat only

Produce a capability matrix with `EXISTS`, `PARTIAL`, or `MISSING`, with file/function evidence.

At minimum verify:
1. Direct conversations
2. Group conversations
3. Project/general/channel chat
4. Private/team channel controls
5. Message pagination/history
6. Realtime message delivery
7. Typing
8. Delivery/read receipts
9. Reactions
10. Reply/thread workflow
11. Mentions
12. Edit/delete
13. Files / Google Drive / pasted images
14. Voice / meeting / Huddle
15. Search + message deep-link/jump
16. Pins / decisions
17. Convert message to real Task
18. Notifications / TNC opening TCS targets
19. Presence
20. Templates / commands
21. Moderation / insights
22. Global unread and scope unread
23. Draft persistence per chat scope
24. Conversation notification controls (mute/snooze or equivalent)
25. Save/star/bookmark message or equivalent personal follow-up mechanism
26. Conversation lifecycle controls (archive/hide/leave where appropriate)
27. Scheduled send or equivalent deferred-send workflow
28. Keyboard/power-user navigation where applicable
29. Mobile + desktop-window behavior
30. Failure/retry states for workflows that write server state

Do NOT mark something missing just because its exact label is absent. Inspect existing behavior and API contracts.

---

# Phase B — Select only real V6 gaps

After the matrix, choose the highest-value real gaps using these rules:

- Prefer daily workflow value over feature count.
- Prefer completing PARTIAL flows before inventing new systems.
- Reuse existing data models, APIs, socket events and notification infrastructure whenever possible.
- Do not duplicate TNC, task management, file management, meetings, Huddle, or existing chat notification systems.
- Do not implement speculative enterprise features with no user-facing benefit.
- Keep V6 coherent: normally 2–4 meaningful workflow improvements, not 15 tiny features.

Candidate areas to inspect carefully (NOT automatically required):
- per-conversation/channel mute or snooze
- saved/starred/bookmarked messages for personal follow-up
- archive/hide/leave conversation workflows
- scheduled/deferred send
- better durable draft handling
- keyboard navigation / command palette shortcuts
- reliable retry/unsynced recovery for task/decision actions
- deep-link/open-to-specific-message/thread workflow from TNC and internal links

If these already exist, do not rebuild them. Choose other evidenced gaps.

---

# Phase C — Implementation requirements

For every selected V6 workflow:

1. Use existing TCS UI and desktop-window design language.
2. Keep the TCS launcher and desktop window mechanics unchanged unless a proven bug requires a minimal fix.
3. Preserve realtime unread, TNC, Ramzy, Projects, Tasks, Files, TWS and global navigation.
4. All persistent actions must have authoritative backend state. Do not present localStorage-only state as server-persisted state.
5. If optimistic UI is used, reconcile with the authoritative response and show failure/retry accurately.
6. If a new socket event is genuinely required, use the existing singleton Socket.IO connection and realtime patterns. Never create a second socket or polling loop.
7. Respect permissions and membership boundaries on every backend mutation/read.
8. Arabic/English + light/dark + desktop-window large/medium/narrow must remain usable.
9. Preserve accessibility: keyboard reachability, focus state, aria labels and reduced motion.

### Database rule
Do NOT add a schema/migration unless the selected real workflow truly requires durable state and cannot safely use an existing model.

If an additive Prisma migration is genuinely required:
- explain why existing schema cannot represent the state
- keep it additive/backward-compatible
- do not reset or rewrite production data
- validate Prisma and migration safety
- deploy only through the existing official TOS deployment workflow

---

# Explicit non-goals

- No new chat system.
- No root `client/`, `server/`, `drizzle/`, or `drizzle.config.ts` changes.
- No TCS rebranding redesign.
- No replacement of the draggable desktop window.
- No replacement of the existing floating launcher.
- No duplicate notification center.
- No duplicate Task system.
- No fake/local-only persistence presented as successful server save.
- No broad refactor of mature chat code unless directly needed for the selected workflow.
- No new branch.

---

# Validation gates

Run at minimum:

```bash
cd /var/www/TOS
./scripts/tos-production-preflight.sh --live

git diff --check

cd /var/www/TOS/backend
node --check src/routes/chat.routes.js
npm test
npm run prisma:validate

cd /var/www/TOS/frontend
npm run build
```

Also run focused tests for every changed backend/service/helper contract.

Validate the selected V6 workflows with evidence for:
- happy path
- authorization boundary
- persistence after refresh/reopen
- realtime reconciliation where applicable
- failure/retry behavior
- no duplicate notification/socket effects
- Arabic and English
- light and dark
- desktop-window large/medium/narrow

If a safe second authorized user session is available, run two-user realtime QA. If not available, report `BLOCKED_SECOND_AUTHORIZED_SESSION` without creating users, resetting passwords, guessing credentials or impersonating anyone.

---

# Commit and Push policy

Create local implementation commit(s) in `/var/www/TOS` only after validation.

Suggested primary commit message:
`feat(tcs): complete v6 chat workflows`

## FINAL PUSH — mandatory in-system route

DO NOT:
- run terminal `git push`
- use SSH push
- use GitHub CLI push
- use PAT/deploy-key fallback
- push implementation to `TOS-Patchs`
- force push

After local commits and validation:
1. Open the running TOS system.
2. Open its existing Developer Hub / GitHub integration.
3. Use the system's own Push action.
4. Target `mohamedamouseo-a11y/TOS` branch `main`.
5. Verify the remote SHA equals the final local SHA.
6. If in-system push fails, STOP and report the exact sanitized blocker. No terminal fallback.

---

# Deployment

Deploy only after successful in-system push.

If frontend-only:
```bash
cd /var/www/TOS
./scripts/tos-production-deploy.sh --scope frontend
```

If canonical backend was changed:
```bash
cd /var/www/TOS
./scripts/tos-production-deploy.sh --scope both
```

Run final live preflight and targeted post-deploy QA.

---

# Required report

Return exactly:
`TCS_V6_FEATURE_WORKFLOW_AUDIT_COMPLETION_REPORT.zip`

Include:
- starting local SHA
- starting remote SHA
- full capability audit matrix with evidence
- selected V6 gaps and why they were selected
- rejected candidate features because they already existed or were low-value
- changed files
- schema/migration status
- tests/build/preflight results
- final local SHA
- in-system Developer Hub push evidence
- remote final SHA
- deployment scope/result
- live QA matrix
- any blocked two-user QA
- no secrets

Final status block:

```text
IMPLEMENTATION_WORKDIR=/var/www/TOS
IMPLEMENTATION_REPO=mohamedamouseo-a11y/TOS
BRANCH=main
START_REMOTE_SHA=
CAPABILITY_AUDIT=PASS|FAIL
REAL_GAPS_SELECTED=
DUPLICATE_FEATURES_ADDED=NO
LOCAL_ONLY_FAKE_PERSISTENCE=NO
SCHEMA_CHANGE=YES|NO
MIGRATION=YES|NO
FRONTEND_BUILD=PASS|FAIL
BACKEND_TESTS=PASS|FAIL
PRISMA_VALIDATE=PASS|FAIL
REALTIME_VALIDATION=PASS|BLOCKED_SECOND_AUTHORIZED_SESSION|FAIL
IN_SYSTEM_PUSH=PASS|FAIL
TERMINAL_GIT_PUSH_USED=NO
REMOTE_FINAL_SHA=
DEPLOY_SCOPE=frontend|both
DEPLOYMENT=PASS|FAIL
V6_STATUS=PASS|PARTIAL_BLOCKED_SECOND_AUTHORIZED_SESSION|FAIL
```
