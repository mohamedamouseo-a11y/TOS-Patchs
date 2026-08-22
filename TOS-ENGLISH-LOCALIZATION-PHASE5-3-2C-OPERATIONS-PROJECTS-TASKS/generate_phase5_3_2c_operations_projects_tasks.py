#!/usr/bin/env python3
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

EXPECTED_HEAD = "5311de3e893eeecbd46a2741f8c535836962f0fe"
TARGET = "frontend/src/pages/SettingsPage.jsx"
EXPECTED_BLOB = "705c1a3fea878aef1185eb56aa3fc1dbce8298c0"
REGION_START = "function SettingsOperationsInfo({ user }) {"
REGION_END = "function SettingsSectionHeader({ section }) {"

REPLACEMENTS = [
    (
        '{ key: "projectsTasks", label: "المشاريع والمهام", icon: FolderKanban },',
        '{ key: "projectsTasks", label: opsText("المشاريع والمهام", "Projects & Tasks"), icon: FolderKanban },',
    ),
    ('if (!name) return setError("اكتب اسم نوع المشروع أولًا.");', 'if (!name) return setError(opsText("اكتب اسم نوع المشروع أولًا.", "Enter the project type name first."));'),
    ('setError("نوع المشروع موجود بالفعل.");', 'setError(opsText("نوع المشروع موجود بالفعل.", "This project type already exists."));'),
    ('if (!window.confirm(`حذف نوع المشروع: ${item.name}؟`)) return;', 'if (!window.confirm(opsText(`حذف نوع المشروع: ${item.name}؟`, `Delete project type: ${item.name}?`))) return;'),
    ('if (!/^image\\/(png|jpe?g|webp|gif)$/i.test(file.type || "")) return "ارفع صورة بصيغة PNG أو JPG أو WEBP أو GIF.";', 'if (!/^image\\/(png|jpe?g|webp|gif)$/i.test(file.type || "")) return opsText("ارفع صورة بصيغة PNG أو JPG أو WEBP أو GIF.", "Upload a PNG, JPG, WEBP, or GIF image.");'),
    ('if (file.size > PROJECT_TYPE_IMAGE_MAX_FILE_SIZE_BYTES) return `حجم صورة نوع المشروع يجب ألا يتجاوز ${PROJECT_TYPE_IMAGE_MAX_FILE_SIZE_MB}MB.`;', 'if (file.size > PROJECT_TYPE_IMAGE_MAX_FILE_SIZE_BYTES) return opsText(`حجم صورة نوع المشروع يجب ألا يتجاوز ${PROJECT_TYPE_IMAGE_MAX_FILE_SIZE_MB}MB.`, `Project type image size must not exceed ${PROJECT_TYPE_IMAGE_MAX_FILE_SIZE_MB}MB.`);'),
    ('async function persistProjectTypes(nextProjectTypes, successMessage = "تم حفظ أنواع المشاريع.", options = {}) {', 'async function persistProjectTypes(nextProjectTypes, successMessage = opsText("تم حفظ أنواع المشاريع.", "Project types saved."), options = {}) {'),
    ('const message = getErrorMessage(err, "تم رفع الصورة لكن تعذر حفظ ربطها بنوع المشروع.");', 'const message = getErrorMessage(err, opsText("تم رفع الصورة لكن تعذر حفظ ربطها بنوع المشروع.", "The image was uploaded, but linking it to the project type could not be saved."));'),
    ('setProjectTypeUploadState(uploadKey, { status: "uploading", progress: 1, fileName: file.name || "image", message: "جاري رفع الصورة..." });', 'setProjectTypeUploadState(uploadKey, { status: "uploading", progress: 1, fileName: file.name || "image", message: opsText("جاري رفع الصورة...", "Uploading image...") });'),
    ('onProgress: (percent) => setProjectTypeUploadState(uploadKey, { status: "uploading", progress: percent, message: `جاري رفع الصورة... ${Math.round(percent || 0)}%` }),', 'onProgress: (percent) => setProjectTypeUploadState(uploadKey, { status: "uploading", progress: percent, message: opsText(`جاري رفع الصورة... ${Math.round(percent || 0)}%`, `Uploading image... ${Math.round(percent || 0)}%`) }),'),
    ('if (!imageUrl) throw new Error("لم يرجع السيرفر رابط صورة صالح.");', 'if (!imageUrl) throw new Error(opsText("لم يرجع السيرفر رابط صورة صالح.", "The server did not return a valid image URL."));'),
    ('setProjectTypeUploadState(uploadKey, { status: "success", progress: 100, message: "تم رفع الصورة، جاري حفظ الربط..." });', 'setProjectTypeUploadState(uploadKey, { status: "success", progress: 100, message: opsText("تم رفع الصورة، جاري حفظ الربط...", "Image uploaded; saving the link...") });'),
    ('const message = getErrorMessage(err, "تعذر رفع صورة نوع المشروع على Google Drive.");', 'const message = getErrorMessage(err, opsText("تعذر رفع صورة نوع المشروع على Google Drive.", "Unable to upload the project type image to Google Drive."));'),
    ('const saved = await persistProjectTypes(nextProjectTypes, "تم رفع وحفظ صورة نوع المشروع.", { globalLoading: false, silent: true });', 'const saved = await persistProjectTypes(nextProjectTypes, opsText("تم رفع وحفظ صورة نوع المشروع.", "Project type image uploaded and saved."), { globalLoading: false, silent: true });'),
    ('setProjectTypeUploadState(uploadKey, { status: "success", progress: 100, message: "تم رفع وحفظ صورة النوع" });', 'setProjectTypeUploadState(uploadKey, { status: "success", progress: 100, message: opsText("تم رفع وحفظ صورة النوع", "Project type image uploaded and saved") });'),
    ('setMessage("تم رفع وحفظ صورة نوع المشروع بدون تحديث الصفحة.");', 'setMessage(opsText("تم رفع وحفظ صورة نوع المشروع بدون تحديث الصفحة.", "Project type image uploaded and saved without refreshing the page."));'),
    ('setProjectTypeUploadState(uploadKey, { status: "error", progress: 100, message: saved.message || "تعذر حفظ ربط الصورة بنوع المشروع." });', 'setProjectTypeUploadState(uploadKey, { status: "error", progress: 100, message: saved.message || opsText("تعذر حفظ ربط الصورة بنوع المشروع.", "Unable to save the image link for this project type.") });'),
    ('setProjectTypeUploadState(uploadKey, { status: "uploading", progress: 35, message: "جاري حذف الصورة وحفظ التعديل..." });', 'setProjectTypeUploadState(uploadKey, { status: "uploading", progress: 35, message: opsText("جاري حذف الصورة وحفظ التعديل...", "Removing image and saving the change...") });'),
    ('const saved = await persistProjectTypes(nextProjectTypes, "تم حذف صورة نوع المشروع وحفظ التعديل.", { globalLoading: false, silent: true });', 'const saved = await persistProjectTypes(nextProjectTypes, opsText("تم حذف صورة نوع المشروع وحفظ التعديل.", "Project type image removed and change saved."), { globalLoading: false, silent: true });'),
    ('setProjectTypeUploadState(uploadKey, { status: saved.ok ? "success" : "error", progress: 100, message: saved.ok ? "تم حذف الصورة وحفظ التعديل" : (saved.message || "تعذر حذف الصورة.") });', 'setProjectTypeUploadState(uploadKey, { status: saved.ok ? "success" : "error", progress: 100, message: saved.ok ? opsText("تم حذف الصورة وحفظ التعديل", "Image removed and change saved") : (saved.message || opsText("تعذر حذف الصورة.", "Unable to remove the image.")) });'),
    (
        '<section className="flex items-start justify-between gap-4"><div><h4 className="text-xl font-black text-zinc-950 dark:text-white">المشاريع والمهام</h4><p className="mt-1 text-xs font-bold text-zinc-500 dark:text-zinc-400">أنواع المشاريع وإعدادات المهام الافتراضية في قسم واحد.</p></div><div className="grid h-12 w-12 place-items-center rounded-2xl bg-violet-100 text-violet-700 dark:bg-violet-500/15 dark:text-violet-200"><FolderKanban size={23} /></div></section>',
        '<section className="flex items-start justify-between gap-4"><div><h4 className="text-xl font-black text-zinc-950 dark:text-white">{opsText("المشاريع والمهام", "Projects & Tasks")}</h4><p className="mt-1 text-xs font-bold text-zinc-500 dark:text-zinc-400">{opsText("أنواع المشاريع وإعدادات المهام الافتراضية في قسم واحد.", "Project types and default task settings in one section.")}</p></div><div className="grid h-12 w-12 place-items-center rounded-2xl bg-violet-100 text-violet-700 dark:bg-violet-500/15 dark:text-violet-200"><FolderKanban size={23} /></div></section>',
    ),
    (
        '{[["projectTypes", "أنواع المشاريع", FolderKanban], ["taskDefaults", "إعدادات المهام الافتراضية", ListChecks]].map(([key, label, Icon]) =>',
        '{[["projectTypes", opsText("أنواع المشاريع", "Project Types"), FolderKanban], ["taskDefaults", opsText("إعدادات المهام الافتراضية", "Default Task Settings"), ListChecks]].map(([key, label, Icon]) =>',
    ),
    ('>أنواع المشاريع المعتمدة</h5><p className="mt-1 text-xs font-bold text-zinc-400">الأنواع المفعلة تظهر عند إنشاء المشاريع وفي الفلاتر.</p>', '>{opsText("أنواع المشاريع المعتمدة", "Approved Project Types")}</h5><p className="mt-1 text-xs font-bold text-zinc-400">{opsText("الأنواع المفعلة تظهر عند إنشاء المشاريع وفي الفلاتر.", "Active types appear when creating projects and in filters.")}</p>'),
    ('placeholder="اسم نوع المشروع"', 'placeholder={opsText("اسم نوع المشروع", "Project type name")}'),
    ('projectTypeImageUploads.draft?.status === "uploading" ? `${Math.round(projectTypeImageUploads.draft?.progress || 0)}%` : "صورة النوع"', 'projectTypeImageUploads.draft?.status === "uploading" ? `${Math.round(projectTypeImageUploads.draft?.progress || 0)}%` : opsText("صورة النوع", "Type image")'),
    ('{projectTypeDraft.editingId ? "تحديث" : "إضافة نوع"}', '{projectTypeDraft.editingId ? opsText("تحديث", "Update") : opsText("إضافة نوع", "Add type")}'),
    ('{item.isActive ? "مفعل" : "معطل"}', '{item.isActive ? opsText("مفعل", "Active") : opsText("معطل", "Inactive")}'),
    ('uploading ? `${Math.round(uploadState?.progress || 0)}%` : imageUrl ? "تغيير الصورة" : "رفع صورة"', 'uploading ? `${Math.round(uploadState?.progress || 0)}%` : imageUrl ? opsText("تغيير الصورة", "Change image") : opsText("رفع صورة", "Upload image")'),
    ('disabled={uploading}>حذف الصورة</Button>', 'disabled={uploading}>{opsText("حذف الصورة", "Remove image")}</Button>'),
    ('<PencilLine size={13} /> تعديل</Button>', '<PencilLine size={13} /> {opsText("تعديل", "Edit")}</Button>'),
    ('>إعدادات المهام الافتراضية</h5><p className="mt-1 text-xs font-bold text-zinc-400">تستخدم هذه القيم كبداية عند إنشاء المشاريع الجديدة.</p>', '>{opsText("إعدادات المهام الافتراضية", "Default Task Settings")}</h5><p className="mt-1 text-xs font-bold text-zinc-400">{opsText("تستخدم هذه القيم كبداية عند إنشاء المشاريع الجديدة.", "These values are used as defaults when creating new projects.")}</p>'),
    ('<span>الوقت التقديري الافتراضي بالساعات</span>', '<span>{opsText("الوقت التقديري الافتراضي بالساعات", "Default estimated time (hours)")}</span>'),
    ('>تتبع الوقت للمشاريع الجديدة</span><span className="mt-1 block text-[11px] text-zinc-400">يكون مفعلًا بصورة افتراضية</span>', '>{opsText("تتبع الوقت للمشاريع الجديدة", "Time tracking for new projects")}</span><span className="mt-1 block text-[11px] text-zinc-400">{opsText("يكون مفعلًا بصورة افتراضية", "Enabled by default")}</span>'),
]


def die(message, code=1):
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(code)


def run(args, cwd, check=True):
    p = subprocess.run(args, cwd=cwd, text=True, capture_output=True)
    if p.stdout:
        print(p.stdout, end="")
    if p.stderr:
        print(p.stderr, end="", file=sys.stderr)
    if check and p.returncode:
        die(f"command failed rc={p.returncode}: {' '.join(args)}", 90)
    return p


def main():
    if len(sys.argv) != 3:
        die("usage: generate_phase5_3_2c_operations_projects_tasks.py REPO_ROOT OUTPUT_PATCH", 2)

    root = Path(sys.argv[1]).resolve()
    output = Path(sys.argv[2]).resolve()
    target = root / TARGET

    if not (root / ".git").is_dir():
        die("not a git repository", 3)
    if not target.is_file():
        die(f"missing target: {TARGET}", 4)

    head = run(["git", "rev-parse", "HEAD"], root).stdout.strip()
    print(f"HEAD={head}")
    if head != EXPECTED_HEAD:
        die(f"HEAD mismatch expected={EXPECTED_HEAD} actual={head}", 5)

    blob = run(["git", "hash-object", TARGET], root).stdout.strip()
    print(f"SOURCE_BLOB={blob}")
    if blob != EXPECTED_BLOB:
        die(f"blob mismatch expected={EXPECTED_BLOB} actual={blob}", 6)

    if run(["git", "diff", "--cached", "--", TARGET], root).stdout.strip():
        die("target has staged changes", 7)

    raw = target.read_bytes()
    if b"\r\n" in raw:
        die("CRLF detected", 8)
    terminal_newline = raw.endswith(b"\n")
    text = raw.decode("utf-8")

    start = text.find(REGION_START)
    end = text.find(REGION_END, start + len(REGION_START))
    if start < 0 or end < 0:
        die("Operations region markers missing", 9)

    before, region, after = text[:start], text[start:end], text[end:]

    for idx, (old, new) in enumerate(REPLACEMENTS, start=1):
        count = region.count(old)
        print(f"REPLACEMENT_{idx}_MATCHES={count}")
        if count != 1:
            die(f"replacement {idx} expected exactly 1 match, found {count}", 20 + idx)
        region = region.replace(old, new, 1)

    text = before + region + after

    tmp = Path(tempfile.mkdtemp(prefix="tos-phase5-3-2c-"))
    try:
        run(["git", "init", "-q"], tmp)
        run(["git", "config", "user.email", "phase5-3-2c@tos.local"], tmp)
        run(["git", "config", "user.name", "TOS Phase 5.3.2C Generator"], tmp)
        tmp_target = tmp / TARGET
        tmp_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(target, tmp_target)
        run(["git", "add", "--", TARGET], tmp)
        run(["git", "commit", "-qm", "exact post-5.3.2b baseline"], tmp)

        encoded = text.encode("utf-8")
        if terminal_newline and not encoded.endswith(b"\n"):
            encoded += b"\n"
        elif not terminal_newline and encoded.endswith(b"\n"):
            encoded = encoded[:-1]
        tmp_target.write_bytes(encoded)

        diff = subprocess.run(["git", "diff", "--binary", "--full-index", "--", TARGET], cwd=tmp, text=True, capture_output=True)
        if diff.returncode or not diff.stdout.strip():
            die("failed to generate patch", 70)
        output.write_text(diff.stdout, encoding="utf-8", newline="\n")
        print(f"GENERATED_PATCH_SHA256={hashlib.sha256(output.read_bytes()).hexdigest()}")

        numstat = run(["git", "apply", "--numstat", str(output)], root).stdout.strip().splitlines()
        paths = {row.split("\t")[-1] for row in numstat if row.strip()}
        if paths != {TARGET}:
            die(f"unexpected patch paths: {sorted(paths)}", 71)
        print("PARSER=PASS")
        run(["git", "apply", "--check", str(output)], root)
        print("APPLY_CHECK=PASS")
        print("GENERATION_MODE=PROJECTS_TASKS_REGION_SCOPED_FROM_EXACT_POST_5_3_2B_SOURCE")
        print("PHASE5_3_2C_OPERATIONS_PROJECTS_TASKS_GENERATOR=PASS")
        print(f"OUTPUT={output}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
