#!/usr/bin/env python3
# TOS-MY-WORKSPACE-STICKY-SCROLLBAR-V1
# Sticky, viewport-persistent, synchronized horizontal scrollbar for My Workspace Kanban.
# Frontend-only; preserves spacious layout + Trello drag/drop behavior.

from pathlib import Path
import shutil
import sys
import time

ROOT = Path.cwd()
TARGET = ROOT / "frontend/src/pages/MyTaskWorkspace.jsx"
MARKER = "TOS_MY_WORKSPACE_STICKY_SCROLLBAR_V1"
REQUIRED_SPACIOUS_MARKER = "TOS_MY_WORKSPACE_SPACIOUS_PREMIUM_V1"
REQUIRED_DND_MARKER = "TOS_MY_WORKSPACE_TRELLO_DRAG_DROP_V1"


def die(message):
    print(f"PATCH=FAIL\nERROR={message}")
    sys.exit(1)


def replace_once(text, old, new, label):
    count = text.count(old)
    if count != 1:
        die(f"{label}: expected exactly 1 anchor, found {count}")
    return text.replace(old, new, 1)


if not TARGET.exists():
    die(f"missing file: {TARGET}")

source = TARGET.read_text(encoding="utf-8")

if MARKER in source:
    print("PATCH=SKIP_ALREADY_APPLIED")
    sys.exit(0)

for required in (REQUIRED_SPACIOUS_MARKER, REQUIRED_DND_MARKER):
    if required not in source:
        die(f"required marker missing: {required}")

backup = TARGET.with_name(
    TARGET.name + f".bak-sticky-scrollbar-v1-{int(time.time())}"
)
shutil.copy2(TARGET, backup)

source = replace_once(
    source,
    'import { useEffect, useMemo, useState } from "react";',
    'import { useEffect, useMemo, useRef, useState } from "react";',
    "React useRef import",
)

state_anchor = '''  const [waitingClientMoveDraft, setWaitingClientMoveDraft] = useState(null);'''
state_replacement = '''  const [waitingClientMoveDraft, setWaitingClientMoveDraft] = useState(null);
  // TOS_MY_WORKSPACE_STICKY_SCROLLBAR_V1
  const boardScrollRef = useRef(null);
  const stickyScrollRef = useRef(null);
  const [stickyScrollMetrics, setStickyScrollMetrics] = useState({
    visible: false,
    left: 0,
    width: 0,
    contentWidth: 0,
  });'''
source = replace_once(source, state_anchor, state_replacement, "sticky scrollbar refs/state")

function_anchor = '''  function updateFilter(key, value) {
    setFilters((current) => ({ ...current, [key]: value }));
  }'''

function_replacement = '''  function handleBoardHorizontalScroll(event) {
    const sticky = stickyScrollRef.current;
    if (!sticky) return;
    const next = event.currentTarget.scrollLeft;
    if (Math.abs(sticky.scrollLeft - next) > 0.5) sticky.scrollLeft = next;
  }

  function handleStickyHorizontalScroll(event) {
    const board = boardScrollRef.current;
    if (!board) return;
    const next = event.currentTarget.scrollLeft;
    if (Math.abs(board.scrollLeft - next) > 0.5) board.scrollLeft = next;
  }

  useEffect(() => {
    const board = boardScrollRef.current;
    if (!board || typeof window === "undefined") return undefined;

    let frame = 0;

    const updateStickyScrollbar = () => {
      frame = 0;
      const rect = board.getBoundingClientRect();
      const viewportHeight = window.innerHeight || document.documentElement.clientHeight || 0;
      const viewportWidth = window.innerWidth || document.documentElement.clientWidth || 0;
      const contentWidth = Math.max(board.scrollWidth, board.clientWidth);
      const hasHorizontalOverflow = contentWidth > board.clientWidth + 2;
      const visible = hasHorizontalOverflow
        && rect.top < viewportHeight - 30
        && rect.bottom > 46
        && rect.right > 0
        && rect.left < viewportWidth;
      const left = Math.max(8, Math.round(rect.left));
      const right = Math.min(viewportWidth - 8, Math.round(rect.right));
      const width = Math.max(0, right - left);

      setStickyScrollMetrics((current) => {
        const next = {
          visible: Boolean(visible && width > 120),
          left,
          width,
          contentWidth: Math.round(contentWidth),
        };
        if (
          current.visible === next.visible
          && current.left === next.left
          && current.width === next.width
          && current.contentWidth === next.contentWidth
        ) return current;
        return next;
      });

      const sticky = stickyScrollRef.current;
      if (sticky && Math.abs(sticky.scrollLeft - board.scrollLeft) > 0.5) {
        sticky.scrollLeft = board.scrollLeft;
      }
    };

    const scheduleUpdate = () => {
      if (frame) return;
      frame = window.requestAnimationFrame(updateStickyScrollbar);
    };

    scheduleUpdate();
    window.addEventListener("resize", scheduleUpdate, { passive: true });
    window.addEventListener("scroll", scheduleUpdate, { passive: true });

    const resizeObserver = typeof ResizeObserver !== "undefined"
      ? new ResizeObserver(scheduleUpdate)
      : null;
    resizeObserver?.observe(board);
    if (board.firstElementChild) resizeObserver?.observe(board.firstElementChild);

    return () => {
      if (frame) window.cancelAnimationFrame(frame);
      window.removeEventListener("resize", scheduleUpdate);
      window.removeEventListener("scroll", scheduleUpdate);
      resizeObserver?.disconnect();
    };
  }, [tasks.length, filteredTasks.length, isAr]);

  function updateFilter(key, value) {
    setFilters((current) => ({ ...current, [key]: value }));
  }'''

source = replace_once(source, function_anchor, function_replacement, "sticky scrollbar sync engine")

board_anchor = '''<div data-tos-my-workspace-spacious-premium="v1" className="tos-my-workspace-board-scroll mt-4 overflow-x-auto overscroll-x-contain pb-3 pt-1">'''
board_replacement = '''<div
          ref={boardScrollRef}
          data-tos-my-workspace-spacious-premium="v1"
          data-tos-my-workspace-sticky-scrollbar-source="v1"
          onScroll={handleBoardHorizontalScroll}
          className="tos-my-workspace-board-scroll mt-4 overflow-x-auto overscroll-x-contain pb-3 pt-1 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden"
        >'''
source = replace_once(source, board_anchor, board_replacement, "board scroll source")

sticky_anchor = '''        </div>
      )}

      {!loading && tasks.length > 0 && !filteredTasks.length && ('''

sticky_replacement = '''        </div>
      )}

      {stickyScrollMetrics.visible ? (
        <div
          data-tos-my-workspace-sticky-scrollbar="v1"
          className="pointer-events-none fixed bottom-2 z-[85]"
          style={{
            left: `${stickyScrollMetrics.left}px`,
            width: `${stickyScrollMetrics.width}px`,
          }}
          aria-hidden="true"
        >
          <div className="rounded-full border border-amber-200/80 bg-white/92 px-2 pt-1 shadow-[0_10px_28px_rgba(15,23,42,0.16)] backdrop-blur-xl dark:border-amber-400/20 dark:bg-zinc-950/92">
            <div
              ref={stickyScrollRef}
              onScroll={handleStickyHorizontalScroll}
              className="pointer-events-auto h-[15px] overflow-x-auto overflow-y-hidden"
              style={{
                scrollbarWidth: "thin",
                scrollbarColor: "#d6a84b transparent",
              }}
            >
              <div
                className="h-px"
                style={{ width: `${stickyScrollMetrics.contentWidth}px` }}
              />
            </div>
          </div>
        </div>
      ) : null}

      {!loading && tasks.length > 0 && !filteredTasks.length && ('''

source = replace_once(source, sticky_anchor, sticky_replacement, "sticky scrollbar renderer")

TARGET.write_text(source, encoding="utf-8")

print("PATCH=PASS")
print("PATCH_NAME=TOS-MY-WORKSPACE-STICKY-SCROLLBAR-V1")
print(f"FILES_CHANGED={TARGET.relative_to(ROOT)}")
print("STICKY_VIEWPORT_SCROLLBAR=ACTIVE")
print("BOARD_STICKY_SCROLL_SYNC=ACTIVE")
print("ORIGINAL_BOARD_SCROLLBAR=HIDDEN")
print("AUTO_VISIBILITY_BY_BOARD_VIEWPORT=ACTIVE")
print("RTL_LTR_RAW_SCROLL_SYNC=PRESERVED")
print("SPACIOUS_PREMIUM=PRESERVED")
print("MY_WORKSPACE_DRAG_DROP=PRESERVED")
print("WAITING_CLIENT_GATE=PRESERVED")
print("BACKEND_UNCHANGED=YES")
print("DB_UNCHANGED=YES")
print("DEPENDENCIES_ADDED=NO")
print("NEXT=build frontend, atomic deploy, verify sticky synced horizontal scrolling")
