#!/usr/bin/env python3
import importlib.util
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
BASE = SCRIPT_DIR / "generate_phase5_3_2a_operations_shell_general_security.py"

spec = importlib.util.spec_from_file_location("phase532a_base", BASE)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)

# V2 narrows replacement 2 so Phase 5.3.2A localizes only the two in-scope
# sidebar labels (General and Security). Workforce and Projects/Tasks labels
# remain untouched until their dedicated sub-phases.
base.REPLACEMENTS[1] = (
    '''  const operationsSubSections = [\n    { key: "generalNotifications", label: "النظام العام والتنبيهات", icon: Bell },\n    { key: "security", label: "الأمان والجلسات", icon: Shield },\n    { key: "workforce", label: "سياسات الدوام والإجازات", icon: CalendarDays },\n    { key: "projectsTasks", label: "المشاريع والمهام", icon: FolderKanban },\n  ];''',
    '''  const operationsSubSections = [\n    { key: "generalNotifications", label: opsText("النظام العام والتنبيهات", "General System & Notifications"), icon: Bell },\n    { key: "security", label: opsText("الأمان والجلسات", "Security & Sessions"), icon: Shield },\n    { key: "workforce", label: "سياسات الدوام والإجازات", icon: CalendarDays },\n    { key: "projectsTasks", label: "المشاريع والمهام", icon: FolderKanban },\n  ];''',
    1,
)

if __name__ == "__main__":
    base.main()
