# TCS Phase 1 — QA Only V12

Repository: `mohamedamouseo-a11y/TOS`
Branch: `main` ONLY
Expected remote HEAD: `ecc88cb10c4741437f65f0788888bd9fcc9c5de0`

## Purpose

V11 completed source push, canonical frontend deployment, live TCS branding verification, service health checks, and protected chat API checks. The only remaining strict gate is the live two-user direct-chat smoke test.

This V12 is QA ONLY.

## Strict rules

1. Do NOT create a branch.
2. Do NOT modify source code.
3. Do NOT commit or push anything.
4. Do NOT deploy anything.
5. Do NOT restart backend or frontend.
6. Do NOT run any database migration or direct database write.
7. Do NOT create a test user, reset any password, alter any real user account, or guess credentials.
8. Use ONLY two already-authorized TOS user sessions/accounts whose valid access is explicitly available in the current operator/session context.
9. Never expose passwords, cookies, JWTs, session tokens, or any credential material in logs or reports.
10. If a second authorized user session/account is not available, STOP and report `SECOND_AUTHORIZED_USER_REQUIRED`; do not weaken the test.
11. Product name is `TCS — Tamayouz Chat System`; no TACS branding.

## Preconditions

Verify remote source state without changing it:

```bash
cd /var/www/TOS
git branch --show-current
git rev-parse HEAD
git status --short
```

Required:

- branch = `main`
- HEAD = `ecc88cb10c4741437f65f0788888bd9fcc9c5de0`
- no tracked source modifications

Verify live health only:

```bash
./scripts/tos-production-preflight.sh --live
curl -fsS -o /dev/null -w 'HOME_HTTP=%{http_code}\n' https://tos.tamiyouz.com/
curl -fsS -o /dev/null -w 'CHAT_HTTP=%{http_code}\n' https://tos.tamiyouz.com/chat
```

## Two-user smoke gate

Use User A and User B in two independent authenticated browser sessions.

Required PASS sequence:

1. A opens `https://tos.tamiyouz.com/chat` and sees `TCS` / `TCS — Tamayouz Chat System`.
2. B opens the same TCS surface independently.
3. A opens or starts a direct conversation with B.
4. A sends exactly one message with a unique marker such as `TCS-V12-A-<timestamp>`.
5. B receives the message without full-page reload or relogin.
6. Verify B shows the new unread state/badge before opening the direct conversation.
7. B opens the conversation and verify the unread state clears.
8. B replies exactly once with marker `TCS-V12-B-<timestamp>`.
9. A receives B's reply without full-page reload or relogin.
10. Refresh both sessions and verify both messages persist in history.
11. Verify an existing group/channel chat surface still loads.
12. Verify TCS branding is visible and no newly introduced TACS branding appears.

## Cleanup

If the normal TCS UI supports deleting the two V12 smoke messages without affecting unrelated history, delete only those two smoke messages after evidence is captured. If message deletion is not safely available, leave the two clearly marked V12 smoke messages in place and report their markers. Do not perform direct DB cleanup.

## Completion criteria

Phase 1 strict QA is PASS only if every required two-user step passes.

If no valid second authorized user is available, return a report with:

`SECOND_AUTHORIZED_USER_REQUIRED`

and do not attempt account creation, password reset, impersonation, token minting, or credential guessing.

## Final report

Return `TCS_PHASE1_PRODUCTION_V12_REPORT.zip` containing:

- branch and HEAD evidence
- live preflight result
- homepage/chat HTTP results
- A session TCS branding evidence
- B session TCS branding evidence
- A->B message marker and realtime receipt result
- B unread result
- unread-clear result
- B->A reply marker and realtime receipt result
- refresh/history persistence result
- group/channel regression result
- branding/TACS result
- cleanup result
- final verdict: `TCS_PHASE1_STRICT_QA_PASS` or `SECOND_AUTHORIZED_USER_REQUIRED`
