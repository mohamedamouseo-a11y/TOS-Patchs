from pathlib import Path

base = Path(__file__).resolve().parent
installer = base / "apply_tos_task_details_v2_12_phase1_r27_scroll_anchor_clip_guard.py"
source = installer.read_text()
old = 'for token in ("tosR27ClipGuard", "r27MoreGeometryRef", "currentTabsTop"):'
new = 'for token in ("tosR27ClipGuard", ".tos-task-detail-tabs", ".tos-task-details-layout"):'
if source.count(old) != 2:
    raise RuntimeError(f"R27 production token-check contract mismatch: {source.count(old)}")
source = source.replace(old, new)
namespace = {"__name__": "__main__", "__file__": str(installer)}
exec(compile(source, str(installer), "exec"), namespace, namespace)
