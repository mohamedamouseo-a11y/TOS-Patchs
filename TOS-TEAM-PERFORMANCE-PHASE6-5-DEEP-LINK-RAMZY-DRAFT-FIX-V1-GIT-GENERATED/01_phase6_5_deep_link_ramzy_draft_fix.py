#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path("/var/www/TOS")


def load(rel):
    path = ROOT / rel
    return path, path.read_text(encoding="utf-8")


def save(path, text):
    path.write_text(text, encoding="utf-8")


def replace_if_needed(text, old, new, label):
    if new in text:
        return text
    count = text.count(old)
    if count == 1:
        return text.replace(old, new, 1)
    raise SystemExit(f"PHASE6_5_FIX_ERROR={label}_MATCH_COUNT_{count}")


def ensure_workflow_action(text, key, anchor, label_key):
    marker = f'key: "{key}"'
    start = text.find(marker)
    if start < 0:
        raise SystemExit(f"PHASE6_5_FIX_ERROR=WORKFLOW_{key}_NOT_FOUND")
    next_start = text.find('\n    {\n      key: ', start + len(marker))
    end = next_start if next_start >= 0 else len(text)
    block = text[start:end]
    desired = f'action: {{ page: "teamPerformance", anchor: "{anchor}", labelKey: "{label_key}" }}'
    if desired in block:
        return text
    pattern = re.compile(r'action: \{ page: "teamPerformance", anchor: "[^"]*", labelKey: "[^"]*" \}')
    updated, count = pattern.subn(desired, block, count=1)
    if count != 1:
        raise SystemExit(f"PHASE6_5_FIX_ERROR=WORKFLOW_{key}_ACTION_NOT_FOUND")
    return text[:start] + updated + text[end:]


def ensure_component_wrapper(text, component, dom_id):
    if f'id="{dom_id}"' in text:
        return text
    pattern = re.compile(rf"(?ms)^      <{re.escape(component)}\n.*?^      />$")
    match = pattern.search(text)
    if not match:
        raise SystemExit(f"PHASE6_5_FIX_ERROR={component}_BLOCK_NOT_FOUND")
    block = match.group(0)
    wrapped = f'      <div id="{dom_id}">\n{block}\n      </div>'
    return text[:match.start()] + wrapped + text[match.end():]


# App.jsx — resilient cross-page navigation + open closed disclosures.
app_path, app = load("frontend/src/App.jsx")
old_bridge = '''function HelpNavigateBridge({ setActive, setActiveProjectId }) {
  useEffect(() => {
    function handleNavigate(event) {
      const { page, section } = event.detail || {};
      if (!page) return;
      setActive(page);
      if (section) {
        requestAnimationFrame(() => {
          const el = document.getElementById(section);
          if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
        });
      }
    }
    window.addEventListener("tos:help-navigate", handleNavigate);
    return () => window.removeEventListener("tos:help-navigate", handleNavigate);
  }, [setActive, setActiveProjectId]);
  return null;
}'''
new_bridge = '''function HelpNavigateBridge({ setActive }) {
  useEffect(() => {
    let scrollTimer = null;

    function scrollToSection(section, attempt = 0) {
      if (!section) return;
      const el = document.getElementById(section);
      if (el) {
        const disclosure = el.matches?.("details") ? el : el.closest?.("details");
        if (disclosure && !disclosure.open) disclosure.open = true;
        requestAnimationFrame(() => el.scrollIntoView({ behavior: "smooth", block: "start" }));
        return;
      }
      if (attempt >= 20) return;
      scrollTimer = window.setTimeout(() => scrollToSection(section, attempt + 1), 75);
    }

    function handleNavigate(event) {
      const { page, section } = event.detail || {};
      if (!page) return;
      if (scrollTimer) {
        window.clearTimeout(scrollTimer);
        scrollTimer = null;
      }
      setActive(page);
      scrollToSection(section);
    }

    window.addEventListener("tos:help-navigate", handleNavigate);
    return () => {
      window.removeEventListener("tos:help-navigate", handleNavigate);
      if (scrollTimer) window.clearTimeout(scrollTimer);
    };
  }, [setActive]);
  return null;
}'''
if "function scrollToSection(section, attempt = 0)" not in app:
    app = replace_if_needed(app, old_bridge, new_bridge, "APP_BRIDGE")
app = replace_if_needed(
    app,
    '<HelpNavigateBridge setActive={setActive} setActiveProjectId={setActiveProjectId} />',
    '<HelpNavigateBridge setActive={setActive} />',
    "APP_BRIDGE_RENDER",
)
save(app_path, app)


# Help Center — normalize labels, anchors, and Arabic wording.
help_path, help_text = load("frontend/src/components/performance/TeamPerformanceHelpCenter.jsx")
old_labels = '''    summary: ["فتح الملخص الإداري", "Open management summary"],
    executive: ["فتح مركز القيادة", "Open Executive Command Center"],
    archive: ["فتح الأرشيف", "Open archive"],
    permissions: ["فتح الصلاحيات", "Open permissions"],'''
new_labels = '''    summary: ["فتح الملخص الإداري", "Open management summary"],
    goals: ["فتح الأهداف", "Open goals"],
    workforce: ["فتح تخطيط القوى العاملة", "Open workforce planning"],
    reviews: ["فتح المراجعات", "Open reviews"],
    skills: ["فتح المهارات", "Open skills"],
    talent: ["فتح المواهب", "Open talent"],
    recognition: ["فتح التقدير", "Open recognition"],
    executive: ["فتح مركز القيادة", "Open Executive Command Center"],
    archive: ["فتح الأرشيف", "Open archive"],
    permissions: ["فتح الصلاحيات", "Open permissions"],'''
if 'goals: ["فتح الأهداف", "Open goals"]' not in help_text:
    help_text = replace_if_needed(help_text, old_labels, new_labels, "HELP_ACTION_LABELS")

arabic_replacements = [
    (
        'tx("افتح الموظف أو الـDrill-down عندما تحتاج السبب وراء الرقم.", "Open employee detail or drill-down when you need the reason behind a number.")',
        'tx("افتح تفاصيل الموظف أو التفاصيل المتعمقة عندما تحتاج السبب وراء الرقم.", "Open employee detail or drill-down when you need the reason behind a number.")',
        "HELP_AR_DRILLDOWN_OVERVIEW",
    ),
    (
        'tx("افتح الـDrill-down وراجع المهمة والموعد والحالة والنشاط.", "Open drill-down and review the task, due date, status, and activity.")',
        'tx("افتح التفاصيل المتعمقة وراجع المهمة والموعد والحالة والنشاط.", "Open drill-down and review the task, due date, status, and activity.")',
        "HELP_AR_DRILLDOWN_OVERDUE",
    ),
]
for old, new, label in arabic_replacements:
    if old in help_text:
        help_text = replace_if_needed(help_text, old, new, label)

for key, anchor, label_key in [
    ("goals", "phase1-goals-disclosure", "goals"),
    ("workforce", "team-performance-workforce", "workforce"),
    ("reviews", "team-performance-reviews", "reviews"),
    ("skills", "team-performance-skills", "skills"),
    ("talent", "team-performance-talent", "talent"),
    ("recognition", "team-performance-recognition", "recognition"),
]:
    help_text = ensure_workflow_action(help_text, key, anchor, label_key)
save(help_path, help_text)


# Team Performance — stable module targets, safe to re-run.
dashboard_path, dashboard = load("frontend/src/pages/TeamPerformanceDashboard.jsx")
for component, dom_id in [
    ("PerformanceReviewsPanel", "team-performance-reviews"),
    ("WorkforcePlanningPanel", "team-performance-workforce"),
    ("SkillsDevelopmentPanel", "team-performance-skills"),
    ("TalentSuccessionPanel", "team-performance-talent"),
    ("RecognitionRewardsPanel", "team-performance-recognition"),
]:
    dashboard = ensure_component_wrapper(dashboard, component, dom_id)
save(dashboard_path, dashboard)


# Ramzy — preserve draft and keep Help Center suggestion recoverable, safe to re-run.
ramzy_path, ramzy = load("frontend/src/components/RamzyAssistant.jsx")
if "const [helpSuggestion, setHelpSuggestion]" not in ramzy:
    ramzy = replace_if_needed(
        ramzy,
        '  const [input, setInput] = useState("");\n  const [loading, setLoading] = useState(false);',
        '  const [input, setInput] = useState("");\n  const [helpSuggestion, setHelpSuggestion] = useState(null);\n  const [loading, setLoading] = useState(false);',
        "RAMZY_SUGGESTION_STATE",
    )

old_ramzy_bridge = '''  // Phase 6.5 — Help Center bridge
  useEffect(() => {
    function handleRamzyHelp(event) {
      const detail = event.detail || {};
      const prompt = String(detail.prompt || "").trim();
      if (!prompt) return;
      setMinimized(false);
      setOpen(true);
      setInput((prev) => {
        const existing = String(prev || "").trim();
        if (existing) return prev;
        return prompt;
      });
      setTimeout(() => { composerRef.current?.focus(); }, 80);
    }
    window.addEventListener("tos:ramzy-help", handleRamzyHelp);
    return () => window.removeEventListener("tos:ramzy-help", handleRamzyHelp);
  }, []);'''
new_ramzy_bridge = '''  // Phase 6.5 — Help Center bridge
  useEffect(() => {
    function handleRamzyHelp(event) {
      const detail = event.detail || {};
      const prompt = String(detail.prompt || "").trim();
      if (!prompt) return;
      setMinimized(false);
      setOpen(true);
      const existing = String(input || "").trim();
      if (existing) {
        setHelpSuggestion({
          prompt,
          topicKey: String(detail.topicKey || ""),
          source: String(detail.source || "help-center"),
        });
      } else {
        setInput(prompt);
        setHelpSuggestion(null);
      }
      setTimeout(() => { composerRef.current?.focus(); }, 80);
    }
    window.addEventListener("tos:ramzy-help", handleRamzyHelp);
    return () => window.removeEventListener("tos:ramzy-help", handleRamzyHelp);
  }, [input]);'''
if "setHelpSuggestion({" not in ramzy:
    ramzy = replace_if_needed(ramzy, old_ramzy_bridge, new_ramzy_bridge, "RAMZY_BRIDGE")

if "function applyHelpSuggestion()" not in ramzy:
    ramzy = replace_if_needed(
        ramzy,
        '  function handleComposerInput(event) {',
        '''  function applyHelpSuggestion() {
    const prompt = String(helpSuggestion?.prompt || "").trim();
    if (!prompt) return;
    setInput(prompt);
    setHelpSuggestion(null);
    setTimeout(() => { composerRef.current?.focus(); }, 0);
  }

  function handleComposerInput(event) {''',
        "RAMZY_APPLY_SUGGESTION",
    )

send_marker = '    if (!content || loading || sendLockRef.current) return;\n    setHelpSuggestion(null);\n    sendLockRef.current = true;'
if send_marker not in ramzy:
    ramzy = replace_if_needed(
        ramzy,
        '    if (!content || loading || sendLockRef.current) return;\n    sendLockRef.current = true;',
        send_marker,
        "RAMZY_SEND_CLEAR_SUGGESTION",
    )

if "Use Help Center question" not in ramzy:
    ramzy = replace_if_needed(
        ramzy,
        '          <footer className="ramzy-composer">\n            <textarea',
        '''          <footer className="ramzy-composer">
            {helpSuggestion?.prompt ? (
              <div className="mb-2 flex items-center justify-between gap-2 rounded-xl border border-amber-300/50 bg-amber-50 px-3 py-2 text-xs font-bold text-amber-900 dark:border-amber-400/20 dark:bg-amber-400/10 dark:text-amber-100" role="status">
                <span>{isEnglish ? "A Help Center question is ready." : "يوجد سؤال مقترح من مركز المساعدة."}</span>
                <div className="flex shrink-0 items-center gap-1">
                  <button type="button" onClick={applyHelpSuggestion} className="rounded-lg bg-amber-500 px-2 py-1 font-black text-zinc-950">{isEnglish ? "Use Help Center question" : "استخدام سؤال مركز المساعدة"}</button>
                  <button type="button" onClick={() => setHelpSuggestion(null)} className="grid h-7 w-7 place-items-center rounded-lg" aria-label={isEnglish ? "Dismiss Help Center question" : "إخفاء سؤال مركز المساعدة"}><X size={13} /></button>
                </div>
              </div>
            ) : null}
            <textarea''',
        "RAMZY_SUGGESTION_UI",
    )
save(ramzy_path, ramzy)

print("PHASE6_5_DEEP_LINK_RAMZY_DRAFT_FIX=PASS")
