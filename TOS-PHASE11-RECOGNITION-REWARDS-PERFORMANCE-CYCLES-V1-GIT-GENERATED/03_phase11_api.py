#!/usr/bin/env python3
from pathlib import Path
import sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
path = repo / "frontend/src/lib/api.js"
text = path.read_text()
anchor = '    performanceReviewSummary: (params = {}) => request(`/api/tasks/reports/team-performance/reviews/summary${queryString(params)}`),'
if "recognitionOverview:" in text:
    raise SystemExit("Phase 11 frontend API already present")
if "talentOverview:" not in text:
    raise SystemExit("Phase 10 frontend API baseline missing")
if anchor not in text:
    raise SystemExit("frontend API anchor missing")

methods = r'''    recognitionOverview: (params = {}) => request(`/api/tasks/reports/team-performance/recognition/overview${queryString(params)}`),
    recognitionCycles: (params = {}) => request(`/api/tasks/reports/team-performance/recognition/cycles${queryString(params)}`),
    createRecognitionCycle: (payload = {}) => request("/api/tasks/reports/team-performance/recognition/cycles", { method: "POST", body: JSON.stringify(payload || {}) }),
    updateRecognitionCycle: (cycleId, payload = {}) => request(`/api/tasks/reports/team-performance/recognition/cycles/${encodeURIComponent(cycleId)}`, { method: "PATCH", body: JSON.stringify(payload || {}) }),
    openRecognitionCycle: (cycleId) => request(`/api/tasks/reports/team-performance/recognition/cycles/${encodeURIComponent(cycleId)}/open`, { method: "POST", body: JSON.stringify({}) }),
    closeRecognitionCycle: (cycleId) => request(`/api/tasks/reports/team-performance/recognition/cycles/${encodeURIComponent(cycleId)}/close`, { method: "POST", body: JSON.stringify({}) }),
    deactivateRecognitionCycle: (cycleId) => request(`/api/tasks/reports/team-performance/recognition/cycles/${encodeURIComponent(cycleId)}`, { method: "DELETE" }),
    recognitionCategories: (params = {}) => request(`/api/tasks/reports/team-performance/recognition/categories${queryString(params)}`),
    createRecognitionCategory: (payload = {}) => request("/api/tasks/reports/team-performance/recognition/categories", { method: "POST", body: JSON.stringify(payload || {}) }),
    updateRecognitionCategory: (categoryId, payload = {}) => request(`/api/tasks/reports/team-performance/recognition/categories/${encodeURIComponent(categoryId)}`, { method: "PATCH", body: JSON.stringify(payload || {}) }),
    deactivateRecognitionCategory: (categoryId) => request(`/api/tasks/reports/team-performance/recognition/categories/${encodeURIComponent(categoryId)}`, { method: "DELETE" }),
    createRecognitionNomination: (payload = {}) => request("/api/tasks/reports/team-performance/recognition/nominations", { method: "POST", body: JSON.stringify(payload || {}) }),
    approveRecognitionNomination: (nominationId, payload = {}) => request(`/api/tasks/reports/team-performance/recognition/nominations/${encodeURIComponent(nominationId)}/approve`, { method: "POST", body: JSON.stringify(payload || {}) }),
    rejectRecognitionNomination: (nominationId, payload = {}) => request(`/api/tasks/reports/team-performance/recognition/nominations/${encodeURIComponent(nominationId)}/reject`, { method: "POST", body: JSON.stringify(payload || {}) }),
    updateRecognitionAward: (awardId, payload = {}) => request(`/api/tasks/reports/team-performance/recognition/awards/${encodeURIComponent(awardId)}`, { method: "PATCH", body: JSON.stringify(payload || {}) }),
    recognitionFeed: () => request("/api/tasks/reports/team-performance/recognition/feed"),
    employeeRecognition: (employeeId) => request(`/api/tasks/reports/team-performance/recognition/employee/${encodeURIComponent(employeeId)}`),
'''
path.write_text(text.replace(anchor, methods + anchor, 1))
print("FRONTEND_RECOGNITION_API=PASS")
