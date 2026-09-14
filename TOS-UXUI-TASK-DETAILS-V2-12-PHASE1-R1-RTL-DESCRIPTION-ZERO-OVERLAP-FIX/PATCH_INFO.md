# TOS Task Details V2.12 Phase 1 R1 — RTL + Description + Zero Overlap Fix

VERSION=TOS_TASK_DETAILS_V2_12_PHASE1_R1_RTL_DESCRIPTION_ZERO_OVERLAP
PATCH=TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-R1-RTL-DESCRIPTION-ZERO-OVERLAP-FIX
BASELINE=TOS_TASK_DETAILS_V2_12_PHASE1_ZERO_OVERLAP
BASELINE_PATCH_COMMIT=a80fb9c22e2ff086f65615931e951d2a12b882e5
PATCH_SCOPE=FRONTEND_RTL_AND_LAYOUT_HOTFIX

## Why R1 exists
Real production screenshots after Phase 1 showed three remaining failures:

1. Task Details root/layout still carried hardcoded `dir="ltr"` even when the task UI was Arabic RTL.
2. The Description rich-text toolbar clipped controls at the physical left edge and produced broken/vertical-looking toolbar content.
3. Assignee and More Details surfaces still visually covered task content even though their dimensions were bounded.

R1 fixes those root causes rather than adding another z-index-only patch.

## Exact source changes
`frontend/src/components/ProfessionalTaskBoard.jsx`

- Task Details root: `dir="ltr"` -> `dir={modalDirection}`.
- Task Details layout wrapper: `dir="ltr"` -> `dir={modalDirection}`.
- Assignee popup geometry estimate: max height reduced from 480 to 300 so the popup stays in the reserved Hero lane at common desktop viewports.
- Import one standalone R1 CSS file so Vite preserves the `:has()` rules and runtime marker.

No task/business logic is changed.

## CSS outcome

### RTL
- Arabic Task Details receives a real RTL root direction.
- Primary tabs read in RTL order.
- Main content, Description, right rail and advanced rail inherit Arabic direction correctly.
- Physical desktop workspace geometry remains intentionally stable.

### Description
- Decluttered toolbar wraps groups instead of clipping them.
- No vertical-looking or half-hidden toolbar controls.
- Editor text uses logical `start` alignment and inherits RTL.
- Empty Description is reduced to a more practical minimum height.

### Assignee
- Popup height is capped.
- User list scrolls internally.
- While the popup is open, the Hero reserves vertical space so Tabs/Description move down instead of being covered.

### More Details
- The legacy advanced side rail is no longer `position: fixed`.
- It consumes real layout width on desktop and returns to normal flow on narrow screens.
- It must not float over Task Progress or Description.

## Frozen / unchanged
- Backend
- Database
- API
- Authentication
- Permissions
- Task workflow/business rules
- `taskBoardParts.jsx`
- `App.jsx`
- Chat System / TCS
- Ramzy
- Comments logic
- Attachments logic
- Timer logic
- Status/Priority business logic

## Apply

```bash
python3 \
  /var/www/TOS-Patchs/TOS-UXUI-TASK-DETAILS-V2-12-PHASE1-R1-RTL-DESCRIPTION-ZERO-OVERLAP-FIX/apply_tos_task_details_v2_12_phase1_r1_rtl_description_zero_overlap_fix.py \
  /var/www/TOS
```

## QA policy
OpenHands must NOT use a browser, take screenshots, or perform visual QA.
Its responsibility ends at patch/build/deploy/technical verification.
Manual visual QA is performed separately by the user + ChatGPT.

NO_BROWSER_QA=YES
NO_SCREENSHOTS=YES
PUSH=NO
