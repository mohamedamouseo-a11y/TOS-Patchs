# Phase 02 — Projects Light Visibility Lock V15

Final screenshot-driven Light Mode correction after V14.

Targets only:
- Inspector `Active` badge visibility.
- Project Overview progress gauge shape and percentage visibility.

Implementation note:
- Adds dedicated high-specificity anchors so older broad Phase 02 selectors cannot override these two elements.
- Keeps the progress value dynamic via `--tos-project-progress`.
- Dark Mode and business logic are intentionally untouched.

Apply:

```bash
bash TOS-UXUI-PHASE-02-PROJECTS-LIGHT-VISIBILITY-LOCK-V15/apply_phase02_projects_light_visibility_lock_v15.sh /var/www/TOS
```

The script builds, deploys to `/opt/apps/tamiyouz-front/build`, verifies runtime markers, and does not commit or push TOS changes.
