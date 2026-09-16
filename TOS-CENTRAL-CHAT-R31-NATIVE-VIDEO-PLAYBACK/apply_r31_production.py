from pathlib import Path
import json
import shutil
import subprocess
import sys
import time

PATCH = "TOS-CENTRAL-CHAT-R31-NATIVE-VIDEO-PLAYBACK"
VERSION = "TOS_CENTRAL_CHAT_R31"
BASE_TOS_COMMIT = "cced65cb5ad09d36054bff7f70c8ab990693808c"
R31_MARKER = "TOS_CENTRAL_CHAT_R31_NATIVE_VIDEO_PLAYER"
R31_CLASS = "tos-chat-native-video-r31"

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS")
FRONTEND = ROOT / "frontend"
CHAT = FRONTEND / "src/components/ChatPanel.jsx"
MANIFEST = ROOT / "deployment/tos-production-runtime.json"


def fail(message):
    raise RuntimeError(message)


def run(command, cwd=None):
    subprocess.run(command, cwd=cwd, check=True)


for path in (FRONTEND, CHAT, MANIFEST):
    if not path.exists():
        fail(f"required path missing: {path}")
for command in ("node", "npm"):
    if not shutil.which(command):
        fail(f"required command missing: {command}")

source = CHAT.read_text()
if R31_MARKER in source or R31_CLASS in source:
    fail("R31 already appears to be applied")

# Guard the current production contracts reviewed for R31.
for contract in (
    'function isImageFile(file = {})',
    'function isAudioFile(file = {})',
    'function chatFileType(file = {})',
    'function MessageFiles({ files = [], canDeleteFile = () => false, onDeleteFile = () => {} })',
    'const previewUrl = api.files.previewUrl(file.id);',
    '<audio controls preload="metadata" src={previewUrl} className="w-full" />',
    'api.files.downloadUrl(file.id)',
):
    if contract not in source:
        fail(f"required current Central Chat contract missing: {contract}")

old_helpers = '''function isAudioFile(file = {}) {
  const mimeType = String(file.mimeType || file.type || "").toLowerCase();
  const ext = fileExtension(file.name);
  return mimeType.startsWith("audio/") || [".webm", ".mp3", ".mpeg", ".mpga"].includes(ext);
}

function chatFileType(file = {}) {
  const mimeType = String(file.mimeType || file.type || "").toLowerCase();
  const ext = fileExtension(file.name);
  if (isImageFile(file)) return "images";
  if (mimeType.startsWith("video/") || [".mp4", ".webm"].includes(ext)) return "videos";'''

new_helpers = '''// TOS_CENTRAL_CHAT_R31_NATIVE_VIDEO_PLAYER
function isVideoFile(file = {}) {
  const mimeType = String(file.mimeType || file.type || "").toLowerCase();
  const ext = fileExtension(file.name);
  if (mimeType.startsWith("audio/")) return false;
  return mimeType.startsWith("video/") || [".mp4", ".webm"].includes(ext);
}

function isAudioFile(file = {}) {
  const mimeType = String(file.mimeType || file.type || "").toLowerCase();
  const ext = fileExtension(file.name);
  if (mimeType.startsWith("video/")) return false;
  return mimeType.startsWith("audio/") || [".mp3", ".mpeg", ".mpga"].includes(ext);
}

function chatFileType(file = {}) {
  const mimeType = String(file.mimeType || file.type || "").toLowerCase();
  const ext = fileExtension(file.name);
  if (isImageFile(file)) return "images";
  if (isVideoFile(file)) return "videos";'''

if source.count(old_helpers) != 1:
    fail(f"expected exactly one current audio/video helper anchor, found {source.count(old_helpers)}")
updated = source.replace(old_helpers, new_helpers, 1)

old_flags = '''        const imageFile = isImageFile(file);
        const audioFile = isAudioFile(file);
        const previewUrl = api.files.previewUrl(file.id);'''
new_flags = '''        const imageFile = isImageFile(file);
        const videoFile = isVideoFile(file);
        const audioFile = isAudioFile(file);
        const previewUrl = api.files.previewUrl(file.id);'''
if updated.count(old_flags) != 1:
    fail(f"expected exactly one MessageFiles media flag anchor, found {updated.count(old_flags)}")
updated = updated.replace(old_flags, new_flags, 1)

old_media = '''            {imageFile && (
              <a href={previewUrl} target="_blank" rel="noreferrer" className="block bg-zinc-50 dark:bg-zinc-950" title="معاينة الصورة">
                <img src={previewUrl} alt={file.name} loading="lazy" className="h-36 w-full object-cover" />
              </a>
            )}
            {audioFile && (
              <div className="bg-zinc-50 px-3 py-3 dark:bg-zinc-950">
                <audio controls preload="metadata" src={previewUrl} className="w-full" />
              </div>
            )}'''
new_media = '''            {imageFile && (
              <a href={previewUrl} target="_blank" rel="noreferrer" className="block bg-zinc-50 dark:bg-zinc-950" title="معاينة الصورة">
                <img src={previewUrl} alt={file.name} loading="lazy" className="h-36 w-full object-cover" />
              </a>
            )}
            {videoFile && (
              <div className="bg-black">
                <video
                  controls
                  preload="metadata"
                  playsInline
                  src={previewUrl}
                  className="tos-chat-native-video-r31 max-h-72 w-full bg-black object-contain"
                  aria-label={file.name || (currentChatLang() === "en" ? "Video attachment" : "فيديو مرفق")}
                />
              </div>
            )}
            {audioFile && (
              <div className="bg-zinc-50 px-3 py-3 dark:bg-zinc-950">
                <audio controls preload="metadata" src={previewUrl} className="w-full" />
              </div>
            )}'''
if updated.count(old_media) != 1:
    fail(f"expected exactly one MessageFiles media renderer anchor, found {updated.count(old_media)}")
updated = updated.replace(old_media, new_media, 1)

old_icon = '''{imageFile ? <ImageIcon size={16} className="shrink-0 text-amber-600" /> : audioFile ? <Mic size={16} className="shrink-0 text-amber-600" /> : <FileText size={16} className="shrink-0 text-amber-600" />}'''
new_icon = '''{imageFile ? <ImageIcon size={16} className="shrink-0 text-amber-600" /> : videoFile ? <Video size={16} className="shrink-0 text-amber-600" /> : audioFile ? <Mic size={16} className="shrink-0 text-amber-600" /> : <FileText size={16} className="shrink-0 text-amber-600" />}'''
if updated.count(old_icon) != 1:
    fail(f"expected exactly one MessageFiles icon anchor, found {updated.count(old_icon)}")
updated = updated.replace(old_icon, new_icon, 1)

old_preview_action = '''                {imageFile && (
                  <a href={previewUrl} target="_blank" rel="noreferrer" className="grid h-8 w-8 place-items-center rounded-xl border border-zinc-100 bg-white text-zinc-600 hover:bg-zinc-50 dark:border-white/10 dark:bg-zinc-950 dark:text-zinc-200" title="معاينة">
                    <Eye size={14} />
                  </a>
                )}'''
new_preview_action = '''                {(imageFile || videoFile) && (
                  <a href={previewUrl} target="_blank" rel="noreferrer" className="grid h-8 w-8 place-items-center rounded-xl border border-zinc-100 bg-white text-zinc-600 hover:bg-zinc-50 dark:border-white/10 dark:bg-zinc-950 dark:text-zinc-200" title={videoFile ? (currentChatLang() === "en" ? "Open video" : "فتح الفيديو") : (currentChatLang() === "en" ? "Preview" : "معاينة")}>
                    <Eye size={14} />
                  </a>
                )}'''
if updated.count(old_preview_action) != 1:
    fail(f"expected exactly one MessageFiles preview action anchor, found {updated.count(old_preview_action)}")
updated = updated.replace(old_preview_action, new_preview_action, 1)

# Verify semantic scope before writing.
if updated.count(R31_MARKER) != 1 or updated.count(R31_CLASS) != 1:
    fail("R31 marker/class verification failed")
if updated.count('const videoFile = isVideoFile(file);') != 1:
    fail("R31 video detection was not installed exactly once")
if source.count('api.files.downloadUrl(file.id)') != updated.count('api.files.downloadUrl(file.id)'):
    fail("download behavior changed unexpectedly")
if source.count('<audio controls preload="metadata" src={previewUrl} className="w-full" />') != updated.count('<audio controls preload="metadata" src={previewUrl} className="w-full" />'):
    fail("audio playback behavior changed unexpectedly")
message_files_region = updated.split('function MessageFiles(', 1)[1].split('function DriveDeleteFailures(', 1)[0]
for contract in ('<video', 'controls', 'preload="metadata"', 'playsInline', 'src={previewUrl}', R31_CLASS):
    if contract not in message_files_region:
        fail(f"R31 native video contract missing: {contract}")
if 'autoPlay' in message_files_region:
    fail("R31 must not autoplay chat video attachments")

manifest = json.loads(MANIFEST.read_text())
if manifest.get("application") != "TOS" or manifest.get("environment") != "production":
    fail("unexpected production runtime manifest")
frontend_runtime = manifest.get("frontend") or {}
if Path(str(frontend_runtime.get("sourceDir") or "")) != FRONTEND:
    fail("frontend runtime sourceDir mismatch")
if str(frontend_runtime.get("buildCommand") or "") != "npm run build":
    fail("unexpected frontend build command")
DIST = Path(str(frontend_runtime.get("buildOutputDir") or ""))
LIVE = Path(str(frontend_runtime.get("publishedBuildDir") or ""))
if DIST != FRONTEND / "dist":
    fail(f"unexpected frontend build output: {DIST}")
if LIVE != Path("/opt/apps/tamiyouz-front/build"):
    fail(f"unexpected live frontend path: {LIVE}")

stamp = int(time.time())
backup_root = Path(f"/var/backups/tos-patches/central-chat-r31-{stamp}")
backup_root.mkdir(parents=True, exist_ok=False)
shutil.copy2(CHAT, backup_root / CHAT.name)

LIVE.parent.mkdir(parents=True, exist_ok=True)
staging = LIVE.parent / f"build.central-chat-r31-staging-{stamp}"
live_backup = LIVE.parent / f"build.central-chat-r31-backup-{stamp}"
live_swapped = False

try:
    CHAT.write_text(updated)
    written = CHAT.read_text()
    if R31_MARKER not in written or R31_CLASS not in written:
        fail("R31 source marker missing after write")

    run(["npm", "run", "build"], cwd=FRONTEND)
    if not DIST.exists() or not (DIST / "index.html").exists():
        fail("frontend dist missing after build")

    built_js = "\n".join(p.read_text(errors="ignore") for p in DIST.rglob("*.js"))
    if R31_CLASS not in built_js:
        fail("R31 native video player class missing from build")

    if staging.exists():
        shutil.rmtree(staging)
    shutil.copytree(DIST, staging)
    if LIVE.exists():
        if live_backup.exists():
            shutil.rmtree(live_backup)
        LIVE.rename(live_backup)
    staging.rename(LIVE)
    live_swapped = True

    live_js = "\n".join(p.read_text(errors="ignore") for p in LIVE.rglob("*.js"))
    if R31_CLASS not in live_js:
        fail("R31 native video player class missing from live build")

except Exception:
    shutil.copy2(backup_root / CHAT.name, CHAT)
    if live_swapped:
        if LIVE.exists():
            shutil.rmtree(LIVE)
        if live_backup.exists():
            live_backup.rename(LIVE)
    elif staging.exists():
        shutil.rmtree(staging)
    raise

print(f"VERSION={VERSION}")
print(f"PATCH_APPLIED={PATCH}")
print(f"BASE_TOS_COMMIT_REVIEWED={BASE_TOS_COMMIT}")
print("BUILD_STATUS=PASS")
print("DEPLOY_STATUS=PASS")
print("NATIVE_VIDEO_PLAYER=YES")
print("VIDEO_CONTROLS=YES")
print("VIDEO_AUTOPLAY=NO")
print("VIDEO_PRELOAD=METADATA")
print("VIDEO_PLAYS_INLINE=YES")
print("IMAGE_PREVIEW_PRESERVED=YES")
print("AUDIO_PLAYBACK_PRESERVED=YES")
print("DOWNLOAD_ACTION_PRESERVED=YES")
print("BACKEND_CHANGED=NO")
print("API_CHANGED=NO")
print("DATABASE_CHANGED=NO")
print("STORAGE_CHANGED=NO")
print("PERMISSIONS_CHANGED=NO")
print("SOURCE_PROJECT_PUSHED=NO")
print("PUSH=NO")
print("STATUS=READY_FOR_FUNCTIONAL_VISUAL_QA")
