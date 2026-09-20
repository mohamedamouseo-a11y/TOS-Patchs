# TOS PERMISSIONS — AUDIT & I18N FIX V1
# Effective-access truthfulness + English localization cleanup

Baseline:
`17380028e1e94a639dfe2be69c16f01087c47376`

Goal:
Audit the existing permissions UX against actual TOS authorization behavior, fix confirmed misleading role copy, and remove Arabic leakage from English permissions-related UI.

Keep this focused.
Do NOT redesign the permissions engine.
Do NOT change Ramzy role matrix values.
Do NOT weaken project/workspace/task RBAC.
Do NOT change unrelated pages.

---

## 1) Confirmed audit findings to fix

### A. Permissions role-summary copy is currently misleading

Current `PermissionsPage.jsx` static role meta does not exactly match backend access rules.

Confirmed examples:

- ADMIN currently says "selected departments and projects", but backend `hasSystemWideProjectAccess()` treats ADMIN and SUPER_ADMIN as system-wide project access; `resolveProjectAccess()` returns OWNER-equivalent global project access for ADMIN.

- MANAGER currently says "own department only", but actual project access may come from:
  - managed department scope,
  - explicit project membership,
  - projectManagerId/teamLeadId direct assignment.
  A MANAGER with no managed department does not automatically own a department scope.

- TEAM_MEMBER currently says "assigned tasks only", but a TEAM_MEMBER may have project membership and existing project/member work permissions; task access is not accurately described by that absolute phrase.

- PROJECT_MANAGER access is primarily assigned/project membership/direct project role, not a generic company-wide project authority.

Fix role summary text so it describes the actual layered model, not an oversimplified absolute.

Recommended wording:

SUPER_ADMIN
AR scope: `كل النظام وكل المشاريع`
EN scope: `Entire system and all projects`
AR usage: `تحكم كامل، مع استثناءات الأمان المحجوزة حيث يحددها النظام`
EN usage: `Full system control, subject to explicit reserved safety rules`

ADMIN
AR scope: `وصول إداري عام للمشاريع + صلاحيات النظام المفعلة`
EN scope: `System-wide project access + enabled system permissions`
AR usage: `إدارة المشاريع عالميًا، وباقي الوحدات حسب Permission Matrix`
EN usage: `Global project administration; other modules follow the Permission Matrix`

MANAGER
AR scope: `الأقسام التي يديرها + المشاريع المعين عليها أو المشترك بها`
EN scope: `Managed departments + assigned/member projects`
AR usage: `صلاحياته الفعلية تجمع الدور العام مع نطاق القسم/المشروع`
EN usage: `Effective access combines system role with department/project scope`

PROJECT_MANAGER
AR scope: `المشاريع المعين عليها أو المشترك بها`
EN scope: `Assigned/member projects`
AR usage: `إدارة العمل داخل نطاق المشروع حسب دوره داخل المشروع`
EN usage: `Manages work within project scope according to project role`

TEAM_MEMBER
AR scope: `المشاريع والبوردات والمهام المسموح بها ضمن عضويته`
EN scope: `Projects, boards, and tasks available through membership`
AR usage: `تنفيذ العمل والتعاون داخل النطاق المسموح، وليس وصولًا إداريًا عامًا`
EN usage: `Executes and collaborates within allowed scope; no general administrative access`

Do not claim permissions that code does not provide.

---

## 2) Make layered permission semantics explicit in UI

Add one concise notice near Permission Matrix:

AR:
`مهم: بعض صلاحيات المشاريع لها مساران للوصول: صلاحية عامة أو عضوية/دور داخل المشروع. إيقاف الصلاحية العامة لا يلغي تلقائيًا صلاحية ناتجة عن عضوية المشروع.`

EN:
`Important: some project permissions have two access paths: a global permission or project membership/role. Disabling the global permission does not automatically remove access granted by project membership.`

This is required because current backend intentionally uses project scope/role for many project operations rather than the global permission toggle alone.

Do NOT change that authorization model in this patch.

---

## 3) Targeted permission enforcement audit

Audit every current `PERMISSION_DEFINITIONS` key and classify it as one of:

- GLOBAL_GATE
- SCOPED_OR_GLOBAL
- SCOPED_ONLY / contextual
- RESERVED / hard-role constrained
- RAMZY_ADDITIVE_GATE

At minimum verify these known paths:

- users.manage
- clients.manage
- projects.view
- projects.create
- projects.manage
- workspaces.manage
- boards.manage
- tasks.manage
- design_queue.assign
- files.upload
- tws.manage
- chat.use
- reports.view
- performance.view_self
- performance.view_team
- performance.view_all
- sla.policies.manage
- all ramzy.* granular keys

Important:
Do NOT force all project permissions through a single global switch.
Preserve existing project membership/role behavior.

Only fix a backend authorization defect if the current code contradicts the documented intended semantics or creates a privilege bypass.

Create a concise developer audit artifact in repo, e.g.
`backend/src/services/permissions.audit.md`
or a test fixture/commented matrix that records:
permission key -> enforcement model -> main backend gate(s).

Prefer tests over documentation-only where practical.

---

## 4) English localization — use permission KEY, not Arabic label

Current `PermissionsPage.jsx` translates by matching Arabic `permission.label`.
This is fragile and incomplete.

Replace with a key-based frontend copy map, e.g.:

```js
const PERMISSION_COPY = {
  "users.manage": { ar: { label, description }, en: { label, description } },
  ...
}
```

Cover EVERY permission key returned by `PERMISSION_DEFINITIONS`, including:

- sla.policies.manage
- ramzy.use
- ramzy.tasks.create
- ramzy.tasks.comment
- ramzy.tasks.checklist
- ramzy.tasks.change_due
- ramzy.tasks.assign
- ramzy.tasks.multi_step
- ramzy.analytics.team
- ramzy.settings.manage
- ramzy.execute_actions

For unknown future keys:
- EN fallback should prefer key/humanized key, NOT Arabic backend text.
- AR may use backend label/description fallback.

Create helpers:
- `permissionUiLabel(permission, lang)`
- `permissionUiDescription(permission, lang)`

Use them everywhere on PermissionsPage.

Specifically replace:
`<small>{permission.description}</small>`
inside Ramzy matrix with localized description helper.

English page must not display Arabic permission labels/descriptions.

---

## 5) PermissionsPage English leak audit

With language = English, inspect ALL visible text in `PermissionsPage.jsx`.

No Arabic text may appear in rendered English UI, except:
- user-entered data,
- project/user names,
- backend error text that has no translated API error mapping (do not broaden this patch for all backend errors).

Fix all static permissions-page leaks.

Known likely leak:
- Ramzy labels/descriptions from backend Arabic catalog.

Also ensure `sla.policies.manage` has English label.

---

## 6) TeamPage permissions-related English leak audit

Audit the permissions/role explanation area in:
`frontend/src/pages/TeamPage.jsx`

Confirmed issue:
`RolePermissionCards` currently hardcodes Arabic headings/descriptions and uses Arabic role/project labels even when English is selected.

Make this block language-aware using existing:
- currentTeamLang / teamText
- SYSTEM_ROLE_HINTS_AR / SYSTEM_ROLE_HINTS_EN
- PROJECT_ROLE_LABELS_AR / PROJECT_ROLE_LABELS_EN
- PROJECT_ROLE_HINTS_AR / PROJECT_ROLE_HINTS_EN

Required English translations for the two card headers/descriptions.

Do NOT refactor unrelated TeamPage UI.

If there are other permissions-related Arabic literals rendered in English mode in this same section, fix them.

---

## 7) UI must reflect LIVE matrix, not hardcoded permission claims

Role overview cards should NOT imply their short copy is the exact current grant list.

Add a compact count based on `matrix.rolePermissions` where useful:
- enabled global permissions count
- enabled Ramzy action count

But do not add visual clutter.

The detailed Permission Matrix remains the authoritative role-wide toggle view.

Project membership/role remains a separate access layer.

---

## 8) Tests / audit checks

Add focused checks:

1. Permission copy map covers every current backend permission key.
2. English permission label helper returns no Arabic-script characters for every known permission.
3. English permission description helper returns no Arabic-script characters for every known permission.
4. Ramzy English matrix uses localized label + description.
5. SLA permission English label exists.
6. Permissions generic matrix still excludes `ramzy.*` duplicates.
7. Role summary copy matches backend scope model:
   - ADMIN is global project access.
   - MANAGER is not described as automatically department-only.
   - TEAM_MEMBER is not described as assigned-tasks-only.
8. TeamPage RolePermissionCards English mode does not use Arabic role/project explanatory copy.
9. Existing backend permission/RBAC tests pass.
10. Existing Ramzy permission tests pass.

No DB migration expected.

---

## 9) Live QA

As SUPER_ADMIN:

Arabic:
- /permissions role cards read correctly.
- Permission Matrix toggles unchanged.
- Ramzy section unchanged functionally.

English:
- /permissions has no Arabic static permission text.
- Ramzy labels/descriptions are English.
- SLA permission is English.
- role summary is English and accurate.
- Team page role/permission explainer is English.

Behavior:
- do one representative scoped project check for MANAGER/PROJECT_MANAGER/TEAM_MEMBER.
- confirm membership-based project access still works.
- confirm no privilege expansion.

Frontend build.
Backend tests only if backend/tests/docs changed.
Atomic frontend deploy if frontend changed.
Commit + push.

---

## Return ONLY

```
PATCH=TOS-PERMISSIONS-AUDIT-I18N-V1
PASS/FAIL=
ROLE_COPY_AUDIT=PASS/FAIL
PERMISSION_ENFORCEMENT_AUDIT=PASS/FAIL
LAYERED_ACCESS_COPY=PASS/FAIL
PERMISSION_KEY_I18N=PASS/FAIL
RAMZY_ENGLISH=PASS/FAIL
SLA_ENGLISH=PASS/FAIL
PERMISSIONS_PAGE_ENGLISH=PASS/FAIL
TEAM_PERMISSION_ENGLISH=PASS/FAIL
PROJECT_SCOPE_SEMANTICS_PRESERVED=PASS/FAIL
NO_PRIVILEGE_EXPANSION=PASS/FAIL
BACKEND_TEST=PASS/FAIL/NOT_NEEDED
FRONTEND_BUILD=PASS/FAIL
LIVE_AR_QA=PASS/FAIL
LIVE_EN_QA=PASS/FAIL
LIVE_DEPLOY=PASS/FAIL
DB_MIGRATION=NO/YES
COMMIT=
PUSH=YES/NO
ERROR=
```
