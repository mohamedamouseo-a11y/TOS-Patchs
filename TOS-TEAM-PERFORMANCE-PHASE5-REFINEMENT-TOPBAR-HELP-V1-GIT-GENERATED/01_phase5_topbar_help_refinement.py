#!/usr/bin/env python3
from pathlib import Path

ROOT = Path('/var/www/TOS')
APP = ROOT / 'frontend/src/App.jsx'
TOPBAR = ROOT / 'frontend/src/components/layout/Topbar.jsx'
DASHBOARD = ROOT / 'frontend/src/pages/TeamPerformanceDashboard.jsx'
HELP = ROOT / 'frontend/src/components/performance/TeamPerformanceHelpCenter.jsx'

for path, key in [(APP, 'APP'), (TOPBAR, 'TOPBAR'), (DASHBOARD, 'DASHBOARD'), (HELP, 'HELP')]:
    if not path.exists():
        raise SystemExit(f'PHASE5_TOPBAR_HELP_ERROR={key}_NOT_FOUND')

help_text = HELP.read_text(encoding='utf-8')
if 'export function TeamPerformanceHelpCenter' not in help_text:
    raise SystemExit('PHASE5_TOPBAR_HELP_ERROR=HELP_COMPONENT_NOT_PHASE5')

# -----------------------------------------------------------------------------
# Topbar: add a context help icon beside notifications.
# -----------------------------------------------------------------------------
topbar = TOPBAR.read_text(encoding='utf-8')

old = 'import { Bell, Menu, Moon, Plus, Sun, UserRound } from "lucide-react";'
new = 'import { Bell, CircleHelp, Menu, Moon, Plus, Sun, UserRound } from "lucide-react";'
if old not in topbar:
    raise SystemExit('PHASE5_TOPBAR_HELP_ERROR=TOPBAR_IMPORT_ANCHOR_NOT_FOUND')
topbar = topbar.replace(old, new, 1)

old = 'export function Topbar({ title, subtitle, actionLabel, onAction, onOpenSidebar, menuButtonRef, user, onProfileClick, onNotificationsClick, notificationUnreadCount = 0 }) {'
new = 'export function Topbar({ title, subtitle, actionLabel, onAction, onOpenSidebar, menuButtonRef, user, onProfileClick, onNotificationsClick, notificationUnreadCount = 0, onHelpClick = null }) {'
if old not in topbar:
    raise SystemExit('PHASE5_TOPBAR_HELP_ERROR=TOPBAR_SIGNATURE_ANCHOR_NOT_FOUND')
topbar = topbar.replace(old, new, 1)

notification_anchor = '''        <button
          type="button"
          onClick={onNotificationsClick}
          className="tos-premium-topbar-icon-button relative grid h-10 w-10 shrink-0 place-items-center rounded-xl border border-transparent bg-white text-zinc-600 transition hover:border-amber-200 hover:bg-amber-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-400 dark:bg-zinc-900 dark:text-zinc-300 dark:hover:bg-zinc-800"
          title={isEnglish ? "Open notifications" : "فتح مركز الإشعارات"}
          aria-label={isEnglish ? "Open notifications" : "فتح مركز الإشعارات"}
        >'''
help_button = '''        {onHelpClick ? (
          <button
            type="button"
            onClick={onHelpClick}
            className="tos-premium-topbar-icon-button grid h-10 w-10 shrink-0 place-items-center rounded-xl border border-transparent bg-white text-zinc-600 transition hover:border-amber-200 hover:bg-amber-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-400 dark:bg-zinc-900 dark:text-amber-300 dark:hover:bg-zinc-800"
            title={isEnglish ? "Help Center" : "مركز المساعدة"}
            aria-label={isEnglish ? "Open Help Center" : "فتح مركز المساعدة"}
          >
            <CircleHelp size={18} />
          </button>
        ) : null}

'''
if notification_anchor not in topbar:
    raise SystemExit('PHASE5_TOPBAR_HELP_ERROR=NOTIFICATION_BUTTON_ANCHOR_NOT_FOUND')
topbar = topbar.replace(notification_anchor, help_button + notification_anchor, 1)
TOPBAR.write_text(topbar, encoding='utf-8')

# -----------------------------------------------------------------------------
# App: expose contextual help only on Team Performance for now.
# This avoids a dead global button on pages whose help content does not exist yet.
# -----------------------------------------------------------------------------
app = APP.read_text(encoding='utf-8')
old = '''            onNotificationsClick={() => setTncOpen((value) => !value)}
            notificationUnreadCount={tncUnreadCount}
          />'''
new = '''            onNotificationsClick={() => setTncOpen((value) => !value)}
            notificationUnreadCount={tncUnreadCount}
            onHelpClick={active === "teamPerformance" ? () => window.dispatchEvent(new CustomEvent("tos:team-performance-help", { detail: { article: "overview" } })) : null}
          />'''
if old not in app:
    raise SystemExit('PHASE5_TOPBAR_HELP_ERROR=APP_TOPBAR_ANCHOR_NOT_FOUND')
app = app.replace(old, new, 1)
APP.write_text(app, encoding='utf-8')

# -----------------------------------------------------------------------------
# Team Performance: remove duplicate page-level Help button and listen to Topbar.
# Keep the existing Phase 5 Help Center component/state/search/content unchanged.
# -----------------------------------------------------------------------------
dashboard = DASHBOARD.read_text(encoding='utf-8')

old = '  CircleHelp,\n  Download,'
new = '  Download,'
if old not in dashboard:
    raise SystemExit('PHASE5_TOPBAR_HELP_ERROR=DASHBOARD_CIRCLE_HELP_IMPORT_NOT_FOUND')
dashboard = dashboard.replace(old, new, 1)

old = '''  function openHelpCenter(articleKey = "overview") {
    setHelpArticle(articleKey);
    setHelpCenterOpen(true);
  }

  async function exportReport(format) {'''
new = '''  function openHelpCenter(articleKey = "overview") {
    setHelpArticle(articleKey);
    setHelpCenterOpen(true);
  }

  useEffect(() => {
    if (typeof window === "undefined") return undefined;
    const handleTopbarHelp = (event) => openHelpCenter(event?.detail?.article || "overview");
    window.addEventListener("tos:team-performance-help", handleTopbarHelp);
    return () => window.removeEventListener("tos:team-performance-help", handleTopbarHelp);
  }, []);

  async function exportReport(format) {'''
if old not in dashboard:
    raise SystemExit('PHASE5_TOPBAR_HELP_ERROR=DASHBOARD_HELP_FUNCTION_ANCHOR_NOT_FOUND')
dashboard = dashboard.replace(old, new, 1)

old = '''        actions={<div className="flex flex-wrap items-center gap-2"><button type="button" onClick={() => openHelpCenter("overview")} className="inline-flex items-center gap-2 rounded-xl border border-zinc-200 bg-white px-3 py-2 text-xs font-black text-zinc-700 hover:border-amber-300 hover:text-amber-700 dark:border-white/10 dark:bg-white/[0.03] dark:text-zinc-200 dark:hover:border-amber-400/30 dark:hover:text-amber-300"><CircleHelp size={15} /> Help Center</button>{canManageTargets ? <button type="button" onClick={openTargetManager} className="rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-xs font-black text-amber-700 hover:bg-amber-100 dark:border-amber-400/20 dark:bg-amber-400/10 dark:text-amber-300">Manage Targets</button> : null}<Badge tone="success"><ShieldCheck size={14} /> Live data</Badge></div>}
'''
new = '''        actions={<div className="flex items-center gap-2">{canManageTargets ? <button type="button" onClick={openTargetManager} className="rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-xs font-black text-amber-700 hover:bg-amber-100 dark:border-amber-400/20 dark:bg-amber-400/10 dark:text-amber-300">Manage Targets</button> : null}<Badge tone="success"><ShieldCheck size={14} /> Live data</Badge></div>}
'''
if old not in dashboard:
    raise SystemExit('PHASE5_TOPBAR_HELP_ERROR=PAGE_LEVEL_HELP_BUTTON_ANCHOR_NOT_FOUND')
dashboard = dashboard.replace(old, new, 1)

DASHBOARD.write_text(dashboard, encoding='utf-8')

print('PHASE5_TOPBAR_HELP_REFINEMENT_APPLIED=YES')
print('TOPBAR_HELP_ICON=YES')
print('TOPBAR_HELP_POSITION=BESIDE_NOTIFICATIONS')
print('PAGE_LEVEL_HELP_BUTTON_REMOVED=YES')
print('HELP_CENTER_COMPONENT_REUSED=YES')
print('TEAM_PERFORMANCE_CONTEXT_ONLY=YES')
print('RAMZY_CHANGED=NO')
print('BACKEND_CHANGED=NO')
print('SCHEMA_CHANGED=NO')
