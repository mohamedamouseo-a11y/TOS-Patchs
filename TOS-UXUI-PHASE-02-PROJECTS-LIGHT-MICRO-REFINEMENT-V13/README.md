# Phase 02 — Projects Light Micro Refinement V13

Recovery/published version after the earlier missing-folder execution attempt.

Scope: Projects screen, Light Mode only.

Targets exactly the two remaining visual issues from V12 review:
- Project Overview progress micro-card.
- Active pagination page beside Previous.

Dark Mode and business logic are intentionally untouched.

Apply:

```bash
bash TOS-UXUI-PHASE-02-PROJECTS-LIGHT-MICRO-REFINEMENT-V13/apply_phase02_projects_light_micro_refinement_v13.sh /var/www/TOS
```

The script builds and deploys to `/opt/apps/tamiyouz-front/build`, verifies runtime markers, and does not commit or push TOS changes.
