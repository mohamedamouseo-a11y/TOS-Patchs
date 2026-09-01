#!/usr/bin/env python3
from pathlib import Path
import sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
path = repo / "frontend/src/lib/api.js"
text = path.read_text()
anchor = '    copyPerformanceTarget: (targetId, payload = {}) => request(`/api/tasks/reports/team-performance/targets/${encodeURIComponent(targetId)}/copy`, { method: "POST", body: JSON.stringify(payload || {}) }),\n'
if text.count(anchor) != 1:
    raise SystemExit(f"PHASE7_API_ANCHOR=FAIL count={text.count(anchor)}")
if "performanceReviewSummary:" in text:
    raise SystemExit("PHASE7_API_ALREADY_PRESENT=FAIL")

addition = anchor + '''    performanceReviewSummary: (params = {}) => request(`/api/tasks/reports/team-performance/reviews/summary${queryString(params)}`),
    performanceReviews: (params = {}) => request(`/api/tasks/reports/team-performance/reviews${queryString(params)}`),
    performanceReview: (reviewId) => request(`/api/tasks/reports/team-performance/reviews/${encodeURIComponent(reviewId)}`),
    createPerformanceReview: (payload = {}) => request("/api/tasks/reports/team-performance/reviews", { method: "POST", body: JSON.stringify(payload || {}) }),
    updatePerformanceReview: (reviewId, payload = {}) => request(`/api/tasks/reports/team-performance/reviews/${encodeURIComponent(reviewId)}`, { method: "PATCH", body: JSON.stringify(payload || {}) }),
    sharePerformanceReview: (reviewId) => request(`/api/tasks/reports/team-performance/reviews/${encodeURIComponent(reviewId)}/share`, { method: "POST", body: JSON.stringify({}) }),
    acknowledgePerformanceReview: (reviewId, payload = {}) => request(`/api/tasks/reports/team-performance/reviews/${encodeURIComponent(reviewId)}/acknowledge`, { method: "POST", body: JSON.stringify(payload || {}) }),
    completePerformanceReview: (reviewId) => request(`/api/tasks/reports/team-performance/reviews/${encodeURIComponent(reviewId)}/complete`, { method: "POST", body: JSON.stringify({}) }),
    createPerformanceAction: (reviewId, payload = {}) => request(`/api/tasks/reports/team-performance/reviews/${encodeURIComponent(reviewId)}/actions`, { method: "POST", body: JSON.stringify(payload || {}) }),
    updatePerformanceAction: (reviewId, actionId, payload = {}) => request(`/api/tasks/reports/team-performance/reviews/${encodeURIComponent(reviewId)}/actions/${encodeURIComponent(actionId)}`, { method: "PATCH", body: JSON.stringify(payload || {}) }),
    cancelPerformanceAction: (reviewId, actionId) => request(`/api/tasks/reports/team-performance/reviews/${encodeURIComponent(reviewId)}/actions/${encodeURIComponent(actionId)}`, { method: "DELETE" }),
'''
text = text.replace(anchor, addition, 1)
path.write_text(text)
print("FRONTEND_REVIEW_API=PASS")
