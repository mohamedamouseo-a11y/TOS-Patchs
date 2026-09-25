#!/usr/bin/env python3
# TOS-TWS-TSHEETS-CASUAL-P02-B01-SIDEBAR-BRANDING-V1
from pathlib import Path
import sys

ROOT = Path("/var/www/TOS")
SIDEBAR = ROOT / "frontend/src/components/layout/Sidebar.jsx"
LAB = ROOT / "frontend/src/pages/tws/TSheetsCasualLab.jsx"
MARKER = "TOS_TWS_TSHEETS_CASUAL_P02_B01_SIDEBAR_BRANDING_V1"

def die(message):
    print("PATCH=FAIL")
    print(f"ERROR={message}")
    sys.exit(1)

def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        die(f"{label}: expected 1 anchor, found {count}")
    return text.replace(old, new, 1)

for path in (SIDEBAR, LAB):
    if not path.exists():
        die(f"MISSING:{path}")

sidebar = SIDEBAR.read_text(encoding="utf-8")

if MARKER not in sidebar:
    sidebar = replace_once(
        sidebar,
        '''  SlidersHorizontal,
  UsersRound,''',
        '''  SlidersHorizontal,
  Table2,
  UsersRound,''',
        "Table2 import",
    )

    sidebar = replace_once(
        sidebar,
        '''const SIDEBAR_COLLAPSED_KEY = "tamiyouz.sidebar.collapsed";


function getStoredSidebarCollapsed() {''',
        '''const SIDEBAR_COLLAPSED_KEY = "tamiyouz.sidebar.collapsed";

// TOS_TWS_TSHEETS_CASUAL_P02_B01_SIDEBAR_BRANDING_V1
const TWS_LAB_PATH = "/tws/sheets-lab";

function isTwsLabLocation() {
  if (typeof window === "undefined") return false;
  return /^\\/tws\\/sheets-lab\\/?$/.test(window.location.pathname);
}


function getStoredSidebarCollapsed() {''',
        "TWS Lab route constants",
    )

    sidebar = replace_once(
        sidebar,
        '''  const [activeSettingsSection, setActiveSettingsSection] = useState(readSettingsSectionFromLocation);
  const [collapsedTooltip, setCollapsedTooltip] = useState(null);

  const { lang } = usePreferences();''',
        '''  const [activeSettingsSection, setActiveSettingsSection] = useState(readSettingsSectionFromLocation);
  const [collapsedTooltip, setCollapsedTooltip] = useState(null);
  const [twsLabActive, setTwsLabActive] = useState(isTwsLabLocation);

  const { lang } = usePreferences();''',
        "TWS Lab active state",
    )

    sidebar = replace_once(
        sidebar,
        '''  }, [active]);

  useEffect(() => {
    function syncSettingsSection() {''',
        '''  }, [active]);

  useEffect(() => {
    function syncTwsLabRoute() {
      setTwsLabActive(isTwsLabLocation());
    }
    window.addEventListener("popstate", syncTwsLabRoute);
    syncTwsLabRoute();
    return () => window.removeEventListener("popstate", syncTwsLabRoute);
  }, []);

  useEffect(() => {
    function syncSettingsSection() {''',
        "TWS Lab route sync effect",
    )

    sidebar = replace_once(
        sidebar,
        '''  function selectPage(pageId) {
    if (pageId === "settings") {''',
        '''  function selectPage(pageId) {
    if (pageId === "tws") {
      setActive("tws");
      setTwsLabActive(false);
      if (!isCollapsedMode) setOpenMenuId("workspaceGroup");
      if (typeof window !== "undefined" && window.location.pathname !== "/tws") {
        window.history.pushState({ ...(window.history.state || {}), tosPage: "tws" }, "", "/tws");
        window.dispatchEvent(new Event("popstate"));
      }
      if (mobile) onClose?.();
      return;
    }

    if (pageId === "settings") {''',
        "TWS parent navigation",
    )

    sidebar = replace_once(
        sidebar,
        '''  function isModifiedNavigationClick(event) {
    return event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey;
  }''',
        '''  function selectTwsLab() {
    setActive("tws");
    setOpenMenuId("workspaceGroup");
    setTwsLabActive(true);
    if (typeof window !== "undefined" && window.location.pathname !== TWS_LAB_PATH) {
      window.history.pushState({ ...(window.history.state || {}), tosPage: "tws", tosTwsView: "sheetsLab" }, "", TWS_LAB_PATH);
    }
    if (typeof window !== "undefined") window.dispatchEvent(new Event("popstate"));
    if (mobile) onClose?.();
  }

  function isModifiedNavigationClick(event) {
    return event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey;
  }''',
        "TWS Lab navigation function",
    )

    old_map = '''            {children.map((subItem) => {
              const SubIcon = subItem.icon;
              const subSelected = item.id === "settings" ? active === "settings" && activeSettingsSection === subItem.id : active === subItem.id;
              return (
                <a
                  key={subItem.id}
                  href={item.id === "settings" ? settingsSectionHref(subItem.id) : pathForPage(subItem.id)}
                  onClick={(event) => handleNavigationLinkClick(event, () => item.id === "settings" ? selectSettingsSection(subItem.id) : selectPage(subItem.id))}
                  aria-current={subSelected ? "page" : undefined}
                  aria-label={subItem.label}
                  className={cn(
                    "group/sub relative flex w-full min-w-0 scroll-mt-14 items-center gap-2 rounded-xl px-3 py-2.5 text-start text-xs font-extrabold transition focus:outline-none focus:ring-2 focus:ring-amber-300/50",
                    subSelected
                      ? "bg-amber-50/80 text-slate-950 ring-1 ring-amber-200/60 before:absolute before:inset-y-2 before:start-0 before:w-1 before:rounded-full before:bg-amber-500 dark:bg-amber-500/10 dark:text-white"
                      : "text-slate-500 hover:bg-slate-50 hover:text-slate-900"
                  )}
                >
                  <SubIcon size={15} className={cn("shrink-0", subSelected ? "text-amber-600" : "text-slate-400 group-hover/sub:text-slate-600")} />
                  <span className="min-w-0 flex-1 whitespace-normal break-words leading-[1.3]">{subItem.label}</span>
                  <span className={cn("ms-auto h-1.5 w-1.5 rounded-full", subSelected ? "bg-amber-500" : "bg-slate-300")} />
                </a>
              );
            })}'''

    new_map = '''            {children.map((subItem) => {
              const SubIcon = subItem.icon;
              const subSelected = item.id === "settings" ? active === "settings" && activeSettingsSection === subItem.id : active === subItem.id;
              return (
                <div key={subItem.id} className="contents">
                  <a
                    href={item.id === "settings" ? settingsSectionHref(subItem.id) : pathForPage(subItem.id)}
                    onClick={(event) => handleNavigationLinkClick(event, () => item.id === "settings" ? selectSettingsSection(subItem.id) : selectPage(subItem.id))}
                    aria-current={subSelected ? "page" : undefined}
                    aria-label={subItem.label}
                    className={cn(
                      "group/sub relative flex w-full min-w-0 scroll-mt-14 items-center gap-2 rounded-xl px-3 py-2.5 text-start text-xs font-extrabold transition focus:outline-none focus:ring-2 focus:ring-amber-300/50",
                      subSelected
                        ? "bg-amber-50/80 text-slate-950 ring-1 ring-amber-200/60 before:absolute before:inset-y-2 before:start-0 before:w-1 before:rounded-full before:bg-amber-500 dark:bg-amber-500/10 dark:text-white"
                        : "text-slate-500 hover:bg-slate-50 hover:text-slate-900"
                    )}
                  >
                    <SubIcon size={15} className={cn("shrink-0", subSelected ? "text-amber-600" : "text-slate-400 group-hover/sub:text-slate-600")} />
                    <span className="min-w-0 flex-1 whitespace-normal break-words leading-[1.3]">{subItem.label}</span>
                    <span className={cn("ms-auto h-1.5 w-1.5 rounded-full", subSelected ? "bg-amber-500" : "bg-slate-300")} />
                  </a>
                  {item.id === "workspaceGroup" && subItem.id === "tws" && (
                    <a
                      href={TWS_LAB_PATH}
                      onClick={(event) => handleNavigationLinkClick(event, selectTwsLab)}
                      aria-current={twsLabActive ? "page" : undefined}
                      aria-label={lang === "en" ? "T-Sheets Lab" : "T-Sheets تجريبي"}
                      data-tws-tsheets-lab-nav="p02-b01-v1"
                      className={cn(
                        "group/tsheets relative ms-7 me-1 mt-1 flex min-w-0 items-center gap-2 rounded-xl border px-2.5 py-2 text-start text-[11px] font-black transition focus:outline-none focus:ring-2 focus:ring-emerald-300/50",
                        twsLabActive
                          ? "border-emerald-200 bg-emerald-50/90 text-emerald-900 shadow-sm dark:border-emerald-500/30 dark:bg-emerald-500/10 dark:text-emerald-100"
                          : "border-transparent text-slate-500 hover:border-emerald-100 hover:bg-emerald-50/60 hover:text-emerald-800 dark:text-zinc-400 dark:hover:bg-emerald-500/10 dark:hover:text-emerald-200"
                      )}
                    >
                      <Table2 size={14} className={cn("shrink-0", twsLabActive ? "text-emerald-600" : "text-emerald-500/80")} />
                      <span className="min-w-0 flex-1 truncate">{lang === "en" ? "T-Sheets Lab" : "T-Sheets تجريبي"}</span>
                      <span className="rounded-md bg-emerald-100 px-1.5 py-0.5 text-[8px] font-black tracking-wide text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-200">NEW</span>
                    </a>
                  )}
                </div>
              );
            })}'''

    sidebar = replace_once(sidebar, old_map, new_map, "Workspace nested T-Sheets link")
    SIDEBAR.write_text(sidebar, encoding="utf-8")

lab = LAB.read_text(encoding="utf-8")
if MARKER not in lab:
    expected = '''// TOS_TWS_TSHEETS_CASUAL_P01_B01_SIDE_BY_SIDE_INTEGRATION_V1
export function TSheetsCasualLab() {
  return (
    <section
      data-tsheets-casual-lab="p01-b01-v1"
      className="h-[calc(100dvh-64px)] min-h-[640px] w-full overflow-hidden bg-white"
    >
      <iframe
        title="TSheets Lab"
        src="/tws-casual-runtime/"
        className="h-full w-full border-0 bg-white"
        allow="clipboard-read; clipboard-write"
      />
    </section>
  );
}
'''
    if lab != expected:
        die("LAB_COMPONENT_BASELINE_MISMATCH")

    payload = Path("/tmp/tsheets-casual-p02-b01/TSheetsCasualLab.jsx")
    if not payload.exists():
        die("LAB_PAYLOAD_MISSING")
    LAB.write_text(payload.read_text(encoding="utf-8"), encoding="utf-8")

print("PATCH=PASS")
print("PATCH_NAME=TOS-TWS-TSHEETS-CASUAL-P02-B01-SIDEBAR-BRANDING-V1")
print("SIDEBAR_TWS_CHILD=T-Sheets Lab")
print("LAB_ROUTE=/tws/sheets-lab")
print("BRANDING_LAYER=SAME_ORIGIN_IFRAME")
print("UPSTREAM_SOURCE_CHANGED=NO")
print("OLD_TSHEETS_CHANGED=NO")
print("BACKEND_CHANGED=NO")
print("DB_CHANGED=NO")
