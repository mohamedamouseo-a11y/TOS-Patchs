# TOS Task Details Canonical Reference V2

Patch entrypoint:
`apply_tos_uxui_task_details_canonical_reference_v2.py`

This patch is based on the user-confirmed 1664×936 Task Details reference and supersedes the prior V1 visual target.

Integrity:
- Packed installer payload SHA256: `f33ed08eae7a0a269452cb867b9b375490b7573e7331cb4620c42c6882960911`
- Unpacked installer source SHA256: `6eb2b543f5be818445e4c868c56e9a0dfa52f7e652be36c636e117f0370ce864`
- Canonical original PNG SHA256: `27e4d6442e0855f86cd62db169fae0d122a664b1ba10e294b6e35e31b4294b80`

Required predecessor runtime markers:
- V1 Premium SaaS Reference
- V1.2 Shell Geometry
- V1.3 Macro Layout Fidelity
- V1.4 Hero/Tabs/Editor Fidelity

V2 target:
- reference-style search/profile topbar
- breadcrumb + Back / More / Archive Card / Save changes row
- hero with task title/subtitle, mountain treatment and quote
- four controls: Assignees / Status / Priority / Due date
- tabs: Overview / Checklist / Attachments / Activity / Subtasks
- Overview two-column body: Description editor + right rail
- right rail: Quick actions / Task information / Tags / TCS Assistant
- no API, database, permission, or task-business-logic contract changes
- Duplicate task and Ask TCS remain visually represented but disabled because no existing verified Task Details action was found for those two controls

Success state:
`STATUS=READY_FOR_VISUAL_QA`

Do not push TOS before visual QA against the locked V2 reference.