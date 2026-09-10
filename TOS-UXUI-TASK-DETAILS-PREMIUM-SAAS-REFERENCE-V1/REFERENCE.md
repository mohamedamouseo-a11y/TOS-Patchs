# Task Details Premium SaaS Reference V1

This patch locks the user's latest approved Task Details design as the canonical visual source of truth for this screen until the user explicitly replaces it.

- Canonical repository reference: `reference/premium_saas_task_details_dashboard.webp`
- Original design filename: `premium_saas_task_details_dashboard.png`
- Canonical viewport: `1664 × 936`
- Original PNG SHA256: `4c00a8fa806c7a6d5dfd110282f3a0e581a88a98c8287624e8657173722b6a33`
- Repository WebP SHA256: `298021973b60db7575fc3ef33ee3b58701af3ff8f9d21df732eccac237dbfb5b`
- Reference status: **LOCKED**

## Fidelity acceptance order

1. Preserve the TOS app shell: desktop sidebar `272px` (`88px` collapsed) and topbar `72px` remain visible.
2. Match the Task Details header: document identity, breadcrumb, Archive Card action, previous/next navigation and counter.
3. Match the hero summary geometry: task icon/title/subtitle plus exactly three primary cards for Quick status, Priority and Due date.
4. Match the tab/action rail: Task details, Subtasks, Attachments, Activity, Checklist, then More actions and Mark as complete.
5. Match Description card/editor hierarchy, radius, spacing, toolbar density and editor height.
6. Light mode is compared directly to the canonical image for geometry, spacing, typography, ivory/cream surfaces, navy ink and restrained champagne/gold accent.
7. Dark mode must preserve the same geometry while translating the material treatment to Obsidian/Titanium/Platinum/Champagne with strong contrast and no white bands.
8. Functional controls must reuse existing Task Details behavior. APIs, database/data contracts, permissions and business logic must not be changed for visual fidelity.
9. TWS internals are out of scope. Ramzy and TCS are out of scope.

## Permanent QA rule

For every future Task Details UX/UI patch, use this file and the canonical reference image as the visual source of truth. Compare the current screenshot against the reference at the same viewport in this order: macro layout → spacing → typography → card geometry → controls → gold accents → editor → dark-mode translation.

Do not approve **Final Visual PASS** while a material mismatch remains visible. Any replacement of this reference requires an explicit user instruction that a newer design becomes the canonical reference.
