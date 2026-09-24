#!/usr/bin/env python3
# TOS-MY-WORKSPACE-STICKY-SCROLLBAR-V1_1
# Fix sticky scrollbar side-offset / geometry.
# Portal to document.body + normalized scroll progress + exact board viewport width.
# Frontend-only; preserves Spacious Premium + Trello DnD.

from pathlib import Path
import shutil
import sys
import time

ROOT = Path.cwd()
TARGET = ROOT / "frontend/src/pages/MyTaskWorkspace.jsx"
MARKER = "TOS_MY_WORKSPACE_STICKY_SCROLLBAR_V1_1"
REQ_V1 = "TOS_MY_WORKSPACE_STICKY_SCROLLBAR_V1"
REQ_PREMIUM = "TOS_MY_WORKSPACE_SPACIOUS_PREMIUM_V1"
REQ_DND = "TOS_MY_WORKSPACE_TRELLO_DRAG_DROP_V1"

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

for required in (REQ_V1, REQ_PREMIUM, REQ_DND):
    if required not in source:
        die(f"required marker missing: {required}")

backup = TARGET.with_name(
    TARGET.name + f".bak-sticky-scrollbar-v1_1-{int(time.time())}"
)
shutil.copy2(TARGET, backup)

source = replace_once(
    source,
    'import { useEffect, useMemo, useRef, useState } from "react";',
    'import { useEffect, useMemo, useRef, useState } from "react";\nimport { createPortal } from "react-dom";',
    "createPortal import",
)

old_engine = r'''  function handleBoardHorizontalScroll(event) {
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
  }, [tasks.length, filteredTasks.length, isAr]);'''

new_engine = r'''  // TOS_MY_WORKSPACE_STICKY_SCROLLBAR_V1_1
  function getBoardScrollProgress(board) {
    if (!board) return 0;
    const maxScroll = Math.max(0, board.scrollWidth - board.clientWidth);
    if (!maxScroll) return 0;
    const isRtlBoard = window.getComputedStyle(board).direction === "rtl";
    const raw = Number(board.scrollLeft) || 0;
    const normalized = isRtlBoard ? Math.abs(raw) : raw;
    return Math.max(0, Math.min(1, normalized / maxScroll));
  }

  function setBoardScrollProgress(board, progress) {
    if (!board) return;
    const maxScroll = Math.max(0, board.scrollWidth - board.clientWidth);
    const safeProgress = Math.max(0, Math.min(1, Number(progress) || 0));
    const isRtlBoard = window.getComputedStyle(board).direction === "rtl";
    board.scrollLeft = (isRtlBoard ? -1 : 1) * maxScroll * safeProgress;
  }

  function handleBoardHorizontalScroll(event) {
    const sticky = stickyScrollRef.current;
    const board = event.currentTarget;
    if (!sticky || !board) return;
    const stickyMax = Math.max(0, sticky.scrollWidth - sticky.clientWidth);
    const next = getBoardScrollProgress(board) * stickyMax;
    if (Math.abs(sticky.scrollLeft - next) > 0.75) sticky.scrollLeft = next;
  }

  function handleStickyHorizontalScroll(event) {
    const board = boardScrollRef.current;
    const sticky = event.currentTarget;
    if (!board || !sticky) return;
    const stickyMax = Math.max(0, sticky.scrollWidth - sticky.clientWidth);
    const progress = stickyMax > 0 ? sticky.scrollLeft / stickyMax : 0;
    setBoardScrollProgress(board, progress);
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
      const left = Math.max(8, Math.round(rect.left));
      const width = Math.max(
        0,
        Math.min(
          Math.round(board.clientWidth),
          Math.round(viewportWidth - left - 8),
        ),
      );
      const hasHorizontalOverflow = contentWidth > board.clientWidth + 2;
      const visible = hasHorizontalOverflow
        && rect.top < viewportHeight - 34
        && rect.bottom > 54
        && rect.right > 0
        && rect.left < viewportWidth;

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
      if (sticky) {
        const stickyMax = Math.max(0, sticky.scrollWidth - sticky.clientWidth);
        const next = getBoardScrollProgress(board) * stickyMax;
        if (Math.abs(sticky.scrollLeft - next) > 0.75) sticky.scrollLeft = next;
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
  }, [tasks.length, filteredTasks.length, isAr]);'''

source = replace_once(source, old_engine, new_engine, "sticky geometry/sync engine")

old_render = r'''      {stickyScrollMetrics.visible ? (
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
      ) : null}'''

new_render = r'''      {typeof document !== "undefined" && stickyScrollMetrics.visible
        ? createPortal(
            <div
              data-tos-my-workspace-sticky-scrollbar="v1_1"
              className="pointer-events-none fixed bottom-[14px] z-[95]"
              style={{
                left: `${stickyScrollMetrics.left}px`,
                width: `${stickyScrollMetrics.width}px`,
              }}
              aria-hidden="true"
            >
              <div className="rounded-full border border-amber-200/75 bg-white/94 px-2.5 pt-1 shadow-[0_12px_32px_rgba(15,23,42,0.18)] backdrop-blur-xl dark:border-amber-400/20 dark:bg-zinc-950/94">
                <div
                  ref={stickyScrollRef}
                  dir="ltr"
                  onScroll={handleStickyHorizontalScroll}
                  className="pointer-events-auto h-[16px] w-full overflow-x-auto overflow-y-hidden"
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
            </div>,
            document.body,
          )
        : null}'''

source = replace_once(source, old_render, new_render, "sticky portal renderer")

TARGET.write_text(source, encoding="utf-8")

print("PATCH=PASS")
print("PATCH_NAME=TOS-MY-WORKSPACE-STICKY-SCROLLBAR-V1_1")
print(f"FILES_CHANGED={TARGET.relative_to(ROOT)}")
print("PORTAL_TO_DOCUMENT_BODY=ACTIVE")
print("BOARD_VIEWPORT_GEOMETRY=FIXED")
print("SCROLL_PROGRESS_SYNC=NORMALIZED")
print("RTL_LTR_SYNC=FIXED")
print("STICKY_SIDE_OFFSET=FIXED")
print("SPACIOUS_PREMIUM=PRESERVED")
print("MY_WORKSPACE_DRAG_DROP=PRESERVED")
print("WAITING_CLIENT_GATE=PRESERVED")
print("BACKEND_UNCHANGED=YES")
print("DB_UNCHANGED=YES")
print("DEPENDENCIES_ADDED=NO")
print("NEXT=build frontend, atomic deploy, verify sticky rail aligns exactly with board viewport")
