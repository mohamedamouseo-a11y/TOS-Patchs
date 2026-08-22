#!/usr/bin/env python3
import importlib.util
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
V2_GENERATOR = SCRIPT_DIR / "generate_phase5_3_1_settings_core_v2.py"

spec = importlib.util.spec_from_file_location("phase531_v2", V2_GENERATOR)
v2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v2)

# V3 fixes only replacement 43. The JSX source stores literal backslash-n
# sequences inside the fallback leave-types placeholder. The original Python
# literal decoded those sequences into real newlines before matching.
v2.REPLACEMENTS[42] = (
    r'''placeholder={'أنواع إجازات احتياطية عند عدم توفر THRS\nمثال:\nleave_type_id_1|إجازة سنوية|ANNUAL\nleave_type_id_2|إجازة مرضية|SICK'}''',
    r'''placeholder={thrsText('أنواع إجازات احتياطية عند عدم توفر THRS\nمثال:\nleave_type_id_1|إجازة سنوية|ANNUAL\nleave_type_id_2|إجازة مرضية|SICK', 'Fallback leave types when THRS is unavailable\nExample:\nleave_type_id_1|Annual Leave|ANNUAL\nleave_type_id_2|Sick Leave|SICK')}''',
    1,
)

# Rebuild region slices after replacing tuple 43 so the THRS region uses the
# corrected exact-match tuple.
v2.REGIONS = [
    (
        "GOOGLE_DRIVE",
        "function GoogleDriveAdmin({ user }) {",
        "function formatBackupBytes(value)",
        v2.REPLACEMENTS[0:24],
    ),
    (
        "THRS",
        "function ThrsIntegrationAdmin({ user }) {",
        "function SystemBackupAdmin({ user }) {",
        v2.REPLACEMENTS[24:49],
    ),
    (
        "IDENTITY",
        "function SettingsIdentityAdmin({ user }) {",
        "function normalizeProjectTypeImageForSettings(value = \"\") {",
        v2.REPLACEMENTS[49:],
    ),
]

if __name__ == "__main__":
    v2.main()
