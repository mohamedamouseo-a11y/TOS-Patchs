#!/usr/bin/env python3
from pathlib import Path
import sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
path = repo / "frontend/src/lib/api.js"
text = path.read_text()
anchor = '    recognitionOverview: (params = {}) => request(`/api/tasks/reports/team-performance/recognition/overview${queryString(params)}`),'
if "executiveCommandCenter:" in text:
    raise SystemExit("Phase 12 frontend API already present")
if "recognitionOverview:" not in text:
    raise SystemExit("Phase 11 frontend API baseline missing")
if anchor not in text:
    raise SystemExit("frontend API anchor missing")
method = '    executiveCommandCenter: (params = {}) => request(`/api/tasks/reports/team-performance/executive-command-center${queryString(params)}`),\n'
path.write_text(text.replace(anchor, method + anchor, 1))
print("FRONTEND_EXECUTIVE_API=PASS")
