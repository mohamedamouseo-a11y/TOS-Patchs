#!/usr/bin/env python3
from pathlib import Path
import sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
path = repo / "frontend/src/pages/TeamPerformanceDashboard.jsx"
text = path.read_text()

import_anchor = 'import { EmployeeReviewsSection, PerformanceReviewsPanel } from "../components/performance/PerformanceReviews";\n'
if text.count(import_anchor) != 1:
    raise SystemExit(f"WORKFORCE_IMPORT_ANCHOR=FAIL count={text.count(import_anchor)}")
text = text.replace(import_anchor, import_anchor + 'import { EmployeeWorkforceOutlook, WorkforcePlanningPanel } from "../components/performance/WorkforcePlanning";\n', 1)

state_anchor = '  const [targetForm, setTargetForm] = useState({ scopeType: "EMPLOYEE", employeeId: "", department: "", periodType: "MONTHLY", effectiveFrom: "", effectiveTo: "", targetScore: "85", targetCompletionRate: "90", targetCompletedTasks: "", targetLoggedHours: "", maxOverdueTasks: "2" });\n'
if text.count(state_anchor) != 1:
    raise SystemExit(f"WORKFORCE_STATE_ANCHOR=FAIL count={text.count(state_anchor)}")
text = text.replace(state_anchor, state_anchor + '  const [workforceData, setWorkforceData] = useState(null);\n', 1)

derive_anchor = '  const selectedEmployeeTarget = selectedEmployee ? targetByEmployee.get(selectedEmployee.id) || null : null;\n'
if text.count(derive_anchor) != 1:
    raise SystemExit(f"WORKFORCE_DERIVE_ANCHOR=FAIL count={text.count(derive_anchor)}")
text = text.replace(derive_anchor, derive_anchor + '  const selectedEmployeeForecast = selectedEmployee ? (workforceData?.rows || []).find((row) => row.employeeId === selectedEmployee.id) || null : null;\n', 1)

panel_anchor = '''      <PerformanceReviewsPanel
        user={user}
        employees={filteredEmployees}
        selectedRange={selectedRange}
        employeeFilter={employeeFilter}
        departmentFilter={departmentFilter}
        refreshToken={`${refreshNonce}:${realtimeRefreshVersion}`}
      />

'''
if text.count(panel_anchor) != 1:
    raise SystemExit(f"WORKFORCE_PANEL_ANCHOR=FAIL count={text.count(panel_anchor)}")
panel = panel_anchor + '''      <WorkforcePlanningPanel
        user={user}
        employees={allEmployees}
        employeeFilter={employeeFilter}
        departmentFilter={departmentFilter}
        refreshToken={`${refreshNonce}:${realtimeRefreshVersion}`}
        onOpenEmployee={openEmployee}
        onData={setWorkforceData}
      />

'''
text = text.replace(panel_anchor, panel, 1)

drawer_anchor = '''                <EmployeeReviewsSection
                  user={user}
                  employee={selectedEmployee}
                  selectedRange={selectedRange}
                />

'''
if text.count(drawer_anchor) != 1:
    raise SystemExit(f"WORKFORCE_DRAWER_ANCHOR=FAIL count={text.count(drawer_anchor)}")
text = text.replace(drawer_anchor, drawer_anchor + '                <EmployeeWorkforceOutlook forecast={selectedEmployeeForecast} />\n\n', 1)

path.write_text(text)
print("FRONTEND_WORKFORCE_DASHBOARD=PASS")
print("FRONTEND_WORKFORCE_DRAWER=PASS")
