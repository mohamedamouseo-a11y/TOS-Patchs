#!/usr/bin/env python3
from pathlib import Path
import sys

repo = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
path = repo / "backend/src/routes/tasks.routes.js"
text = path.read_text()
if "function recognitionBoundaryDate(" in text:
    raise SystemExit("Phase 11 date boundary hardening already present")

anchor = '''function recognitionRewardType(value) {
'''
helper = '''function recognitionBoundaryDate(value, label, required = false, boundary = "start") {
  const date = recognitionDate(value, label, required);
  if (date && boundary === "end" && typeof value === "string" && /^\\d{4}-\\d{2}-\\d{2}$/.test(value.trim())) {
    date.setUTCHours(23, 59, 59, 999);
  }
  return date;
}

'''
if anchor not in text:
    raise SystemExit("recognition helper anchor missing")
text = text.replace(anchor, helper + anchor, 1)

replacements = {
'''  const startDate = recognitionDate(payload.startDate === undefined ? existing?.startDate : payload.startDate, "startDate", true);
  const endDate = recognitionDate(payload.endDate === undefined ? existing?.endDate : payload.endDate, "endDate", true);
''': '''  const startDateValue = payload.startDate === undefined ? existing?.startDate : payload.startDate;
  const endDateValue = payload.endDate === undefined ? existing?.endDate : payload.endDate;
  const startDate = recognitionBoundaryDate(startDateValue, "startDate", true, "start");
  const endDate = recognitionBoundaryDate(endDateValue, "endDate", true, "end");
''',
'''  const nominationStart = recognitionDate(payload.nominationStart === undefined ? existing?.nominationStart : payload.nominationStart, "nominationStart", false);
  const nominationEnd = recognitionDate(payload.nominationEnd === undefined ? existing?.nominationEnd : payload.nominationEnd, "nominationEnd", false);
''': '''  const nominationStartValue = payload.nominationStart === undefined ? existing?.nominationStart : payload.nominationStart;
  const nominationEndValue = payload.nominationEnd === undefined ? existing?.nominationEnd : payload.nominationEnd;
  const nominationStart = recognitionBoundaryDate(nominationStartValue, "nominationStart", false, "start");
  const nominationEnd = recognitionBoundaryDate(nominationEndValue, "nominationEnd", false, "end");
''',
}
for old, new in replacements.items():
    if old not in text:
        raise SystemExit("date normalization target missing")
    text = text.replace(old, new, 1)

path.write_text(text)
print("RECOGNITION_DATE_BOUNDARY_HARDENING=PASS")
