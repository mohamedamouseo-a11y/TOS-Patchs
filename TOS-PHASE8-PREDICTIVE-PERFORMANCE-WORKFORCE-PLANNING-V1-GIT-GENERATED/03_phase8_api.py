#!/usr/bin/env python3
from pathlib import Path
import sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
path = repo / "frontend/src/lib/api.js"
text = path.read_text()
anchor = '    performanceReviewSummary: (params = {}) => request(`/api/tasks/reports/team-performance/reviews/summary${queryString(params)}`),\n'
if text.count(anchor) != 1:
    raise SystemExit(f"FRONTEND_API_ANCHOR=FAIL count={text.count(anchor)}")
if "workforceForecast:" in text:
    raise SystemExit("FRONTEND_WORKFORCE_API_ALREADY_PRESENT=FAIL")
addition = '''    workforceForecast: (params = {}) => request(`/api/tasks/reports/team-performance/workforce/forecast${queryString(params)}`),
    workforceCapacityPlans: (params = {}) => request(`/api/tasks/reports/team-performance/workforce/capacity-plans${queryString(params)}`),
    createWorkforceCapacityPlan: (payload = {}) => request("/api/tasks/reports/team-performance/workforce/capacity-plans", { method: "POST", body: JSON.stringify(payload || {}) }),
    updateWorkforceCapacityPlan: (planId, payload = {}) => request(`/api/tasks/reports/team-performance/workforce/capacity-plans/${encodeURIComponent(planId)}`, { method: "PATCH", body: JSON.stringify(payload || {}) }),
    deactivateWorkforceCapacityPlan: (planId) => request(`/api/tasks/reports/team-performance/workforce/capacity-plans/${encodeURIComponent(planId)}`, { method: "DELETE" }),
'''
path.write_text(text.replace(anchor, addition + anchor, 1))
print("FRONTEND_WORKFORCE_API=PASS")
