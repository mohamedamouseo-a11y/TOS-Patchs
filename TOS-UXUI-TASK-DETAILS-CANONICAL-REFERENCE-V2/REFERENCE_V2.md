# TOS Task Details — Canonical Reference V2

Status: **LOCKED**

This reference **supersedes Task Details Premium SaaS Reference V1**. The user explicitly confirmed the 1664 × 936 Task Details design shown in the working conversation as the original approved reference.

## Canonical image identity

- Viewport: `1664 × 936`
- Original user PNG SHA256: `27e4d6442e0855f86cd62db169fae0d122a664b1ba10e294b6e35e31b4294b80`
- Reference state: `LOCKED_SUPERSEDES_V1`

## Source-of-truth structure

1. Keep the left TOS sidebar visible.
2. Task Details topbar uses the reference search surface and current-user zone.
3. Breadcrumb/action row contains Home / Tasks / Task details plus Back, More, Archive Card and Save changes.
4. Hero contains task identity, title, subtitle, restrained mountain line-art, the “Better systems build brighter futures.” reference quote, and four controls: Assignees, Status, Priority, Due date.
5. Primary tabs are exactly: `Overview → Checklist → Attachments → Activity → Subtasks`.
6. Overview body is a two-column composition: large Description/rich-editor workspace plus a right rail.
7. Right rail contains: Quick actions, Task information, Tags, TCS Assistant.
8. Existing Task Details behavior must be preserved. Presentation changes must not introduce new API, database, permission or task-business-logic contracts.
9. Duplicate task and Ask TCS must not invent backend behavior when an existing supported Task Details path cannot be verified. Their V2 reference controls stay visually present but disabled until implemented separately.
10. Existing advanced Task Details controls remain accessible through More.
11. Dark mode preserves V2 geometry and changes material/color treatment only.

## QA acceptance order

At `1664 × 936`, compare in this order:

**App shell → topbar → breadcrumb/action row → hero → four controls → primary tabs → two-column body → editor → right rail → spacing → typography → gold accents → dark translation**

Do not approve **Final Visual PASS** while a material mismatch remains visible.

Any future Task Details UX/UI patch must treat this V2 contract and the PNG hash above as the canonical reference until the user explicitly replaces it.
