#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")

checks = {
    "backend/src/routes/agent.routes.js": [
        'router.get("/settings", requireRole("SUPER_ADMIN", "ADMIN")',
        'router.patch("/settings", requireRole("SUPER_ADMIN", "ADMIN")',
        'router.get("/audit", requireRole("SUPER_ADMIN")',
    ],
    "frontend/src/pages/SettingsPage.jsx": [
        'ADMIN_SETTINGS_SECTION_KEYS = new Set(["identity", "operations", "ramzy"])',
    ],
    "frontend/src/components/RamzySettingsAdmin.jsx": [
        '["SUPER_ADMIN", "ADMIN"].includes(user?.role)',
        'user?.role === "SUPER_ADMIN" ? api.agent.audit',
    ],
    "backend/src/agency-operator/services/ramzyProductionHardening.service.js": [
        "RAMZY_VOICE_ACTION_PRODUCTION_HARDENING_V1",
    ],
    "backend/src/agency-operator/tests/ramzyAdminSettingsAccessPhase16Repair.test.js": [
        "Ramzy settings GET and PATCH are available to ADMIN and SUPER_ADMIN",
        "Ramzy audit remains SUPER_ADMIN-only",
    ],
}

for rel, needles in checks.items():
    path = ROOT / rel
    if not path.exists():
        raise SystemExit(f"AUTH_BOUNDARY_REPAIR_ERROR=MISSING:{rel}")
    text = path.read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"AUTH_BOUNDARY_REPAIR_ERROR=MISSING_CONTRACT:{rel}:{needle}")

print("PHASE16_ADMIN_SETTINGS_SOURCE_STATE=PASS")
print("ADMIN_SETTINGS_API_GUARD=ADMIN_PLUS_SUPER_ADMIN")
print("SUPER_ADMIN_AUDIT_BOUNDARY=PRESERVED")
print("SOURCE_CHANGES_REQUIRED=NO")
