#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import shutil, sys

PATCH = "TCS-ATTACHMENTS-GDRIVE-FLOW-V1"
ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
CHAT = ROOT / "frontend/src/components/ChatPanel.jsx"

if not CHAT.exists():
    raise SystemExit(f"{PATCH}: missing {CHAT}")

src = CHAT.read_text(encoding="utf-8")
backup_dir = Path("/tmp") / f"{PATCH}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
backup_dir.mkdir(parents=True, exist_ok=True)
shutil.copy2(CHAT, backup_dir / "ChatPanel.jsx")

# Stable queue key for retained browser File objects.
helper_anchor = '''function uniqueMessages(messages = []) {
  return [...new Set(messages.filter(Boolean))];
}'''
helper_replacement = helper_anchor + '''

function chatUploadQueueKey(file = {}) {
  return [file.name || "file", file.size || 0, file.lastModified || 0].join(":");
}'''
if "function chatUploadQueueKey(" not in src:
    if helper_anchor not in src:
        raise SystemExit(f"{PATCH}: uniqueMessages helper anchor not found")
    src = src.replace(helper_anchor, helper_replacement, 1)

# Add retry helpers after selected-file removal.
remove_anchor = '''  function removeSelectedFile(index) {
    setSelectedFiles((prev) => prev.filter((_, itemIndex) => itemIndex !== index));
  }'''
retry_helpers = remove_anchor + '''

  async function retryQueuedAttachment(queueKey) {
    const queued = uploadQueue.find((item) => item.key === queueKey);
    if (!queued?.file || !queued?.messageId || queued.status === "uploading" || queued.status === "done") return false;

    setUploadingFiles(true);
    setLocalError("");
    setUploadQueue((prev) => prev.map((item) => (
      item.key === queueKey ? { ...item, status: "uploading", error: "" } : item
    )));

    try {
      await uploadChatFile(queued.messageId, queued.file);
      setUploadQueue((prev) => {
        const next = prev.map((item) => (
          item.key === queueKey ? { ...item, status: "done", error: "" } : item
        ));
        if (next.every((item) => item.status === "done")) {
          window.setTimeout(() => setUploadQueue([]), 1400);
        }
        return next;
      });
      clearError?.();
      if (isDirectMode) loadDirectFiles(activeConversationId);
      setLocalSuccess(lang === "en" ? `${queued.name} uploaded to Google Drive.` : `تم رفع ${queued.name} إلى Google Drive.`);
      return true;
    } catch (err) {
      clearError?.();
      const message = getErrorMessage(err, lang === "en" ? "Attachment upload failed." : "تعذر رفع المرفق.");
      setUploadQueue((prev) => prev.map((item) => (
        item.key === queueKey ? { ...item, status: "failed", error: message } : item
      )));
      setLocalError(message);
      return false;
    } finally {
      setUploadingFiles(false);
    }
  }

  async function retryAllFailedAttachments() {
    const failedKeys = uploadQueue.filter((item) => item.status === "failed").map((item) => item.key);
    if (!failedKeys.length) return;
    for (const key of failedKeys) {
      await retryQueuedAttachment(key);
    }
  }'''
if "async function retryQueuedAttachment(" not in src:
    if remove_anchor not in src:
        raise SystemExit(f"{PATCH}: removeSelectedFile anchor not found")
    src = src.replace(remove_anchor, retry_helpers, 1)

# Replace attachment upload transaction:
# - keep the sent message
# - upload every file independently
# - preserve successes
# - retain failed File objects for retry
old_upload_block = '''        if (message?.id && selectedFiles.length) {
          setUploadingFiles(true);
          setUploadQueue(selectedFiles.map((file) => ({ name: file.name, size: file.size, status: "pending" })));
          try {
            for (const file of selectedFiles) {
              setUploadQueue((prev) => prev.map((item) => (item.name === file.name && item.size === file.size ? { ...item, status: "uploading" } : item)));
              await uploadChatFile(message.id, file);
              setUploadQueue((prev) => prev.map((item) => (item.name === file.name && item.size === file.size ? { ...item, status: "done" } : item)));
            }
            clearError?.();
            setLocalError("");
            setLocalSuccess(`تم رفع ${selectedFiles.length} ملف على Google Drive.`);
          } catch (uploadError) {
            setUploadQueue((prev) => prev.map((item) => (item.status === "done" ? item : { ...item, status: "failed" })));
            await deleteMessage(message.id).catch(() => null);
            throw uploadError;
          }
        }'''
new_upload_block = '''        let failedAttachmentCount = 0;
        if (message?.id && selectedFiles.length) {
          setUploadingFiles(true);
          const initialQueue = selectedFiles.map((file) => ({
            key: chatUploadQueueKey(file),
            file,
            messageId: message.id,
            name: file.name,
            size: file.size,
            status: "pending",
            error: "",
          }));
          setUploadQueue(initialQueue);

          for (const file of selectedFiles) {
            const key = chatUploadQueueKey(file);
            setUploadQueue((prev) => prev.map((item) => (
              item.key === key ? { ...item, status: "uploading", error: "" } : item
            )));
            try {
              await uploadChatFile(message.id, file);
              setUploadQueue((prev) => prev.map((item) => (
                item.key === key ? { ...item, status: "done", error: "" } : item
              )));
            } catch (uploadError) {
              failedAttachmentCount += 1;
              clearError?.();
              const uploadMessage = getErrorMessage(uploadError, lang === "en" ? "Attachment upload failed." : "تعذر رفع المرفق.");
              setUploadQueue((prev) => prev.map((item) => (
                item.key === key ? { ...item, status: "failed", error: uploadMessage } : item
              )));
            }
          }

          clearError?.();
          if (failedAttachmentCount > 0) {
            setLocalError(lang === "en"
              ? `${failedAttachmentCount} attachment(s) failed. The message and successful uploads were kept; retry the failed files below.`
              : `فشل رفع ${failedAttachmentCount} مرفق. تم الاحتفاظ بالرسالة والملفات الناجحة؛ أعد محاولة الملفات الفاشلة بالأسفل.`);
          } else {
            setLocalError("");
            setLocalSuccess(lang === "en"
              ? `${selectedFiles.length} file(s) uploaded to Google Drive.`
              : `تم رفع ${selectedFiles.length} ملف على Google Drive.`);
          }
        }'''
if "failedAttachmentCount = 0" not in src:
    if old_upload_block not in src:
        raise SystemExit(f"{PATCH}: attachment upload transaction anchor not found")
    src = src.replace(old_upload_block, new_upload_block, 1)

# Current cleanup always hides the queue. Keep failed queue visible for retry.
old_cleanup = '''      setSelectedFiles([]);
      window.setTimeout(() => setUploadQueue([]), 1200);
      if (composerRef.current) composerRef.current.style.height = "auto";'''
new_cleanup = '''      setSelectedFiles([]);
      if (!uploadQueue.some((item) => item.status === "failed") && !localError) {
        window.setTimeout(() => setUploadQueue((prev) => prev.some((item) => item.status === "failed") ? prev : []), 1600);
      }
      if (composerRef.current) composerRef.current.style.height = "auto";'''
# Use a safer deterministic form: schedule clear, but callback preserves any failed entries.
new_cleanup = '''      setSelectedFiles([]);
      window.setTimeout(() => setUploadQueue((prev) => prev.some((item) => item.status === "failed") ? prev : []), 1600);
      if (composerRef.current) composerRef.current.style.height = "auto";'''
if old_cleanup in src:
    src = src.replace(old_cleanup, new_cleanup, 1)
elif 'prev.some((item) => item.status === "failed") ? prev : []' not in src:
    raise SystemExit(f"{PATCH}: upload queue cleanup anchor not found")

# Update the stale generic error: attachment failures no longer cancel/delete the sent message.
old_catch = '''    } catch (err) {
      setLocalError(getErrorMessage(err, selectedFiles.length ? "فشل رفع الملف، وتم إلغاء الرسالة لحماية الشات." : "تعذر تنفيذ العملية."));
    } finally {'''
new_catch = '''    } catch (err) {
      setLocalError(getErrorMessage(err, "تعذر تنفيذ العملية."));
    } finally {'''
if old_catch in src:
    src = src.replace(old_catch, new_catch, 1)

# Upgrade queue UI with retry-per-file and retry-all.
old_queue = '''          {uploadQueue.length > 0 && (
            <div className="mb-3 rounded-3xl border border-emerald-100 bg-emerald-50 p-3 text-xs text-emerald-900 dark:border-emerald-500/20 dark:bg-emerald-500/10 dark:text-emerald-100">
              <div className="mb-2 font-black">حالة الرفع إلى Google Drive</div>
              <div className="grid gap-2 sm:grid-cols-2">
                {uploadQueue.map((file, index) => (
                  <div key={`${file.name}-${file.size}-${index}`} className="rounded-2xl bg-white px-3 py-2 dark:bg-zinc-950">
                    <div className="flex items-center justify-between gap-2">
                      <span className="truncate font-black">{file.name}</span>
                      <span className="shrink-0 rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-100">
                        {file.status === "done" ? "تم" : file.status === "failed" ? "فشل" : file.status === "uploading" ? "جاري" : "انتظار"}
                      </span>
                    </div>
                    <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-emerald-100 dark:bg-emerald-500/20">
                      <div className={`h-full rounded-full bg-emerald-500 transition-all ${file.status === "done" ? "w-full" : file.status === "failed" ? "w-full bg-red-400" : file.status === "uploading" ? "w-2/3 animate-pulse" : "w-1/4"}`} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}'''
new_queue = '''          {uploadQueue.length > 0 && (
            <div data-tcs-attachments-drive-flow="v1" className="mb-3 rounded-3xl border border-emerald-100 bg-emerald-50 p-3 text-xs text-emerald-900 dark:border-emerald-500/20 dark:bg-emerald-500/10 dark:text-emerald-100">
              <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                <div className="font-black">{lang === "en" ? "Google Drive upload status" : "حالة الرفع إلى Google Drive"}</div>
                <div className="flex items-center gap-2">
                  {uploadQueue.some((item) => item.status === "failed") && (
                    <button type="button" onClick={retryAllFailedAttachments} disabled={uploadingFiles} className="rounded-xl bg-zinc-950 px-2.5 py-1.5 text-[10px] font-black text-white disabled:opacity-50 dark:bg-white dark:text-zinc-950">
                      {lang === "en" ? "Retry failed" : "إعادة الفاشل"}
                    </button>
                  )}
                  {!uploadingFiles && uploadQueue.some((item) => item.status === "failed") && (
                    <button type="button" onClick={() => setUploadQueue([])} className="rounded-xl border border-emerald-200 bg-white px-2.5 py-1.5 text-[10px] font-black text-emerald-800 dark:border-emerald-500/20 dark:bg-zinc-950 dark:text-emerald-100">
                      {lang === "en" ? "Dismiss" : "إخفاء"}
                    </button>
                  )}
                </div>
              </div>
              <div className="grid gap-2 sm:grid-cols-2">
                {uploadQueue.map((file) => (
                  <div key={file.key || `${file.name}-${file.size}`} className="rounded-2xl bg-white px-3 py-2 dark:bg-zinc-950">
                    <div className="flex items-center justify-between gap-2">
                      <span className="min-w-0 flex-1 truncate font-black">{file.name}</span>
                      <div className="flex shrink-0 items-center gap-1.5">
                        <span className={`rounded-full px-2 py-0.5 text-[10px] ${file.status === "failed" ? "bg-red-100 text-red-700 dark:bg-red-500/20 dark:text-red-100" : "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-100"}`}>
                          {file.status === "done" ? (lang === "en" ? "Done" : "تم") : file.status === "failed" ? (lang === "en" ? "Failed" : "فشل") : file.status === "uploading" ? (lang === "en" ? "Uploading" : "جاري") : (lang === "en" ? "Pending" : "انتظار")}
                        </span>
                        {file.status === "failed" && (
                          <button type="button" onClick={() => retryQueuedAttachment(file.key)} disabled={uploadingFiles} className="rounded-lg bg-red-50 px-2 py-1 text-[9px] font-black text-red-700 disabled:opacity-50 dark:bg-red-500/10 dark:text-red-100">
                            {lang === "en" ? "Retry" : "إعادة"}
                          </button>
                        )}
                      </div>
                    </div>
                    <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-emerald-100 dark:bg-emerald-500/20">
                      <div className={`h-full rounded-full bg-emerald-500 transition-all ${file.status === "done" ? "w-full" : file.status === "failed" ? "w-full bg-red-400" : file.status === "uploading" ? "w-2/3 animate-pulse" : "w-1/4"}`} />
                    </div>
                    {file.status === "failed" && file.error && <div className="mt-1.5 line-clamp-2 text-[10px] text-red-600 dark:text-red-200">{file.error}</div>}
                  </div>
                ))}
              </div>
            </div>
          )}'''
if 'data-tcs-attachments-drive-flow="v1"' not in src:
    if old_queue not in src:
        raise SystemExit(f"{PATCH}: upload queue UI anchor not found")
    src = src.replace(old_queue, new_queue, 1)

CHAT.write_text(src, encoding="utf-8")

print(f"PATCH={PATCH}")
print("MODE=FUNCTIONAL_FRONTEND")
print("FILE_VALIDATION=PRESERVED")
print("MULTI_FILE_UPLOAD=INDEPENDENT")
print("PARTIAL_SUCCESS=PRESERVED")
print("MESSAGE_ROLLBACK_ON_UPLOAD_FAIL=REMOVED")
print("FAILED_UPLOAD_RETRY=YES")
print("RETRY_ALL_FAILED=YES")
print("DOWNLOAD_PREVIEW=PRESERVED")
print("DELETE_DRIVE_CLEANUP=PRESERVED")
print("DIRECT_FILES_REFRESH=PRESERVED")
print("BACKEND_UNCHANGED=YES")
print(f"BACKUP_DIR={backup_dir}")
print("NEXT=BUILD_VERIFY_DEPLOY")
