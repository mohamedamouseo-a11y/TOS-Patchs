# TACS Phase 1 — Manus Apply & Test Prompt

Repository to modify: `mohamedamouseo-a11y/TOS`
Target branch: `main` ONLY.
Patch source repository: `mohamedamouseo-a11y/TOS-Patchs`
Patch path: `TACS/Phase-1/TACS_PHASE_1_CORE_DM_V1.patch`

## Non-negotiable rules

1. Do NOT create a new branch.
2. Do NOT rewrite, redesign, or independently implement the feature.
3. Do NOT edit unrelated files.
4. Apply the supplied ChatGPT patch exactly first.
5. If `git apply --check` fails because of source drift, stop and report the exact rejected hunk/file/context. Do not invent replacement code.
6. Preserve the existing Ramzy / AI chat and Help Center behavior.
7. Do not remove the current Operational Inbox or TWorkspace in this phase.
8. Commit and push to `TOS/main` only after every required validation passes.

## Goal

Deploy TACS (Tamayouz Chat System) Phase 1 as a native TOS module with:

- Floating TACS launcher above the existing AI/Ramzy launcher area.
- Right-side TACS chat panel available across the authenticated TOS UI.
- Team directory search.
- One-to-one direct conversations.
- Persistent chat history.
- Unread counters/badge.
- Mark-as-read behavior.
- Lightweight near-real-time refresh using polling.
- Separate TACS database tables; do not reuse the existing AI `chat_messages` table.
- Database foundation already supports future group conversations.

## Execution

From the TOS working copy on the existing `main` branch:

```bash
git status --short
git branch --show-current
git pull --ff-only
```

Confirm the branch is exactly `main` and the working tree is clean before continuing.

Fetch/copy the patch from `TOS-Patchs/main`:

`TACS/Phase-1/TACS_PHASE_1_CORE_DM_V1.patch`

Then run:

```bash
git apply --check TACS_PHASE_1_CORE_DM_V1.patch
git apply TACS_PHASE_1_CORE_DM_V1.patch
```

Inspect the diff and confirm only these intended source areas changed:

- `drizzle/schema.ts`
- `server/tacsRouter.ts` (new)
- `server/routers.ts`
- `client/src/components/TacsChat.tsx` (new)
- `client/src/components/DashboardLayout.tsx`

## Database migration

Generate and apply the Drizzle migration using the project's existing workflow:

```bash
pnpm db:push
```

Do not hand-edit an existing production migration. Keep any newly generated migration files produced by the repository's normal Drizzle process.

Verify these tables exist after migration:

- `tacs_conversations`
- `tacs_conversation_members`
- `tacs_messages`

## Required validation gate

Run all of the following:

```bash
pnpm check
pnpm test
pnpm build
```

All must pass.

Then perform an authenticated functional smoke test with two real TOS users:

1. User A opens TACS.
2. User A can search/find User B.
3. User A starts a direct chat with User B.
4. User A sends a text message.
5. User B sees the conversation and unread badge.
6. User B opens it; unread count clears.
7. User B replies.
8. User A receives the reply after the polling refresh without reloading the TOS page.
9. Refresh both browsers and confirm conversation history persists.
10. Confirm Ramzy/AI assistant still opens and works.
11. Confirm Help Center assistant still renders and works.
12. Confirm TWorkspace and Operational Inbox routes still work.

Also verify authorization manually:

- A user cannot request messages for a conversation they do not belong to.
- A user cannot send to a conversation they do not belong to.
- A user cannot start a direct chat with their own user ID.

## Commit and push

Only after all validation passes:

```bash
git status --short
git diff --check
git add drizzle server client
git commit -m "feat(tacs): add phase 1 direct messaging"
git push origin main
```

## Final report required in this session

Return one concise report containing:

- Starting TOS commit SHA.
- Patch apply result.
- Migration filename(s) generated, if any.
- `pnpm check` result.
- `pnpm test` result.
- `pnpm build` result.
- Functional smoke-test results for both users.
- Authorization test results.
- Final commit SHA pushed to `TOS/main`.
- Exact changed-file list.
- Any issue/blocker with command output evidence.

If any gate fails, do NOT push. Report the failure and evidence only.