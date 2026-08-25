# TCS Phase 1 — Manus Apply & Test Retry V2

Repository: `mohamedamouseo-a11y/TOS`
Target branch: `main` ONLY.
Pinned baseline: `03a61b7bc84baa8e801ec40f33d24bbaf0969894`

## Important context

The previous run stopped at precheck only. ChatGPT independently verified that the server HEAD reported in the precheck (`03a61b7bc84baa8e801ec40f33d24bbaf0969894`) is also the current latest `TOS/main` commit on GitHub. Therefore DO NOT run `git pull` in this retry.

Three existing untracked ZIP artifacts are present in `/var/www/TOS`. They are unrelated production artifacts. DO NOT delete, move, stash, reset, modify, or add them. Their presence is allowed. The tracked working tree must still be clean.

## Non-negotiable rules

1. Do NOT create a branch.
2. Do NOT write or redesign the feature yourself.
3. Do NOT edit unrelated files.
4. Apply only the supplied ChatGPT patches, in the exact order below.
5. Do NOT touch the three existing untracked ZIP files.
6. Preserve Ramzy / AI Chat / Help Center / Operational Inbox / TWorkspace.
7. User-facing product name is **TCS — Tamayouz Chat System**. Never display TACS.
8. If patch validation, migration, typecheck, tests, build, functional checks, or authorization checks fail, do NOT push.
9. Never enter GitHub credentials interactively. If final push authentication fails, report it with evidence.

## Step 1 — strict baseline check

From `/var/www/TOS`:

```bash
git branch --show-current
git rev-parse HEAD
git diff --quiet && echo TRACKED_WORKTREE_CLEAN
git diff --cached --quiet && echo INDEX_CLEAN
git status --short
```

Required:

- branch = `main`
- HEAD = `03a61b7bc84baa8e801ec40f33d24bbaf0969894`
- tracked worktree clean
- index clean

The following untracked files are expected and MUST remain untouched:

```text
?? TOS_V1.15.91_THRS_ACCORDION_COMMENTS_ATTENDANCE_PASSWORD_STRICT.zip
?? TOS_V1.15.92_TEAM_MEMBER_DETAILS_REFERENCE3_PASSWORD_VISIBILITY_STRICT.zip
?? TOS_V1.15.93_TEAM_MEMBER_DETAILS_DEDUP_HEADER_STRICT.zip
```

Do NOT run `git pull`.

## Step 2 — obtain ChatGPT patches

Use a temporary copy of the public patch repository outside `/var/www/TOS`:

```bash
rm -rf /tmp/TOS-Patchs-TCS-Phase1
git clone --depth 1 https://github.com/mohamedamouseo-a11y/TOS-Patchs.git /tmp/TOS-Patchs-TCS-Phase1
```

Patches to apply IN THIS ORDER:

1. Core Phase 1 patch (legacy filename only):
   `/tmp/TOS-Patchs-TCS-Phase1/TACS/Phase-1/TACS_PHASE_1_CORE_DM_V1.patch`
2. TCS branding correction:
   `/tmp/TOS-Patchs-TCS-Phase1/TCS/Phase-1/TCS_PHASE_1_BRANDING_CORRECTION_V1.patch`

The legacy TACS filename/path is only the original artifact name. Final user-facing branding must be TCS.

## Step 3 — patch apply gate

```bash
git apply --check /tmp/TOS-Patchs-TCS-Phase1/TACS/Phase-1/TACS_PHASE_1_CORE_DM_V1.patch
git apply /tmp/TOS-Patchs-TCS-Phase1/TACS/Phase-1/TACS_PHASE_1_CORE_DM_V1.patch

git apply --check /tmp/TOS-Patchs-TCS-Phase1/TCS/Phase-1/TCS_PHASE_1_BRANDING_CORRECTION_V1.patch
git apply /tmp/TOS-Patchs-TCS-Phase1/TCS/Phase-1/TCS_PHASE_1_BRANDING_CORRECTION_V1.patch

git diff --check
git status --short
```

Expected source areas only:

- `drizzle/schema.ts`
- `server/tacsRouter.ts` (new technical module filename from the core patch)
- `server/routers.ts`
- `client/src/components/TacsChat.tsx` (new technical component filename from the core patch)
- `client/src/components/DashboardLayout.tsx`

Confirm there are no user-facing `TACS` strings in the changed source:

```bash
git diff | grep -n 'TACS' || true
```

If any added user-facing TACS label remains, STOP and report it. Do not edit it manually.

## Step 4 — database migration

```bash
pnpm db:push
```

Verify the generated Phase 1 tables exist according to the applied schema. Do not hand-edit an existing migration.

## Step 5 — validation gate

```bash
pnpm check
pnpm test
pnpm build
```

All must pass.

## Step 6 — functional smoke test with two real TOS users

1. User A opens TCS.
2. User A finds User B.
3. User A opens/creates a direct conversation.
4. User A sends a text message.
5. User B sees the conversation and unread badge.
6. User B opens it; unread clears.
7. User B replies.
8. User A receives the reply through polling without full page reload.
9. Refresh both browsers; history persists.
10. UI says **TCS**, never TACS.
11. Ramzy / AI Assistant still works.
12. Help Center assistant still works.
13. Operational Inbox still works.
14. TWorkspace still works.

Authorization checks:

- user cannot read a conversation they are not a member of
- user cannot send to a conversation they are not a member of
- user cannot start a direct conversation with themselves

## Step 7 — commit and push

Only after every gate passes:

```bash
git diff --check
git add drizzle server client
git commit -m "feat(tcs): add phase 1 direct messaging"
GIT_TERMINAL_PROMPT=0 git push origin main
```

If push fails only because authentication is unavailable, DO NOT enter credentials interactively and DO NOT reset the successful local commit. Report the local commit SHA and exact push error.

## Final report required

Return one concise report containing:

- starting branch and HEAD
- tracked cleanliness result
- confirmation that the three untracked ZIPs were untouched
- core patch apply result
- TCS branding correction patch apply result
- generated migration filename(s), if any
- table verification
- `pnpm check`
- `pnpm test`
- `pnpm build`
- two-user smoke test
- authorization tests
- TCS branding verification
- final local commit SHA
- push result and remote SHA if successful
- exact changed-file list
- any blocker with command-output evidence

If any validation gate fails: DO NOT PUSH.