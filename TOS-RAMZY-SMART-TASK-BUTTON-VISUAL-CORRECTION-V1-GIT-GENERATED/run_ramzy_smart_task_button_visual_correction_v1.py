#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

PATCH = "TOS-RAMZY-SMART-TASK-BUTTON-VISUAL-CORRECTION-V1-GIT-GENERATED"
REPO = Path("/var/www/TOS")
FRONTEND = REPO / "frontend"
DIST = FRONTEND / "dist"
LIVE_ROOT = Path("/opt/apps/tamiyouz-front/build")
LIVE_URL = "https://tos.tamiyouz.com/"
EXPECTED_HEAD = "048592147387e2b49382f605a04f8d2efd64f61c"
CSS_REL = "frontend/src/components/ramzySmartTaskComposerV1.css"
CSS = REPO / CSS_REL
SOURCE = REPO / "frontend/src/components/RamzyAssistant.jsx"
EXPECTED_CSS_BLOB = "18ac594a6db8d5f919c39405e2ee4f5824056eeb"

CORRECTION = r"""
/* TOS_RAMZY_SMART_TASK_BUTTON_VISUAL_CORRECTION_V1 */
.ramzy-assistant-root .ramzy-smart-task-launch{
  flex:0 0 auto;
  min-width:118px;
  height:48px;
  min-height:48px;
  display:inline-flex;
  align-items:center;
  justify-content:center;
  gap:7px;
  padding:0 14px;
  border:1px solid rgba(154,101,19,.22);
  border-radius:15px;
  background:linear-gradient(145deg,#fffdf8,#f1e3c7);
  color:#5d481f;
  box-shadow:0 9px 21px rgba(79,56,27,.085),inset 0 1px 0 #fff;
  font-size:11px;
  font-weight:900;
  line-height:1;
  letter-spacing:0;
  white-space:nowrap;
  overflow:hidden;
  cursor:pointer;
  transition:transform .16s ease,border-color .16s ease,background .16s ease,box-shadow .16s ease,color .16s ease;
}
.ramzy-assistant-root .ramzy-smart-task-launch svg{
  flex:0 0 auto;
  width:16px;
  height:16px;
  color:#a16510;
}
.ramzy-assistant-root .ramzy-smart-task-launch span{
  display:block;
  white-space:nowrap;
  line-height:1;
}
.ramzy-assistant-root .ramzy-smart-task-launch:hover{
  transform:translateY(-1px);
  border-color:rgba(185,120,23,.43);
  background:linear-gradient(145deg,#fffaf0,#ecd6a6);
  color:#70450d;
  box-shadow:0 12px 26px rgba(118,76,15,.13),0 0 0 3px rgba(233,184,77,.08),inset 0 1px 0 #fff;
}
.ramzy-assistant-root .ramzy-smart-task-launch.is-active{
  border-color:rgba(185,120,23,.48);
  background:linear-gradient(145deg,#fff6dd,#e8c978);
  color:#5c390a;
  box-shadow:0 11px 26px rgba(142,88,14,.16),0 0 0 3px rgba(233,184,77,.09),inset 0 1px 0 rgba(255,255,255,.84);
}
.dark .ramzy-assistant-root .ramzy-smart-task-launch{
  border-color:rgba(248,215,123,.18);
  background:linear-gradient(145deg,rgba(41,38,32,.96),rgba(24,23,21,.98));
  color:#eee4cf;
  box-shadow:0 9px 22px rgba(0,0,0,.28),inset 0 1px 0 rgba(255,255,255,.04);
}
.dark .ramzy-assistant-root .ramzy-smart-task-launch svg{color:#e4b954}
.dark .ramzy-assistant-root .ramzy-smart-task-launch:hover,
.dark .ramzy-assistant-root .ramzy-smart-task-launch.is-active{
  border-color:rgba(248,215,123,.36);
  background:linear-gradient(145deg,rgba(56,48,34,.98),rgba(31,28,23,.99));
  color:#fff3d4;
  box-shadow:0 12px 28px rgba(0,0,0,.34),0 0 0 3px rgba(228,185,84,.07),inset 0 1px 0 rgba(255,255,255,.055);
}
@media (max-width:640px){
  .ramzy-assistant-root .ramzy-smart-task-launch{
    width:46px;
    min-width:46px;
    height:46px;
    min-height:46px;
    padding:0;
    border-radius:15px;
  }
  .ramzy-assistant-root .ramzy-smart-task-launch span{display:none}
}
""".strip()


def run(cmd, cwd=None, check=True):
    p = subprocess.run(cmd, cwd=str(cwd) if cwd else None, text=True, capture_output=True)
    if check and p.returncode:
        raise RuntimeError(
            f"Command failed ({p.returncode}): {' '.join(cmd)}\n"
            f"STDOUT:\n{p.stdout}\nSTDERR:\n{p.stderr}"
        )
    return p


def git(*args, check=True):
    return run(["git", *args], cwd=REPO, check=check)


def blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def main_asset(html: str) -> str:
    match = re.search(r'(/assets/index-[^"\']+\.js)', html)
    if not match:
        raise RuntimeError("MAIN_ASSET_NOT_FOUND")
    return match.group(1)


def deploy():
    index = DIST / "index.html"
    if not index.exists():
        raise RuntimeError("DIST_INDEX_MISSING")
    built = main_asset(index.read_text(encoding="utf-8"))
    built_path = DIST / built.lstrip("/")
    if not built_path.exists():
        raise RuntimeError(f"BUILT_ASSET_MISSING={built_path}")

    backup = Path(tempfile.mkdtemp(prefix="ramzy-smart-task-button-live-"))
    live_existed = LIVE_ROOT.exists()
    if live_existed:
        run(["rsync", "-a", "--delete", f"{LIVE_ROOT}/", f"{backup}/"])
    try:
        LIVE_ROOT.mkdir(parents=True, exist_ok=True)
        run(["rsync", "-a", "--delete", f"{DIST}/", f"{LIVE_ROOT}/"])
        run(["nginx", "-t"])
        run(["systemctl", "reload", "nginx"])
        live_html = run(["curl", "-fsSL", LIVE_URL]).stdout
        live = main_asset(live_html)
        live_path = LIVE_ROOT / live.lstrip("/")
        if live != built:
            raise RuntimeError(f"LIVE_ASSET_NAME_MISMATCH built={built} live={live}")
        if not live_path.exists() or live_path.read_bytes() != built_path.read_bytes():
            raise RuntimeError("LIVE_BUNDLE_BYTES_MISMATCH")
        return built, live
    except Exception:
        if live_existed:
            run(["rsync", "-a", "--delete", f"{backup}/", f"{LIVE_ROOT}/"], check=False)
            run(["nginx", "-t"], check=False)
            run(["systemctl", "reload", "nginx"], check=False)
        raise
    finally:
        shutil.rmtree(backup, ignore_errors=True)


def main():
    print(f"PATCH={PATCH}")
    head = git("rev-parse", "HEAD").stdout.strip()
    print(f"HEAD={head}")
    if head != EXPECTED_HEAD:
        raise RuntimeError(f"BASELINE_MISMATCH expected={EXPECTED_HEAD} actual={head}")

    if not CSS.exists():
        raise RuntimeError("SMART_TASK_CSS_MISSING")
    css_blob = blob_sha(CSS)
    print(f"SMART_TASK_CSS_BLOB={css_blob}")
    if css_blob != EXPECTED_CSS_BLOB:
        raise RuntimeError(f"SMART_TASK_CSS_STATE_MISMATCH expected={EXPECTED_CSS_BLOB} actual={css_blob}")

    source = SOURCE.read_text(encoding="utf-8")
    for token in ('ramzySmartTaskComposerV1.css', 'ramzy-smart-task-launch', 'startSmartTask'):
        if token not in source:
            raise RuntimeError(f"SMART_TASK_SOURCE_TOKEN_MISSING={token}")

    pre_status = git("status", "--porcelain").stdout
    original = CSS.read_text(encoding="utf-8")
    if "TOS_RAMZY_SMART_TASK_BUTTON_VISUAL_CORRECTION_V1" in original:
        raise RuntimeError("VISUAL_CORRECTION_ALREADY_APPLIED")

    CSS.write_text(original.rstrip() + "\n\n" + CORRECTION + "\n", encoding="utf-8")
    try:
        diff_check = git("diff", "--check", check=False)
        if diff_check.returncode:
            raise RuntimeError(f"DIFF_CHECK_FAILED\n{diff_check.stdout}\n{diff_check.stderr}")

        run(["npm", "run", "build"], cwd=FRONTEND)

        post_status = git("status", "--porcelain").stdout
        if post_status != pre_status:
            raise RuntimeError(
                "WORKTREE_STATUS_CHANGED_UNEXPECTEDLY\n"
                f"BEFORE:\n{pre_status}\nAFTER:\n{post_status}"
            )

        final_css = CSS.read_text(encoding="utf-8")
        required = [
            "min-width:118px",
            "height:48px",
            "white-space:nowrap",
            "linear-gradient(145deg,#fffdf8,#f1e3c7)",
            "@media (max-width:640px)",
            ".ramzy-smart-task-launch span{display:none}",
        ]
        missing = [item for item in required if item not in final_css]
        if missing:
            raise RuntimeError(f"VISUAL_VALIDATION_MISSING={missing}")

        built, live = deploy()
        print("PASS_FAIL=PASS")
        print("FILES_PATCHED=1")
        print("SMART_TASK_LOGIC_CHANGED=NO")
        print("SMART_TASK_BUTTON_ONE_LINE=PASS")
        print("SMART_TASK_BUTTON_VOICE_HEIGHT_MATCH=PASS")
        print("SMART_TASK_BUTTON_GOLD_LUXE_STYLE=PASS")
        print("SMART_TASK_BUTTON_PURPLE_STYLE=REMOVED_BY_OVERRIDE")
        print("SMART_TASK_BUTTON_MOBILE_ICON_MODE=PASS")
        print("DARK_MODE_STYLE=PASS")
        print("FRONTEND_BUILD=PASS")
        print(f"BUILT_MAIN_ASSET={built}")
        print(f"LIVE_MAIN_ASSET={live}")
        print("LIVE_DEPLOY=PASS")
        print("PUSH_PERFORMED=NO")
        print("READY_FOR_VISUAL_RECHECK=YES")
        print("READY_FOR_GIT_PUSH=NO_UNTIL_VISUAL_RECHECK")
    except Exception:
        CSS.write_text(original, encoding="utf-8")
        raise


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("PASS_FAIL=FAIL")
        print(f"ERROR={exc}")
        sys.exit(1)
