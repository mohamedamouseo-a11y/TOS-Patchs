# TCS — Complete End-to-End With In-System Push V3

## CRITICAL: PUSH MUST COME FROM INSIDE TOS

The prompt repository `mohamedamouseo-a11y/TOS-Patchs` is ONLY where this instruction is stored.

The implementation target remains the production TOS project at:
- Working copy: `/var/www/TOS`
- GitHub repository: `mohamedamouseo-a11y/TOS`
- Branch: `main` ONLY

Manus must complete the remaining TCS implementation and validation in the production TOS project, but the final GitHub push MUST be triggered **from inside the running TOS system itself using its existing Developer Hub / GitHub integration push action**.

## Absolutely forbidden

- DO NOT run `git push` from the terminal.
- DO NOT use SSH push.
- DO NOT use a deploy key for the final push.
- DO NOT use GitHub CLI to push.
- DO NOT push code to `TOS-Patchs`.
- DO NOT create a new branch.
- DO NOT force push.

If the TOS Developer Hub / GitHub integration cannot perform the push, STOP and report the exact sanitized in-system blocker. Do not fall back to shell/SSH/CLI push.

## Execution

1. Work on the existing production TOS working copy in `/var/www/TOS`.
2. Preserve the already validated local TCS Phase 2 commit lineage.
3. Audit the entire canonical production TCS (`frontend/` + `backend/`).
4. Implement all remaining real TCS gaps/defects in one run. Do not duplicate features already present.
5. Run all required frontend/backend/security/realtime/regression validation gates.
6. Create the required local commit(s) in the TOS working copy.
7. Open the running TOS system.
8. Navigate to its existing Developer Hub / GitHub integration area.
9. Use the TOS system's own Push action to push the completed TOS `main` state to `mohamedamouseo-a11y/TOS` → `main`.
10. Verify from inside the TOS system that the push succeeded and capture the resulting remote commit SHA/evidence.
11. Only after the in-system push succeeds, deploy the validated production changes using the existing official TOS production deployment workflow.
12. Run post-deploy TCS QA and return one final report.

## TCS completion scope

Audit and finish all real remaining gaps across:
- TCS branding/navigation
- global unread badge
- background realtime notifications
- reconnect + visibility recovery
- stale toast lifecycle
- direct messages
- group conversations
- project general chat
- public/private channels
- replies
- reactions
- edit/delete
- typing indicators
- delivered/read receipts
- presence
- attachments/upload/download/delete
- voice recording where currently supported
- meeting/call integration where currently supported
- message-to-task
- pins/decisions/notes where currently supported
- mentions
- search
- notification persistence and exact-scope read reconciliation
- authorization/membership/private-channel security
- Arabic/English
- light/dark mode
- mobile/narrow layout
- TOS shell regressions (Ramzy, Tasks, TWS/TGWS, Sidebar, Settings)

Reuse the existing production architecture and Prisma chat models. Do not create a duplicate chat system. No database migration unless an objectively missing capability requires a reviewed additive non-destructive change.

## Required push evidence

The final report must prove the push was performed from inside TOS, not from the shell. Include sanitized evidence such as:
- Developer Hub / GitHub integration section used
- in-system push result/status
- target repository = `mohamedamouseo-a11y/TOS`
- target branch = `main`
- remote SHA reported/verified after the in-system push

The final report must explicitly state:

```text
IMPLEMENTATION_WORKDIR=/var/www/TOS
IMPLEMENTATION_REPO=mohamedamouseo-a11y/TOS
IMPLEMENTATION_BRANCH=main
PROMPT_REPO=mohamedamouseo-a11y/TOS-Patchs
CODE_PUSHED_TO_PATCH_REPO=NO
TERMINAL_GIT_PUSH_USED=NO
SSH_PUSH_USED=NO
GITHUB_CLI_PUSH_USED=NO
DEPLOY_KEY_PUSH_USED=NO
IN_SYSTEM_DEVELOPER_HUB_PUSH_USED=YES
IN_SYSTEM_PUSH_TARGET=mohamedamouseo-a11y/TOS
IN_SYSTEM_PUSH_BRANCH=main
IN_SYSTEM_PUSH_RESULT=
REMOTE_FINAL_SHA=
DEPLOYMENT=
PHASE2_AND_TCS_COMPLETION_STATUS=
```

`PHASE2_AND_TCS_COMPLETION_STATUS=PASS` is allowed only when all mandatory TCS validation gates pass, the in-system Developer Hub push succeeds to `TOS/main`, the remote SHA is verified, deployment succeeds, and no unresolved critical/high-severity TCS defect remains.

Return one ZIP only:
`TCS_COMPLETE_END_TO_END_IN_SYSTEM_V3_REPORT.zip`
