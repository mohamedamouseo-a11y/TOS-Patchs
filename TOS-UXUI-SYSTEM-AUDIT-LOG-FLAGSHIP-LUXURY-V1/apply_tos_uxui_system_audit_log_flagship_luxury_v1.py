from pathlib import Path
import hashlib
import os
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
PAGE = FRONTEND / "src/pages/AuditLogPage.jsx"
STYLE = FRONTEND / "src/pages/auditLogFlagshipLuxuryV1.css"
DIST = FRONTEND / "dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_PAGE_GIT_BLOB = "b368609eff741cd5afdaba416d7ba75a98d9c163"
IMPORT_ANCHOR = 'import { usePreferences } from "../contexts/PreferencesContext";'
IMPORT_LINE = 'import "./auditLogFlagshipLuxuryV1.css";'
OLD_SECTION = '<section dir={isEnglish ? "ltr" : "rtl"} className="p-4 sm:p-6">'
NEW_SECTION = '<section dir={isEnglish ? "ltr" : "rtl"} className="tos-audit-flagship-v1 p-4 sm:p-6">'
OLD_SHELL = '<div className="rounded-[30px] border border-zinc-100 bg-white p-5 shadow-sm dark:border-white/10 dark:bg-zinc-950">'
NEW_SHELL = '<div className="tos-audit-shell rounded-[30px] border border-zinc-100 bg-white p-5 shadow-sm dark:border-white/10 dark:bg-zinc-950">'
OLD_HERO = '<div className="flex flex-wrap items-start justify-between gap-4">'
NEW_HERO = '<div className="tos-audit-hero flex flex-wrap items-start justify-between gap-4">'
OLD_KPIS = '<div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">'
NEW_KPIS = '<div className="tos-audit-kpis mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">'
OLD_FILTERS = '<div className="mt-5 grid gap-3 lg:grid-cols-4">'
NEW_FILTERS = '<div className="tos-audit-filters mt-5 grid gap-3 lg:grid-cols-4">'
OLD_FILTER_FOOTER = '<div className="mt-3 flex flex-wrap items-center justify-between gap-3">'
NEW_FILTER_FOOTER = '<div className="tos-audit-filter-footer mt-3 flex flex-wrap items-center justify-between gap-3">'
OLD_EVENTS = '<div className="mt-5 overflow-hidden rounded-3xl border border-zinc-100 dark:border-white/10">'
NEW_EVENTS = '<div className="tos-audit-events mt-5 overflow-hidden rounded-3xl border border-zinc-100 dark:border-white/10">'

CSS = r''':root {
  --tos-audit-log-flagship-luxury-v1-runtime: 1;
}

.tos-audit-flagship-v1 {
  --audit-gold-1: #fff0b4;
  --audit-gold-2: #e6bd51;
  --audit-gold-3: #c98f18;
  --audit-antique: #8e5a08;
  --audit-pearl: #fffdf8;
  --audit-ivory: #fbf5e9;
  --audit-ink: #18120b;
  --audit-obsidian: #0b0d0e;
  --audit-titanium: #15191c;
  --audit-line: rgba(188,126,18,.20);
  position: relative;
  isolation: isolate;
}

.tos-audit-flagship-v1::before {
  content: "";
  position: absolute;
  inset: 0;
  z-index: -1;
  pointer-events: none;
  background:
    radial-gradient(circle at 8% 0%, rgba(237,207,144,.18), transparent 27%),
    radial-gradient(circle at 98% 4%, rgba(225,179,73,.11), transparent 23%);
}

.tos-audit-flagship-v1 .tos-audit-shell {
  position: relative;
  overflow: hidden;
  border-color: rgba(182,119,13,.18) !important;
  background:
    radial-gradient(circle at 95% 0%, rgba(245,222,168,.20), transparent 23%),
    linear-gradient(155deg,#fffefa 0%,#fffdf9 50%,#fbf4e7 100%) !important;
  box-shadow:
    0 26px 58px rgba(70,42,2,.085),
    0 3px 10px rgba(57,34,2,.035),
    inset 0 1px rgba(255,255,255,.98) !important;
}

.tos-audit-flagship-v1 .tos-audit-shell::before {
  content: "";
  position: absolute;
  inset-inline: 28px;
  top: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(222,173,55,.78), transparent);
  opacity: .8;
}

/* Executive security hero */
.tos-audit-flagship-v1 .tos-audit-hero {
  position: relative;
  margin: -2px -2px 0;
  padding: 22px 22px 20px;
  border: 1px solid rgba(184,122,17,.16);
  border-radius: 24px;
  background:
    linear-gradient(115deg, transparent 0 30%, rgba(255,255,255,.55) 39%, transparent 49%),
    radial-gradient(ellipse at 88% 110%, rgba(229,190,104,.24), transparent 41%),
    linear-gradient(150deg,#fffefa 0%,#fbf2df 70%,#f4dfb0 100%);
  box-shadow: inset 0 1px rgba(255,255,255,.95), 0 14px 34px rgba(74,43,1,.06);
}

.tos-audit-flagship-v1 .tos-audit-hero > div:first-child > div:first-child {
  width: 54px !important;
  height: 54px !important;
  border: 1px solid rgba(145,91,5,.24) !important;
  color: #815307 !important;
  background: linear-gradient(145deg,#fff6cf,#e7bf59 65%,#ca901a) !important;
  box-shadow: 0 12px 26px rgba(115,70,2,.16), inset 0 1px rgba(255,255,255,.85) !important;
}

.tos-audit-flagship-v1 .tos-audit-hero h2 {
  font-family: Georgia, "Times New Roman", serif;
  font-size: clamp(1.45rem,2vw,2rem) !important;
  line-height: 1.05;
  letter-spacing: -.035em;
  color: #17110a !important;
}

.tos-audit-flagship-v1 .tos-audit-hero h2 + span {
  border: 1px solid rgba(10,132,91,.16);
  background: linear-gradient(180deg,#edfff8,#dff7ee) !important;
  box-shadow: inset 0 1px rgba(255,255,255,.85);
}

.tos-audit-flagship-v1 .tos-audit-hero p {
  max-width: 760px;
  color: #746754 !important;
  line-height: 1.65;
}

/* TWS-like metallic hardware */
.tos-audit-flagship-v1 button {
  transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease, filter .18s ease;
}
.tos-audit-flagship-v1 button:hover:not(:disabled) {
  transform: translateY(-1px);
}
.tos-audit-flagship-v1 .tos-audit-hero button {
  min-height: 42px;
  border-radius: 12px !important;
  border: 1px solid rgba(154,96,4,.22) !important;
  color: #38270d !important;
  background: linear-gradient(180deg,#fffefa,#f8ecd0 72%,#efdbad) !important;
  box-shadow: 0 9px 21px rgba(73,43,1,.065), inset 0 1px rgba(255,255,255,.96) !important;
}
.tos-audit-flagship-v1 .tos-audit-hero button[class*="bg-zinc-950"] {
  color: #211500 !important;
  border-color: rgba(130,77,0,.40) !important;
  background: linear-gradient(180deg,#fff2bb 0%,#f1cf69 28%,#dda936 68%,#c78913 100%) !important;
  box-shadow:
    0 12px 25px rgba(126,76,1,.18),
    inset 0 1px rgba(255,255,255,.86),
    inset 0 -2px rgba(95,55,0,.13) !important;
}
.tos-audit-flagship-v1 .tos-audit-hero button svg {
  color: #78500d;
}

/* Executive KPI tiles */
.tos-audit-flagship-v1 .tos-audit-kpis {
  gap: 12px !important;
}
.tos-audit-flagship-v1 .tos-audit-kpis > div {
  position: relative;
  overflow: hidden;
  min-height: 104px;
  border: 1px solid rgba(177,116,15,.15) !important;
  border-radius: 18px !important;
  background:
    radial-gradient(circle at 100% 0%, rgba(239,207,137,.15), transparent 36%),
    linear-gradient(150deg,#fffefa,#fbf5e9) !important;
  box-shadow: 0 12px 29px rgba(64,38,2,.055), inset 0 1px rgba(255,255,255,.95) !important;
}
.tos-audit-flagship-v1 .tos-audit-kpis > div::before {
  content: "";
  position: absolute;
  inset-block: 14px;
  inset-inline-start: 0;
  width: 3px;
  border-radius: 999px;
  background: linear-gradient(#f2d77f,#bd7d0b);
}
.tos-audit-flagship-v1 .tos-audit-kpis > div:nth-child(4)::before {
  background: linear-gradient(#55d39c,#087b55);
}
.tos-audit-flagship-v1 .tos-audit-kpis > div > div:first-child {
  letter-spacing: .06em;
  text-transform: uppercase;
  color: #8f806d !important;
}
.tos-audit-flagship-v1 .tos-audit-kpis > div > div:nth-child(2) {
  color: #17110a !important;
}

/* Luxury filter studio */
.tos-audit-flagship-v1 .tos-audit-filters {
  margin-top: 18px !important;
  padding: 18px;
  border: 1px solid rgba(178,117,15,.14);
  border-radius: 21px;
  background:
    radial-gradient(circle at 100% 0%, rgba(237,204,132,.12), transparent 31%),
    linear-gradient(180deg,#fffefa,#fbf6ec);
  box-shadow: inset 0 1px rgba(255,255,255,.96), 0 12px 30px rgba(63,37,1,.045);
}
.tos-audit-flagship-v1 .tos-audit-filters label > span {
  display: inline-block;
  margin-bottom: 4px;
  color: #6f604d !important;
  letter-spacing: .025em;
}
.tos-audit-flagship-v1 .tos-audit-filters label > div,
.tos-audit-flagship-v1 .tos-audit-filters select,
.tos-audit-flagship-v1 .tos-audit-filters input[type="date"] {
  min-height: 45px !important;
  border: 1px solid rgba(162,104,10,.17) !important;
  border-radius: 12px !important;
  color: #2a2117 !important;
  background: linear-gradient(180deg,#fffefa,#faf4e8) !important;
  box-shadow: inset 0 1px rgba(255,255,255,.95), 0 5px 13px rgba(62,37,2,.025) !important;
}
.tos-audit-flagship-v1 .tos-audit-filters select {
  cursor: pointer;
}
.tos-audit-flagship-v1 .tos-audit-filters input::placeholder {
  color: #a99c8a !important;
}
.tos-audit-flagship-v1 .tos-audit-filters label:focus-within > div,
.tos-audit-flagship-v1 .tos-audit-filters select:focus,
.tos-audit-flagship-v1 .tos-audit-filters input[type="date"]:focus {
  border-color: rgba(201,143,24,.62) !important;
  box-shadow: 0 0 0 3px rgba(221,173,60,.11), inset 0 1px rgba(255,255,255,.96) !important;
}

.tos-audit-flagship-v1 .tos-audit-filter-footer {
  margin-top: 12px !important;
  padding: 10px 12px;
  border-radius: 14px;
  border: 1px solid rgba(175,114,14,.09);
  background: rgba(255,252,244,.72);
}
.tos-audit-flagship-v1 .tos-audit-filter-footer input[type="checkbox"] {
  width: 16px;
  height: 16px;
  accent-color: #c98f18;
}
.tos-audit-flagship-v1 .tos-audit-filter-footer button:not([class*="text-red"]) {
  border: 1px solid rgba(157,100,8,.14);
  color: #5a4320 !important;
  background: linear-gradient(180deg,#fffefa,#f5e8c9);
  box-shadow: inset 0 1px rgba(255,255,255,.92);
}
.tos-audit-flagship-v1 .tos-audit-filter-footer button[class*="text-red"] {
  border-color: rgba(192,55,55,.18) !important;
  background: linear-gradient(180deg,#fffafa,#feeceb) !important;
  box-shadow: inset 0 1px rgba(255,255,255,.92);
}

/* Audit event ledger */
.tos-audit-flagship-v1 .tos-audit-events {
  border: 1px solid rgba(176,115,15,.16) !important;
  border-radius: 21px !important;
  background: linear-gradient(155deg,#fffefa,#fbf5e9) !important;
  box-shadow: 0 15px 34px rgba(67,40,2,.055), inset 0 1px rgba(255,255,255,.95);
}
.tos-audit-flagship-v1 .tos-audit-events table {
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
}
.tos-audit-flagship-v1 .tos-audit-events thead {
  background: linear-gradient(180deg,#fff5d5,#f3dfad) !important;
}
.tos-audit-flagship-v1 .tos-audit-events th {
  color: #59431f !important;
  font-size: 10px !important;
  font-weight: 900 !important;
  letter-spacing: .055em;
  text-transform: uppercase;
  border-color: rgba(156,98,8,.10) !important;
}
.tos-audit-flagship-v1 .tos-audit-events td {
  color: #3c3226;
  border-color: rgba(165,108,14,.075) !important;
}
.tos-audit-flagship-v1 .tos-audit-events tbody tr {
  background: rgba(255,254,250,.78);
  transition: background .16s ease, transform .16s ease;
}
.tos-audit-flagship-v1 .tos-audit-events tbody tr:hover {
  background: #fff8e8 !important;
}
.tos-audit-flagship-v1 .tos-audit-events button {
  border-radius: 10px !important;
}

/* Empty / loading state */
.tos-audit-flagship-v1 .tos-audit-events > div:not([class*="divide-y"]) {
  min-height: 180px;
  color: #9a8a74 !important;
  background:
    radial-gradient(circle at 50% 45%, rgba(234,201,124,.13), transparent 28%),
    linear-gradient(180deg,#fffefa,#fbf6ed);
}
.tos-audit-flagship-v1 .tos-audit-events > div:not([class*="divide-y"]) svg {
  color: #b98520;
}

/* Generic controls inside the ledger/footer */
.tos-audit-flagship-v1 button:focus-visible,
.tos-audit-flagship-v1 input:focus-visible,
.tos-audit-flagship-v1 select:focus-visible {
  outline: none !important;
  box-shadow: 0 0 0 3px rgba(222,176,74,.18) !important;
}
.tos-audit-flagship-v1 button:disabled {
  filter: grayscale(.18);
  cursor: not-allowed;
}

/* ===== Dark — Obsidian / Titanium / Champagne ===== */
.dark .tos-audit-flagship-v1::before {
  background:
    radial-gradient(circle at 7% 0%, rgba(211,160,47,.09), transparent 26%),
    radial-gradient(circle at 97% 5%, rgba(201,143,24,.08), transparent 21%);
}
.dark .tos-audit-flagship-v1 .tos-audit-shell {
  border-color: rgba(218,169,56,.20) !important;
  background:
    radial-gradient(circle at 100% 0%, rgba(197,139,21,.10), transparent 24%),
    linear-gradient(155deg,#0a0c0d 0%,#0f1112 48%,#11100d 100%) !important;
  box-shadow: 0 30px 64px rgba(0,0,0,.42), inset 0 1px rgba(255,255,255,.025) !important;
}
.dark .tos-audit-flagship-v1 .tos-audit-hero {
  border-color: rgba(220,169,50,.22) !important;
  background:
    radial-gradient(ellipse at 8% 0%, rgba(226,178,67,.15), transparent 37%),
    radial-gradient(ellipse at 92% 120%, rgba(170,111,6,.18), transparent 39%),
    linear-gradient(145deg,#0c0f10,#141719 58%,#17130c) !important;
  box-shadow: 0 18px 40px rgba(0,0,0,.34), inset 0 1px rgba(255,255,255,.03) !important;
}
.dark .tos-audit-flagship-v1 .tos-audit-hero h2 {
  color: #fffaf0 !important;
}
.dark .tos-audit-flagship-v1 .tos-audit-hero p {
  color: #a9a296 !important;
}
.dark .tos-audit-flagship-v1 .tos-audit-hero button {
  color: #d8d1c5 !important;
  border-color: rgba(225,175,62,.16) !important;
  background: linear-gradient(180deg,#202326,#16191b) !important;
  box-shadow: 0 10px 22px rgba(0,0,0,.28), inset 0 1px rgba(255,255,255,.045) !important;
}
.dark .tos-audit-flagship-v1 .tos-audit-hero button[class*="dark:bg-white"] {
  color: #201400 !important;
  border-color: rgba(221,173,60,.42) !important;
  background: linear-gradient(180deg,#f8df8a,#dfad37 64%,#bf7f0c) !important;
  box-shadow: 0 11px 25px rgba(184,123,8,.20), inset 0 1px rgba(255,255,255,.48) !important;
}
.dark .tos-audit-flagship-v1 .tos-audit-kpis > div {
  border-color: rgba(220,170,54,.16) !important;
  background:
    radial-gradient(circle at 100% 0%, rgba(203,148,28,.08), transparent 34%),
    linear-gradient(145deg,#151819,#0f1112) !important;
  box-shadow: 0 14px 29px rgba(0,0,0,.27), inset 0 1px rgba(255,255,255,.025) !important;
}
.dark .tos-audit-flagship-v1 .tos-audit-kpis > div > div:first-child {
  color: #8e897f !important;
}
.dark .tos-audit-flagship-v1 .tos-audit-kpis > div > div:nth-child(2) {
  color: #fff9ec !important;
}
.dark .tos-audit-flagship-v1 .tos-audit-filters {
  border-color: rgba(218,168,52,.14) !important;
  background: linear-gradient(155deg,#101314,#0c0e0f) !important;
  box-shadow: inset 0 1px rgba(255,255,255,.025), 0 14px 32px rgba(0,0,0,.25) !important;
}
.dark .tos-audit-flagship-v1 .tos-audit-filters label > span {
  color: #aaa397 !important;
}
.dark .tos-audit-flagship-v1 .tos-audit-filters label > div,
.dark .tos-audit-flagship-v1 .tos-audit-filters select,
.dark .tos-audit-flagship-v1 .tos-audit-filters input[type="date"] {
  color: #eee7dc !important;
  border-color: rgba(218,168,52,.15) !important;
  background: linear-gradient(180deg,#171a1c,#111416) !important;
  box-shadow: inset 0 1px rgba(255,255,255,.025) !important;
}
.dark .tos-audit-flagship-v1 .tos-audit-filters input::placeholder {
  color: #706c65 !important;
}
.dark .tos-audit-flagship-v1 .tos-audit-filter-footer {
  border-color: rgba(218,168,52,.10);
  background: rgba(18,20,20,.76);
}
.dark .tos-audit-flagship-v1 .tos-audit-filter-footer label {
  color: #aaa399 !important;
}
.dark .tos-audit-flagship-v1 .tos-audit-filter-footer button:not([class*="text-red"]) {
  color: #d8d0c3 !important;
  border-color: rgba(218,168,52,.15);
  background: linear-gradient(180deg,#1d2022,#151719);
}
.dark .tos-audit-flagship-v1 .tos-audit-events {
  border-color: rgba(220,169,50,.17) !important;
  background: linear-gradient(155deg,#111415,#0c0f10) !important;
  box-shadow: 0 17px 36px rgba(0,0,0,.28), inset 0 1px rgba(255,255,255,.022) !important;
}
.dark .tos-audit-flagship-v1 .tos-audit-events thead {
  background: linear-gradient(180deg,#2a2417,#1d1a13) !important;
}
.dark .tos-audit-flagship-v1 .tos-audit-events th {
  color: #d8c79c !important;
  border-color: rgba(220,169,50,.12) !important;
}
.dark .tos-audit-flagship-v1 .tos-audit-events td {
  color: #d8d2c8 !important;
  border-color: rgba(220,169,50,.075) !important;
}
.dark .tos-audit-flagship-v1 .tos-audit-events tbody tr {
  background: rgba(17,20,21,.82) !important;
}
.dark .tos-audit-flagship-v1 .tos-audit-events tbody tr:hover {
  background: #191913 !important;
}
.dark .tos-audit-flagship-v1 .tos-audit-events > div:not([class*="divide-y"]) {
  color: #77736b !important;
  background:
    radial-gradient(circle at 50% 45%, rgba(203,148,28,.07), transparent 29%),
    linear-gradient(180deg,#111415,#0c0e0f) !important;
}

@media (max-width: 767px) {
  .tos-audit-flagship-v1 .tos-audit-hero { padding: 18px; }
  .tos-audit-flagship-v1 .tos-audit-filters { padding: 14px; }
}
'''


def git_blob_sha(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def run(cmd, cwd=None):
    print("$", " ".join(cmd), flush=True)
    proc = subprocess.run(cmd, cwd=str(cwd) if cwd else None, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(proc.stdout, end="")
    if proc.returncode != 0:
        raise RuntimeError(f"command failed ({proc.returncode}): {' '.join(cmd)}")
    return proc


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"guard failed for {label}: expected exactly 1 occurrence, found {count}")
    return text.replace(old, new, 1)


def verify_functional_markers(text):
    required = [
        "api.auditLog.v2(query)",
        "api.auditLog.v2Filters()",
        "api.auditLog.retention()",
        "api.auditLog.exportV2",
        "api.auditLog.runRetention",
        "setSelectedId",
        "limit: 50",
    ]
    for marker in required:
        if marker not in text:
            raise RuntimeError(f"protected Audit Log marker missing: {marker}")


def main():
    print("RUNNING=TOS_UXUI_SYSTEM_AUDIT_LOG_FLAGSHIP_LUXURY_V1")
    if not PAGE.exists():
        raise RuntimeError(f"missing page: {PAGE}")
    if not FRONTEND.exists():
        raise RuntimeError(f"missing frontend: {FRONTEND}")

    original_bytes = PAGE.read_bytes()
    original = original_bytes.decode("utf-8")
    verify_functional_markers(original)

    already = IMPORT_LINE in original and NEW_SECTION in original and STYLE.exists()
    if already:
        if STYLE.read_text(encoding="utf-8") != CSS:
            raise RuntimeError("existing Audit Log luxury stylesheet differs from canonical V1")
        patched = original
        print("SOURCE_STATE=ALREADY_APPLIED")
    else:
        actual_blob = git_blob_sha(original_bytes)
        if actual_blob != EXPECTED_PAGE_GIT_BLOB:
            raise RuntimeError(f"unexpected AuditLogPage baseline git blob: {actual_blob}")
        if STYLE.exists():
            raise RuntimeError("stylesheet already exists in unrecognized partial state")
        if IMPORT_LINE in original or NEW_SECTION in original:
            raise RuntimeError("partial Audit Log luxury source state detected")

        patched = original
        patched = replace_once(patched, IMPORT_ANCHOR, IMPORT_ANCHOR + "\n" + IMPORT_LINE, "stylesheet import")
        patched = replace_once(patched, OLD_SECTION, NEW_SECTION, "page wrapper")
        patched = replace_once(patched, OLD_SHELL, NEW_SHELL, "luxury shell")
        patched = replace_once(patched, OLD_HERO, NEW_HERO, "hero")
        patched = replace_once(patched, OLD_KPIS, NEW_KPIS, "KPI grid")
        patched = replace_once(patched, OLD_FILTERS, NEW_FILTERS, "filter studio")
        patched = replace_once(patched, OLD_FILTER_FOOTER, NEW_FILTER_FOOTER, "filter footer")
        patched = replace_once(patched, OLD_EVENTS, NEW_EVENTS, "events ledger")

        verify_functional_markers(patched)

        # Prove only visual hooks/import were added to JSX.
        normalized = patched
        normalized = normalized.replace(IMPORT_ANCHOR + "\n" + IMPORT_LINE, IMPORT_ANCHOR, 1)
        normalized = normalized.replace(NEW_SECTION, OLD_SECTION, 1)
        normalized = normalized.replace(NEW_SHELL, OLD_SHELL, 1)
        normalized = normalized.replace(NEW_HERO, OLD_HERO, 1)
        normalized = normalized.replace(NEW_KPIS, OLD_KPIS, 1)
        normalized = normalized.replace(NEW_FILTERS, OLD_FILTERS, 1)
        normalized = normalized.replace(NEW_FILTER_FOOTER, OLD_FILTER_FOOTER, 1)
        normalized = normalized.replace(NEW_EVENTS, OLD_EVENTS, 1)
        if normalized != original:
            raise RuntimeError("visual-only normalization guard failed")

        PAGE.write_text(patched, encoding="utf-8")
        STYLE.write_text(CSS, encoding="utf-8")
        print("SOURCE_STATE=PATCHED")

    try:
        run(["npm", "run", "build"], cwd=FRONTEND)
        if not DIST.exists() or not (DIST / "index.html").exists():
            raise RuntimeError("frontend build output missing")

        built_text = ""
        for path in DIST.rglob("*"):
            if path.is_file() and path.suffix in {".css", ".js", ".html"}:
                try:
                    built_text += path.read_text(encoding="utf-8", errors="ignore")
                except Exception:
                    pass
        if "--tos-audit-log-flagship-luxury-v1-runtime" not in built_text:
            raise RuntimeError("runtime CSS marker missing from build")
        if "tos-audit-flagship-v1" not in built_text:
            raise RuntimeError("runtime JSX class marker missing from build")

        stamp = int(time.time())
        LIVE_PARENT.mkdir(parents=True, exist_ok=True)
        backup = LIVE_PARENT / f"build.audit-log-flagship-luxury-v1-backup-{stamp}"
        staging = LIVE_PARENT / f".build.audit-log-flagship-luxury-v1-staging-{stamp}"
        previous = LIVE_PARENT / f".build.audit-log-flagship-luxury-v1-previous-{stamp}"

        if staging.exists(): shutil.rmtree(staging)
        if previous.exists(): shutil.rmtree(previous)
        if LIVE.exists():
            shutil.copytree(LIVE, backup)
        shutil.copytree(DIST, staging)

        try:
            if LIVE.exists(): os.replace(LIVE, previous)
            os.replace(staging, LIVE)
            if previous.exists(): shutil.rmtree(previous)
        except Exception:
            if LIVE.exists(): shutil.rmtree(LIVE)
            if previous.exists(): os.replace(previous, LIVE)
            elif backup.exists(): shutil.copytree(backup, LIVE)
            raise

        print("PASS/FAIL=PASS")
        print("BUILD_RESULT=PASS")
        print("LIVE_DEPLOY=PASS")
        print("AUDIT_LOG_FLAGSHIP_LUXURY_V1_RUNTIME=YES")
        print("AUDIT_VISUAL_SCOPE=FLAGSHIP_LUXURY_ONLY")
        print("AUDIT_REFERENCE_LANGUAGE=TWS_PEARL_IVORY_CHAMPAGNE")
        print("AUDIT_DARK_LANGUAGE=OBSIDIAN_TITANIUM_CHAMPAGNE")
        print("AUDIT_HERO=EXECUTIVE_SECURITY_FLAGSHIP")
        print("AUDIT_HEADER_ACTIONS=METALLIC_HARDWARE")
        print("AUDIT_KPI_SYSTEM=EXECUTIVE_LUXURY")
        print("AUDIT_FILTER_STUDIO=PEARL_LUXURY")
        print("AUDIT_EVENT_LEDGER=LUXURY_AUDIT_LEDGER")
        print("AUDIT_API_CHANGED=NO")
        print("AUDIT_FILTER_LOGIC_CHANGED=NO")
        print("AUDIT_EXPORT_LOGIC_CHANGED=NO")
        print("AUDIT_RETENTION_LOGIC_CHANGED=NO")
        print("AUDIT_APPEND_ONLY_CHANGED=NO")
        print("DATABASE_CHANGED=NO")
        print("TWS_CHANGED=NO")
        print("SLA_CHANGED=NO")
        print("RAMZY_CHANGED=NO")
        print("TCS_CHANGED=NO")
        print(f"AUDIT_LOG_PAGE_SHA256={sha256(PAGE.read_bytes())}")
        print(f"AUDIT_LOG_STYLE_SHA256={sha256(STYLE.read_bytes())}")
        print(f"LIVE_BACKUP={backup if backup.exists() else 'NONE'}")
        print("STATUS=READY")
    except Exception:
        # Restore source only if this invocation performed the write.
        if not already:
            PAGE.write_bytes(original_bytes)
            if STYLE.exists(): STYLE.unlink()
        raise


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"PASS/FAIL=FAIL")
        print(f"ERROR={exc}")
        print("BUILD_RESULT=FAIL_OR_SKIPPED")
        print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
        print("AUDIT_LOG_FLAGSHIP_LUXURY_V1_RUNTIME=NO")
        print("STATUS=STOPPED")
        sys.exit(1)
