# Phase 03 — Tasks Flagship Signature V5R

Recovery runner for V5 after the committed `frontend/src/main.jsx` baseline advanced.

What it changes:
- It does **not** relax the visual V4 baseline checks.
- It validates the actual `main.jsx` worktree is exactly the reviewed Tasks CSS-import state.
- It dynamically rebases only V5's obsolete committed-main guard to the server's current HEAD.
- Then it runs the original V5 package unchanged, including the ProfessionalTaskBoard baseline, V4 CSS SHA, semantic-hook checks, build, deploy, and no-commit/no-push rules.

Apply:

```bash
bash TOS-UXUI-PHASE-03-TASKS-FLAGSHIP-SIGNATURE-V5R/apply_phase03_tasks_flagship_signature_v5r.sh /var/www/TOS
```
