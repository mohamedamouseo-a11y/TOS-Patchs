# TOS — Team Performance Premium Dark Mode V1

## Purpose

Polish `/team-performance` in dark mode only, keeping the current information architecture, Phase 3–12 behavior, API contracts, calculations, RBAC, and light mode unchanged.

Baseline TOS HEAD:

`8b29fd2ec2c96ce422b927711310b35fe6c52c61`

## Design direction

- Executive premium dark palette instead of white/light sheets on a black shell.
- Main background family: `#0D0F12`.
- Main surface: `#14171C`.
- Raised surface: `#191D24`.
- Border: low-contrast white alpha around 7–11%.
- Primary accent: muted premium gold `#D9A441`.
- Semantic colors remain functional only: green success, red risk, amber/orange warning, blue informational.
- Semantic backgrounds are deliberately subtle tints rather than large saturated blocks.
- Large performance tables are converted from light/beige sheet appearance into dark executive surfaces.
- Active segmented controls use premium gold instead of bright white inversion.
- Inputs, popovers, dividers, scrollbars and typography are harmonized.
- No layout redesign and no reduction/removal of Phase 3–12 information.

## Patch files

- `01_team_performance_premium_dark.py`
- `run_team_performance_premium_dark_v1.sh`

## TOS files changed by the patch

Exactly:

- `frontend/src/pages/TeamPerformanceDashboard.jsx`
- `frontend/src/components/performance/teamPerformancePremiumDark.css` (new)

No backend, schema, migration, package, lockfile, API or permission changes.

## Apply

```bash
cd /var/www/TOS-Patchs/TOS-TEAM-PERFORMANCE-PREMIUM-DARK-MODE-V1-GIT-GENERATED
bash run_team_performance_premium_dark_v1.sh
```

The runner requires a clean TOS working tree and the exact baseline commit above. It applies the scoped stylesheet, adds the Team Performance root class/import, runs contract guards, `git diff --check`, and a frontend build.

## Expected local status after application

```text
 M frontend/src/pages/TeamPerformanceDashboard.jsx
?? frontend/src/components/performance/teamPerformancePremiumDark.css
```

## Deployment

After the runner passes, copy the fresh `frontend/dist/` to the actual production frontend root and reload the existing frontend PM2 process:

```bash
rm -rf /opt/apps/tamiyouz-front/build/*
cp -a /var/www/TOS/frontend/dist/. /opt/apps/tamiyouz-front/build/
pm2 reload tamiyouz-frontend
```

Then verify live `/team-performance` returns HTTP 200 and the live `index.html` references the same hashed assets as current `frontend/dist/index.html`.

## Git safety

OpenHands must **not** commit or push TOS. The final TOS push remains manual through Developer Hub.
