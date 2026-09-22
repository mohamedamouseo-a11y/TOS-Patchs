#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import shutil
import sys

PATCH = "TCS-REFERENCE-DESIGN-LOCK-V1.1"
ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
CHAT = ROOT / "frontend/src/components/ChatPanel.jsx"
CSS = ROOT / "frontend/src/components/tcsReferencePolishV1_1.css"

if not CHAT.exists():
    raise SystemExit(f"{PATCH}: missing {CHAT}")

src = CHAT.read_text(encoding="utf-8")

backup_dir = Path("/tmp") / f"TCS-REFERENCE-DESIGN-LOCK-V1_1-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
backup_dir.mkdir(parents=True, exist_ok=True)
shutil.copy2(CHAT, backup_dir / "ChatPanel.jsx")

# 1) Keep conversation titles compact/readable.
old_title = '''function conversationTitle(conversation, currentUserId) {
  const others = (conversation?.members || []).filter((member) => member.userId !== currentUserId).map((member) => member.user?.name).filter(Boolean);
  return others.join("، ") || "محادثة خاصة";
}'''
new_title = '''function conversationTitle(conversation, currentUserId) {
  const explicit = String(conversation?.name || conversation?.title || conversation?.groupName || conversation?.displayName || "").trim();
  if (explicit) return explicit;
  const others = (conversation?.members || []).filter((member) => member.userId !== currentUserId).map((member) => member.user?.name).filter(Boolean);
  if (others.length <= 2) return others.join("، ") || "محادثة خاصة";
  return `${others[0]} +${others.length - 1}`;
}'''
if old_title in src:
    src = src.replace(old_title, new_title, 1)
elif 'return `${others[0]} +${others.length - 1}`;' not in src:
    raise SystemExit(f"{PATCH}: conversationTitle marker not found")

# 2) Give conversation title a stable visual hook.
old_span = '<span>{conversationTitle(conversation, user?.id)}</span>'
new_span = '<span className="tcs-ref-conversation-title" title={conversationTitle(conversation, user?.id)}>{conversationTitle(conversation, user?.id)}</span>'
src = src.replace(old_span, new_span)

# 3) Details and tools must never stay open together.
state_anchor = '  const [toolbarOpen, setToolbarOpen] = useState(false);'
effect_block = '''  const [toolbarOpen, setToolbarOpen] = useState(false);

  // TCS_REFERENCE_DESIGN_LOCK_V1_1
  // Keep the workspace uncluttered: details and tools are mutually exclusive.
  useEffect(() => {
    if (detailsPanelOpen) setToolbarOpen(false);
  }, [detailsPanelOpen]);'''
if "TCS_REFERENCE_DESIGN_LOCK_V1_1" not in src:
    if state_anchor not in src:
        raise SystemExit(f"{PATCH}: toolbar state marker not found")
    src = src.replace(state_anchor, effect_block, 1)

# 4) Load isolated V1.1 visual corrections.
import_anchor = 'import "./tcsReferenceLockV1.css";'
polish_import = 'import "./tcsReferencePolishV1_1.css";'
if polish_import not in src:
    if import_anchor not in src:
        raise SystemExit(f"{PATCH}: reference CSS import not found")
    src = src.replace(import_anchor, import_anchor + "\n" + polish_import, 1)

CHAT.write_text(src, encoding="utf-8")

CSS.write_text(r'''
:root { --tcs-reference-design-lock-v1-1: 1; }

/* TCS Reference Design Lock V1.1
   Visual/usability correction only.
   No API, socket, permission, Drive, upload, message or backend behavior changes. */

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tcs-ref-conversation-title {
  display: block;
  min-width: 0;
  max-width: 210px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 12px;
  font-weight: 800;
  line-height: 1.35;
  color: inherit;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-v8-rail > .min-h-0.flex-1 .space-y-1 > button {
  min-height: 54px !important;
  gap: 8px !important;
  align-items: center !important;
  overflow: hidden !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-v8-rail > .min-h-0.flex-1 .space-y-1 > button > span:last-child:not(.tcs-ref-conversation-title) {
  flex: 0 0 auto;
}

/* Conversation tools: compact and aligned to the trigger instead of covering the center workspace. */
html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tcs-v16-tools-menu {
  left: auto !important;
  right: 0 !important;
  width: 300px !important;
  max-height: min(560px, calc(100vh - 180px));
  overflow-y: auto;
  border: 1px solid #e8dfcb !important;
  border-radius: 18px !important;
  background: rgba(255,253,248,.985) !important;
  box-shadow: 0 18px 44px rgba(36,27,12,.16) !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1[dir="rtl"] .tcs-v16-tools-menu {
  right: auto !important;
  left: 0 !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tcs-v16-tools-menu .tcs-v8-toolbar-menu-actions button,
html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tcs-v16-tools-menu > .grid button,
html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tcs-v16-status-segment button {
  min-height: 38px;
  border-radius: 11px !important;
  box-shadow: none !important;
}

/* Details drawer: always use the workspace edge, never sit on top of conversation navigation. */
html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-details-panel {
  padding: 10px !important;
  background: rgba(27,24,20,.16) !important;
  backdrop-filter: blur(4px) !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1[dir="ltr"] .tos-chat-details-panel > div {
  width: min(380px, 92%) !important;
  margin-left: auto !important;
  margin-right: 0 !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1[dir="rtl"] .tos-chat-details-panel > div {
  width: min(380px, 92%) !important;
  margin-right: auto !important;
  margin-left: 0 !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-details-panel > div {
  border: 1px solid #e9e5dd !important;
  border-radius: 18px !important;
  background: #fbfaf7 !important;
  box-shadow: 0 20px 54px rgba(28,24,18,.18) !important;
}

/* Main command/search region: a little tighter and clearer. */
html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-command-center {
  padding-block: 15px !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tcs-v16-inline-search-shell {
  min-height: 48px !important;
  border-radius: 13px !important;
}

html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tos-chat-empty-clean-card {
  max-width: 450px !important;
  padding: 32px 30px !important;
}

/* Keep the left navigation quiet; active destination is the only strong accent. */
html:not(.dark) .tcs-desktop-window .tcs-ref-primary-nav-item {
  min-height: 56px !important;
  color: #77747a !important;
}

html:not(.dark) .tcs-desktop-window .tcs-ref-primary-nav-item.is-active {
  color: #9b690a !important;
  background: #fbf5e6 !important;
  box-shadow: inset 3px 0 0 #c89224 !important;
}

@media (max-width: 1180px) {
  html:not(.dark) .tcs-desktop-window .tcs-reference-lock-v1 .tcs-ref-conversation-title {
    max-width: 170px;
  }
}
''', encoding="utf-8")

print(f"PATCH={PATCH}")
print("CONVERSATION_TITLES=COMPACT")
print("TOOLS_PANEL=COMPACT_EDGE_ALIGNED")
print("DETAILS_DRAWER=EDGE_ALIGNED")
print("TOOLS_DETAILS_EXCLUSIVE=YES")
print("VISUAL_POLISH=PASS")
print("BACKEND_UNCHANGED=YES")
print(f"BACKUP_DIR={backup_dir}")
print("NEXT=BUILD_AND_DEPLOY_FRONTEND")
