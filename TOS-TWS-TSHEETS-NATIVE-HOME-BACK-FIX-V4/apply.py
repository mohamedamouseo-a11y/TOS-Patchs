from pathlib import Path
import re, sys

root = Path("/var/www/TOS")
title_p = root/"vendor/tsheets-casual-upstream/apps/web/src/shell/TitleBar.tsx"
app_p = root/"vendor/tsheets-casual-upstream/apps/web/src/App.tsx"
home_p = root/"vendor/tsheets-casual-upstream/apps/web/src/home/HomeScreen.tsx"

def rw(p):
    if not p.exists():
        raise SystemExit(f"MISSING:{p}")
    return p.read_text()

title, app, home = rw(title_p), rw(app_p), rw(home_p)

# TitleBar: one deterministic event, no prop/fallback navigation.
title = re.sub(r"export function TitleBar\(\{ onBackHome \}: \{ onBackHome\?: \(\) => void \} = \{\}\) \{",
               "export function TitleBar() {", title)
title = title.replace("onClick={() => (onBackHome ? onBackHome() : navigate('/home'))}",
'''onClick={() => {
          window.dispatchEvent(new CustomEvent('tos:tsheets-open-home'));
        }}''')
title = title.replace("onClick={() => navigate('/home')}",
'''onClick={() => {
          window.dispatchEvent(new CustomEvent('tos:tsheets-open-home'));
        }}''')

# App: remove V2/V3 cross-component forced-home plumbing entirely.
app = re.sub(r"\n\s*const \[homeForcedOpen, setHomeForcedOpen\] = useState\(false\);", "", app)
app = re.sub(r"\n\s*useEffect\(\(\) => \{\s*const openHome = \(\) => \{\s*setHomeForcedOpen\(true\);\s*setHomeDismissed\(false\);\s*\};\s*window\.addEventListener\('tos:tsheets-open-home', openHome\);\s*return \(\) => \{\s*window\.removeEventListener\('tos:tsheets-open-home', openHome\);\s*\};\s*\}, \[\]\);", "", app, flags=re.S)
app = re.sub(r"<TitleBar\s+onBackHome=\{\(\) => \{.*?\}\}\s*/>", "<TitleBar />", app, flags=re.S)
app = re.sub(r"\s*forceVisible=\{homeForcedOpen\}\n", "\n", app)
app = re.sub(r"onDismiss=\{\(\) => \{\s*setHomeForcedOpen\(false\);\s*setHomeDismissed\(true\);\s*\}\}",
             "onDismiss={() => setHomeDismissed(true)}", app, flags=re.S)

# HomeScreen owns the forced-open event locally. This is the same component
# that already renders the known-good Home/Recent/Templates surface.
if "TOS_TSHEETS_NATIVE_HOME_LOCAL_EVENT_V4" not in home:
    home = home.replace("import { useEffect, useMemo, useState } from 'react';",
                        "import { useCallback, useEffect, useMemo, useState } from 'react';")
    home = re.sub(r"\n\s*forceVisible = false,", "", home)
    home = re.sub(r"\n\s*forceVisible\?: boolean;", "", home)
    home = home.replace("onDismiss();", "dismissHome();")
    home = home.replace("onClick={onDismiss}", "onClick={dismissHome}")
    home = home.replace("[visible, onDismiss]", "[visible, dismissHome]")
    marker = "  const [collapsed, setCollapsed] = useState(false);"
    inject = marker + '''

  // TOS_TSHEETS_NATIVE_HOME_LOCAL_EVENT_V4
  const [forcedOpen, setForcedOpen] = useState(false);
  const dismissHome = useCallback(() => {
    setForcedOpen(false);
    onDismiss();
  }, [onDismiss]);

  useEffect(() => {
    const openHome = () => {
      setView('home');
      setForcedOpen(true);
    };
    window.addEventListener('tos:tsheets-open-home', openHome);
    return () => window.removeEventListener('tos:tsheets-open-home', openHome);
  }, []);
'''
    if marker not in home:
        raise SystemExit("ANCHOR_MISSING:collapsed")
    home = home.replace(marker, inject, 1)
    home = home.replace("const visible = !dismissed && (forceVisible || isBlank) && !inCollabRoom;",
                        "const visible = (forcedOpen || (!dismissed && isBlank)) && !inCollabRoom;")
    home = home.replace("const visible = !dismissed && isBlank && !inCollabRoom;",
                        "const visible = (forcedOpen || (!dismissed && isBlank)) && !inCollabRoom;")

# Guards.
if "data-testid=\"titlebar-back-home\"" not in title or "tos:tsheets-open-home" not in title:
    raise SystemExit("VERIFY_FAIL:title")
if "homeForcedOpen" in app or "onBackHome=" in app:
    raise SystemExit("VERIFY_FAIL:app_old_plumbing")
for needle in ["TOS_TSHEETS_NATIVE_HOME_LOCAL_EVENT_V4", "forcedOpen || (!dismissed && isBlank)", "setView('home')"]:
    if needle not in home:
        raise SystemExit("VERIFY_FAIL:home:"+needle)

title_p.write_text(title)
app_p.write_text(app)
home_p.write_text(home)
print("PATCH=PASS")
print("FILES=TitleBar.tsx,App.tsx,HomeScreen.tsx")
print("MODEL=LOCAL_HOMESCREEN_EVENT")
