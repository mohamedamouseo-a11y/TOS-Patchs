#!/usr/bin/env python3
from pathlib import Path
import sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
path = repo / "frontend/src/pages/TeamPerformanceDashboard.jsx"
text = path.read_text()
if "RecognitionRewardsPanel" in text:
    raise SystemExit("Phase 11 dashboard already integrated")
if "TalentSuccessionPanel" not in text:
    raise SystemExit("Phase 10 dashboard baseline missing")

import_anchor = 'import { EmployeeTalentSuccession, TalentSuccessionPanel } from "../components/performance/TalentSuccession";'
import_line = import_anchor + '\nimport { EmployeeRecognitionRewards, RecognitionRewardsPanel } from "../components/performance/RecognitionRewards";'
if import_anchor not in text:
    raise SystemExit("dashboard import anchor missing")
text = text.replace(import_anchor, import_line, 1)

panel_anchor = '''      <TalentSuccessionPanel
        user={user}
        employees={allEmployees}
        selectedRange={selectedRange}
        employeeFilter={employeeFilter}
        departmentFilter={departmentFilter}
        refreshToken={`${refreshNonce}:${realtimeRefreshVersion}`}
        onOpenEmployee={openEmployee}
      />
'''
panel_add = panel_anchor + '''
      <RecognitionRewardsPanel
        user={user}
        employees={allEmployees}
        employeeFilter={employeeFilter}
        departmentFilter={departmentFilter}
        refreshToken={`${refreshNonce}:${realtimeRefreshVersion}`}
        onOpenEmployee={openEmployee}
      />
'''
if panel_anchor not in text:
    raise SystemExit("dashboard Phase 10 panel anchor missing")
text = text.replace(panel_anchor, panel_add, 1)

drawer_anchor = '''                <EmployeeTalentSuccession
                  user={user}
                  employee={selectedEmployee}
                  selectedRange={selectedRange}
                  refreshToken={`${refreshNonce}:${realtimeRefreshVersion}`}
                />
'''
drawer_add = drawer_anchor + '''
                <EmployeeRecognitionRewards
                  user={user}
                  employee={selectedEmployee}
                  refreshToken={`${refreshNonce}:${realtimeRefreshVersion}`}
                />
'''
if drawer_anchor not in text:
    raise SystemExit("dashboard Phase 10 drawer anchor missing")
text = text.replace(drawer_anchor, drawer_add, 1)
path.write_text(text)
print("FRONTEND_RECOGNITION_DASHBOARD=PASS")
print("FRONTEND_RECOGNITION_DRAWER=PASS")
