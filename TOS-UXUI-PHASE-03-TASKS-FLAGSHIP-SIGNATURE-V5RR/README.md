# Phase 03 — Tasks Flagship Signature V5RR

Recovery for the V5/V5R false task-card guard failure.

What changed:
- Keeps the reviewed V4 CSS baseline pinned.
- Keeps `ProfessionalTaskBoard.jsx` committed blob pinned.
- Rebases only the committed `main.jsx` guard to the current HEAD while still validating the exact reviewed Tasks import worktree content.
- Replaces the obsolete `.tos-modern-task-card` guard with the stable `data-tos-task-card-layout-polish="v1"` DOM anchor.
- Applies the original V5 flagship patch unchanged otherwise.
- Adds a semantic task-card fallback using the stable DOM anchor so signature card styling still applies even when the legacy class is absent.

Review location:
- TOS → Tasks (`/tasks`)
- Open the same project
- Compare Light and Dark against V4

No business logic, permissions, drag/drop, realtime, Ramzy, TCS, or Help Center behavior changes.

Apply:

```bash
bash TOS-UXUI-PHASE-03-TASKS-FLAGSHIP-SIGNATURE-V5RR/apply_phase03_tasks_flagship_signature_v5rr.sh /var/www/TOS
```

No commit or push is performed on TOS.
