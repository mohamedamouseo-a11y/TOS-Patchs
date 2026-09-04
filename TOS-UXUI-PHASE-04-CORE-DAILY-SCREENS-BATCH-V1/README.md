# Phase 04 — Core Daily Screens Premium Batch V1

One visual-only batch for four high-frequency TOS screens using the accepted Projects / Tasks premium reference.

Screens:
- Design Queue
- Employee Work Hub
- Team Members
- Team Performance

Visual direction:
- Porcelain / Ivory light surfaces.
- Obsidian / Black Titanium dark surfaces.
- Champagne Gold accents with restrained use.
- Cleaner hierarchy, quieter borders, layered cards, stronger table readability, compact filters and premium focus states.
- Consistent spacing/radius/shadows across the four screens.
- Existing danger/success/action semantics are preserved.
- Light + Dark supported.

Scope is presentation only. No API, permissions, workflow, task, attendance, team, performance, save or business logic changes.

Run:

```bash
bash TOS-UXUI-PHASE-04-CORE-DAILY-SCREENS-BATCH-V1/apply_phase04_core_daily_screens_batch_v1.sh /var/www/TOS
```

The script validates the post-Phase-03 pushed source, adds stable page hooks, appends the Phase 04 visual layer, builds and deploys the frontend, validates live assets, and never commits or pushes TOS.
