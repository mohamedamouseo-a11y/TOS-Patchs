#!/usr/bin/env python3
from pathlib import Path
import sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
path = repo / "frontend/src/pages/TeamPerformanceDashboard.jsx"
text = path.read_text()

if 'from "../components/performance/TalentSuccession"' in text:
    print("FRONTEND_TALENT_DASHBOARD=PASS already-present")
    raise SystemExit(0)

import_anchor = 'import { EmployeeSkillsDevelopment, SkillsDevelopmentPanel } from "../components/performance/SkillsDevelopment";'
if import_anchor not in text:
    raise SystemExit("Phase 10 dashboard import anchor not found")
text = text.replace(import_anchor, import_anchor + '\nimport { EmployeeTalentSuccession, TalentSuccessionPanel } from "../components/performance/TalentSuccession";', 1)

panel_anchor = '''      <SkillsDevelopmentPanel
        user={user}
        employees={allEmployees}
        employeeFilter={employeeFilter}
        departmentFilter={departmentFilter}
        refreshToken={`${refreshNonce}:${realtimeRefreshVersion}`}
        onOpenEmployee={openEmployee}
      />
'''
if panel_anchor not in text:
    raise SystemExit("Phase 10 dashboard panel anchor not found")
panel = panel_anchor + '''
      <TalentSuccessionPanel
        user={user}
        employees={allEmployees}
        selectedRange={selectedRange}
        employeeFilter={employeeFilter}
        departmentFilter={departmentFilter}
        refreshToken={`${refreshNonce}:${realtimeRefreshVersion}`}
        onOpenEmployee={openEmployee}
      />
'''
text = text.replace(panel_anchor, panel, 1)

drawer_anchor = '''                <EmployeeSkillsDevelopment
                  user={user}
                  employee={selectedEmployee}
                  refreshToken={`${refreshNonce}:${realtimeRefreshVersion}`}
                />
'''
if drawer_anchor not in text:
    raise SystemExit("Phase 10 drawer anchor not found")
drawer = drawer_anchor + '''
                <EmployeeTalentSuccession
                  user={user}
                  employee={selectedEmployee}
                  selectedRange={selectedRange}
                  refreshToken={`${refreshNonce}:${realtimeRefreshVersion}`}
                />
'''
text = text.replace(drawer_anchor, drawer, 1)

path.write_text(text)
print("FRONTEND_TALENT_DASHBOARD=PASS")
print("FRONTEND_TALENT_DRAWER=PASS")
