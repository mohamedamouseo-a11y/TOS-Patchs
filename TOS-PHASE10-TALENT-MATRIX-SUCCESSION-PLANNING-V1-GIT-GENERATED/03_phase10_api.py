#!/usr/bin/env python3
from pathlib import Path
import sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
path = repo / "frontend/src/lib/api.js"
text = path.read_text()

if "talentOverview:" in text:
    print("FRONTEND_TALENT_API=PASS already-present")
    raise SystemExit(0)

anchor = '    performanceReviewSummary: (params = {}) => request(`/api/tasks/reports/team-performance/reviews/summary${queryString(params)}`),'
if anchor not in text:
    raise SystemExit("Phase 10 API anchor not found")

block = r'''    talentOverview: (params = {}) => request(`/api/tasks/reports/team-performance/talent/overview${queryString(params)}`),
    assessTalentPotential: (payload = {}) => request("/api/tasks/reports/team-performance/talent/assessments", { method: "POST", body: JSON.stringify(payload || {}) }),
    deactivateTalentAssessment: (employeeId) => request(`/api/tasks/reports/team-performance/talent/assessments/${encodeURIComponent(employeeId)}`, { method: "DELETE" }),
    successionRoles: (params = {}) => request(`/api/tasks/reports/team-performance/talent/succession-roles${queryString(params)}`),
    createSuccessionRole: (payload = {}) => request("/api/tasks/reports/team-performance/talent/succession-roles", { method: "POST", body: JSON.stringify(payload || {}) }),
    updateSuccessionRole: (roleId, payload = {}) => request(`/api/tasks/reports/team-performance/talent/succession-roles/${encodeURIComponent(roleId)}`, { method: "PATCH", body: JSON.stringify(payload || {}) }),
    deactivateSuccessionRole: (roleId) => request(`/api/tasks/reports/team-performance/talent/succession-roles/${encodeURIComponent(roleId)}`, { method: "DELETE" }),
    nominateSuccessionCandidate: (roleId, payload = {}) => request(`/api/tasks/reports/team-performance/talent/succession-roles/${encodeURIComponent(roleId)}/candidates`, { method: "POST", body: JSON.stringify(payload || {}) }),
    updateSuccessionCandidate: (roleId, candidateId, payload = {}) => request(`/api/tasks/reports/team-performance/talent/succession-roles/${encodeURIComponent(roleId)}/candidates/${encodeURIComponent(candidateId)}`, { method: "PATCH", body: JSON.stringify(payload || {}) }),
    deactivateSuccessionCandidate: (roleId, candidateId) => request(`/api/tasks/reports/team-performance/talent/succession-roles/${encodeURIComponent(roleId)}/candidates/${encodeURIComponent(candidateId)}`, { method: "DELETE" }),
'''

text = text.replace(anchor, block + anchor, 1)
path.write_text(text)
print("FRONTEND_TALENT_API=PASS")
