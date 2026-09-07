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
        raise SystemExit(f"V3_SOURCE_VALIDATION_FAIL=MISSING:{rel}")
    text = path.read_text(encoding="utf-8")
    for needle in needles:
        if needle not in text:
            raise SystemExit(f"V3_SOURCE_VALIDATION_FAIL=MISSING_CONTRACT:{rel}:{needle}")

csrf = ROOT / "backend/src/middleware/csrf.js"
if not csrf.exists():
    raise SystemExit("V3_SOURCE_VALIDATION_FAIL=MISSING:backend/src/middleware/csrf.js")
csrf_text = csrf.read_text(encoding="utf-8")
for needle in [
    'const SAFE_METHODS = new Set(["GET", "HEAD", "OPTIONS"])',
    'return next(new AppError("Invalid CSRF token", 403))',
    'const cookieToken = readCookieFromHeader(req.headers.cookie, CSRF_COOKIE_NAME)',
    'const headerToken = req.headers[CSRF_HEADER_NAME]',
]:
    if needle not in csrf_text:
        raise SystemExit(f"V3_SOURCE_VALIDATION_FAIL=CSRF_CONTRACT_MISSING:{needle}")

app = ROOT / "backend/src/app.js"
app_text = app.read_text(encoding="utf-8")
if "app.use(csrfMiddleware);" not in app_text:
    raise SystemExit("V3_SOURCE_VALIDATION_FAIL=CSRF_MIDDLEWARE_NOT_GLOBAL")

print("PHASE16_ADMIN_SETTINGS_SOURCE_STATE=PASS")
print("ADMIN_SETTINGS_API_GUARD=ADMIN_PLUS_SUPER_ADMIN")
print("SUPER_ADMIN_AUDIT_BOUNDARY=PRESERVED")
print("CSRF_PRE_AUTH_BOUNDARY=CONFIRMED")
print("SOURCE_CHANGES_REQUIRED=NO")
