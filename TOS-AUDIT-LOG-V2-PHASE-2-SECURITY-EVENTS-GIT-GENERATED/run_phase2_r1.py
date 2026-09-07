#!/usr/bin/env python3
from pathlib import Path
import runpy

here = Path(__file__).resolve().parent
generator = here / "generate_tos_audit_log_v2_phase2_security_events.py"
text = generator.read_text(encoding="utf-8")
old = '    require("await logTeamAudit({" not in text, "unscoped team audit call remained")\n'
new = '    import re\n    require(not re.search(r"await logTeamAudit\\(\\{(?! req,)", text), "unscoped team audit call remained")\n'
if old in text:
    generator.write_text(text.replace(old, new, 1), encoding="utf-8")
elif 're.search(r"await logTeamAudit\\(\\{(?! req,)"' not in text:
    raise SystemExit("R1 guard anchor not found; stop")
runpy.run_path(str(generator), run_name="__main__")
