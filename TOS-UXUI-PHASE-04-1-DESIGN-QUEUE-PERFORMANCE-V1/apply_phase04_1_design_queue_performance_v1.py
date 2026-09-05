from pathlib import Path
import subprocess, sys, hashlib

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
DQ = ROOT / "frontend/src/pages/DesignQueuePage.jsx"
PREF = ROOT / "frontend/src/contexts/PreferencesContext.jsx"
CSS = ROOT / "frontend/src/index.css"
MARKER = "TOS_DQ_PERFORMANCE_V1"
DQ_PRE_SHA = "d1a7d362d18506582e61f2a6f552fb88793bebd8174c3b6d60c74a3214a9cb3c"
CSS_V6_SHA = "2fa061485f20af185aeae3df1fe99033cbf12d2babe31f87c0f2e776e31fcb13"

print("RUNNING=PHASE04_1_DESIGN_QUEUE_PERFORMANCE_V1")

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 match, found {count}")
    return text.replace(old, new, 1)

if sha(CSS) != CSS_V6_SHA:
    raise RuntimeError("V6 CSS state mismatch")

if MARKER not in DQ.read_text():
    if sha(DQ) != DQ_PRE_SHA:
        raise RuntimeError("Design Queue source differs from verified V6 state")

    dq = DQ.read_text()
    pref = PREF.read_text()

    dq = replace_once(dq, 'import { useEffect, useMemo, useRef, useState } from "react";', 'import { memo, useEffect, useMemo, useRef, useState } from "react";', 'react import')
    dq = replace_once(dq, 'import { usePreferences } from "../contexts/PreferencesContext";', 'import { useLanguagePreferences } from "../contexts/PreferencesContext";', 'preferences import')
    dq = replace_once(dq, 'export function DesignQueuePage({ user, projects = [] }) {\n  const { lang, isAr } = usePreferences();', 'function DesignQueuePageComponent({ user, projects = [] }) {\n  // TOS_DQ_PERFORMANCE_V1: keep theme toggles from re-rendering the full queue.\n  const { lang, isAr } = useLanguagePreferences();', 'component declaration')
    dq = replace_once(dq, 'async function loadQueue(nextFilters = filters, { preserveModal = true } = {}) {', 'async function loadQueue(nextFilters = filters, { preserveModal = true, silent = false } = {}) {', 'loadQueue signature')
    dq = replace_once(dq, 'pendingQueueLoadRef.current = { nextFilters, preserveModal };', 'pendingQueueLoadRef.current = { nextFilters, preserveModal, silent };', 'pending queue')
    dq = replace_once(dq, '        setLoading(true);', '        if (!silent) setLoading(true);', 'loading start')
    dq = replace_once(dq, '        setLoading(false);', '        if (!silent) setLoading(false);', 'loading stop')
    dq = replace_once(dq, 'if (pending) void loadQueue(pending.nextFilters, { preserveModal: pending.preserveModal });', 'if (pending) void loadQueue(pending.nextFilters, { preserveModal: pending.preserveModal, silent: pending.silent });', 'pending replay')
    dq = replace_once(dq, 'refreshTimerRef.current = window.setTimeout(() => loadQueue(filters), delay);', 'refreshTimerRef.current = window.setTimeout(() => loadQueue(filters, { silent: true }), delay);', 'silent refresh')
    dq = replace_once(dq, '    function handleFocus() {\n      if (Date.now() - lastQueueLoadAtRef.current < 15_000) return;\n      scheduleRefresh({ at: Date.now() });\n    }\n', '', 'focus handler')
    dq = replace_once(dq, '    window.addEventListener("focus", handleFocus);\n', '', 'focus add')
    dq = replace_once(dq, '      window.removeEventListener("focus", handleFocus);\n', '', 'focus remove')
    dq = dq.rstrip() + '\n\nexport const DesignQueuePage = memo(DesignQueuePageComponent);\n'

    pref = replace_once(pref, 'const PreferencesContext = createContext(null);', 'const PreferencesContext = createContext(null);\nconst LanguagePreferencesContext = createContext(null);', 'language context')
    old = '''  return (\n    <PreferencesContext.Provider value={value}>\n      {children}\n    </PreferencesContext.Provider>\n  );'''
    new = '''  const languageValue = useMemo(() => ({\n    lang, isAr, setLang, setUserLang, applyDefaultLang,\n    toggleLang: () => setUserLang(l => l === "ar" ? "en" : "ar"),\n  }), [lang, isAr, setLang, setUserLang, applyDefaultLang]);\n\n  return (\n    <PreferencesContext.Provider value={value}>\n      <LanguagePreferencesContext.Provider value={languageValue}>\n        {children}\n      </LanguagePreferencesContext.Provider>\n    </PreferencesContext.Provider>\n  );'''
    pref = replace_once(pref, old, new, 'provider split')
    pref = pref.rstrip() + '''\n\nexport function useLanguagePreferences() {\n  const ctx = useContext(LanguagePreferencesContext);\n  if (!ctx) throw new Error("useLanguagePreferences must be inside PreferencesProvider");\n  return ctx;\n}\n'''

    DQ.write_text(dq)
    PREF.write_text(pref)

if DQ.read_text().count(MARKER) != 1:
    raise RuntimeError("performance marker invalid")
if 'window.addEventListener("focus", handleFocus)' in DQ.read_text():
    raise RuntimeError("focus refetch still present")
if DQ.read_text().count('loadQueue(filters, { silent: true })') != 1:
    raise RuntimeError("silent background refresh missing")
if PREF.read_text().count('export function useLanguagePreferences()') != 1:
    raise RuntimeError("language-only hook missing")
if sha(CSS) != CSS_V6_SHA:
    raise RuntimeError("V6 CSS changed unexpectedly")

subprocess.run(["npm", "run", "build"], cwd=ROOT / "frontend", check=True)

print("PHASE04_1_DESIGN_QUEUE_PERFORMANCE_V1=PASS")
print("FOCUS_REFETCH_REMOVED=YES")
print("BACKGROUND_REFRESH_SILENT=YES")
print("THEME_QUEUE_RERENDER_GUARD=YES")
print("BUSINESS_LOGIC_CHANGED=NO")
print("DESIGN_CHANGED=NO")
print("BUILD_RESULT=PASS")
print(f"DESIGN_QUEUE_SHA256={sha(DQ)}")
print(f"PREFERENCES_CONTEXT_SHA256={sha(PREF)}")
print(f"INDEX_CSS_SHA256={sha(CSS)}")
