#!/usr/bin/env python3
from pathlib import Path
import sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
path = repo / "backend/src/routes/tasks.routes.js"
text = path.read_text()

old_access = '''async function assertWorkforceCapacityAccess(req, employeeId) {
  const scope = await getWorkforceScope(req, { requireManage: true });
  if (!scope.userIds.includes(employeeId)) throw new AppError("Unauthorized workforce employee", 403);
  const employee = scope.users.find((user) => user.id === employeeId);
  if (!employee) throw new AppError("Workforce employee not found", 404);
  return { scope, employee };
}'''
new_access = '''async function assertWorkforceCapacityAccess(req, employeeId) {
  const scope = await getWorkforceScope(req, { requireManage: true });
  if (!scope.userIds.includes(employeeId)) {
    if (scope.isAdmin) {
      const rawEmployee = await prisma.user.findUnique({ where: { id: employeeId }, select: { id: true, role: true } });
      if (!rawEmployee) throw new AppError("Workforce employee not found", 404);
      if (["CLIENT", "FORMER_EMPLOYEE"].includes(rawEmployee.role)) throw new AppError("Employee is not eligible for workforce planning", 400);
    }
    throw new AppError("Unauthorized workforce employee", 403);
  }
  const employee = scope.users.find((user) => user.id === employeeId);
  if (!employee) throw new AppError("Workforce employee not found", 404);
  return { scope, employee };
}'''
if text.count(old_access) != 1:
    raise SystemExit(f"WORKFORCE_ACCESS_HARDENING=FAIL count={text.count(old_access)}")
text = text.replace(old_access, new_access, 1)

old_outlook = '  if (["CRITICAL", "HIGH"].includes(risk) || Number(performanceScore) < 50 || Number(scoreDelta) <= -10 || overdueActions > 0) return "AT_RISK";'
new_outlook = '  if (["CRITICAL", "HIGH"].includes(risk) || (performanceScore != null && Number(performanceScore) < 50) || Number(scoreDelta) <= -10 || overdueActions > 0) return "AT_RISK";'
if text.count(old_outlook) != 1:
    raise SystemExit(f"NO_ACTIVITY_OUTLOOK_HARDENING=FAIL count={text.count(old_outlook)}")
text = text.replace(old_outlook, new_outlook, 1)

path.write_text(text)
print("WORKFORCE_ACCESS_HARDENING=PASS")
print("NO_ACTIVITY_OUTLOOK_HARDENING=PASS")
