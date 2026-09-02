#!/usr/bin/env python3
from pathlib import Path
import sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
path = repo / "frontend/src/lib/api.js"
text = path.read_text()

if "skillsMatrix:" in text:
    raise SystemExit("PHASE9_API_ALREADY_PRESENT")

anchor = '    performanceReviewSummary: (params = {}) => request(`/api/tasks/reports/team-performance/reviews/summary${queryString(params)}`),'
if anchor not in text:
    raise SystemExit("PHASE9_API_ANCHOR_MISSING")

block = r'''    skillsMatrix: (params = {}) => request(`/api/tasks/reports/team-performance/skills/matrix${queryString(params)}`),
    skillCatalog: (params = {}) => request(`/api/tasks/reports/team-performance/skills/catalog${queryString(params)}`),
    createSkillDefinition: (payload = {}) => request("/api/tasks/reports/team-performance/skills/catalog", { method: "POST", body: JSON.stringify(payload || {}) }),
    updateSkillDefinition: (skillId, payload = {}) => request(`/api/tasks/reports/team-performance/skills/catalog/${encodeURIComponent(skillId)}`, { method: "PATCH", body: JSON.stringify(payload || {}) }),
    deactivateSkillDefinition: (skillId) => request(`/api/tasks/reports/team-performance/skills/catalog/${encodeURIComponent(skillId)}`, { method: "DELETE" }),
    skillRequirements: () => request("/api/tasks/reports/team-performance/skills/requirements"),
    createSkillRequirement: (payload = {}) => request("/api/tasks/reports/team-performance/skills/requirements", { method: "POST", body: JSON.stringify(payload || {}) }),
    updateSkillRequirement: (requirementId, payload = {}) => request(`/api/tasks/reports/team-performance/skills/requirements/${encodeURIComponent(requirementId)}`, { method: "PATCH", body: JSON.stringify(payload || {}) }),
    deactivateSkillRequirement: (requirementId) => request(`/api/tasks/reports/team-performance/skills/requirements/${encodeURIComponent(requirementId)}`, { method: "DELETE" }),
    assessEmployeeSkill: (payload = {}) => request("/api/tasks/reports/team-performance/skills/assessments", { method: "POST", body: JSON.stringify(payload || {}) }),
    removeEmployeeSkillAssessment: (employeeId, skillId) => request(`/api/tasks/reports/team-performance/skills/assessments/${encodeURIComponent(employeeId)}/${encodeURIComponent(skillId)}`, { method: "DELETE" }),
    developmentPlans: (params = {}) => request(`/api/tasks/reports/team-performance/development-plans${queryString(params)}`),
    createDevelopmentPlan: (payload = {}) => request("/api/tasks/reports/team-performance/development-plans", { method: "POST", body: JSON.stringify(payload || {}) }),
    updateDevelopmentPlan: (planId, payload = {}) => request(`/api/tasks/reports/team-performance/development-plans/${encodeURIComponent(planId)}`, { method: "PATCH", body: JSON.stringify(payload || {}) }),
    activateDevelopmentPlan: (planId) => request(`/api/tasks/reports/team-performance/development-plans/${encodeURIComponent(planId)}/activate`, { method: "POST", body: JSON.stringify({}) }),
    completeDevelopmentPlan: (planId) => request(`/api/tasks/reports/team-performance/development-plans/${encodeURIComponent(planId)}/complete`, { method: "POST", body: JSON.stringify({}) }),
    cancelDevelopmentPlan: (planId) => request(`/api/tasks/reports/team-performance/development-plans/${encodeURIComponent(planId)}`, { method: "DELETE" }),
    createDevelopmentAction: (planId, payload = {}) => request(`/api/tasks/reports/team-performance/development-plans/${encodeURIComponent(planId)}/actions`, { method: "POST", body: JSON.stringify(payload || {}) }),
    updateDevelopmentAction: (planId, actionId, payload = {}) => request(`/api/tasks/reports/team-performance/development-plans/${encodeURIComponent(planId)}/actions/${encodeURIComponent(actionId)}`, { method: "PATCH", body: JSON.stringify(payload || {}) }),
    cancelDevelopmentAction: (planId, actionId) => request(`/api/tasks/reports/team-performance/development-plans/${encodeURIComponent(planId)}/actions/${encodeURIComponent(actionId)}`, { method: "DELETE" }),
'''

text = text.replace(anchor, block + anchor, 1)
path.write_text(text)
print("FRONTEND_SKILLS_API=PASS")
