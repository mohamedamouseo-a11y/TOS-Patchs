#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
MARKER = "RAMZY_ADMIN_SETTINGS_ACCESS_V1"

ROUTES_REL = "backend/src/routes/agent.routes.js"
SETTINGS_PAGE_REL = "frontend/src/pages/SettingsPage.jsx"
RAMZY_SETTINGS_REL = "frontend/src/components/RamzySettingsAdmin.jsx"
TEST_REL = "backend/src/agency-operator/tests/ramzyAdminSettingsAccessPhase16Repair.test.js"


def fail(reason):
    raise SystemExit(f"RAMZY_ADMIN_SETTINGS_ACCESS_PATCH_ERROR={reason}")


def read(rel):
    path = ROOT / rel
    if not path.exists():
        fail(f"MISSING_FILE:{rel}")
    return path.read_text(encoding="utf-8")


def write(rel, text):
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        fail(f"{label}_COUNT_{count}")
    return text.replace(old, new, 1)


routes = read(ROUTES_REL)
routes = replace_once(
    routes,
    'router.get("/settings", requireRole("SUPER_ADMIN"), asyncHandler(async (_req, res) => {',
    'router.get("/settings", requireRole("SUPER_ADMIN", "ADMIN"), asyncHandler(async (_req, res) => {',
    "SETTINGS_GET_ROLE",
)
routes = replace_once(
    routes,
    'router.patch("/settings", requireRole("SUPER_ADMIN"), asyncHandler(async (req, res) => {',
    'router.patch("/settings", requireRole("SUPER_ADMIN", "ADMIN"), asyncHandler(async (req, res) => {',
    "SETTINGS_PATCH_ROLE",
)
routes = routes.replace(
    'عطّل Read-only من إعدادات Super Admin للتنفيذ.',
    'عطّل Read-only من إعدادات رمزي للتنفيذ.',
)
routes = routes.replace(
    'تنفيذ إجراءات رمزي متوقف من إعدادات Super Admin',
    'تنفيذ إجراءات رمزي متوقف من إعدادات رمزي',
)
if 'router.get("/audit", requireRole("SUPER_ADMIN")' not in routes:
    fail("AUDIT_SUPER_ADMIN_BOUNDARY_MISSING")
write(ROUTES_REL, routes)

settings_page = read(SETTINGS_PAGE_REL)
settings_page = replace_once(
    settings_page,
    'const ADMIN_SETTINGS_SECTION_KEYS = new Set(["identity", "operations"]);',
    'const ADMIN_SETTINGS_SECTION_KEYS = new Set(["identity", "operations", "ramzy"]);',
    "ADMIN_SETTINGS_SECTION_KEYS",
)
write(SETTINGS_PAGE_REL, settings_page)

ramzy_settings = read(RAMZY_SETTINGS_REL)
ramzy_settings = replace_once(
    ramzy_settings,
    '      const [data, auditData] = await Promise.all([api.agent.settings(), api.agent.audit().catch(() => null)]);',
    '      const auditRequest = user?.role === "SUPER_ADMIN" ? api.agent.audit().catch(() => null) : Promise.resolve(null);\n      const [data, auditData] = await Promise.all([api.agent.settings(), auditRequest]);',
    "ADMIN_AUDIT_REQUEST_SPLIT",
)
ramzy_settings = replace_once(
    ramzy_settings,
    '  useEffect(() => { if (user?.role === "SUPER_ADMIN") load(); }, [user?.role]);',
    '  useEffect(() => { if (["SUPER_ADMIN", "ADMIN"].includes(user?.role)) load(); }, [user?.role]);',
    "ADMIN_LOAD_EFFECT",
)
ramzy_settings = replace_once(
    ramzy_settings,
    '  if (user?.role !== "SUPER_ADMIN") return null;',
    '  if (!["SUPER_ADMIN", "ADMIN"].includes(user?.role)) return null;',
    "ADMIN_RENDER_BOUNDARY",
)
write(RAMZY_SETTINGS_REL, ramzy_settings)

TEST = r'''import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const here = path.dirname(fileURLToPath(import.meta.url));
const backendSrc = path.resolve(here, "../..");
const repoRoot = path.resolve(backendSrc, "../..");
const readBackend = (relative) => readFile(path.join(backendSrc, relative), "utf8");
const readRepo = (relative) => readFile(path.join(repoRoot, relative), "utf8");

test("Ramzy settings GET and PATCH are available to ADMIN and SUPER_ADMIN", async () => {
  const routes = await readBackend("routes/agent.routes.js");
  assert.match(routes, /router\.get\("\/settings", requireRole\("SUPER_ADMIN", "ADMIN"\)/);
  assert.match(routes, /router\.patch\("\/settings", requireRole\("SUPER_ADMIN", "ADMIN"\)/);
});

test("Ramzy audit remains SUPER_ADMIN-only", async () => {
  const routes = await readBackend("routes/agent.routes.js");
  assert.match(routes, /router\.get\("\/audit", requireRole\("SUPER_ADMIN"\)/);
  assert.doesNotMatch(routes, /router\.get\("\/audit", requireRole\("SUPER_ADMIN", "ADMIN"\)/);
});

test("ADMIN Settings navigation exposes the Ramzy section", async () => {
  const page = await readRepo("frontend/src/pages/SettingsPage.jsx");
  assert.match(page, /ADMIN_SETTINGS_SECTION_KEYS = new Set\(\["identity", "operations", "ramzy"\]\)/);
});

test("RamzySettingsAdmin loads and renders for ADMIN without requesting full audit", async () => {
  const component = await readRepo("frontend/src/components/RamzySettingsAdmin.jsx");
  assert.match(component, /\["SUPER_ADMIN", "ADMIN"\]\.includes\(user\?\.role\)/);
  assert.match(component, /user\?\.role === "SUPER_ADMIN" \? api\.agent\.audit/);
  assert.match(component, /Promise\.resolve\(null\)/);
  assert.doesNotMatch(component, /if \(user\?\.role !== "SUPER_ADMIN"\) return null/);
});

test("Phase 16 security boundaries remain intact while ADMIN can manage Ramzy settings", async () => {
  const hardening = await readBackend("agency-operator/services/ramzyProductionHardening.service.js");
  const voice = await readBackend("agency-operator/services/ramzyVoice.service.js");
  const tools = await readBackend("agency-operator/tools/createRamzyTools.js");
  assert.match(hardening, /RAMZY_VOICE_ACTION_PRODUCTION_HARDENING_V1/);
  assert.match(hardening, /publicTargetIdsExposed: false/);
  assert.match(voice, /actionExecutionFromVoice:\s*false/);
  assert.match(tools, /assertRamzyToolInvocationScope/);
});
'''
write(TEST_REL, TEST)

print("RAMZY_ADMIN_SETTINGS_ACCESS_PATCH=PASS")
print(f"MARKER={MARKER}")
print("ADMIN_RAMZY_SETTINGS=ENABLED")
print("SUPER_ADMIN_AUDIT_BOUNDARY=PRESERVED")
