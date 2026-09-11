# TOS Task Details Canonical Reference V2.3

## Patch
`TOS-UXUI-TASK-DETAILS-CANONICAL-REFERENCE-V2-3-INTERNAL-HERO-GRID-FIDELITY`

## Purpose
Visual-fidelity correction after V2.2 successfully fixed the outer App Shell / RTL structural geometry.

V2.3 MUST NOT modify the App Shell. It only corrects the internal Task Details composition confirmed by the V2.2 visual QA recording and screenshot.

## Scope
- Compact the oversized Hero to the canonical desktop proportion.
- Keep Mountain / Quote and Task identity composition intact.
- Force the existing Hero controls into one four-column row:
  - Assignees
  - Status
  - Priority
  - Due date
- Preserve the existing primary tabs and their order:
  - Overview
  - Checklist
  - Attachments
  - Activity
  - Subtasks
- Keep Description / Rich Text Editor in the main left column.
- Align the existing Right Rail with the Overview body rather than the Hero.
- Right Rail content remains:
  - Quick actions
  - Task information
  - Tags
  - TCS Assistant
- Keep the global floating TCS launcher unchanged.

## Explicitly Out of Scope
- Sidebar geometry
- App Frame direction
- Topbar direction/order
- Breadcrumb / action-row structural geometry
- V2.2 Structural LTR lock
- Arabic text direction behavior
- Backend
- Database
- API contracts
- Permissions
- Task business logic
- Upload logic
- TWS internals
- Ramzy
- TCS logic

## Runtime predecessor requirements
The installer requires the live canonical stylesheet to contain:
- Canonical V2 runtime marker
- V2.1 RTL structural geometry runtime marker
- V2.2 App Shell + Canonical Grid Lock runtime marker

The Task Details source must still contain the V2.2 `data-content-dir={modalDirection}` marker.

## Canonical QA viewport
`1664x936`

## Expected success state
- Technical PASS
- V2.2 App Shell preserved
- Hero compact
- Four controls in one row
- Overview two-column placement restored
- Right Rail starts with Overview body
- No push until ChatGPT visual QA of the new Google Drive screenshot
