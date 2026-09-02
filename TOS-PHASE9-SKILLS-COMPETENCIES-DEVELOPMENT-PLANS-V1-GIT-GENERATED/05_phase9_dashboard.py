#!/usr/bin/env python3
from pathlib import Path
import sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
path = repo / "frontend/src/pages/TeamPerformanceDashboard.jsx"
text = path.read_text()

if "SkillsDevelopmentPanel" in text:
    raise SystemExit("PHASE9_DASHBOARD_ALREADY_PRESENT")

import_anchor = 'import { EmployeeWorkforceOutlook, WorkforcePlanningPanel } from "../components/performance/WorkforcePlanning";'
if import_anchor not in text:
    raise SystemExit("PHASE9_DASHBOARD_IMPORT_ANCHOR_MISSING")
text = text.replace(import_anchor, import_anchor + '\nimport { EmployeeSkillsDevelopment, SkillsDevelopmentPanel } from "../components/performance/SkillsDevelopment";', 1)

panel_anchor = '''      <WorkforcePlanningPanel
        user={user}
        employees={allEmployees}
        employeeFilter={employeeFilter}
        departmentFilter={departmentFilter}
        refreshToken={`${refreshNonce}:${realtimeRefreshVersion}`}
        onOpenEmployee={openEmployee}
        onData={setWorkforceData}
      />
'''
if panel_anchor not in text:
    raise SystemExit("PHASE9_DASHBOARD_PANEL_ANCHOR_MISSING")
panel = panel_anchor + '''
      <SkillsDevelopmentPanel
        user={user}
        employees={allEmployees}
        employeeFilter={employeeFilter}
        departmentFilter={departmentFilter}
        refreshToken={`${refreshNonce}:${realtimeRefreshVersion}`}
        onOpenEmployee={openEmployee}
      />
'''
text = text.replace(panel_anchor, panel, 1)

drawer_anchor = '                <EmployeeWorkforceOutlook forecast={selectedEmployeeForecast} />'
if drawer_anchor not in text:
    raise SystemExit("PHASE9_DASHBOARD_DRAWER_ANCHOR_MISSING")
text = text.replace(drawer_anchor, drawer_anchor + '''

                <EmployeeSkillsDevelopment
                  user={user}
                  employee={selectedEmployee}
                  refreshToken={`${refreshNonce}:${realtimeRefreshVersion}`}
                />''', 1)

path.write_text(text)
print("FRONTEND_SKILLS_DASHBOARD=PASS")
print("FRONTEND_SKILLS_DRAWER=PASS")
