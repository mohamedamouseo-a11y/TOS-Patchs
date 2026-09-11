# TOS Task Details V2.11C

VERSION=TOS_TASK_DETAILS_V2_11C
MICRO_STEP=PRIMARY_TABS_ONLY
BASELINE_CHAIN=TOS_TASK_DETAILS_V2_11B3

Scope is intentionally limited to the five canonical primary Task Details tabs:

1. Overview
2. Checklist
3. Attachments
4. Activity
5. Subtasks

Visual target: a clean premium tab rail with balanced spacing, clear active state, restrained amber treatment, consistent icons/count badges, and no content/layout changes.

Frozen and out of scope: Hero shell and identity, all four Hero controls and B1/B2/B3 custom popovers, Description/Editor, tab contents, Right Rail, Ramzy AI Assistant, TCS System Chat, APIs, DB, permissions, task business logic, uploads, TWS, More/advanced actions.

Ramzy = AI Assistant. TCS = System Chat.

This patch is CSS-only and must keep ProfessionalTaskBoard.jsx byte-identical.
