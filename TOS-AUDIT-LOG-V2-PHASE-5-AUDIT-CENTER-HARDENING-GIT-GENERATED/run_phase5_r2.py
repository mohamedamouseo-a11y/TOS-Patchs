#!/usr/bin/env python3
import urllib.request

RUNNER_URL = "https://raw.githubusercontent.com/mohamedamouseo-a11y/TOS-Patchs/main/TOS-AUDIT-LOG-V2-PHASE-5-AUDIT-CENTER-HARDENING-GIT-GENERATED/run_phase5.py"
OLD_CENTER_BLOB = "2ffcdcef91fefb0bdb700568fbc07a7f92f2a4ca"
NEW_CENTER_BLOB = "9bff6d40c8c5c8a684eb75453575d21a59ac969b"
OLD_API = '''    v2: (filters = {}) => request(`/api/audit-log/v2${queryString(filters)}`),
    v2Filters: () => request("/api/audit-log/v2/filters"),
    eventV2: (id) => request(`/api/audit-log/v2/${encodeURIComponent(id)}`),
    retention: () => request("/api/audit-log/v2/retention"),
    runRetention: (payload = {}) => request("/api/audit-log/v2/retention/run", { method: "POST", body: JSON.stringify(payload || {}) }),
    exportV2: (filters = {}) => downloadRequest(`/api/audit-log/v2/export${queryString(filters)}`),'''
NEW_API = '''    v2: (filters = {}) => {
      const params = new URLSearchParams();
      Object.entries(filters || {}).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== "") params.set(key, String(value));
      });
      const query = params.toString();
      return request(`/api/audit-log/v2${query ? `?${query}` : ""}`);
    },
    v2Filters: () => request("/api/audit-log/v2/filters"),
    eventV2: (id) => request(`/api/audit-log/v2/${encodeURIComponent(id)}`),
    retention: () => request("/api/audit-log/v2/retention"),
    runRetention: (payload = {}) => request("/api/audit-log/v2/retention/run", { method: "POST", body: JSON.stringify(payload || {}) }),
    exportV2: (filters = {}) => {
      const params = new URLSearchParams();
      Object.entries(filters || {}).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== "") params.set(key, String(value));
      });
      const query = params.toString();
      return downloadRequest(`/api/audit-log/v2/export${query ? `?${query}` : ""}`);
    },'''

with urllib.request.urlopen(RUNNER_URL, timeout=30) as response:
    source = response.read().decode("utf-8")

if source.count(OLD_CENTER_BLOB) != 1:
    raise SystemExit("PHASE_5_R2=FAIL: center guard mismatch")
if source.count(OLD_API) != 1:
    raise SystemExit("PHASE_5_R2=FAIL: audit API transform mismatch")

source = source.replace(OLD_CENTER_BLOB, NEW_CENTER_BLOB, 1)
source = source.replace(OLD_API, NEW_API, 1)
exec(compile(source, "run_phase5_r2_inner.py", "exec"), {"__name__": "__main__"})
