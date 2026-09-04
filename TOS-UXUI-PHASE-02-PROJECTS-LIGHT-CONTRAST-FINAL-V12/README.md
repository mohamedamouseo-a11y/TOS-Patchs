# Phase 02 — Projects Light Contrast Final V12

Screenshot-driven final Light Mode legibility pass on top of reviewed Couture Contrast V11.

Scope: Projects screen only.

Fixes:
- Project row avatar initials/letters in Light Mode.
- Selected-project hero text and avatar contrast.
- Inspector metric labels and numeric values.
- Project overview progress percentage visibility.
- Filter/select labels and values.
- Small table metadata, dates, counters and badges.
- Dark Mode intentionally unchanged.

Apply:

```bash
bash TOS-UXUI-PHASE-02-PROJECTS-LIGHT-CONTRAST-FINAL-V12/apply_phase02_projects_light_contrast_final_v12.sh /var/www/TOS
```

The script builds and deploys to `/opt/apps/tamiyouz-front/build`, verifies the runtime marker, and does not commit or push TOS changes.
