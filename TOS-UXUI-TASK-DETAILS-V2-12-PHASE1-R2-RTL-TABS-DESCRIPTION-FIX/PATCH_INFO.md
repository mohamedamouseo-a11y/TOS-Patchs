# TOS Task Details V2.12 Phase 1 R2 — RTL Tabs + Description Fix

VERSION=TOS_TASK_DETAILS_V2_12_PHASE1_R2_RTL_TABS_DESCRIPTION
PATCH=TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-R2-RTL-TABS-DESCRIPTION-FIX
BASELINE=TOS_TASK_DETAILS_V2_12_PHASE1_R1_RTL_DESCRIPTION_ZERO_OVERLAP
BASELINE_PATCH_COMMIT=87b1159b4a58421606a1b0f3adf78e3b2a849d0e
PATCH_SCOPE=RTL_TABS_AND_DESCRIPTION_ONLY

## Why R2 exists
Manual production QA after R1 confirmed that Assignee overlap is fixed, but two visual defects remain:

1. Arabic Task Details still shows several internal surfaces in LTR visual order, especially the primary tabs and Hero controls.
2. The Description editor needs a stronger high-specificity RTL/toolbar contract so older canonical rules cannot reintroduce clipping, horizontal-scroll fragments, or oversized empty editor space.

R2 is intentionally narrow. It does not redesign Task Details and does not touch the R1 Assignee or More Details geometry that already improved overlap behavior.

## Exact source changes
`frontend/src/components/ProfessionalTaskBoard.jsx`

- Add ONE stylesheet import only:
  `../styles/taskDetailsV2_12_Phase1R2RtlTabsDescriptionFix.css`

No other JSX source changes are allowed.

## CSS outcome

### Remaining RTL
- Primary tabs use true RTL order with Overview on the physical right in Arabic.
- Hero summary controls use RTL auto-placement/order.
- Status / Priority / Assignee / Date triggers inherit RTL text direction.
- Portal dropdowns respect their existing `dir="rtl"` attribute.

### Description
- High-specificity RTL direction on Description panel/editor only.
- Toolbar uses a wrapped horizontal row instead of clipping/scroll fragments.
- Toolbar groups/buttons/selects remain horizontal.
- Deterministic group order is preserved.
- Editable content starts from the RTL side.
- Empty Description canvas minimum height is reduced to 180px desktop / 150px small screens.

## Frozen / unchanged
- Phase 1 Assignee geometry
- R1 Assignee Hero reservation
- R1 More Details geometry
- Backend
- Database
- API
- Authentication
- Permissions
- Task workflow/business rules
- `taskBoardParts.jsx`
- `App.jsx`
- Canonical stylesheet
- Phase 1 stylesheet
- R1 stylesheet
- Chat System / TCS
- Ramzy
- Comments logic
- Attachments logic
- Timer logic
- Status/Priority business logic

## Apply

```bash
python3 \
  /var/www/TOS-Patchs/TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-R2-RTL-TABS-DESCRIPTION-FIX/apply_tos_task_details_v2_12_phase1_r2_rtl_tabs_description_fix.py \
  /var/www/TOS
```

## QA policy
OpenHands must NOT use a browser, take screenshots, or perform visual QA.
Its responsibility ends at patch/build/deploy/technical verification.
Manual visual QA is performed separately by the user + ChatGPT.

NO_BROWSER_QA=YES
NO_SCREENSHOTS=YES
PUSH=NO
