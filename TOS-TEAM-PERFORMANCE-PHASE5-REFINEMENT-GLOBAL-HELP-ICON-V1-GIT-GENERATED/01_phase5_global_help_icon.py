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
# Topbar owns the Help Center globally so the ? icon is present on every page
# for every authenticated user. The existing Team Performance help content is
# reused unchanged; future phases can make the content page-contextual.
# -----------------------------------------------------------------------------
topbar = TOPBAR.read_text(encoding='utf-8')

old = 'import { Bell, CircleHelp, Menu, Moon, Plus, Sun, UserRound } from "lucide-react";\n'
new = 'import { useState } from "react";\n' + old
if old not in topbar or 'import { useState } from "react";' in topbar:
    raise SystemExit('PHASE5_GLOBAL_HELP_ERROR=TOPBAR_REACT_IMPORT_ANCHOR_NOT_FOUND')
topbar = topbar.replace(old, new, 1)

old = 'import { usePreferences } from "../../contexts/PreferencesContext";\n'
new = old + 'import { TeamPerformanceHelpCenter } from "../performance/TeamPerformanceHelpCenter";\n'
if old not in topbar or 'TeamPerformanceHelpCenter' in topbar:
    raise SystemExit('PHASE5_GLOBAL_HELP_ERROR=TOPBAR_HELP_IMPORT_ANCHOR_NOT_FOUND')
topbar = topbar.replace(old, new, 1)

old = 'export function Topbar({ title, subtitle, actionLabel, onAction, onOpenSidebar, menuButtonRef, user, onProfileClick, onNotificationsClick, notificationUnreadCount = 0, onHelpClick = null }) {'
new = 'export function Topbar({ title, subtitle, actionLabel, onAction, onOpenSidebar, menuButtonRef, user, onProfileClick, onNotificationsClick, notificationUnreadCount = 0 }) {'
if old not in topbar:
    raise SystemExit('PHASE5_GLOBAL_HELP_ERROR=TOPBAR_SIGNATURE_ANCHOR_NOT_FOUND')
topbar = topbar.replace(old, new, 1)

old = '  const isEnglish = lang === "en";\n  const displayName = user?.name || user?.email || (isEnglish ? "User" : "مستخدم");\n'
new = '  const isEnglish = lang === "en";\n  const [helpOpen, setHelpOpen] = useState(false);\n  const displayName = user?.name || user?.email || (isEnglish ? "User" : "مستخدم");\n'
if old not in topbar:
    raise SystemExit('PHASE5_GLOBAL_HELP_ERROR=TOPBAR_STATE_ANCHOR_NOT_FOUND')
topbar = topbar.replace(old, new, 1)

old = '''        {onHelpClick ? (\n          <button\n            type="button"\n            onClick={onHelpClick}\n            className="tos-premium-topbar-icon-button grid h-10 w-10 shrink-0 place-items-center rounded-xl border border-transparent bg-white text-zinc-600 transition hover:border-amber-200 hover:bg-amber-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-400 dark:bg-zinc-900 dark:text-amber-300 dark:hover:bg-zinc-800"\n            title={isEnglish ? "Help Center" : "مركز المساعدة"}\n            aria-label={isEnglish ? "Open Help Center" : "فتح مركز المساعدة"}\n          >\n            <CircleHelp size={18} />\n          </button>\n        ) : null}\n\n'''
new = '''        <button\n          type="button"\n          onClick={() => setHelpOpen(true)}\n          className="tos-premium-topbar-icon-button grid h-10 w-10 shrink-0 place-items-center rounded-xl border border-transparent bg-white text-zinc-600 transition hover:border-amber-200 hover:bg-amber-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-400 dark:bg-zinc-900 dark:text-amber-300 dark:hover:bg-zinc-800"\n          title={isEnglish ? "Help Center" : "مركز المساعدة"}\n          aria-label={isEnglish ? "Open Help Center" : "فتح مركز المساعدة"}\n        >\n          <CircleHelp size={18} />\n        </button>\n\n'''
if old not in topbar:
    raise SystemExit('PHASE5_GLOBAL_HELP_ERROR=CONDITIONAL_HELP_BUTTON_NOT_FOUND')
topbar = topbar.replace(old, new, 1)

old = '    </header>\n  );\n}\n'
new = '''      <TeamPerformanceHelpCenter\n        open={helpOpen}\n        onClose={() => setHelpOpen(false)}\n        lang={lang}\n        initialArticle="overview"\n      />\n    </header>\n  );\n}\n'''
if old not in topbar:
    raise SystemExit('PHASE5_GLOBAL_HELP_ERROR=TOPBAR_RENDER_END_ANCHOR_NOT_FOUND')
topbar = topbar.replace(old, new, 1)
TOPBAR.write_text(topbar, encoding='utf-8')

# -----------------------------------------------------------------------------
# App no longer conditionally wires help to the Team Performance page.
# Topbar owns it globally.
# -----------------------------------------------------------------------------
app = APP.read_text(encoding='utf-8')
old = '            onHelpClick={active === "teamPerformance" ? () => window.dispatchEvent(new CustomEvent("tos:team-performance-help", { detail: { article: "overview" } })) : null}\n'
if old not in app:
    raise SystemExit('PHASE5_GLOBAL_HELP_ERROR=APP_CONTEXT_HELP_WIRING_NOT_FOUND')
app = app.replace(old, '', 1)
APP.write_text(app, encoding='utf-8')

# -----------------------------------------------------------------------------
# Team Performance no longer owns a duplicate Help Center instance/state.
# The global Topbar instance reuses the same component/content.
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
print('HELP_OWNER=TOPBAR')
print('EXISTING_HELP_COMPONENT_REUSED=YES')
print('DUPLICATE_PAGE_HELP_INSTANCE=NO')
print('RAMZY_CHANGED=NO')
print('BACKEND_CHANGED=NO')
print('SCHEMA_CHANGED=NO')
