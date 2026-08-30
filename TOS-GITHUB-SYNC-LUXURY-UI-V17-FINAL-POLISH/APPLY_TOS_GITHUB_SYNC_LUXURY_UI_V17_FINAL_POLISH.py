#!/usr/bin/env python3
from pathlib import Path

UI = Path('frontend/src/components/GithubAdvancedAdmin.jsx')
CSS = Path('frontend/src/index.css')
for p in (UI, CSS):
    if not p.exists():
        raise SystemExit(f'BLOCKED: target not found: {p}')

ui = UI.read_text(encoding='utf-8')
css = CSS.read_text(encoding='utf-8')
css0 = css

required = [
    'id="github-overview"',
    'id="github-workflow"',
    'id="github-changes"',
    'id="github-connection"',
    'id="github-console"',
    'min-h-[154px]',
    'break-all font-mono',
]
for token in required:
    if token not in ui:
        raise SystemExit(f'BLOCKED: required DOM anchor missing: {token}')

if '/* TOS_GITHUB_LUXURY_V16_START */' not in css or '/* TOS_GITHUB_LUXURY_V16_END */' not in css:
    raise SystemExit('BLOCKED: V16 direct-ID CSS contract not found; V17 must run on V16')

START = '/* TOS_GITHUB_LUXURY_V17_START */'
END = '/* TOS_GITHUB_LUXURY_V17_END */'
if START in css:
    a = css.find(START)
    b = css.find(END, a)
    if b < 0:
        raise SystemExit('BLOCKED: malformed existing V17 CSS block')
    css = css[:a] + css[b + len(END):]

v17 = r'''
/* TOS_GITHUB_LUXURY_V17_START */
/* Final luxury polish on top of V16: topbar integration, softer orbit, stronger depth, restrained gold. */

/* 1) Integrate the GLOBAL TOS topbar into the approved GitHub dark experience. */
html.dark body:has(#github-overview) .tos-premium-topbar {
  background:
    radial-gradient(circle at 88% -80%, rgba(214,161,54,.10), transparent 34%),
    linear-gradient(135deg, rgba(5,14,23,.96) 0%, rgba(8,22,35,.96) 100%) !important;
  border-color: rgba(103,137,166,.16) !important;
  box-shadow: 0 14px 38px rgba(0,0,0,.24), inset 0 1px 0 rgba(255,255,255,.025) !important;
  backdrop-filter: blur(18px) saturate(125%) !important;
}
html.dark body:has(#github-overview) .tos-premium-topbar h1 { color:#F4F7FA !important; }
html.dark body:has(#github-overview) .tos-premium-topbar p { color:#90A0B0 !important; }
html.dark body:has(#github-overview) .tos-premium-topbar > div:last-child {
  background: rgba(7,17,27,.72) !important;
  border-color: rgba(105,138,165,.14) !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.024) !important;
}
html.dark body:has(#github-overview) .tos-premium-topbar button {
  background:#091624 !important;
  color:#CBD5DF !important;
  border-color:rgba(105,138,165,.10) !important;
}
html.dark body:has(#github-overview) .tos-premium-topbar button:hover {
  background:#0C1D2D !important;
  border-color:rgba(205,157,61,.20) !important;
}
html.dark body:has(#github-overview) .tos-premium-topbar .tos-premium-user-chip {
  background:linear-gradient(135deg,#091725,#0A1A29) !important;
  border-color:rgba(111,145,173,.12) !important;
}

/* 2) Hero: keep the signature orbit, but make it subtler and more expensive-looking. */
html.dark #github-overview {
  background:
    radial-gradient(circle at 78% 45%, rgba(219,164,52,.085), transparent 18%),
    radial-gradient(circle at 91% -10%, rgba(42,91,136,.17), transparent 34%),
    linear-gradient(135deg,#071522 0%,#0A1A2A 48%,#07131F 100%) !important;
  border-color:rgba(202,151,54,.30) !important;
  box-shadow:0 26px 68px rgba(0,0,0,.30),inset 0 1px 0 rgba(255,255,255,.04) !important;
}
html.dark #github-overview::before {
  width:560px !important;
  height:150px !important;
  right:8% !important;
  top:42% !important;
  border-bottom-color:rgba(225,170,57,.38) !important;
  filter:drop-shadow(0 2px 5px rgba(220,164,48,.16)) !important;
  opacity:.72 !important;
}
html.dark #github-overview::after {
  width:118px !important;
  height:118px !important;
  right:28% !important;
  top:26px !important;
  border-color:rgba(207,160,68,.18) !important;
  background:radial-gradient(circle at 42% 38%,rgba(255,255,255,.08),rgba(18,39,59,.15) 38%,rgba(6,15,24,.035) 70%) !important;
  box-shadow:0 0 48px rgba(210,158,50,.075),inset 0 0 34px rgba(255,255,255,.025) !important;
}

/* 3) Stronger hierarchy for the three status cards without gray or harsh gold. */
html.dark .tos-page:has(#github-overview) main > section.grid:not([id]) > article {
  background:
    linear-gradient(180deg,#0B1B2A 0%,#081522 100%) !important;
  border-color:rgba(105,139,168,.18) !important;
  box-shadow:0 16px 42px rgba(0,0,0,.24),inset 0 1px 0 rgba(255,255,255,.032) !important;
}
html.dark .tos-page:has(#github-overview) main > section.grid:not([id]) > article:hover {
  transform:translateY(-1px);
  border-color:rgba(129,160,188,.24) !important;
  box-shadow:0 20px 48px rgba(0,0,0,.27),inset 0 1px 0 rgba(255,255,255,.04) !important;
}
html.dark .tos-page:has(#github-overview) main > section.grid:not([id]) > article [class*='rounded-2xl'],
html.dark .tos-page:has(#github-overview) main > section.grid:not([id]) > article [class*='rounded-[18px]'] {
  background:#0D1F2F !important;
  border-color:rgba(111,145,174,.14) !important;
}

/* 4) Workflow: premium connected cards, clearer depth, less gold noise. */
html.dark #github-workflow {
  border-color:rgba(112,145,173,.17) !important;
  box-shadow:0 18px 48px rgba(0,0,0,.24),inset 0 1px 0 rgba(255,255,255,.024) !important;
}
html.dark #github-workflow [class*='min-h-[154px]'] {
  background:linear-gradient(180deg,#0C1C2B 0%,#091724 100%) !important;
  border-color:rgba(103,138,168,.18) !important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.025),0 10px 24px rgba(0,0,0,.15) !important;
}
html.dark #github-workflow [class*='min-h-[154px]']:first-child {
  background:linear-gradient(180deg,#082729 0%,#071F23 100%) !important;
  border-color:rgba(24,200,156,.31) !important;
}
html.dark #github-workflow [class*='min-h-[154px]']:nth-child(3) {
  border-color:rgba(202,151,54,.20) !important;
}
html.dark #github-workflow [class*='min-h-[154px]']:nth-child(3) button {
  background:linear-gradient(135deg,#A66E1A 0%,#C99A39 48%,#DDB85F 100%) !important;
  box-shadow:0 8px 22px rgba(190,135,39,.16),inset 0 1px 0 rgba(255,243,201,.34) !important;
}

/* 5) Changes/activity/repository surfaces: a three-layer navy system, no flat gray. */
html.dark #github-changes,
html.dark .tos-page:has(#github-overview) #github-changes ~ section,
html.dark #github-connection,
html.dark #github-console {
  border-color:rgba(99,134,164,.16) !important;
  box-shadow:0 14px 38px rgba(0,0,0,.20),inset 0 1px 0 rgba(255,255,255,.022) !important;
}
html.dark #github-changes [class*='rounded-xl'],
html.dark .tos-page:has(#github-overview) article [class*='rounded-xl'] {
  background:#0C1D2C !important;
  border-color:rgba(104,139,168,.13) !important;
}

/* 6) Gold is reserved for hero / active navigation / execute action only. */
html.dark .tos-page:has(#github-overview) article {
  border-color:rgba(102,137,166,.17) !important;
}
html.dark .tos-page:has(#github-overview) article:hover {
  border-color:rgba(122,154,182,.23) !important;
}
html.dark .tos-page:has(#github-overview) [class*='ring-amber'],
html.dark .tos-page:has(#github-overview) article [class*='border-amber'] {
  --tw-ring-color:rgba(202,151,54,.18) !important;
  border-color:rgba(202,151,54,.18) !important;
}

/* 7) Final readability polish. */
html.dark .tos-page:has(#github-overview) [class*='text-zinc-400'] { color:#95A5B4 !important; }
html.dark .tos-page:has(#github-overview) [class*='text-zinc-500'] { color:#A9B7C4 !important; }
html.dark .tos-page:has(#github-overview) [class*='text-zinc-600'],
html.dark .tos-page:has(#github-overview) [class*='text-zinc-700'] { color:#CAD4DD !important; }

/* TOS_GITHUB_LUXURY_V17_END */
'''

css = css.rstrip() + '\n\n' + v17.strip() + '\n'

if css == css0:
    raise SystemExit('BLOCKED: no CSS changes produced')
if UI.read_text(encoding='utf-8') != ui:
    raise SystemExit('BLOCKED: JSX changed unexpectedly')

CSS.write_text(css, encoding='utf-8')

print('PATCH_APPLIED=YES')
print('BASE=V16_DIRECT_ID_LUXURY')
print('FILES_CHANGED=1')
print('PATCH_MODE=CSS_ONLY_FINAL_POLISH')
print('JSX_UNCHANGED=YES')
print('LOGIC_UNCHANGED=YES')
print('LIGHT_MODE_UNCHANGED=YES')
print('GLOBAL_TOPBAR_INTEGRATED=YES')
print('HERO_ORBIT_REFINED=YES')
print('CARD_DEPTH_REFINED=YES')
print('WORKFLOW_DEPTH_REFINED=YES')
print('GOLD_RESTRAINED=YES')
print('READABILITY_POLISHED=YES')
