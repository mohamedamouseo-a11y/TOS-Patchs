# Phase 02 — Projects Light Final V14

Final screenshot-driven light-mode correction on top of reviewed V13.

Scope: Projects screen only.

Targets exactly the two remaining issues:
- Selected-project `Active` badge contrast in Light Mode.
- Project Overview progress gauge visual/contrast in Light Mode.

Dark Mode and business logic are intentionally untouched.

Apply:

```bash
bash TOS-UXUI-PHASE-02-PROJECTS-LIGHT-FINAL-V14/apply_phase02_projects_light_final_v14.sh /var/www/TOS
```

The script builds and deploys to `/opt/apps/tamiyouz-front/build`, verifies runtime markers, and does not commit or push TOS changes.
