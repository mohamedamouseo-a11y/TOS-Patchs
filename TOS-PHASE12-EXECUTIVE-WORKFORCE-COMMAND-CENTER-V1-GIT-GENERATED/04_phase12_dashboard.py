#!/usr/bin/env python3
from pathlib import Path
import sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
path = repo / "frontend/src/pages/TeamPerformanceDashboard.jsx"
text = path.read_text()
if "ExecutiveCommandCenterPanel" in text:
    raise SystemExit("Phase 12 dashboard already integrated")
if "RecognitionRewardsPanel" not in text:
    raise SystemExit("Phase 11 dashboard baseline missing")

import_anchor = 'import { EmployeeRecognitionRewards, RecognitionRewardsPanel } from "../components/performance/RecognitionRewards";'
if import_anchor not in text:
    raise SystemExit("dashboard Phase 11 import anchor missing")
text = text.replace(import_anchor, import_anchor + '\nimport { ExecutiveCommandCenterPanel } from "../components/performance/ExecutiveCommandCenter";', 1)

panel_anchor = '''      <Card className="overflow-hidden p-0">
        <div className="flex flex-col gap-2 border-b border-zinc-100 p-4 dark:border-white/10 sm:flex-row sm:items-center sm:justify-between"><div><p className="text-[11px] font-black uppercase tracking-[0.1em] text-amber-500">Goals & Targets</p>'''
panel = '''      <ExecutiveCommandCenterPanel
        user={user}
        selectedRange={selectedRange}
        employeeFilter={employeeFilter}
        departmentFilter={departmentFilter}
        refreshToken={`${refreshNonce}:${realtimeRefreshVersion}`}
        onOpenEmployee={openEmployee}
      />

'''
if panel_anchor not in text:
    raise SystemExit("dashboard Goals & Targets anchor missing")
text = text.replace(panel_anchor, panel + panel_anchor, 1)
path.write_text(text)
print("FRONTEND_EXECUTIVE_DASHBOARD=PASS")
