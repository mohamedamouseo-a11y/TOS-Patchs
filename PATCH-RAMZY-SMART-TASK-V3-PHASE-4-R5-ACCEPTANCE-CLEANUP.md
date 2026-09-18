# PATCH-RAMZY-SMART-TASK-V3-PHASE-4-R5-ACCEPTANCE-CLEANUP

Baseline: fe4b5c44ae95d5d785ca9cddef7580c3ccf757a4

Fix only:
- reuse existing top-level assertAgentTaskCreateAccess import; remove redundant dynamic import
- assignee empty option:
  - no project: "Select a project first" / "اختر المشروع أولاً"
  - project selected: "Select..." / "اختر..."
- assignee endpoint return available display metadata from current schema: id, name, department, role
- assignee option display: name + department when present; otherwise name + role when useful
- keep exact assigneeId, AUTO/NONE, project-scoped authorization, loading/error, approval/RBAC unchanged

No Phase 5+ changes.
Build + commit only. Do not push.
