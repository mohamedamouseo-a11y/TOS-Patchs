# TOS UX/UI Phase 02 — Projects V1

Screen: **Projects / إدارة المشاريع only**.

Purpose: align the Projects screen with the approved GitHub/Developer Hub premium visual language from Phase 01: warm cream/gold Light Mode, slate premium Dark Mode, stronger text contrast, consistent cards, filters, forms and neutral surfaces.

The patch is presentation-only. It does not change project business logic, Ramzy, TCS, permissions, APIs, or data flow.

It also builds and copies the fresh frontend output to the actual `tos.tamiyouz.com` live root (`/opt/apps/tamiyouz-front/build`) because the public domain does not serve `frontend/dist` directly.

Run:

```bash
bash TOS-UXUI-PHASE-02-PROJECTS-GITHUB-REFERENCE-V1/apply_phase02_projects_v1.sh /var/www/TOS
```

OpenHands must not reset, stash, commit, or push. After visual approval, the user performs Push from inside TOS.
