#!/usr/bin/env python3
from pathlib import Path
import sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
path = repo / "frontend/src/pages/TeamPerformanceDashboard.jsx"
text = path.read_text()

import_anchor = 'import { Badge, Card, Notice, PageIntro } from "../components/ui/Primitives";\n'
main_anchor = '      <Card className="overflow-hidden p-0">\n        <div className="flex flex-col gap-3 border-b border-zinc-100 p-4 dark:border-white/10 lg:flex-row lg:items-center lg:justify-between">\n'
drawer_anchor = '                <section className="mt-4 rounded-2xl border border-zinc-100 p-4 dark:border-white/10">\n                  <div className="flex items-center justify-between"><h3 className="text-sm font-black text-zinc-950 dark:text-white">Score Breakdown</h3>'

if text.count(import_anchor) != 1:
    raise SystemExit(f"PHASE7_IMPORT_ANCHOR=FAIL count={text.count(import_anchor)}")
if text.count(main_anchor) != 1:
    raise SystemExit(f"PHASE7_MAIN_ANCHOR=FAIL count={text.count(main_anchor)}")
if text.count(drawer_anchor) != 1:
    raise SystemExit(f"PHASE7_DRAWER_ANCHOR=FAIL count={text.count(drawer_anchor)}")
if "PerformanceReviewsPanel" in text or "EmployeeReviewsSection" in text:
    raise SystemExit("PHASE7_DASHBOARD_ALREADY_PRESENT=FAIL")

text = text.replace(
    import_anchor,
    import_anchor + 'import { EmployeeReviewsSection, PerformanceReviewsPanel } from "../components/performance/PerformanceReviews";\n',
    1,
)

main_insert = '''      <PerformanceReviewsPanel
        user={user}
        employees={filteredEmployees}
        selectedRange={selectedRange}
        employeeFilter={employeeFilter}
        departmentFilter={departmentFilter}
        refreshToken={`${refreshNonce}:${realtimeRefreshVersion}`}
      />

'''
text = text.replace(main_anchor, main_insert + main_anchor, 1)

drawer_insert = '''                <EmployeeReviewsSection
                  user={user}
                  employee={selectedEmployee}
                  selectedRange={selectedRange}
                />

'''
text = text.replace(drawer_anchor, drawer_insert + drawer_anchor, 1)

path.write_text(text)
print("FRONTEND_REVIEW_PANEL_INTEGRATION=PASS")
print("FRONTEND_REVIEW_DRAWER_INTEGRATION=PASS")
