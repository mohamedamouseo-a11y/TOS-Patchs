#!/usr/bin/env python3
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

EXPECTED_HEAD = "65e4fa5496e831504ddc20fb1493aba1324341dc"
TARGET = "frontend/src/components/settings/TgwsSettingsAdmin.jsx"
EXPECTED_BLOB = "e85c3657279eb6715c9778e85a8ee4c99f4df16b"

REPLACEMENTS = [
    ('import { getErrorMessage } from "../../lib/errors";\n', 'import { getErrorMessage } from "../../lib/errors";\nimport { usePreferences } from "../../contexts/PreferencesContext";\n'),
    ('function formatSavedAt(value) {\n  if (!value) return "—";\n  try { return new Date(value).toLocaleString("ar-EG"); } catch { return "—"; }\n}', 'function formatSavedAt(value, locale = "ar-EG") {\n  if (!value) return "—";\n  try { return new Date(value).toLocaleString(locale); } catch { return "—"; }\n}'),
    ('export function TgwsSettingsAdmin({ user }) {\n', 'export function TgwsSettingsAdmin({ user }) {\n  const { isAr } = usePreferences();\n  const tgwsText = (ar, en) => (isAr ? ar : en);\n  const tgwsLocale = isAr ? "ar-EG" : "en-US";\n'),
    ('throw new Error("تعذر إنشاء سجل إعدادات TGWS داخل قاعدة البيانات.");', 'throw new Error(tgwsText("تعذر إنشاء سجل إعدادات TGWS داخل قاعدة البيانات.", "Unable to create the TGWS settings record in the database."));'),
    ('throw new Error("نسخة Backend الخاصة بربط Google Editor Email ليست V1R7.");', 'throw new Error(tgwsText("نسخة Backend الخاصة بربط Google Editor Email ليست V1R7.", "The Google Editor Email backend build is not V1R7."));'),
    ('setError(getErrorMessage(err, "تعذر تحميل إعدادات TGWS."));', 'setError(getErrorMessage(err, tgwsText("تعذر تحميل إعدادات TGWS.", "Unable to load TGWS settings.")));'),
    ('if (!result?.url) throw new Error("لم يتم استلام رابط OAuth.");', 'if (!result?.url) throw new Error(tgwsText("لم يتم استلام رابط OAuth.", "OAuth URL was not received."));'),
    ('setMessage("تم فتح صفحة Google. بعد إتمام الربط ارجع إلى هذه الصفحة.");', 'setMessage(tgwsText("تم فتح صفحة Google. بعد إتمام الربط ارجع إلى هذه الصفحة.", "Google was opened. Return to this page after completing the connection."));'),
    ('throw new Error("تعذر تهيئة سجل إعدادات TGWS قبل الحفظ.");', 'throw new Error(tgwsText("تعذر تهيئة سجل إعدادات TGWS قبل الحفظ.", "Unable to initialize the TGWS settings record before saving."));'),
    ('throw new Error("نسخة Backend الخاصة بـ TGWS ليست V1R7. أعد Build وRestart ثم حدّث الصفحة.");', 'throw new Error(tgwsText("نسخة Backend الخاصة بـ TGWS ليست V1R7. أعد Build وRestart ثم حدّث الصفحة.", "The TGWS backend build is not V1R7. Rebuild and restart, then refresh the page."));'),
    ('throw new Error("تعذر التأكد من تثبيت إعدادات TGWS في قاعدة البيانات. لم يتم عرض رسالة نجاح.");', 'throw new Error(tgwsText("تعذر التأكد من تثبيت إعدادات TGWS في قاعدة البيانات. لم يتم عرض رسالة نجاح.", "Unable to verify that TGWS settings were persisted in the database. No success message was shown."));'),
    ('throw new Error("تم حفظ الإعدادات لكن حالة التشغيل المقروءة لا تطابقها. راجع Logs قبل الاستخدام.");', 'throw new Error(tgwsText("تم حفظ الإعدادات لكن حالة التشغيل المقروءة لا تطابقها. راجع Logs قبل الاستخدام.", "Settings were saved, but the runtime state does not match them. Review the logs before use."));'),
    ('setMessage(`تم حفظ سياسة TGWS والتأكد منها بعد قراءة جديدة من قاعدة البيانات — ${formatSavedAt(verified.savedAt || verified.updatedAt)}.`);', 'setMessage(tgwsText(`تم حفظ سياسة TGWS والتأكد منها بعد قراءة جديدة من قاعدة البيانات — ${formatSavedAt(verified.savedAt || verified.updatedAt, tgwsLocale)}.`, `TGWS policy saved and verified with a fresh database read — ${formatSavedAt(verified.savedAt || verified.updatedAt, tgwsLocale)}.`));'),
    ('throw new Error("الخادم لم يؤكد حفظ Google Editor Email في قاعدة البيانات.");', 'throw new Error(tgwsText("الخادم لم يؤكد حفظ Google Editor Email في قاعدة البيانات.", "The server did not confirm that Google Editor Email was saved in the database."));'),
    ('if (!persisted) throw new Error("تعذر قراءة المستخدم بعد حفظ الربط.");', 'if (!persisted) throw new Error(tgwsText("تعذر قراءة المستخدم بعد حفظ الربط.", "Unable to read the user after saving the mapping."));'),
    ('throw new Error("لم يتم تثبيت Google Editor Email في قاعدة البيانات.");', 'throw new Error(tgwsText("لم يتم تثبيت Google Editor Email في قاعدة البيانات.", "Google Editor Email was not persisted in the database."));'),
    ('setMessage(`تم حفظ الربط والتحقق منه من قاعدة البيانات${persisted.usesConnectedOwner ? " — الحساب يستخدم Google المالك" : ""}${rotated ? ` — تمت مزامنة ${rotated} صلاحية` : ""}.`);', 'setMessage(tgwsText(`تم حفظ الربط والتحقق منه من قاعدة البيانات${persisted.usesConnectedOwner ? " — الحساب يستخدم Google المالك" : ""}${rotated ? ` — تمت مزامنة ${rotated} صلاحية` : ""}.`, `Mapping saved and verified from the database${persisted.usesConnectedOwner ? " — using the connected Google owner" : ""}${rotated ? ` — ${rotated} permission${rotated === 1 ? "" : "s"} synchronized` : ""}.`));'),
    ('setError(`${getErrorMessage(err, "تعذر حفظ Google Editor Email.")} لم يتم اعتماد القيمة، وتمت إعادة الحقل إلى آخر قيمة محفوظة.`);', 'setError(tgwsText(`${getErrorMessage(err, "تعذر حفظ Google Editor Email.")} لم يتم اعتماد القيمة، وتمت إعادة الحقل إلى آخر قيمة محفوظة.`, `${getErrorMessage(err, "Unable to save Google Editor Email.")} The value was not accepted and the field was restored to the last saved value.`));'),
    ('setError("حساب Google المالك غير محدد. أعد ربط Google Drive أولًا.");', 'setError(tgwsText("حساب Google المالك غير محدد. أعد ربط Google Drive أولًا.", "The Google owner account is not set. Reconnect Google Drive first."));'),
    ('String(left.name || left.tosEmail).localeCompare(String(right.name || right.tosEmail), "ar")', 'String(left.name || left.tosEmail).localeCompare(String(right.name || right.tosEmail), tgwsLocale)'),

    ('<div><p className="tos-kicker">TGWS</p><h3 className="mt-1 text-2xl font-black">Tamiyouz Google Workspace</h3><p className="tos-muted mt-2">طبقة التحكم في Google Docs وSheets وSlides من داخل TOS.</p></div>', '<div><p className="tos-kicker">TGWS</p><h3 className="mt-1 text-2xl font-black">Tamiyouz Google Workspace</h3><p className="tos-muted mt-2">{tgwsText("طبقة التحكم في Google Docs وSheets وSlides من داخل TOS.", "Control Google Docs, Sheets, and Slides from inside TOS.")}</p></div>'),
    ('<div className="flex flex-wrap items-center gap-2"><Badge tone={drive?.storageReady ? "success" : "danger"}>{drive?.storageReady ? "Google جاهز" : "Google غير جاهز"}</Badge><Badge tone={runtime?.buildTag === EXPECTED_TGWS_BUILD ? "success" : "warning"}>{runtime?.buildTag || "Backend غير محدد"}</Badge><Badge tone={settings?.settingsSource === "DATABASE" ? "success" : "danger"}>{settings?.settingsSource === "DATABASE" ? "السجل محفوظ" : "السجل غير موجود"}</Badge></div>', '<div className="flex flex-wrap items-center gap-2"><Badge tone={drive?.storageReady ? "success" : "danger"}>{drive?.storageReady ? tgwsText("Google جاهز", "Google ready") : tgwsText("Google غير جاهز", "Google not ready")}</Badge><Badge tone={runtime?.buildTag === EXPECTED_TGWS_BUILD ? "success" : "warning"}>{runtime?.buildTag || tgwsText("Backend غير محدد", "Backend not identified")}</Badge><Badge tone={settings?.settingsSource === "DATABASE" ? "success" : "danger"}>{settings?.settingsSource === "DATABASE" ? tgwsText("السجل محفوظ", "Record saved") : tgwsText("السجل غير موجود", "Record missing")}</Badge></div>'),
    ('<StatCard value={loading ? "..." : drive?.connected ? "متصل" : "غير متصل"} label="حساب Google" note="OAuth" icon={ExternalLink} tone={drive?.connected ? "success" : "danger"} />', '<StatCard value={loading ? "..." : drive?.connected ? tgwsText("متصل", "Connected") : tgwsText("غير متصل", "Disconnected")} label={tgwsText("حساب Google", "Google account")} note="OAuth" icon={ExternalLink} tone={drive?.connected ? "success" : "danger"} />'),
    ('<StatCard value={settings?.enabled ? "مفعّل" : "متوقف"} label="TGWS" note="إنشاء الملفات" icon={ShieldCheck} tone={settings?.enabled ? "success" : "zinc"} />', '<StatCard value={settings?.enabled ? tgwsText("مفعّل", "Enabled") : tgwsText("متوقف", "Disabled")} label="TGWS" note={tgwsText("إنشاء الملفات", "File creation")} icon={ShieldCheck} tone={settings?.enabled ? "success" : "zinc"} />'),
    ('<StatCard value={String(settings?.allowedEditorDomains?.length || 0)} label="نطاقات Editor" note="Domain allowlist" icon={ShieldCheck} tone="gold" />', '<StatCard value={String(settings?.allowedEditorDomains?.length || 0)} label={tgwsText("نطاقات Editor", "Editor domains")} note="Domain allowlist" icon={ShieldCheck} tone="gold" />'),
    ('<StatCard value={settings?.externalViewerAllowed ? "Viewer" : "ممنوع"} label="الخارجية" note="لا يوجد External Editor" icon={ShieldCheck} tone="zinc" />', '<StatCard value={settings?.externalViewerAllowed ? "Viewer" : tgwsText("ممنوع", "Blocked")} label={tgwsText("الخارجية", "External access")} note={tgwsText("لا يوجد External Editor", "No external Editor")} icon={ShieldCheck} tone="zinc" />'),
    ('<StatCard value="إجباري" label="ربط المشروع" note="لا ملف مجهول" icon={ShieldCheck} tone="success" />', '<StatCard value={tgwsText("إجباري", "Required")} label={tgwsText("ربط المشروع", "Project mapping")} note={tgwsText("لا ملف مجهول", "No orphan files")} icon={ShieldCheck} tone="success" />'),
    ('<StatCard value="محظور" label="Untitled" note="Backend enforced" icon={ShieldCheck} tone="success" />', '<StatCard value={tgwsText("محظور", "Blocked")} label="Untitled" note="Backend enforced" icon={ShieldCheck} tone="success" />'),
    ('<StatCard value={settings?.secureVaultReady ? "جاهز" : "يُنشأ تلقائيًا"} label="Secure Vault" note="My Drive فقط" icon={ShieldCheck} tone={settings?.secureVaultReady ? "success" : "gold"} />', '<StatCard value={settings?.secureVaultReady ? tgwsText("جاهز", "Ready") : tgwsText("يُنشأ تلقائيًا", "Created automatically")} label="Secure Vault" note={tgwsText("My Drive فقط", "My Drive only")} icon={ShieldCheck} tone={settings?.secureVaultReady ? "success" : "gold"} />'),
    ('{!drive?.hasCredentials && <Notice type="warning" className="mt-4">أكمل Client ID وClient Secret وRedirect URI أولًا من قسم Google Drive الحالي، ثم ارجع إلى TGWS.</Notice>}', '{!drive?.hasCredentials && <Notice type="warning" className="mt-4">{tgwsText("أكمل Client ID وClient Secret وRedirect URI أولًا من قسم Google Drive الحالي، ثم ارجع إلى TGWS.", "Complete Client ID, Client Secret, and Redirect URI in Google Drive settings first, then return to TGWS.")}</Notice>}'),
    ('{drive?.hasCredentials && !drive?.connected && <Notice type="warning" className="mt-4">بيانات OAuth محفوظة لكن حساب Gmail غير مربوط.</Notice>}', '{drive?.hasCredentials && !drive?.connected && <Notice type="warning" className="mt-4">{tgwsText("بيانات OAuth محفوظة لكن حساب Gmail غير مربوط.", "OAuth credentials are saved, but the Gmail account is not connected.")}</Notice>}'),
    ('<div className="mt-5 flex flex-wrap gap-2"><Button type="button" onClick={connectGoogle} disabled={!drive?.hasCredentials || busy === "connect"}>{busy === "connect" ? "جاري الفتح..." : "ربط / إعادة ربط Gmail"}</Button><Button type="button" variant="soft" onClick={load} disabled={loading}><RefreshCw size={17} className={loading ? "animate-spin" : ""} />تحديث الحالة</Button></div>', '<div className="mt-5 flex flex-wrap gap-2"><Button type="button" onClick={connectGoogle} disabled={!drive?.hasCredentials || busy === "connect"}>{busy === "connect" ? tgwsText("جاري الفتح...", "Opening...") : tgwsText("ربط / إعادة ربط Gmail", "Connect / Reconnect Gmail")}</Button><Button type="button" variant="soft" onClick={load} disabled={loading}><RefreshCw size={17} className={loading ? "animate-spin" : ""} />{tgwsText("تحديث الحالة", "Refresh status")}</Button></div>'),

    ('<div><p className="tos-kicker">Google identity mapping</p><h3 className="mt-1 text-xl font-black">ربط مستخدم TOS ببريد Google</h3><p className="tos-muted mt-2">الربط الفعلي يكون: بريد دخول TOS ← Google Editor Email. هذه القائمة منفصلة عن قائمة السماح العامة.</p></div>', '<div><p className="tos-kicker">Google identity mapping</p><h3 className="mt-1 text-xl font-black">{tgwsText("ربط مستخدم TOS ببريد Google", "Map TOS users to Google email")}</h3><p className="tos-muted mt-2">{tgwsText("الربط الفعلي يكون: بريد دخول TOS ← Google Editor Email. هذه القائمة منفصلة عن قائمة السماح العامة.", "The actual mapping is TOS login email → Google Editor Email. This list is separate from the general allowlist.")}</p></div>'),
    ('<div className="flex flex-wrap items-center gap-2"><UserRound className="text-amber-600" /><Badge tone={identities.connectedOwnerEmail ? "success" : "warning"}>{identities.connectedOwnerEmail || "حساب Google غير محدد"}</Badge><Badge tone="gold">{identities.summary?.mapped || 0} ربط مخصص</Badge><Badge tone={identities.summary?.ownerMapped ? "success" : "zinc"}>{identities.summary?.ownerMapped || 0} يستخدم المالك</Badge></div>', '<div className="flex flex-wrap items-center gap-2"><UserRound className="text-amber-600" /><Badge tone={identities.connectedOwnerEmail ? "success" : "warning"}>{identities.connectedOwnerEmail || tgwsText("حساب Google غير محدد", "Google account not set")}</Badge><Badge tone="gold">{identities.summary?.mapped || 0} {tgwsText("ربط مخصص", "custom mappings")}</Badge><Badge tone={identities.summary?.ownerMapped ? "success" : "zinc"}>{identities.summary?.ownerMapped || 0} {tgwsText("يستخدم المالك", "use owner")}</Badge></div>'),
    ('<Notice type="warning" className="mt-4">لحسابك الحالي استخدم البريد المتصل <span dir="ltr" className="font-black">{identities.connectedOwnerEmail || "—"}</span>. عند مطابقته بحساب Google المالك، يتخطى TGWS إنشاء Permission إضافية.</Notice>', '<Notice type="warning" className="mt-4">{tgwsText("لحسابك الحالي استخدم البريد المتصل", "For your current account, use the connected email")} <span dir="ltr" className="font-black">{identities.connectedOwnerEmail || "—"}</span>. {tgwsText("عند مطابقته بحساب Google المالك، يتخطى TGWS إنشاء Permission إضافية.", "When it matches the Google owner account, TGWS skips creating an additional permission.")}</Notice>'),
    ('placeholder="بحث بالاسم أو بريد TOS أو بريد Google"', 'placeholder={tgwsText("بحث بالاسم أو بريد TOS أو بريد Google", "Search by name, TOS email, or Google email")}'),
    ('<span>مستخدم TOS</span><span>بريد TOS</span><span>Google Editor Email</span><span>الإجراء</span>', '<span>{tgwsText("مستخدم TOS", "TOS user")}</span><span>{tgwsText("بريد TOS", "TOS email")}</span><span>Google Editor Email</span><span>{tgwsText("الإجراء", "Action")}</span>'),
    ('{entry.id === user?.id && <Badge tone="gold">حسابك الحالي</Badge>}', '{entry.id === user?.id && <Badge tone="gold">{tgwsText("حسابك الحالي", "Your account")}</Badge>}'),
    ('<p className="mb-1 text-[11px] font-black text-zinc-400 xl:hidden">بريد TOS</p>', '<p className="mb-1 text-[11px] font-black text-zinc-400 xl:hidden">{tgwsText("بريد TOS", "TOS email")}</p>'),
    ('<span className="flex flex-wrap items-center gap-1 font-bold text-zinc-400">المحفوظ فعليًا: <span dir="ltr">{entry.googleEmail || entry.tosEmail}</span>{entry.usesConnectedOwner && <Badge tone="success">حساب Google المالك</Badge>}{entry.explicitGoogleEmail && !entry.usesConnectedOwner && <Badge tone="gold">ربط مخصص</Badge>}</span>', '<span className="flex flex-wrap items-center gap-1 font-bold text-zinc-400">{tgwsText("المحفوظ فعليًا:", "Actually saved:")} <span dir="ltr">{entry.googleEmail || entry.tosEmail}</span>{entry.usesConnectedOwner && <Badge tone="success">{tgwsText("حساب Google المالك", "Google owner account")}</Badge>}{entry.explicitGoogleEmail && !entry.usesConnectedOwner && <Badge tone="gold">{tgwsText("ربط مخصص", "Custom mapping")}</Badge>}</span>'),
    ('<div className="flex flex-wrap gap-2 xl:justify-end"><Button type="button" variant="soft" onClick={() => useConnectedOwner(entry.id)} disabled={!identities.connectedOwnerEmail || busy === `identity:${entry.id}`} title="حفظ حساب Google المتصل مباشرة في قاعدة البيانات"><Link2 size={16} />استخدام المتصل وحفظ</Button><Button type="button" onClick={() => saveGoogleIdentity(entry.id)} disabled={busy === `identity:${entry.id}`}><Save size={16} />{busy === `identity:${entry.id}` ? "جاري الحفظ..." : "حفظ"}</Button>{entry.explicitGoogleEmail && <Button type="button" variant="soft" onClick={() => clearGoogleIdentity(entry.id)} disabled={busy === `identity:${entry.id}`} title="العودة لاستخدام بريد TOS"><Unlink size={16} /></Button>}</div>', '<div className="flex flex-wrap gap-2 xl:justify-end"><Button type="button" variant="soft" onClick={() => useConnectedOwner(entry.id)} disabled={!identities.connectedOwnerEmail || busy === `identity:${entry.id}`} title={tgwsText("حفظ حساب Google المتصل مباشرة في قاعدة البيانات", "Save the connected Google account directly to the database")}><Link2 size={16} />{tgwsText("استخدام المتصل وحفظ", "Use connected & save")}</Button><Button type="button" onClick={() => saveGoogleIdentity(entry.id)} disabled={busy === `identity:${entry.id}`}><Save size={16} />{busy === `identity:${entry.id}` ? tgwsText("جاري الحفظ...", "Saving...") : tgwsText("حفظ", "Save")}</Button>{entry.explicitGoogleEmail && <Button type="button" variant="soft" onClick={() => clearGoogleIdentity(entry.id)} disabled={busy === `identity:${entry.id}`} title={tgwsText("العودة لاستخدام بريد TOS", "Return to using TOS email")}><Unlink size={16} /></Button>}</div>'),
    ('{!loading && !identityUsers.length && <Notice type="warning" className="mt-4">لا توجد نتائج مطابقة.</Notice>}', '{!loading && !identityUsers.length && <Notice type="warning" className="mt-4">{tgwsText("لا توجد نتائج مطابقة.", "No matching results.")}</Notice>}'),
    ('<Notice type="warning" className="mt-4">لا تشارك بيانات دخول Gmail بين الموظفين. الربط يمنح الملف للبريد المحدد فقط ولا يغيّر بريد تسجيل الدخول في TOS.</Notice>', '<Notice type="warning" className="mt-4">{tgwsText("لا تشارك بيانات دخول Gmail بين الموظفين. الربط يمنح الملف للبريد المحدد فقط ولا يغيّر بريد تسجيل الدخول في TOS.", "Do not share Gmail login credentials between employees. Mapping grants the file only to the selected email and does not change the TOS login email.")}</Notice>'),

    ('<div className="flex items-start justify-between gap-4"><div><h3 className="text-xl font-black">سياسة TGWS</h3><p className="tos-muted mt-2">القيود تطبق من Backend؛ لا تعتمد على الواجهة فقط.</p></div><ShieldCheck className="text-amber-600" /></div>', '<div className="flex items-start justify-between gap-4"><div><h3 className="text-xl font-black">{tgwsText("سياسة TGWS", "TGWS Policy")}</h3><p className="tos-muted mt-2">{tgwsText("القيود تطبق من Backend؛ لا تعتمد على الواجهة فقط.", "Restrictions are enforced by the backend; do not rely on the UI alone.")}</p></div><ShieldCheck className="text-amber-600" /></div>'),
    ('<span>تفعيل TGWS</span>', '<span>{tgwsText("تفعيل TGWS", "Enable TGWS")}</span>'),
    ('<span>السماح بمشاهد خارجي</span>', '<span>{tgwsText("السماح بمشاهد خارجي", "Allow external viewer")}</span>'),
    ('<span>نطاقات Editor المسموحة — سطر لكل نطاق</span>', '<span>{tgwsText("نطاقات Editor المسموحة — سطر لكل نطاق", "Allowed Editor domains — one per line")}</span>'),
    ('<span>إيميلات Editor إضافية — سطر لكل بريد</span>', '<span>{tgwsText("إيميلات Editor إضافية — سطر لكل بريد", "Additional Editor emails — one per line")}</span>'),
    ('<span>الظهور الافتراضي</span>', '<span>{tgwsText("الظهور الافتراضي", "Default visibility")}</span>'),
    ('<option value="PROJECT">أعضاء المشروع</option><option value="PRIVATE">خاص</option><option value="SPECIFIC_USERS">مستخدمون محددون</option>', '<option value="PROJECT">{tgwsText("أعضاء المشروع", "Project members")}</option><option value="PRIVATE">{tgwsText("خاص", "Private")}</option><option value="SPECIFIC_USERS">{tgwsText("مستخدمون محددون", "Specific users")}</option>'),
    ('<Notice type="warning" className="mt-4">Editor لا يمنح إلا لموظف TOS نشط. يمكن اعتماده بالقائمة العامة أو بربط Google Editor Email مخصص. أي بريد خارجي يكون Viewer فقط.</Notice>', '<Notice type="warning" className="mt-4">{tgwsText("Editor لا يمنح إلا لموظف TOS نشط. يمكن اعتماده بالقائمة العامة أو بربط Google Editor Email مخصص. أي بريد خارجي يكون Viewer فقط.", "Editor access is granted only to active TOS employees. It can be authorized through the general allowlist or a custom Google Editor Email mapping. Any external email is Viewer-only.")}</Notice>'),
    ('<Notice type="warning" className="mt-3">TGWS V1R1 ينشئ الملفات داخل مجلد خاص مستقل في My Drive. Shared Drive أو أي مجلد موروث الصلاحيات يتم رفضه تلقائيًا لحماية الملفات الخاصة والمحمية.</Notice>', '<Notice type="warning" className="mt-3">{tgwsText("TGWS V1R1 ينشئ الملفات داخل مجلد خاص مستقل في My Drive. Shared Drive أو أي مجلد موروث الصلاحيات يتم رفضه تلقائيًا لحماية الملفات الخاصة والمحمية.", "TGWS V1R1 creates files in an independent private folder in My Drive. Shared Drives or folders with inherited permissions are automatically rejected to protect private and protected files.")}</Notice>'),
    ('<Notice type="warning" className="mt-3">كلمة مرور TGWS طبقة حماية داخل TOS وليست كلمة مرور داخل Google. أي مستخدم لديه صلاحية Google مباشرة يستطيع استخدام رابط Google بعد حصوله عليه.</Notice>', '<Notice type="warning" className="mt-3">{tgwsText("كلمة مرور TGWS طبقة حماية داخل TOS وليست كلمة مرور داخل Google. أي مستخدم لديه صلاحية Google مباشرة يستطيع استخدام رابط Google بعد حصوله عليه.", "The TGWS password is a protection layer inside TOS, not a Google password. Any user with direct Google permission can use the Google link once they receive it.")}</Notice>'),
    ('<div className="mt-5 flex flex-wrap items-center gap-3"><Button type="button" onClick={save} disabled={busy === "save" || !drive?.storageReady}><Save size={17} />{busy === "save" ? "جاري الحفظ والتحقق..." : "حفظ سياسة TGWS"}</Button><span className="text-xs font-bold text-zinc-400">آخر حفظ فعلي: {formatSavedAt(settings?.savedAt || settings?.updatedAt)}</span></div>', '<div className="mt-5 flex flex-wrap items-center gap-3"><Button type="button" onClick={save} disabled={busy === "save" || !drive?.storageReady}><Save size={17} />{busy === "save" ? tgwsText("جاري الحفظ والتحقق...", "Saving & verifying...") : tgwsText("حفظ سياسة TGWS", "Save TGWS policy")}</Button><span className="text-xs font-bold text-zinc-400">{tgwsText("آخر حفظ فعلي:", "Last verified save:")} {formatSavedAt(settings?.savedAt || settings?.updatedAt, tgwsLocale)}</span></div>'),
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
        die("usage: generate_phase5_3_4_tgws.py REPO_ROOT OUTPUT_PATCH", 2)

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
    if run(["git", "diff", "--", TARGET], root).stdout.strip():
        die("target has tracked local changes", 8)

    raw = target.read_bytes()
    if b"\r\n" in raw:
        die("CRLF detected", 9)
    terminal_newline = raw.endswith(b"\n")
    text = raw.decode("utf-8")

    for idx, (old, new) in enumerate(REPLACEMENTS, start=1):
        count = text.count(old)
        print(f"REPLACEMENT_{idx}_MATCHES={count}")
        if count != 1:
            die(f"replacement {idx} expected exactly 1 match, found {count}", 20 + idx)
        text = text.replace(old, new, 1)

    tmp = Path(tempfile.mkdtemp(prefix="tos-phase5-3-4-tgws-"))
    try:
        run(["git", "init", "-q"], tmp)
        run(["git", "config", "user.email", "phase5-3-4@tos.local"], tmp)
        run(["git", "config", "user.name", "TOS Phase 5.3.4 Generator"], tmp)
        tmp_target = tmp / TARGET
        tmp_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(target, tmp_target)
        run(["git", "add", "--", TARGET], tmp)
        run(["git", "commit", "-qm", "exact phase 5.3.4 baseline"], tmp)

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
        print("GENERATION_MODE=TGWS_FULL_FILE_EXACT_BLOB_LOCALIZATION")
        print("PHASE5_3_4_TGWS_GENERATOR=PASS")
        print(f"OUTPUT={output}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
