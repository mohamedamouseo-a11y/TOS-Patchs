# TOS Team Performance — Phase 2 Professional Date Range & Comparison V1

This patch is designed to run **after** the approved local Team Performance Premium Dark Mode, Phase 1 UX cleanup/refinement, and Global Header Premium Dark UX/UI changes, while TOS HEAD is still:

`8b29fd2ec2c96ce422b927711310b35fe6c52c61`

## Goal

Turn the existing quick date buttons into a professional reporting-period and comparison experience without changing backend contracts or score logic.

## Adds

- Reporting period control with explicit From / To fields.
- Quick presets: Today, Yesterday, Week, Month, Quarter, Year, Custom.
- Comparison modes:
  - Previous period
  - Previous month
  - Previous year
  - Custom comparison
  - No comparison
- Visible current-period and comparison-period labels.
- Existing `/team-performance` API reused for the comparison period; no backend change.
- Five core KPI comparison deltas.
- Employee Score comparison in the Team Performance table/mobile cards aligned to the chosen comparison period.
- Quarter correctly maps to `QUARTERLY` in target-management metadata.

## Comparison semantics

- The current Team Performance calculation remains authoritative and unchanged.
- Comparison is presentation/analysis only.
- Current filtered employee cohort is matched by employee ID against the comparison period for apples-to-apples comparison.
- Average score and top-performer score use point deltas.
- Completion uses percentage-point delta.
- Overdue is inverse-semantics: lower is visually positive.
- Logged hours uses hour delta.
- Missing comparison data renders as `—`; it is never converted to zero performance.

## Explicitly not included

- Help Center
- Ramzy
- New score formula
- Backend/schema/migration changes
- New API contract
- Automated management/HR decisions

## Expected final TOS working-tree scope

```text
 M frontend/src/components/layout/Topbar.jsx
 M frontend/src/components/performance/ExecutiveCommandCenter.jsx
 M frontend/src/pages/TeamPerformanceDashboard.jsx
?? frontend/src/components/layout/premiumHeaderDark.css
?? frontend/src/components/performance/PerformanceDisclosure.jsx
?? frontend/src/components/performance/PerformancePeriodControl.jsx
?? frontend/src/components/performance/teamPerformancePremiumDark.css
```

## Run

```bash
cd /var/www/TOS-Patchs/TOS-TEAM-PERFORMANCE-PHASE2-PROFESSIONAL-DATE-COMPARE-V1-GIT-GENERATED
bash run_phase2_professional_date_compare_v1.sh
```

The runner does not commit or push TOS.
