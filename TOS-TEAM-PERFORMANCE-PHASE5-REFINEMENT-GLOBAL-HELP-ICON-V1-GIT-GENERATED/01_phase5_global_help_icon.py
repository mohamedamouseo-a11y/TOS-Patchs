#!/usr/bin/env python3
from pathlib import Path

ROOT = Path('/var/www/TOS')
APP = ROOT / 'frontend/src/App.jsx'
TOPBAR = ROOT / 'frontend/src/components/layout/Topbar.jsx'
DASHBOARD = ROOT / 'frontend/src/pages/TeamPerformanceDashboard.jsx'
HELP = ROOT / 'frontend/src/components/performance/TeamPerformanceHelpCenter.jsx'

for path, key in [(APP, 'APP'), (TOPBAR, 'TOPBAR'), (DASHBOARD, 'DASHBOARD'), (HELP, 'HELP')]:
    if not path.exists():
        raise SystemExit(f'PHASE5_GLOBAL_HELP_ERROR={key}_NOT_FOUND')

help_text = HELP.read_text(encoding='utf-8')
if 'export function TeamPerformanceHelpCenter' not in help_text:
    raise SystemExit('PHASE5_GLOBAL_HELP_ERROR=HELP_COMPONENT_NOT_PHASE5')

# -----------------------------------------------------------------------------
# Topbar: keep ? visible on every authenticated TOS page. It emits one global
# help event; App owns the modal outside the sticky/backdrop-filter header.
# -----------------------------------------------------------------------------
topbar = TOPBAR.read_text(encoding='utf-8')

old = 'export function Topbar({ title, subtitle, actionLabel, onAction, onOpenSidebar, menuButtonRef, user, onProfileClick, onNotificationsClick, notificationUnreadCount = 0, onHelpClick = null }) {'
new = 'export function Topbar({ title, subtitle, actionLabel, onAction, onOpenSidebar, menuButtonRef, user, onProfileClick, onNotificationsClick, notificationUnreadCount = 0 }) {'
if old not in topbar:
    raise SystemExit('PHASE5_GLOBAL_HELP_ERROR=TOPBAR_SIGNATURE_ANCHOR_NOT_FOUND')
topbar = topbar.replace(old, new, 1)

old = '''        {onHelpClick ? (\n          <button\n            type="button"\n            onClick={onHelpClick}\n            className="tos-premium-topbar-icon-button grid h-10 w-10 shrink-0 place-items-center rounded-xl border border-transparent bg-white text-zinc-600 transition hover:border-amber-200 hover:bg-amber-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-400 dark:bg-zinc-900 dark:text-amber-300 dark:hover:bg-zinc-800"\n            title={isEnglish ? "Help Center" : "مركز المساعدة"}\n            aria-label={isEnglish ? "Open Help Center" : "فتح مركز المساعدة"}\n          >\n            <CircleHelp size={18} />\n          </button>\n        ) : null}\n\n'''
new = '''        <button\n          type="button"\n          onClick={() => window.dispatchEvent(new CustomEvent("tos:global-help", { detail: { article: "overview" } }))}\n          className="tos-premium-topbar-icon-button grid h-10 w-10 shrink-0 place-items-center rounded-xl border border-transparent bg-white text-zinc-600 transition hover:border-amber-200 hover:bg-amber-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-400 dark:bg-zinc-900 dark:text-amber-300 dark:hover:bg-zinc-800"\n          title={isEnglish ? "Help Center" : "مركز المساعدة"}\n          aria-label={isEnglish ? "Open Help Center" : "فتح مركز المساعدة"}\n        >\n          <CircleHelp size={18} />\n        </button>\n\n'''
if old not in topbar:
    raise SystemExit('PHASE5_GLOBAL_HELP_ERROR=CONDITIONAL_HELP_BUTTON_NOT_FOUND')
topbar = topbar.replace(old, new, 1)
TOPBAR.write_text(topbar, encoding='utf-8')

# -----------------------------------------------------------------------------
# App: mount one global Help Center bridge outside Topbar so fixed positioning
# is viewport-safe. It is available on every normal authenticated TOS page.
# -----------------------------------------------------------------------------
app = APP.read_text(encoding='utf-8')

old = 'import { TncNotificationCenter } from "./components/TncNotificationCenter";\n'
new = old + 'import { TeamPerformanceHelpCenter } from "./components/performance/TeamPerformanceHelpCenter";\n'
if old not in app or 'import { TeamPerformanceHelpCenter }' in app:
    raise SystemExit('PHASE5_GLOBAL_HELP_ERROR=APP_HELP_IMPORT_ANCHOR_NOT_FOUND')
app = app.replace(old, new, 1)

old = '''function SystemPageLoading({ label = "Loading..." }) {'''
new = '''function GlobalHelpCenterBridge({ lang = "en" }) {\n  const [open, setOpen] = useState(false);\n  const [article, setArticle] = useState("overview");\n\n  useEffect(() => {\n    if (typeof window === "undefined") return undefined;\n    const handleOpen = (event) => {\n      setArticle(event?.detail?.article || "overview");\n      setOpen(true);\n    };\n    window.addEventListener("tos:global-help", handleOpen);\n    return () => window.removeEventListener("tos:global-help", handleOpen);\n  }, []);\n\n  return (\n    <TeamPerformanceHelpCenter\n      open={open}\n      onClose={() => setOpen(false)}\n      lang={lang}\n      initialArticle={article}\n    />\n  );\n}\n\nfunction SystemPageLoading({ label = "Loading..." }) {'''
if old not in app:
    raise SystemExit('PHASE5_GLOBAL_HELP_ERROR=APP_BRIDGE_ANCHOR_NOT_FOUND')
app = app.replace(old, new, 1)

old = '            notificationUnreadCount={tncUnreadCount}\n            onHelpClick={active === "teamPerformance" ? () => window.dispatchEvent(new CustomEvent("tos:team-performance-help", { detail: { article: "overview" } })) : null}\n          />'
new = '            notificationUnreadCount={tncUnreadCount}\n          />'
if old not in app:
    raise SystemExit('PHASE5_GLOBAL_HELP_ERROR=APP_CONTEXT_HELP_WIRING_NOT_FOUND')
app = app.replace(old, new, 1)

old = '        <main className="tos-premium-main-shell min-w-0 flex-1 overflow-hidden rounded-[26px] border border-zinc-200/70 bg-app-card shadow-[0_20px_60px_rgba(15,23,42,0.08)] ring-1 ring-white/80 dark:border-white/10 dark:ring-white/5">\n          <Topbar\n'
new = '        <main className="tos-premium-main-shell min-w-0 flex-1 overflow-hidden rounded-[26px] border border-zinc-200/70 bg-app-card shadow-[0_20px_60px_rgba(15,23,42,0.08)] ring-1 ring-white/80 dark:border-white/10 dark:ring-white/5">\n          <GlobalHelpCenterBridge lang={lang} />\n          <Topbar\n'
if old not in app:
    raise SystemExit('PHASE5_GLOBAL_HELP_ERROR=APP_GLOBAL_RENDER_ANCHOR_NOT_FOUND')
app = app.replace(old, new, 1)
APP.write_text(app, encoding='utf-8')

# -----------------------------------------------------------------------------
# Team Performance: remove the page-owned duplicate help state/listener/render.
# Help content component itself remains unchanged and is now mounted globally.
# -----------------------------------------------------------------------------
dashboard = DASHBOARD.read_text(encoding='utf-8')

old = 'import { TeamPerformanceHelpCenter } from "../components/performance/TeamPerformanceHelpCenter";\n'
if old not in dashboard:
    raise SystemExit('PHASE5_GLOBAL_HELP_ERROR=DASHBOARD_HELP_IMPORT_NOT_FOUND')
dashboard = dashboard.replace(old, '', 1)

old = '  const [toast, setToast] = useState(null);\n  const [helpCenterOpen, setHelpCenterOpen] = useState(false);\n  const [helpArticle, setHelpArticle] = useState("overview");\n\n  const [intelligenceData, setIntelligenceData] = useState(null);'
new = '  const [toast, setToast] = useState(null);\n\n  const [intelligenceData, setIntelligenceData] = useState(null);'
if old not in dashboard:
    raise SystemExit('PHASE5_GLOBAL_HELP_ERROR=DASHBOARD_HELP_STATE_NOT_FOUND')
dashboard = dashboard.replace(old, new, 1)

old = '''  function openHelpCenter(articleKey = "overview") {\n    setHelpArticle(articleKey);\n    setHelpCenterOpen(true);\n  }\n\n  useEffect(() => {\n    if (typeof window === "undefined") return undefined;\n    const handleTopbarHelp = (event) => openHelpCenter(event?.detail?.article || "overview");\n    window.addEventListener("tos:team-performance-help", handleTopbarHelp);\n    return () => window.removeEventListener("tos:team-performance-help", handleTopbarHelp);\n  }, []);\n\n'''
if old not in dashboard:
    raise SystemExit('PHASE5_GLOBAL_HELP_ERROR=DASHBOARD_HELP_EVENT_BLOCK_NOT_FOUND')
dashboard = dashboard.replace(old, '', 1)

old = '''      <TeamPerformanceHelpCenter\n        open={helpCenterOpen}\n        onClose={() => setHelpCenterOpen(false)}\n        lang={lang}\n        initialArticle={helpArticle}\n      />\n\n'''
if old not in dashboard:
    raise SystemExit('PHASE5_GLOBAL_HELP_ERROR=DASHBOARD_HELP_RENDER_NOT_FOUND')
dashboard = dashboard.replace(old, '', 1)
DASHBOARD.write_text(dashboard, encoding='utf-8')

print('PHASE5_GLOBAL_HELP_ICON_APPLIED=YES')
print('HELP_ICON_VISIBILITY=ALL_TOS_PAGES')
print('HELP_ICON_USERS=ALL_AUTHENTICATED_USERS')
print('HELP_MODAL_OWNER=APP_GLOBAL_BRIDGE')
print('EXISTING_HELP_COMPONENT_REUSED=YES')
print('DUPLICATE_PAGE_HELP_INSTANCE=NO')
print('RAMZY_CHANGED=NO')
print('BACKEND_CHANGED=NO')
print('SCHEMA_CHANGED=NO')
