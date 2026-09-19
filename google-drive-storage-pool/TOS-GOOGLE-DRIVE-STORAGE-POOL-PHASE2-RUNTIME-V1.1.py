#!/usr/bin/env python3
from pathlib import Path

ROOT = Path.cwd()
DRIVE = ROOT / "backend/src/services/googleDrive.service.js"
TEST = ROOT / "backend/src/services/googleDriveStoragePoolPhase2.test.js"

if not DRIVE.exists() or not TEST.exists():
    raise SystemExit("PATCH=FAIL\nREASON=Apply Phase2 V1 first")

def replace_once(text, old, new, label):
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"PATCH=FAIL\nREASON={label} expected once, found {n}")
    return text.replace(old, new, 1)

drive = DRIVE.read_text(encoding="utf-8")

if "function driveSettingsKey(drive)" not in drive:
    drive = replace_once(
        drive,
        '''async function withRetry(fn, retries = 2, context = {}) {
''',
        '''function driveSettingsKey(drive) {
  return drive?.__tosGoogleDriveSettingsKey || SETTINGS_ID;
}

async function withRetry(fn, retries = 2, context = {}) {
''',
        "drive settings-key helper",
    )

drive = replace_once(
    drive,
    '''  const google = await getGoogle();
  return { drive: google.drive({ version: "v3", auth: oauth2Client }), settings };
}
''',
    '''  const google = await getGoogle();
  const drive = google.drive({ version: "v3", auth: oauth2Client });
  Object.defineProperty(drive, "__tosGoogleDriveSettingsKey", {
    value: settingsKey,
    enumerable: false,
    configurable: false,
    writable: false,
  });
  return { drive, settings };
}
''',
    "tag drive client with settings key",
)

drive = replace_once(
    drive,
    '''  const r = await withRetry(() => drive.files.list({ q, fields: "files(id,name)", spaces: "drive", pageSize: 1, supportsAllDrives: true, includeItemsFromAllDrives: true }), 2, { action: "drive_find_folder" });
''',
    '''  const r = await withRetry(() => drive.files.list({ q, fields: "files(id,name)", spaces: "drive", pageSize: 1, supportsAllDrives: true, includeItemsFromAllDrives: true }), 2, { action: "drive_find_folder", settingsKey: driveSettingsKey(drive) });
''',
    "find folder settings key",
)

drive = replace_once(
    drive,
    '''  }), 2, { action: "drive_create_folder" });
''',
    '''  }), 2, { action: "drive_create_folder", settingsKey: driveSettingsKey(drive) });
''',
    "create folder settings key",
)

drive = replace_once(
    drive,
    '''    }), 2, { action: "drive_assert_root_folder" });
''',
    '''    }), 2, { action: "drive_assert_root_folder", settingsKey: driveSettingsKey(drive) });
''',
    "assert folder settings key",
)

DRIVE.write_text(drive, encoding="utf-8")

test = TEST.read_text(encoding="utf-8")
extra = r'''
test("Phase 2 never marks the legacy primary disconnected for a secondary folder failure", async () => {
  const driveService = await read("backend/src/services/googleDrive.service.js");

  assert.match(driveService, /__tosGoogleDriveSettingsKey/);
  assert.match(driveService, /drive_find_folder", settingsKey: driveSettingsKey\(drive\)/);
  assert.match(driveService, /drive_create_folder", settingsKey: driveSettingsKey\(drive\)/);
  assert.match(driveService, /drive_assert_root_folder", settingsKey: driveSettingsKey\(drive\)/);
  assert.match(driveService, /const settingsKey = context\.settingsKey \|\| SETTINGS_ID/);
});
'''

if "never marks the legacy primary disconnected for a secondary folder failure" not in test:
    test = test.rstrip() + "\n" + extra
    TEST.write_text(test, encoding="utf-8")

print("PATCH=PASS")
print("FILES_CHANGED=2")
