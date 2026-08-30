# TOS Dashboard Premium UX/UI V1

Deployment patch generator for the TOS executive dashboard.

## Scope
- UI/UX polish only; no business-logic or data-flow changes.
- Keeps the existing dashboard structure and behavior.
- Adds a scoped `frontend/src/dashboard-premium.css` visual layer.
- Adds one CSS import to `frontend/src/main.jsx`.
- Light mode: warm ivory / restrained gold premium surfaces.
- Dark mode: midnight navy / gold accents, refined contrast, cards, progress, actions, activity rows, dropdown, and scrollbar.
- Design reference: the current premium GitHub Sync visual language.

## Safety
The generator is pinned to the exact TOS baseline it was created for and refuses to generate if:
- repository HEAD changed,
- `frontend/src/main.jsx` changed,
- the premium CSS file already exists,
- or the target has local/staged changes.

It generates a standard Git patch and runs `git apply --check` before reporting success. It does **not** apply the patch automatically.

## Generate
```bash
bash TOS-DASHBOARD-PREMIUM-UXUI-V1-GIT-GENERATED/run_dashboard_premium_uxui_v1.sh /var/www/TOS
```

Default output:
```text
/var/tmp/TOS_DASHBOARD_PREMIUM_UXUI_V1.patch
```

## Apply after review
```bash
git -C /var/www/TOS apply --check /var/tmp/TOS_DASHBOARD_PREMIUM_UXUI_V1.patch
git -C /var/www/TOS apply /var/tmp/TOS_DASHBOARD_PREMIUM_UXUI_V1.patch
```

Then run the normal TOS build/deploy validation workflow.

## Patch targets
- `frontend/src/main.jsx`
- `frontend/src/dashboard-premium.css` (new)
