#!/usr/bin/env python3
from pathlib import Path
import sys

BASELINE = "f6b6f60b57d702e62ed488eca7265bfcde0ca601"
MARKER = "RAMZY_EXECUTION_CONTROL_V1"
ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")

PERMISSIONS = ROOT / "backend/src/services/permissions.service.js"
SETTINGS_SERVICE = ROOT / "backend/src/agency-operator/services/agentSettings.service.js"
EXECUTION_SERVICE = ROOT / "backend/src/agency-operator/services/ramzyExecutionControl.service.js"
TASK_COMMANDS = ROOT / "backend/src/agency-operator/services/taskCommands.service.js"
AGENT_ROUTES = ROOT / "backend/src/routes/agent.routes.js"
TEST = ROOT / "backend/src/agency-operator/tests/ramzyExecutionControlPhase16.test.js"
RAMZY_SETTINGS = ROOT / "frontend/src/components/RamzySettingsAdmin.jsx"
RAMZY_ASSISTANT = ROOT / "frontend/src/components/RamzyAssistant.jsx"
RAMZY_CSS = ROOT / "frontend/src/components/ramzyExecutionControlV1.css"
PERMISSIONS_PAGE = ROOT / "frontend/src/pages/PermissionsPage.jsx"


def fail(reason):
    raise SystemExit(f"RAMZY_EXECUTION_CONTROL_PATCH_ERROR={reason}")


def read(path):
    if not path.exists():
        fail(f"MISSING:{path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        fail(f"{label}_COUNT_{count}")
    return text.replace(old, new, 1)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


for new_path in [EXECUTION_SERVICE, TEST, RAMZY_CSS]:
    if new_path.exists():
        fail(f"NEW_FILE_ALREADY_EXISTS:{new_path.relative_to(ROOT)}")

# 1) Dynamic permission catalog: Super Admin always true; Admin default true; other roles default false.
text = read(PERMISSIONS)
permission_anchor = '  { key: "sla.policies.manage", label: "إدارة سياسات SLA", category: "Reports", description: "إنشاء وتعديل وإيقاف سياسات SLA وساعات العمل والتصعيد." },\n'
permission_new = permission_anchor + '  { key: "ramzy.execute_actions", label: "تشغيل إجراءات رمزي", category: "AI & Automation", description: "السماح بتنفيذ إجراءات رمزي بعد الموافقة، مع بقاء صلاحيات TOS الأصلية وإعادة فحص RBAC وقت التنفيذ." },\n'
text = replace_once(text, permission_anchor, permission_new, "PERMISSION_DEFINITION")
admin_anchor = '    "performance.view_team",\n    "sla.policies.manage",\n'
admin_new = '    "performance.view_team",\n    "sla.policies.manage",\n    "ramzy.execute_actions",\n'
text = replace_once(text, admin_anchor, admin_new, "ADMIN_DEFAULT_PERMISSION")
write(PERMISSIONS, text)

# 2) Reinterpret legacy readOnlyMode as an emergency kill switch. New deployments default unlocked.
text = read(SETTINGS_SERVICE)
text = replace_once(
    text,
    '    readOnlyMode: envBoolean("RAMZY_READ_ONLY_MODE", true),',
    '    readOnlyMode: envBoolean("RAMZY_EMERGENCY_LOCK", envBoolean("RAMZY_READ_ONLY_MODE", false)),',
    "EMERGENCY_LOCK_DEFAULT",
)
write(SETTINGS_SERVICE, text)

# 3) Central server-side execution control. Permission never replaces task/project RBAC.
execution_service = r'''import { AppError } from "../../middleware/errors.js";
import { hasPermission } from "../../services/permissions.service.js";
import { getAgentSettings } from "./agentSettings.service.js";

export const RAMZY_EXECUTION_CONTROL_VERSION = "RAMZY_EXECUTION_CONTROL_V1";
export const RAMZY_EXECUTE_ACTIONS_PERMISSION = "ramzy.execute_actions";

function roleAllowed(settings, user) {
  const role = String(user?.role || "").trim().toUpperCase();
  return Boolean(role && (settings?.allowedRoles || []).map((item) => String(item || "").trim().toUpperCase()).includes(role));
}

function stateMessage(state) {
  const messages = {
    ENABLED: {
      ar: "التنفيذ متاح بعد الموافقة ووفق صلاحيات TOS الخاصة بك.",
      en: "Execution is available after approval and remains limited by your TOS permissions.",
    },
    EMERGENCY_LOCK: {
      ar: "تنفيذ رمزي متوقف على مستوى النظام بواسطة قفل الطوارئ.",
      en: "Ramzy execution is stopped system-wide by the emergency lock.",
    },
    APPROVALS_DISABLED: {
      ar: "تنفيذ إجراءات رمزي متوقف من إعدادات رمزي.",
      en: "Ramzy action execution is disabled in Ramzy settings.",
    },
    PERMISSION_DENIED: {
      ar: "حسابك لا يملك صلاحية تشغيل إجراءات رمزي. يمكن إدارتها من لوحة الصلاحيات.",
      en: "Your account does not have permission to execute Ramzy actions. It can be managed from the Permissions dashboard.",
    },
    AGENT_DISABLED: {
      ar: "رمزي متوقف حاليًا من إعدادات النظام.",
      en: "Ramzy is currently disabled in system settings.",
    },
    ROLE_NOT_ALLOWED: {
      ar: "دور حسابك غير مفعّل لاستخدام رمزي.",
      en: "Your account role is not enabled to use Ramzy.",
    },
  };
  return messages[state] || messages.PERMISSION_DENIED;
}

export async function resolveRamzyExecutionControl(user, { settings: providedSettings = null } = {}) {
  const settings = providedSettings || await getAgentSettings();
  const agentEnabled = Boolean(settings?.enabled);
  const allowedRole = roleAllowed(settings, user);
  const emergencyLocked = Boolean(settings?.readOnlyMode);
  const approvalActionsEnabled = Boolean(settings?.approvalActionsEnabled);
  const permissionGranted = Boolean(await hasPermission(user, RAMZY_EXECUTE_ACTIONS_PERMISSION));

  let state = "ENABLED";
  if (!agentEnabled) state = "AGENT_DISABLED";
  else if (!allowedRole) state = "ROLE_NOT_ALLOWED";
  else if (emergencyLocked) state = "EMERGENCY_LOCK";
  else if (!approvalActionsEnabled) state = "APPROVALS_DISABLED";
  else if (!permissionGranted) state = "PERMISSION_DENIED";

  const message = stateMessage(state);
  return {
    version: RAMZY_EXECUTION_CONTROL_VERSION,
    permissionKey: RAMZY_EXECUTE_ACTIONS_PERMISSION,
    state,
    canExecute: state === "ENABLED",
    permissionGranted,
    emergencyLocked,
    approvalActionsEnabled,
    agentEnabled,
    roleAllowed: allowedRole,
    messageAr: message.ar,
    messageEn: message.en,
    authorization: "SERVER_SIDE_RBAC_AT_EXECUTION",
  };
}

export async function assertRamzyActionExecutionAllowed(user, { settings: providedSettings = null } = {}) {
  const control = await resolveRamzyExecutionControl(user, { settings: providedSettings });
  if (control.state === "AGENT_DISABLED" || control.state === "ROLE_NOT_ALLOWED") {
    throw new AppError(control.messageAr, 403);
  }
  if (control.state === "EMERGENCY_LOCK" || control.state === "APPROVALS_DISABLED") {
    throw new AppError(control.messageAr, 409);
  }
  if (control.state === "PERMISSION_DENIED") {
    throw new AppError(control.messageAr, 403);
  }
  return control;
}

export function getRamzyExecutionControlConfig() {
  return {
    version: RAMZY_EXECUTION_CONTROL_VERSION,
    executionPermission: RAMZY_EXECUTE_ACTIONS_PERMISSION,
    emergencyLockField: "readOnlyMode",
    emergencyLockManagedBy: "SUPER_ADMIN",
    permissionManagedFrom: "PERMISSIONS_DASHBOARD",
    defaultExecutionRoles: ["SUPER_ADMIN", "ADMIN"],
    executionStillRequiresTosRbac: true,
    voiceAddsPermission: false,
  };
}
'''
write(EXECUTION_SERVICE, execution_service)

# 4) Agent API: expose safe execution state; Admin cannot alter emergency lock; approval execution uses central gate.
text = read(AGENT_ROUTES)
import_anchor = '''import {
  getRamzyProductionHardeningConfig,
  publicRamzyApprovalView,
  publicRamzyApprovalViews,
} from "../agency-operator/services/ramzyProductionHardening.service.js";
'''
import_new = import_anchor + '''import {
  assertRamzyActionExecutionAllowed,
  resolveRamzyExecutionControl,
} from "../agency-operator/services/ramzyExecutionControl.service.js";
'''
text = replace_once(text, import_anchor, import_new, "ROUTE_EXECUTION_CONTROL_IMPORT")
status_anchor = '''router.get("/status", asyncHandler(async (req, res) => {
  const settings = await getAgentSettings();
  const allowed = Boolean(
    settings.enabled
    && (settings.allowedRoles || []).map((role) => String(role).toUpperCase()).includes(String(req.user.role || "").toUpperCase()),
  );
  res.json({
'''
status_new = '''router.get("/status", asyncHandler(async (req, res) => {
  const settings = await getAgentSettings();
  const allowed = Boolean(
    settings.enabled
    && (settings.allowedRoles || []).map((role) => String(role).toUpperCase()).includes(String(req.user.role || "").toUpperCase()),
  );
  const executionControl = await resolveRamzyExecutionControl(req.user, { settings });
  res.json({
'''
text = replace_once(text, status_anchor, status_new, "STATUS_CONTROL_RESOLUTION")
text = replace_once(
    text,
    '    productionHardening: getRamzyProductionHardeningConfig(),\n    settings: publicAgentSettings(settings),',
    '    productionHardening: getRamzyProductionHardeningConfig(),\n    executionControl,\n    settings: publicAgentSettings(settings),',
    "STATUS_CONTROL_PUBLIC",
)
patch_anchor = '''router.patch("/settings", requireRole("SUPER_ADMIN", "ADMIN"), asyncHandler(async (req, res) => {
  try {
    const saved = await updateAgentSettings(req.body || {});
    res.json(publicAgentSettings({ ...saved, source: "DATABASE" }, { admin: true }));
'''
patch_new = '''router.patch("/settings", requireRole("SUPER_ADMIN", "ADMIN"), asyncHandler(async (req, res) => {
  try {
    const input = { ...(req.body || {}) };
    // readOnlyMode is now the system-wide emergency execution lock. ADMIN may
    // manage normal Ramzy settings but only SUPER_ADMIN can change this lock.
    if (req.user.role !== "SUPER_ADMIN") delete input.readOnlyMode;
    const saved = await updateAgentSettings(input);
    res.json(publicAgentSettings({ ...saved, source: "DATABASE" }, { admin: true }));
'''
text = replace_once(text, patch_anchor, patch_new, "ADMIN_EMERGENCY_LOCK_BOUNDARY")
old_guard = '''  if (settings.readOnlyMode) {
    throw new AppError("رمزي يعمل حاليًا بوضع الاقتراحات فقط. عطّل Read-only من إعدادات رمزي للتنفيذ.", 409);
  }
  if (!settings.approvalActionsEnabled) {
    throw new AppError("تنفيذ إجراءات رمزي متوقف من إعدادات رمزي", 409);
  }
'''
new_guard = '''  await assertRamzyActionExecutionAllowed(req.user, { settings });
'''
text = replace_once(text, old_guard, new_guard, "APPROVAL_DECISION_EXECUTION_GATE")
write(AGENT_ROUTES, text)

# 5) Core task execution: permission is checked again at action time, including direct low-risk and multi-step child actions.
text = read(TASK_COMMANDS)
settings_import = 'import { getAgentSettings } from "./agentSettings.service.js";\n'
settings_import_new = settings_import + 'import { assertRamzyActionExecutionAllowed } from "./ramzyExecutionControl.service.js";\n'
text = replace_once(text, settings_import, settings_import_new, "TASK_EXECUTION_CONTROL_IMPORT")
lowrisk_anchor = '''  const settings = await getAgentSettings();
  if (settings.readOnlyMode) throw new AppError("رمزي يعمل في وضع الاقتراحات فقط", 409);
  if (!settings.approvalActionsEnabled) throw new AppError("تنفيذ إجراءات رمزي متوقف", 409);
  const policy = assertLowRiskDirectActionAllowed(approval.actionType, settings);
'''
lowrisk_new = '''  const settings = await getAgentSettings();
  await assertRamzyActionExecutionAllowed(user, { settings });
  const policy = assertLowRiskDirectActionAllowed(approval.actionType, settings);
'''
text = replace_once(text, lowrisk_anchor, lowrisk_new, "LOW_RISK_EXECUTION_GATE")
execute_anchor = '''export async function executeApprovedTaskAction({ approval, user, io }) {
  const actionType = String(approval?.actionType || "").toUpperCase();
  if (!ACTIONS.has(actionType)) throw new AppError("Unsupported approved action", 400);
  const settings = await getAgentSettings();
'''
execute_new = '''export async function executeApprovedTaskAction({ approval, user, io }) {
  const actionType = String(approval?.actionType || "").toUpperCase();
  if (!ACTIONS.has(actionType)) throw new AppError("Unsupported approved action", 400);
  const settings = await getAgentSettings();
  // Final server-side execution gate. This is additive to, never a replacement
  // for, project/task/assignment RBAC enforced below for the concrete action.
  await assertRamzyActionExecutionAllowed(user, { settings });
'''
text = replace_once(text, execute_anchor, execute_new, "FINAL_TASK_EXECUTION_GATE")
write(TASK_COMMANDS, text)

# 6) Admin settings UI: emergency lock is clearly named and read-only for ADMIN.
text = read(RAMZY_SETTINGS)
text = replace_once(
    text,
    '["readOnlyMode", "Read-only + Proposals only"]',
    '["readOnlyMode", ramzyText("قفل طوارئ تنفيذ رمزي — Super Admin فقط", "Ramzy emergency execution lock — Super Admin only")]',
    "SETTINGS_EMERGENCY_LABEL",
)
checkbox_anchor = '<input type="checkbox" checked={Boolean(form[key])} onChange={(e) => patch(key, e.target.checked)} />'
checkbox_new = '<input type="checkbox" checked={Boolean(form[key])} disabled={key === "readOnlyMode" && user?.role !== "SUPER_ADMIN"} onChange={(e) => patch(key, e.target.checked)} />'
text = replace_once(text, checkbox_anchor, checkbox_new, "SETTINGS_EMERGENCY_DISABLED_FOR_ADMIN")
write(RAMZY_SETTINGS, text)

# 7) Permissions dashboard English label for the new dynamic permission.
text = read(PERMISSIONS_PAGE)
label_anchor = '  "إدارة TWS": "Manage TWS",\n'
label_new = label_anchor + '  "تشغيل إجراءات رمزي": "Execute Ramzy actions",\n'
text = replace_once(text, label_anchor, label_new, "PERMISSIONS_EN_LABEL")
write(PERMISSIONS_PAGE, text)

# 8) Ramzy window: show why execution is available/blocked, without granting any permission client-side.
text = read(RAMZY_ASSISTANT)
import_css_anchor = 'import "./ramzyFlagshipV2_3FinalLightLuxe.css";\n'
text = replace_once(text, import_css_anchor, import_css_anchor + 'import "./ramzyExecutionControlV1.css";\n', "RAMZY_CONTROL_CSS_IMPORT")
footer_anchor = '          <footer className="ramzy-composer">\n'
status_block = '''          {status?.executionControl && (
            <div className={`ramzy-execution-control is-${String(status.executionControl.state || "permission_denied").toLowerCase()}`} role="status">
              <span className="ramzy-execution-control-dot" aria-hidden="true" />
              <span className="ramzy-execution-control-copy">
                <b>{status.executionControl.canExecute ? (isEnglish ? "Execution enabled" : "التنفيذ متاح") : (isEnglish ? "Execution unavailable" : "التنفيذ غير متاح")}</b>
                <small>{isEnglish ? status.executionControl.messageEn : status.executionControl.messageAr}</small>
              </span>
            </div>
          )}

'''
text = replace_once(text, footer_anchor, status_block + footer_anchor, "RAMZY_EXECUTION_STATUS_UI")
write(RAMZY_ASSISTANT, text)

css = r'''/* RAMZY_EXECUTION_CONTROL_V1 — status only; authorization remains server-side. */
.ramzy-execution-control {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0 16px 10px;
  padding: 10px 13px;
  border: 1px solid rgba(16,185,129,.18);
  border-radius: 15px;
  background: rgba(236,253,245,.76);
  color: #065f46;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.72);
}
.ramzy-execution-control-dot { width: 9px; height: 9px; border-radius: 999px; background: #10b981; box-shadow: 0 0 0 4px rgba(16,185,129,.10); flex: 0 0 auto; }
.ramzy-execution-control-copy { min-width: 0; display: grid; gap: 2px; }
.ramzy-execution-control-copy b { font-size: 12px; font-weight: 950; }
.ramzy-execution-control-copy small { font-size: 10.5px; line-height: 1.55; font-weight: 750; opacity: .78; }
.ramzy-execution-control.is-emergency_lock,
.ramzy-execution-control.is-approvals_disabled { border-color: rgba(220,38,38,.16); background: rgba(254,242,242,.82); color: #991b1b; }
.ramzy-execution-control.is-emergency_lock .ramzy-execution-control-dot,
.ramzy-execution-control.is-approvals_disabled .ramzy-execution-control-dot { background: #ef4444; box-shadow: 0 0 0 4px rgba(239,68,68,.10); }
.ramzy-execution-control.is-permission_denied,
.ramzy-execution-control.is-role_not_allowed,
.ramzy-execution-control.is-agent_disabled { border-color: rgba(217,119,6,.18); background: rgba(255,251,235,.82); color: #92400e; }
.ramzy-execution-control.is-permission_denied .ramzy-execution-control-dot,
.ramzy-execution-control.is-role_not_allowed .ramzy-execution-control-dot,
.ramzy-execution-control.is-agent_disabled .ramzy-execution-control-dot { background: #f59e0b; box-shadow: 0 0 0 4px rgba(245,158,11,.10); }
html.dark .ramzy-execution-control { background: rgba(6,78,59,.20); border-color: rgba(52,211,153,.18); color: #a7f3d0; }
html.dark .ramzy-execution-control.is-emergency_lock,
html.dark .ramzy-execution-control.is-approvals_disabled { background: rgba(127,29,29,.18); border-color: rgba(248,113,113,.18); color: #fecaca; }
html.dark .ramzy-execution-control.is-permission_denied,
html.dark .ramzy-execution-control.is-role_not_allowed,
html.dark .ramzy-execution-control.is-agent_disabled { background: rgba(120,53,15,.18); border-color: rgba(251,191,36,.18); color: #fde68a; }
'''
write(RAMZY_CSS, css)

# 9) Focused static contracts for the complete design.
test = r'''import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { getRamzyExecutionControlConfig, RAMZY_EXECUTE_ACTIONS_PERMISSION } from "../services/ramzyExecutionControl.service.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const backendSrc = path.resolve(here, "../..");
const repoRoot = path.resolve(backendSrc, "../..");
const readBackend = (relative) => readFile(path.join(backendSrc, relative), "utf8");
const readRepo = (relative) => readFile(path.join(repoRoot, relative), "utf8");

test("Ramzy execution control defines a dedicated dashboard permission with Admin default enabled", async () => {
  const source = await readBackend("services/permissions.service.js");
  assert.equal(RAMZY_EXECUTE_ACTIONS_PERMISSION, "ramzy.execute_actions");
  assert.match(source, /key: "ramzy\.execute_actions"/);
  const adminBlock = source.match(/ADMIN:\s*\[([\s\S]*?)\n\s*\],\n\s*MANAGER:/)?.[1] || "";
  assert.match(adminBlock, /"ramzy\.execute_actions"/);
  const managerBlock = source.match(/MANAGER:\s*\[([^\]]*)\]/)?.[1] || "";
  const projectManagerBlock = source.match(/PROJECT_MANAGER:\s*\[([^\]]*)\]/)?.[1] || "";
  const memberBlock = source.match(/TEAM_MEMBER:\s*\[([^\]]*)\]/)?.[1] || "";
  assert.doesNotMatch(managerBlock, /ramzy\.execute_actions/);
  assert.doesNotMatch(projectManagerBlock, /ramzy\.execute_actions/);
  assert.doesNotMatch(memberBlock, /ramzy\.execute_actions/);
});

test("execution control keeps emergency lock separate from dynamic execution permission", () => {
  const config = getRamzyExecutionControlConfig();
  assert.equal(config.version, "RAMZY_EXECUTION_CONTROL_V1");
  assert.equal(config.emergencyLockManagedBy, "SUPER_ADMIN");
  assert.equal(config.permissionManagedFrom, "PERMISSIONS_DASHBOARD");
  assert.deepEqual(config.defaultExecutionRoles, ["SUPER_ADMIN", "ADMIN"]);
  assert.equal(config.executionStillRequiresTosRbac, true);
  assert.equal(config.voiceAddsPermission, false);
});

test("Admin settings cannot change the emergency lock while Super Admin can", async () => {
  const routes = await readBackend("routes/agent.routes.js");
  const component = await readRepo("frontend/src/components/RamzySettingsAdmin.jsx");
  assert.match(routes, /if \(req\.user\.role !== "SUPER_ADMIN"\) delete input\.readOnlyMode/);
  assert.match(component, /disabled=\{key === "readOnlyMode" && user\?\.role !== "SUPER_ADMIN"\}/);
  assert.match(component, /قفل طوارئ تنفيذ رمزي/);
});

test("approval and final task execution both enforce Ramzy execution permission server-side", async () => {
  const routes = await readBackend("routes/agent.routes.js");
  const commands = await readBackend("agency-operator/services/taskCommands.service.js");
  const control = await readBackend("agency-operator/services/ramzyExecutionControl.service.js");
  assert.match(routes, /assertRamzyActionExecutionAllowed\(req\.user, \{ settings \}\)/);
  assert.match(commands, /await assertRamzyActionExecutionAllowed\(user, \{ settings \}\)/);
  assert.match(control, /hasPermission\(user, RAMZY_EXECUTE_ACTIONS_PERMISSION\)/);
  assert.match(commands, /assertAgentTaskCreateAccess/);
  assert.match(commands, /assertAgentTaskActionAccess/);
  assert.match(commands, /assertAssignmentTarget/);
});

test("Ramzy status exposes safe execution state and UI explains the blocking reason", async () => {
  const routes = await readBackend("routes/agent.routes.js");
  const assistant = await readRepo("frontend/src/components/RamzyAssistant.jsx");
  assert.match(routes, /const executionControl = await resolveRamzyExecutionControl/);
  assert.match(routes, /executionControl,/);
  assert.match(assistant, /status\?\.executionControl/);
  assert.match(assistant, /Execution enabled/);
  assert.match(assistant, /التنفيذ متاح/);
  assert.doesNotMatch(assistant, /ramzy\.execute_actions[^\n]{0,100}(true|false)/);
});

test("legacy read-only default is converted to an emergency-lock compatibility alias without schema changes", async () => {
  const settings = await readBackend("agency-operator/services/agentSettings.service.js");
  const schema = await readRepo("backend/prisma/schema.prisma");
  assert.match(settings, /RAMZY_EMERGENCY_LOCK/);
  assert.match(settings, /RAMZY_READ_ONLY_MODE/);
  assert.match(settings, /envBoolean\("RAMZY_READ_ONLY_MODE", false\)/);
  assert.doesNotMatch(schema, /ramzyExecuteActions|ramzyEmergencyLock/);
});
'''
write(TEST, test)

print("RAMZY_EXECUTION_CONTROL_PATCH=PASS")
print(f"MARKER={MARKER}")
print("PERMISSION=ramzy.execute_actions")
print("DEFAULT_EXECUTION_ROLES=SUPER_ADMIN,ADMIN")
print("EMERGENCY_LOCK=SUPER_ADMIN_ONLY")
print("TOS_RBAC_AT_EXECUTION=PRESERVED")
print("VOICE_PERMISSION=BYPASS_NONE")
