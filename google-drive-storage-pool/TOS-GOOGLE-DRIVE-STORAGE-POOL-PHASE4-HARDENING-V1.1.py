#!/usr/bin/env python3
from pathlib import Path

ROOT = Path.cwd()
SERVICE = ROOT / "backend/src/services/googleDrive.service.js"
PHASE21 = ROOT / "backend/src/services/googleDriveStoragePoolPhase2_1.test.js"

for p in (SERVICE, PHASE21):
    if not p.exists():
        raise SystemExit(f"PATCH=FAIL\nREASON=Missing {p}")

def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"PATCH=FAIL\nREASON={label} expected once, found {count}")
    return text.replace(old, new, 1)

changed = []

service = SERVICE.read_text(encoding="utf-8")

# googleapis can return non-extensible resource objects. Keep per-client
# settings ownership out-of-band rather than defining a property on the Drive object.
anchor = 'const CLIENT_FILE_CATEGORIES = new Set(["CLIENT_ASSET", "CLIENT_ASSETS", "CLIENT_FILE", "CLIENT_FILES", "CLIENT_PROVIDED", "CLIENT_UPLOAD", "CLIENT_UPLOADS", "PROJECT_BRIEF", "PROJECT_REQUIREMENTS"]);\n'
if "const DRIVE_SETTINGS_KEYS = new WeakMap();" not in service:
    service = replace_once(
        service,
        anchor,
        anchor + 'const DRIVE_SETTINGS_KEYS = new WeakMap();\n',
        "WeakMap declaration",
    )

old_tag = '''  const google = await getGoogle();
  const drive = google.drive({ version: "v3", auth: oauth2Client });
  Object.defineProperty(drive, "__tosGoogleDriveSettingsKey", {
    value: settingsKey,
    enumerable: false,
    configurable: false,
    writable: false,
  });
  return { drive, settings };
'''
new_tag = '''  const google = await getGoogle();
  const drive = google.drive({ version: "v3", auth: oauth2Client });
  DRIVE_SETTINGS_KEYS.set(drive, settingsKey);
  return { drive, settings };
'''
if old_tag in service:
    service = replace_once(service, old_tag, new_tag, "Drive settings ownership tag")
elif "DRIVE_SETTINGS_KEYS.set(drive, settingsKey);" not in service:
    raise SystemExit("PATCH=FAIL\nREASON=getDriveClientForSettingsKey changed unexpectedly")

old_lookup = '''function driveSettingsKey(drive) {
  return drive?.__tosGoogleDriveSettingsKey || SETTINGS_ID;
}
'''
new_lookup = '''function driveSettingsKey(drive) {
  return (drive && DRIVE_SETTINGS_KEYS.get(drive)) || SETTINGS_ID;
}
'''
if old_lookup in service:
    service = replace_once(service, old_lookup, new_lookup, "Drive settings ownership lookup")
elif "DRIVE_SETTINGS_KEYS.get(drive)" not in service:
    raise SystemExit("PATCH=FAIL\nREASON=driveSettingsKey changed unexpectedly")

if SERVICE.read_text(encoding="utf-8") != service:
    SERVICE.write_text(service, encoding="utf-8")
    changed.append(str(SERVICE.relative_to(ROOT)))

phase21 = PHASE21.read_text(encoding="utf-8")
old_assert = '  assert.match(service, /__tosGoogleDriveSettingsKey/);\n'
new_assert = '''  assert.match(service, /const DRIVE_SETTINGS_KEYS = new WeakMap\\(\\)/);
  assert.match(service, /DRIVE_SETTINGS_KEYS\\.set\\(drive, settingsKey\\)/);
  assert.match(service, /DRIVE_SETTINGS_KEYS\\.get\\(drive\\)/);
  assert.doesNotMatch(service, /Object\\.defineProperty\\(drive/);
'''
if old_assert in phase21:
    phase21 = replace_once(phase21, old_assert, new_assert, "Phase2.1 account isolation contract")
elif "DRIVE_SETTINGS_KEYS" not in phase21:
    raise SystemExit("PATCH=FAIL\nREASON=Phase2.1 isolation test changed unexpectedly")

if PHASE21.read_text(encoding="utf-8") != phase21:
    PHASE21.write_text(phase21, encoding="utf-8")
    changed.append(str(PHASE21.relative_to(ROOT)))

print("PATCH=PASS")
print(f"FILES_CHANGED={len(changed)}")
for p in changed:
    print(p)
