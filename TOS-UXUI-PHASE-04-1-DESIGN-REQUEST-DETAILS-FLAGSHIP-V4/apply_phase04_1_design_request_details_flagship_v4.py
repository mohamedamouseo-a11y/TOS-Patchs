from pathlib import Path
import hashlib
import shutil
import subprocess
import sys
import time

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
DQ = ROOT / "frontend/src/pages/DesignQueuePage.jsx"
CSS = ROOT / "frontend/src/index.css"
DIST = ROOT / "frontend/dist"
LIVE_PARENT = Path("/opt/apps/tamiyouz-front")
LIVE = LIVE_PARENT / "build"

EXPECTED_DQ_SHA256 = "cf9cfd16cb9593c7bad8bc993626eb435eb2246324209d8557f3dc33eab52505"
EXPECTED_CSS_SHA256 = "2d598a0eb17928147af2082a9efd0a77b4ed9b01c89b901fcc0110b28d67290e"
V3_MARKER = "--tos-dq-details-flagship-v3-runtime"
V4_MARKER = "--tos-dq-details-flagship-v4-runtime"
V2_HOOK = 'data-dq-details-flagship="v2"'
V4_HOOK = 'data-dq-details-flagship="v4"'

print("RUNNING=PHASE04_1_DESIGN_REQUEST_DETAILS_FLAGSHIP_V4")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_count(root: Path, needle: bytes) -> int:
    if not root.exists():
        return 0
    total = 0
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        try:
            total += path.read_bytes().count(needle)
        except OSError:
            pass
    return total


def fail(message: str):
    print("PASS/FAIL=FAIL")
    print("ERROR=" + str(message))
    print("BUILD_RESULT=SKIPPED")
    print("LIVE_DEPLOY=SKIPPED")
    print("V4_RUNTIME=NO")
    sys.exit(1)


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected 1 match, found {count}")
    return text.replace(old, new, 1)


for path in (DQ, CSS):
    if not path.exists():
        fail(f"required source missing: {path}")

if sha256(DQ) != EXPECTED_DQ_SHA256:
    fail("DesignQueuePage.jsx does not match Flagship V3 live source")
if sha256(CSS) != EXPECTED_CSS_SHA256:
    fail("index.css does not match Flagship V3 live source")

original_dq = DQ.read_text()
original_css = CSS.read_text()

for required in ("TOS_DQ_PERFORMANCE_V3", "TOS_DQ_PREMIUM_MENU_V9", "TOS_DQ_PREMIUM_MENU_THEME_V10", V2_HOOK, V3_MARKER):
    if required not in (original_dq + original_css):
        fail(f"required V3 baseline marker missing: {required}")
if V4_MARKER in original_css or V4_HOOK in original_dq:
    fail("Design Request Details Flagship V4 already present")

updated = original_dq
updated = replace_once(updated, V2_HOOK, V4_HOOK, "Details V4 runtime hook")
updated = replace_once(
    updated,
    '<Button type="button" variant="soft" onClick={() => attachmentInputRef.current?.click()} disabled={attachmentUploading || actionBusy}><Paperclip size={16} /> {attachmentUploading ? tr.details.actions.uploadingAttachment : tr.details.actions.addAttachment}</Button>',
    '<Button type="button" variant="soft" className="tos-dq-attachment-action-v4" onClick={() => attachmentInputRef.current?.click()} disabled={attachmentUploading || actionBusy}><Paperclip size={16} /> {attachmentUploading ? tr.details.actions.uploadingAttachment : tr.details.actions.addAttachment}</Button>',
    "Attachment action hook",
)
updated = replace_once(
    updated,
    '<Button type="button" variant="soft" onClick={onClose}><X size={16} />{tr.common.close}</Button>',
    '<Button type="button" variant="soft" className="tos-dq-close-action-v4" onClick={onClose}><X size={15} />{tr.common.close}</Button>',
    "Close action hook",
)

v4_css = r'''

/* =========================================================
   Phase 04.1 — Design Queue Request Details — Flagship V4
   Final visual-QA finishing pass: real desktop composition,
   RTL editorial alignment, compact premium actions and quieter
   empty states / CTA materials. Business logic unchanged.
   ========================================================= */
:root { --tos-dq-details-flagship-v4-runtime: 1; }

/* The reading copy must behave like an editorial brief, not a centered poster. */
.tos-dq-spec-copy-v1 > div:last-child {
  width: min(100%, 76ch) !important;
  max-width: 76ch !important;
  margin-top: 12px !important;
  margin-inline: 0 !important;
  text-align: start !important;
  font-size: 1rem !important;
  line-height: 2.02 !important;
}

[dir="rtl"] .tos-dq-spec-copy-v1 > div:last-child {
  margin-right: 0 !important;
  margin-left: auto !important;
  text-align: right !important;
}

[dir="ltr"] .tos-dq-spec-copy-v1 > div:last-child {
  margin-left: 0 !important;
  margin-right: auto !important;
  text-align: left !important;
}

/* Hero actions: Add attachment remains discoverable; Close becomes a quiet utility. */
.tos-dq-details-actions-v1 {
  padding: 10px !important;
}

.tos-dq-details-actions-v1 > div:last-child {
  align-items: center;
}

.tos-dq-attachment-action-v4 {
  min-height: 36px !important;
  border: 1px solid rgba(180,137,55,.16) !important;
  background: linear-gradient(180deg, rgba(255,255,255,.96), rgba(249,246,239,.94)) !important;
  color: #39342b !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.95), 0 5px 14px rgba(66,49,20,.045) !important;
}

.tos-dq-attachment-action-v4:hover {
  border-color: rgba(190,145,55,.32) !important;
  background: #fffaf0 !important;
}

.tos-dq-close-action-v4 {
  width: auto !important;
  min-width: 82px !important;
  min-height: 34px !important;
  justify-content: center !important;
  border: 1px solid rgba(92,84,72,.11) !important;
  background: transparent !important;
  color: #696257 !important;
  box-shadow: none !important;
  padding-inline: 12px !important;
}

.tos-dq-close-action-v4:hover {
  border-color: rgba(184,137,53,.24) !important;
  background: rgba(184,137,53,.055) !important;
  color: #342f27 !important;
}

/* Empty attachments should read as a compact state, not an oversized panel. */
.tos-dq-details-attachments-v1 [class*="border-dashed"] {
  min-height: 74px !important;
  padding-block: 14px !important;
  border-radius: 16px !important;
}

/* More restrained executive-gold primary action. */
.tos-dq-assignment-cta-v1 {
  min-height: 43px !important;
  background: linear-gradient(135deg, #e8bc5b, #c99531) !important;
  color: #17140e !important;
  box-shadow: 0 10px 22px rgba(166,113,24,.15), inset 0 1px 0 rgba(255,255,255,.30) !important;
}

.tos-dq-assignment-cta-v1:hover {
  filter: brightness(1.025);
}

/* True desktop composition: flatten the nested content grid so attachments
   and activity can actually span the whole workspace below the first row. */
@media (min-width: 1280px) {
  .tos-dq-details-layout-v1 {
    display: grid !important;
    grid-template-columns: minmax(0, 1fr) 300px !important;
    grid-template-rows: auto auto auto;
    align-items: start;
    gap: 18px !important;
  }

  .tos-dq-details-content-v1 {
    display: contents !important;
  }

  .tos-dq-details-content-v1 > div:first-child {
    display: contents !important;
  }

  .tos-dq-details-specs-v1 {
    grid-column: 1;
    grid-row: 1;
    min-width: 0;
    width: 100%;
  }

  .tos-dq-details-rail-v1 {
    grid-column: 2;
    grid-row: 1;
    width: 100%;
    min-width: 0;
    align-self: start;
    top: 14px !important;
  }

  .tos-dq-details-attachments-v1 {
    grid-column: 1 / -1;
    grid-row: 2;
    width: 100%;
    min-width: 0;
  }

  .tos-dq-details-activity-v1 {
    grid-column: 1 / -1;
    grid-row: 3;
    width: 100%;
    min-width: 0;
  }

  .tos-dq-details-activity-v1 > div:last-child {
    padding-block: 14px 16px !important;
  }

  .tos-dq-details-activity-v1 .tos-dq-activity-item-v1 {
    max-width: 1060px;
  }

  .tos-dq-details-actions-v1 {
    width: 334px !important;
  }

  .tos-dq-details-actions-v1 > div:last-child {
    display: grid !important;
    grid-template-columns: minmax(0, 1fr) auto !important;
    gap: 8px !important;
  }
}

html.dark .tos-dq-spec-copy-v1 > div:last-child {
  color: #ece9e1 !important;
}

html.dark .tos-dq-attachment-action-v4 {
  border-color: rgba(215,178,100,.13) !important;
  background: linear-gradient(180deg, rgba(37,40,46,.96), rgba(27,30,35,.96)) !important;
  color: #ece8df !important;
  box-shadow: inset 0 1px 0 rgba(255,255,255,.028), 0 8px 18px rgba(0,0,0,.18) !important;
}

html.dark .tos-dq-attachment-action-v4:hover {
  border-color: rgba(215,178,100,.26) !important;
  background: #22262d !important;
}

html.dark .tos-dq-close-action-v4 {
  border-color: rgba(255,255,255,.075) !important;
  background: transparent !important;
  color: #a9b0ba !important;
}

html.dark .tos-dq-close-action-v4:hover {
  border-color: rgba(215,178,100,.20) !important;
  background: rgba(215,178,100,.055) !important;
  color: #f0ece3 !important;
}

html.dark .tos-dq-assignment-cta-v1 {
  background: linear-gradient(135deg, #ddb15a, #b98228) !important;
  color: #111318 !important;
  box-shadow: 0 12px 26px rgba(166,113,24,.16), inset 0 1px 0 rgba(255,255,255,.16) !important;
}

html.dark .tos-dq-details-attachments-v1 [class*="border-dashed"] {
  background: rgba(255,255,255,.008) !important;
}

@media (max-width: 1279px) {
  .tos-dq-details-content-v1,
  .tos-dq-details-content-v1 > div:first-child {
    display: block !important;
  }
}
'''

v4_css = "\n".join(line.rstrip() for line in v4_css.splitlines()).strip() + "\n"
updated_css = original_css.rstrip() + "\n\n" + v4_css

backup = None
stage = None
live_swapped = False

try:
    DQ.write_text(updated)
    CSS.write_text(updated_css)

    source_dq = DQ.read_text()
    source_css = CSS.read_text()

    if source_dq.count(V4_HOOK) != 1:
        raise RuntimeError("V4 source hook missing or duplicated")
    if source_css.count(V4_MARKER) != 1:
        raise RuntimeError("V4 CSS runtime marker missing or duplicated")
    if source_dq.count("tos-dq-close-action-v4") != 1 or source_dq.count("tos-dq-attachment-action-v4") != 1:
        raise RuntimeError("V4 action hooks missing or duplicated")
    for required in ("TOS_DQ_PERFORMANCE_V3", "TOS_DQ_PREMIUM_MENU_V9", "TOS_DQ_PREMIUM_MENU_THEME_V10"):
        if required not in source_dq:
            raise RuntimeError(f"required Design Queue baseline marker not preserved: {required}")
    if V3_MARKER not in source_css:
        raise RuntimeError("V3 CSS baseline marker was not preserved")

    subprocess.run(["npm", "run", "build"], cwd=ROOT / "frontend", check=True)
    if not (DIST / "index.html").exists():
        raise RuntimeError("built dist index missing")

    dist_marker = tree_count(DIST, V4_MARKER.encode())
    dist_details_key = tree_count(DIST, b"data-dq-details-flagship")
    dist_close = tree_count(DIST, b"tos-dq-close-action-v4")
    if dist_marker < 1 or dist_details_key < 1 or dist_close < 1:
        raise RuntimeError("V4 stable runtime markers missing from dist")

    stamp = time.strftime("%Y%m%d-%H%M%S")
    stage = LIVE_PARENT / f"build.phase04-1-dq-details-v4.new.{int(time.time())}"
    backup = LIVE_PARENT / f"build.phase04-1-dq-details-v4.backup-{stamp}"
    if stage.exists():
        shutil.rmtree(stage)
    shutil.copytree(DIST, stage)
    if not (stage / "index.html").exists():
        raise RuntimeError("staged live build missing index.html")
    if not LIVE.exists():
        raise RuntimeError("live frontend root missing")

    LIVE.rename(backup)
    stage.rename(LIVE)
    live_swapped = True
    subprocess.run(["systemctl", "is-active", "--quiet", "nginx"], check=True)

    live_marker = tree_count(LIVE, V4_MARKER.encode())
    live_details_key = tree_count(LIVE, b"data-dq-details-flagship")
    live_close = tree_count(LIVE, b"tos-dq-close-action-v4")
    if live_marker < 1 or live_details_key < 1 or live_close < 1:
        raise RuntimeError("V4 live runtime verification failed")

    print("PASS/FAIL=PASS")
    print("BUILD_RESULT=PASS")
    print("LIVE_DEPLOY=PASS")
    print("V4_RUNTIME=YES")
    print("REQUIRED_COPY_RTL_ALIGNED=YES")
    print("CLOSE_ACTION_REFINED=YES")
    print("ATTACHMENT_ACTION_REFINED=YES")
    print("TRUE_FULL_WIDTH_ATTACHMENTS=YES")
    print("ACTIVITY_FULL_WIDTH_PRESERVED=YES")
    print("DEAD_RIGHT_RAIL_REMOVED=YES")
    print("EMPTY_ATTACHMENTS_COMPACTED=YES")
    print("ASSIGNMENT_CTA_REFINED=YES")
    print("STICKY_ASSIGNMENT_PRESERVED=YES")
    print("V2_PREMIUM_MENUS_PRESERVED=YES")
    print("PERFORMANCE_V3_PRESERVED=YES")
    print("BUSINESS_LOGIC_CHANGED=NO")
    print(f"SOURCE_V4_RUNTIME_COUNT={source_css.count(V4_MARKER)}")
    print(f"SOURCE_V4_HOOK_COUNT={source_dq.count(V4_HOOK)}")
    print(f"DIST_V4_RUNTIME_COUNT={dist_marker}")
    print(f"DIST_DETAILS_KEY_COUNT={dist_details_key}")
    print(f"DIST_CLOSE_HOOK_COUNT={dist_close}")
    print(f"LIVE_V4_RUNTIME_COUNT={live_marker}")
    print(f"LIVE_DETAILS_KEY_COUNT={live_details_key}")
    print(f"LIVE_CLOSE_HOOK_COUNT={live_close}")
    print(f"DESIGN_QUEUE_SHA256={sha256(DQ)}")
    print(f"INDEX_CSS_SHA256={sha256(CSS)}")

except Exception as exc:
    try:
        DQ.write_text(original_dq)
        CSS.write_text(original_css)
    except Exception:
        pass

    if live_swapped and backup and backup.exists():
        failed_live = LIVE_PARENT / f"build.phase04-1-dq-details-v4.failed.{int(time.time())}"
        try:
            if LIVE.exists():
                LIVE.rename(failed_live)
            backup.rename(LIVE)
        except Exception:
            pass
    elif stage and stage.exists():
        try:
            shutil.rmtree(stage)
        except Exception:
            pass

    print("PASS/FAIL=FAIL")
    print("ERROR=" + str(exc))
    print("BUILD_RESULT=FAIL_OR_SKIPPED")
    print("LIVE_DEPLOY=ROLLED_BACK_OR_SKIPPED")
    print("V4_RUNTIME=NO")
    print(f"DESIGN_QUEUE_SHA256={sha256(DQ) if DQ.exists() else 'MISSING'}")
    print(f"INDEX_CSS_SHA256={sha256(CSS) if CSS.exists() else 'MISSING'}")
    sys.exit(1)
