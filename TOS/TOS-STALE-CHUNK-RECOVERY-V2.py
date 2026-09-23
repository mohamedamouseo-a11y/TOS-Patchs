#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import shutil, sys

PATCH = "TOS-STALE-CHUNK-RECOVERY-V2"
ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
MAIN = ROOT / "frontend/src/main.jsx"

if not MAIN.exists():
    raise SystemExit(f"{PATCH}: missing {MAIN}")

src = MAIN.read_text(encoding="utf-8")
backup_dir = Path("/tmp") / f"{PATCH}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
backup_dir.mkdir(parents=True, exist_ok=True)
shutil.copy2(MAIN, backup_dir / "main.jsx")

old = '''// TOS_STALE_CHUNK_RECOVERY_V1
// One-shot guard: if a lazy chunk fails (stale session after deploy), reload once.
// Prevents infinite reload loops via sessionStorage flag.
const STALE_CHUNK_KEY = "__tos_chunk_reload__";
window.addEventListener("unhandledrejection", (event) => {
  const msg = String(event?.reason?.message || event?.reason || "");
  const isChunkError =
    msg.includes("Loading chunk") ||
    msg.includes("Loading CSS chunk") ||
    msg.includes("ChunkLoadError") ||
    msg.includes("Importing a module script failed");
  if (!isChunkError) return;
  if (sessionStorage.getItem(STALE_CHUNK_KEY)) return;
  sessionStorage.setItem(STALE_CHUNK_KEY, "1");
  window.location.reload();
});
'''

new = '''// TOS_STALE_CHUNK_RECOVERY_V2
// Recover once from stale lazy chunks after atomic frontend deploys.
// Keep the guard during startup to prevent loops, then clear it once the app has
// had time to boot successfully so future deploys can recover too.
const STALE_CHUNK_KEY = "__tos_chunk_reload__";

function isStaleChunkError(value) {
  const msg = String(value?.message || value || "");
  return (
    msg.includes("Loading chunk") ||
    msg.includes("Loading CSS chunk") ||
    msg.includes("ChunkLoadError") ||
    msg.includes("Importing a module script failed") ||
    msg.includes("Failed to fetch dynamically imported module") ||
    msg.includes("error loading dynamically imported module")
  );
}

function recoverFromStaleChunk(value) {
  if (!isStaleChunkError(value)) return;
  if (sessionStorage.getItem(STALE_CHUNK_KEY)) return;
  sessionStorage.setItem(STALE_CHUNK_KEY, "1");
  window.location.reload();
}

window.addEventListener("unhandledrejection", (event) => {
  recoverFromStaleChunk(event?.reason);
});

window.addEventListener("error", (event) => {
  recoverFromStaleChunk(event?.error || event?.message);
});

// V1 never cleared the one-shot flag, so a tab that recovered once could later
// get stuck blank after another deploy. Clear only after a stable boot window.
window.addEventListener("load", () => {
  window.setTimeout(() => {
    try { sessionStorage.removeItem(STALE_CHUNK_KEY); } catch {}
  }, 5000);
}, { once: true });
'''

if "TOS_STALE_CHUNK_RECOVERY_V2" in src:
    print(f"PATCH={PATCH}")
    print("ALREADY_APPLIED=YES")
    print("BACKEND_UNCHANGED=YES")
    raise SystemExit(0)

if old not in src:
    raise SystemExit(f"{PATCH}: V1 recovery block not found")

src = src.replace(old, new, 1)
MAIN.write_text(src, encoding="utf-8")

print(f"PATCH={PATCH}")
print("STALE_CHUNK_GUARD=RESET_AFTER_STABLE_BOOT")
print("DYNAMIC_IMPORT_ERRORS=EXPANDED")
print("WINDOW_ERROR_HANDLER=ADDED")
print("BACKEND_UNCHANGED=YES")
print(f"BACKUP_DIR={backup_dir}")
print("NEXT=BUILD_VERIFY_DEPLOY")
