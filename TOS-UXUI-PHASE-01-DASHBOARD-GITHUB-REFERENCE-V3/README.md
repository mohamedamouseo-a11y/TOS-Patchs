# TOS UX/UI Phase 01 — Dashboard V3

This is the recovery/validation package for Phase 01 after V2 successfully applied and built the intended Dashboard changes but incorrectly rejected its own git-status output.

## Why V2 failed
Git reported the new untracked stylesheet directory as:

```text
?? frontend/src/styles/
```

instead of the individual file path expected by V2. The intended changes themselves were correct:

```text
 M frontend/src/main.jsx
?? frontend/src/styles/dashboard-github-reference.css
```

V3 fixes validation by using `git status --porcelain=v1 --untracked-files=all` and accepts only those exact two paths.

## Safety
V3 is idempotent and works in either exact state:
- clean current baseline, or
- exact already-applied V2 state.

It stops on any unrelated/staged changes, mismatched HEAD, altered CSS, partial state, or unexpected main.jsx content.

## Execute

```bash
bash TOS-UXUI-PHASE-01-DASHBOARD-GITHUB-REFERENCE-V3/apply_phase01_dashboard_v3.sh /var/www/TOS
```

## Scope
Dashboard only. No Ramzy, TCS, business logic, or data-flow changes. OpenHands must not commit or push. After validation and manual visual review, the user performs the normal Push from inside TOS.