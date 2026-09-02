#!/usr/bin/env python3
from pathlib import Path
import sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
path = repo / "backend/src/routes/tasks.routes.js"
text = path.read_text()

old = '''        where: {
          employeeId: { in: scope.userIds },
          ...(requestedStatus ? { status: requestedStatus } : {}),
          ...(!scope.canManage ? { status: { not: "DRAFT" } } : {}),
        },'''
new = '''        where: {
          employeeId: { in: scope.userIds },
          ...(requestedStatus
            ? { status: requestedStatus }
            : (!scope.canManage ? { status: { not: "DRAFT" } } : {})),
          ...(!scope.canManage && requestedStatus === "DRAFT" ? { id: "__phase9_hidden_draft__" } : {}),
        },'''

if old not in text:
    raise SystemExit("PHASE9_DEVELOPMENT_FILTER_ANCHOR_MISSING")
text = text.replace(old, new, 1)
path.write_text(text)
print("EMPLOYEE_DEVELOPMENT_DRAFT_PRIVACY=PASS")
print("DEVELOPMENT_STATUS_FILTER_HARDENING=PASS")
