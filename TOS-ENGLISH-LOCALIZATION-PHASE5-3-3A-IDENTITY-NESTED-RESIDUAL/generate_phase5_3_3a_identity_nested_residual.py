#!/usr/bin/env python3
import hashlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

EXPECTED_HEAD = "77dbd47013cf3706634e28b913719664560ffbc6"
TARGET = "frontend/src/pages/SettingsPage.jsx"
EXPECTED_BLOB = "ed02f3ebfcb3ea696cc444c7fd8a726de351c72d"

REPLACEMENTS = [
    ('function SafeColorField({ value, onChangeValue, className = "", compact = false, defaultValue = "", savedValue = "", onResetDefault, onResetSaved }) {\n  const safeValue = normalizeHexColorForIdentity(value, "#000000");', 'function SafeColorField({ value, onChangeValue, className = "", compact = false, defaultValue = "", savedValue = "", onResetDefault, onResetSaved }) {\n  const { lang } = usePreferences();\n  const colorFieldEn = lang === "en";\n  const colorShadeLabels = colorFieldEn ? ["Very light", "Light", "Soft", "Base", "Dark", "Very dark"] : COLOR_SHADE_LABELS;\n  const colorPresetLabels = colorFieldEn\n    ? ["Tamiyouz Gold", "Warm Gold", "Light Gold", "Ivory", "White", "Light Gray", "Soft Border", "Gray Text", "Primary Text", "Success", "Warning", "Danger", "Info"]\n    : SAFE_COLOR_PRESETS.map((preset) => preset.label);\n  const safeValue = normalizeHexColorForIdentity(value, "#000000");'),
    ('          aria-label="معاينة اللون الحالية"\n          title="معاينة اللون الحالي"', '          aria-label={colorFieldEn ? "Current color preview" : "معاينة اللون الحالية"}\n          title={colorFieldEn ? "Current color preview" : "معاينة اللون الحالي"}'),
    ('            aria-label="كود اللون HEX"', '            aria-label={colorFieldEn ? "HEX color code" : "كود اللون HEX"}'),
    ('          {!compact && <p className="text-[10px] font-bold text-zinc-400">يمكنك استخدام HEX أو اختيار درجة جاهزة بالأسفل.</p>}', '          {!compact && <p className="text-[10px] font-bold text-zinc-400">{colorFieldEn ? "Use a HEX value or choose a preset below." : "يمكنك استخدام HEX أو اختيار درجة جاهزة بالأسفل."}</p>}'),
    ('            <span className="text-[11px] font-black text-amber-800 dark:text-amber-200">درجات تلقائية من نفس اللون</span>\n            <button type="button" onClick={() => commitColor(palette[3], { immediate: true })} className="text-[10px] font-black text-amber-700 hover:text-amber-900">تثبيت الأساسي</button>', '            <span className="text-[11px] font-black text-amber-800 dark:text-amber-200">{colorFieldEn ? "Automatic shades from this color" : "درجات تلقائية من نفس اللون"}</span>\n            <button type="button" onClick={() => commitColor(palette[3], { immediate: true })} className="text-[10px] font-black text-amber-700 hover:text-amber-900">{colorFieldEn ? "Keep base" : "تثبيت الأساسي"}</button>'),
    ('                aria-label={`اختيار درجة ${COLOR_SHADE_LABELS[index] || preset}`}', '                aria-label={colorFieldEn ? `Choose ${colorShadeLabels[index] || preset} shade` : `اختيار درجة ${colorShadeLabels[index] || preset}`}'),
    ('                <span>{COLOR_SHADE_LABELS[index] || "درجة"}</span>', '                <span>{colorShadeLabels[index] || (colorFieldEn ? "Shade" : "درجة")}</span>'),
    ('        {SAFE_COLOR_PRESETS.slice(0, compact ? 6 : SAFE_COLOR_PRESETS.length).map((preset) => (', '        {SAFE_COLOR_PRESETS.slice(0, compact ? 6 : SAFE_COLOR_PRESETS.length).map((preset, index) => ('),
    ('            aria-label={`اختيار ${preset.label}`}', '            aria-label={colorFieldEn ? `Choose ${colorPresetLabels[index] || preset.label}` : `اختيار ${preset.label}`}'),
    ('            {!compact && <span>{preset.label}</span>}', '            {!compact && <span>{colorFieldEn ? (colorPresetLabels[index] || preset.label) : preset.label}</span>}'),
    ('          {canResetSaved && <button type="button" onClick={onResetSaved} className="rounded-xl bg-zinc-100 px-3 py-1 text-[10px] font-black text-zinc-600 hover:bg-zinc-200 dark:bg-white/10 dark:text-zinc-200">رجوع للقيمة المحفوظة</button>}\n          {canResetDefault && <button type="button" onClick={onResetDefault} className="rounded-xl bg-amber-100 px-3 py-1 text-[10px] font-black text-amber-800 hover:bg-amber-200 dark:bg-amber-400/10 dark:text-amber-200">استعادة الافتراضي لهذا اللون</button>}', '          {canResetSaved && <button type="button" onClick={onResetSaved} className="rounded-xl bg-zinc-100 px-3 py-1 text-[10px] font-black text-zinc-600 hover:bg-zinc-200 dark:bg-white/10 dark:text-zinc-200">{colorFieldEn ? "Restore saved value" : "رجوع للقيمة المحفوظة"}</button>}\n          {canResetDefault && <button type="button" onClick={onResetDefault} className="rounded-xl bg-amber-100 px-3 py-1 text-[10px] font-black text-amber-800 hover:bg-amber-200 dark:bg-amber-400/10 dark:text-amber-200">{colorFieldEn ? "Restore default color" : "استعادة الافتراضي لهذا اللون"}</button>}'),
    ('function NumberTokenField({ label, value, min = 0, max = 160, step = 1, unit = "px", onChangeValue, savedValue, defaultValue, note = "" }) {\n  const numericValue = Number.isFinite(Number(value)) ? Number(value) : min;', 'function NumberTokenField({ label, value, min = 0, max = 160, step = 1, unit = "px", onChangeValue, savedValue, defaultValue, note = "" }) {\n  const { lang } = usePreferences();\n  const numberTokenEn = lang === "en";\n  const numericValue = Number.isFinite(Number(value)) ? Number(value) : min;'),
    ('        {resetSaved && <button type="button" onClick={() => commit(savedValue)} className="ms-auto rounded-xl bg-white px-2 py-1 text-[10px] font-black text-zinc-500 hover:bg-zinc-100 dark:bg-zinc-950 dark:hover:bg-white/10">القيمة المحفوظة</button>}\n        {resetDefault && <button type="button" onClick={() => commit(defaultValue)} className="rounded-xl bg-amber-100 px-2 py-1 text-[10px] font-black text-amber-800 hover:bg-amber-200 dark:bg-amber-400/10 dark:text-amber-200">الافتراضي</button>}', '        {resetSaved && <button type="button" onClick={() => commit(savedValue)} className="ms-auto rounded-xl bg-white px-2 py-1 text-[10px] font-black text-zinc-500 hover:bg-zinc-100 dark:bg-zinc-950 dark:hover:bg-white/10">{numberTokenEn ? "Saved value" : "القيمة المحفوظة"}</button>}\n        {resetDefault && <button type="button" onClick={() => commit(defaultValue)} className="rounded-xl bg-amber-100 px-2 py-1 text-[10px] font-black text-amber-800 hover:bg-amber-200 dark:bg-amber-400/10 dark:text-amber-200">{numberTokenEn ? "Default" : "الافتراضي"}</button>}'),
    ('function SettingsIdentityAdmin({ user }) {\n  const { lang } = usePreferences();\n  const identityLang = lang === "en" ? "en" : "ar";\n  const identityCopy = getIdentityCopy(identityLang);', 'function SettingsIdentityAdmin({ user }) {\n  const { lang } = usePreferences();\n  const identityLang = lang === "en" ? "en" : "ar";\n  const identityCopy = getIdentityCopy(identityLang);\n  const identityText = (ar, en) => (identityLang === "en" ? en : ar);\n  const buttonStyleCopyEn = {\n    filled: { concept: "Concept 1", label: "Clear Classic", description: "A solid, clear button for fast primary actions.", previewLabel: "Primary button" },\n    outline: { concept: "Concept 2", label: "Balanced Modern", description: "A balance between a solid button and clean borders.", previewLabel: "Primary button" },\n    soft: { concept: "Concept 3", label: "Soft & Friendly", description: "Light, soft surfaces for calm interfaces.", previewLabel: "Primary button" },\n    minimal: { concept: "Concept 4", label: "Premium Minimal", description: "Comfortable spacing, thin borders, and a refined gold touch.", previewLabel: "Primary button" },\n  };\n  const localizedButtonStyleOptions = BRANDING_BUTTON_STYLE_OPTIONS.map((style) => identityLang === "en" ? { ...style, ...(buttonStyleCopyEn[style.key] || {}) } : style);\n  const shadowOptionCopyEn = {\n    none: { label: "No shadow", note: "Flat surface with no depth" },\n    soft: { label: "Soft", note: "Suitable for fields and simple cards" },\n    medium: { label: "Medium", note: "Suitable for dashboard cards" },\n    strong: { label: "Strong", note: "For important or elevated elements" },\n    premium: { label: "Premium Gold", note: "For hover or highlighted elements" },\n    focus: { label: "Focus ring", note: "Focus state for fields" },\n  };\n  const localizedShadowOptions = FRIENDLY_SHADOW_OPTIONS.map((option) => identityLang === "en" ? { ...option, ...(shadowOptionCopyEn[option.key] || {}) } : option);\n  const typographyLabelsEn = { pageTitle: "Page title", sectionTitle: "Section title", cardTitle: "Card title", description: "Description", label: "Labels / fields", button: "Button text" };'),
    ('const activeButtonStyleMeta = BRANDING_BUTTON_STYLE_OPTIONS.find((style) => style.key === normalizedForm.buttonStyle) || BRANDING_BUTTON_STYLE_OPTIONS[0];', 'const activeButtonStyleMeta = localizedButtonStyleOptions.find((style) => style.key === normalizedForm.buttonStyle) || localizedButtonStyleOptions[0];'),
    ('          <p className="text-sm font-black text-zinc-950 dark:text-white">{token.label}</p>', '          <p className="text-sm font-black text-zinc-950 dark:text-white">{identityLang === "en" ? (typographyLabelsEn[tokenKey] || token.label) : token.label}</p>'),
    ('        <label className="space-y-1"><span className="text-[11px] font-black text-zinc-500">الحجم</span><Field type="number" min="10" max="64" value={token.size} onChange={(event) => setTypographyField(tokenKey, "size", event.target.value)} /></label>\n        <label className="space-y-1"><span className="text-[11px] font-black text-zinc-500">الوزن</span><Field as="select" value={token.weight} onChange={(event) => setTypographyField(tokenKey, "weight", event.target.value)}>{BRANDING_WEIGHT_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}</Field></label>', '        <label className="space-y-1"><span className="text-[11px] font-black text-zinc-500">{identityText("الحجم", "Size")}</span><Field type="number" min="10" max="64" value={token.size} onChange={(event) => setTypographyField(tokenKey, "size", event.target.value)} /></label>\n        <label className="space-y-1"><span className="text-[11px] font-black text-zinc-500">{identityText("الوزن", "Weight")}</span><Field as="select" value={token.weight} onChange={(event) => setTypographyField(tokenKey, "weight", event.target.value)}>{BRANDING_WEIGHT_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}</Field></label>'),
    ('        <label className="space-y-1"><span className="text-[11px] font-black text-zinc-500">Shadow</span><Field as="select" value={token.shadow} onChange={(event) => setTypographyField(tokenKey, "shadow", event.target.value)}><option value="none">بدون ظل</option><option value="soft">ظل ناعم</option><option value="strong">ظل واضح</option></Field></label>\n        <label className="space-y-1"><span className="text-[11px] font-black text-zinc-500">اللون</span><SafeColorField value={token.color} onChangeValue={(value) => setTypographyField(tokenKey, "color", value)} /></label>', '        <label className="space-y-1"><span className="text-[11px] font-black text-zinc-500">Shadow</span><Field as="select" value={token.shadow} onChange={(event) => setTypographyField(tokenKey, "shadow", event.target.value)}><option value="none">{identityText("بدون ظل", "No shadow")}</option><option value="soft">{identityText("ظل ناعم", "Soft shadow")}</option><option value="strong">{identityText("ظل واضح", "Strong shadow")}</option></Field></label>\n        <label className="space-y-1"><span className="text-[11px] font-black text-zinc-500">{identityText("اللون", "Color")}</span><SafeColorField value={token.color} onChangeValue={(value) => setTypographyField(tokenKey, "color", value)} /></label>'),
    ('{renderColorToken("primary", "اللون الأساسي", normalizedForm.primaryColor, (value) => setField("primaryColor", value), "يستخدم في الأزرار والعناصر الرئيسية", { defaultValue: BRANDING_DEFAULTS.primaryColor, savedValue: normalizedCommittedForm.primaryColor })}', '{renderColorToken("primary", identityText("اللون الأساسي", "Primary color"), normalizedForm.primaryColor, (value) => setField("primaryColor", value), identityText("يستخدم في الأزرار والعناصر الرئيسية", "Used for buttons and primary interface elements"), { defaultValue: BRANDING_DEFAULTS.primaryColor, savedValue: normalizedCommittedForm.primaryColor })}'),
    ('{renderColorToken("secondary", "اللون الثانوي", normalizedForm.secondaryColor, (value) => setField("secondaryColor", value), "للنصوص والعناصر الثانوية", { defaultValue: BRANDING_DEFAULTS.secondaryColor, savedValue: normalizedCommittedForm.secondaryColor })}', '{renderColorToken("secondary", identityText("اللون الثانوي", "Secondary color"), normalizedForm.secondaryColor, (value) => setField("secondaryColor", value), identityText("للنصوص والعناصر الثانوية", "Used for secondary text and elements"), { defaultValue: BRANDING_DEFAULTS.secondaryColor, savedValue: normalizedCommittedForm.secondaryColor })}'),
    ('{renderColorToken("text", "لون النص العام", normalizedForm.textColor, (value) => setField("textColor", value), "يؤثر على النصوص العامة القديمة في النظام", { defaultValue: BRANDING_DEFAULTS.textColor, savedValue: normalizedCommittedForm.textColor })}', '{renderColorToken("text", identityText("لون النص العام", "Global text color"), normalizedForm.textColor, (value) => setField("textColor", value), identityText("يؤثر على النصوص العامة القديمة في النظام", "Affects legacy global text across the system"), { defaultValue: BRANDING_DEFAULTS.textColor, savedValue: normalizedCommittedForm.textColor })}'),
    ('<div><h4 className="text-base font-black text-zinc-950 dark:text-white">لوحة ألوان الواجهة</h4><p className="mt-1 text-xs font-bold text-zinc-500">خلفيات، أسطح، نصوص، حالات، وحدود — كلها بأسماء واضحة للمدير وليست أسماء تقنية.</p></div>', '<div><h4 className="text-base font-black text-zinc-950 dark:text-white">{identityText("لوحة ألوان الواجهة", "Interface color palette")}</h4><p className="mt-1 text-xs font-bold text-zinc-500">{identityText("خلفيات، أسطح، نصوص، حالات، وحدود — كلها بأسماء واضحة للمدير وليست أسماء تقنية.", "Backgrounds, surfaces, text, states, and borders — all presented with clear admin-friendly names.")}</p></div>'),
    ('<div className="rounded-[28px] border border-zinc-100 bg-white p-4 shadow-sm dark:border-white/10 dark:bg-zinc-950/40"><h4 className="text-base font-black text-zinc-950 dark:text-white">المسافات والتباعد</h4><p className="mt-1 text-xs font-bold text-zinc-500">تحكم في المسافات بدون كتابة أكواد.</p>', '<div className="rounded-[28px] border border-zinc-100 bg-white p-4 shadow-sm dark:border-white/10 dark:bg-zinc-950/40"><h4 className="text-base font-black text-zinc-950 dark:text-white">{identityText("المسافات والتباعد", "Spacing")}</h4><p className="mt-1 text-xs font-bold text-zinc-500">{identityText("تحكم في المسافات بدون كتابة أكواد.", "Control spacing without writing code.")}</p>'),
    ('<div className="rounded-[28px] border border-zinc-100 bg-white p-4 shadow-sm dark:border-white/10 dark:bg-zinc-950/40"><h4 className="text-base font-black text-zinc-950 dark:text-white">الاستدارة Radius</h4><p className="mt-1 text-xs font-bold text-zinc-500">استدارة الكروت، الأزرار، الحقول، والنوافذ.</p>', '<div className="rounded-[28px] border border-zinc-100 bg-white p-4 shadow-sm dark:border-white/10 dark:bg-zinc-950/40"><h4 className="text-base font-black text-zinc-950 dark:text-white">{identityText("الاستدارة Radius", "Radius")}</h4><p className="mt-1 text-xs font-bold text-zinc-500">{identityText("استدارة الكروت، الأزرار، الحقول، والنوافذ.", "Corner radius for cards, buttons, fields, and dialogs.")}</p>'),
    ('              <div className="rounded-[28px] border border-zinc-100 bg-white p-4 shadow-sm dark:border-white/10 dark:bg-zinc-950/40"><h4 className="text-base font-black text-zinc-950 dark:text-white">الظلال Shadows</h4><p className="mt-1 text-xs font-bold text-zinc-500">اختيار جاهز بدل كتابة CSS. القيم المتقدمة ما زالت محفوظة لو كانت موجودة.</p><div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">{Object.entries(shadows).map(([key, value]) => { const currentKey = resolveFriendlyShadowKey(value); const label = key === "sm" ? "ظل خفيف" : key === "md" ? "ظل الكروت — متوسط" : key === "lg" ? "ظل قوي" : key === "hover" ? "ظل عند المرور" : key === "focus" ? "ظل التركيز" : "بدون ظل"; return <div key={key} className="rounded-3xl border border-zinc-100 bg-zinc-50 p-3 dark:border-white/10 dark:bg-white/[0.03]"><div><p className="text-sm font-black text-zinc-950 dark:text-white">{label}</p><p className="text-[11px] font-bold text-zinc-500">{currentKey === "custom" ? "قيمة مخصصة" : currentKey}</p></div><Field as="select" className="mt-3" value={currentKey} onChange={(event) => { const option = FRIENDLY_SHADOW_OPTIONS.find((item) => item.key === event.currentTarget.value); if (option) setDesignTokenField("shadows", key, option.value); }}>{currentKey === "custom" && <option value="custom">قيمة مخصصة محفوظة</option>}{FRIENDLY_SHADOW_OPTIONS.map((option) => <option key={option.key} value={option.key}>{option.label}</option>)}</Field></div>; })}</div></div>', '              <div className="rounded-[28px] border border-zinc-100 bg-white p-4 shadow-sm dark:border-white/10 dark:bg-zinc-950/40"><h4 className="text-base font-black text-zinc-950 dark:text-white">{identityText("الظلال Shadows", "Shadows")}</h4><p className="mt-1 text-xs font-bold text-zinc-500">{identityText("اختيار جاهز بدل كتابة CSS. القيم المتقدمة ما زالت محفوظة لو كانت موجودة.", "Choose a preset instead of writing CSS. Existing advanced values remain preserved.")}</p><div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">{Object.entries(shadows).map(([key, value]) => { const currentKey = resolveFriendlyShadowKey(value); const label = key === "sm" ? identityText("ظل خفيف", "Soft shadow") : key === "md" ? identityText("ظل الكروت — متوسط", "Card shadow — Medium") : key === "lg" ? identityText("ظل قوي", "Strong shadow") : key === "hover" ? identityText("ظل عند المرور", "Hover shadow") : key === "focus" ? identityText("ظل التركيز", "Focus shadow") : identityText("بدون ظل", "No shadow"); const currentOption = localizedShadowOptions.find((option) => option.key === currentKey); return <div key={key} className="rounded-3xl border border-zinc-100 bg-zinc-50 p-3 dark:border-white/10 dark:bg-white/[0.03]"><div><p className="text-sm font-black text-zinc-950 dark:text-white">{label}</p><p className="text-[11px] font-bold text-zinc-500">{currentKey === "custom" ? identityText("قيمة مخصصة", "Custom value") : (currentOption?.label || currentKey)}</p></div><Field as="select" className="mt-3" value={currentKey} onChange={(event) => { const option = FRIENDLY_SHADOW_OPTIONS.find((item) => item.key === event.currentTarget.value); if (option) setDesignTokenField("shadows", key, option.value); }}>{currentKey === "custom" && <option value="custom">{identityText("قيمة مخصصة محفوظة", "Saved custom value")}</option>}{localizedShadowOptions.map((option) => <option key={option.key} value={option.key}>{option.label}</option>)}</Field></div>; })}</div></div>'),
    ('<h4 className="text-base font-black text-zinc-950 dark:text-white">الخطوط حسب اللغة</h4>', '<h4 className="text-base font-black text-zinc-950 dark:text-white">{identityText("الخطوط حسب اللغة", "Fonts by language")}</h4>'),
    ('<label className="space-y-2"><span className="text-xs font-black text-zinc-500">الخط العربي</span>', '<label className="space-y-2"><span className="text-xs font-black text-zinc-500">{identityText("الخط العربي", "Arabic font")}</span>'),
    ('<label className="space-y-2"><span className="text-xs font-black text-zinc-500">الخط الإنجليزي</span>', '<label className="space-y-2"><span className="text-xs font-black text-zinc-500">{identityText("الخط الإنجليزي", "English font")}</span>'),
    ('<h4 className="text-base font-black text-zinc-950 dark:text-white">مفاهيم تصميم الأزرار</h4>', '<h4 className="text-base font-black text-zinc-950 dark:text-white">{identityText("مفاهيم تصميم الأزرار", "Button design concepts")}</h4>'),
    ('<p className="text-xs font-bold text-zinc-500 dark:text-zinc-400">اختر مفهوم الزر أولًا، ثم عدّل خصائصه من الإعدادات أسفل الاختيار. المعاينة الكاملة تظهر فقط في اللوحة الجانبية.</p>', '<p className="text-xs font-bold text-zinc-500 dark:text-zinc-400">{identityText("اختر مفهوم الزر أولًا، ثم عدّل خصائصه من الإعدادات أسفل الاختيار. المعاينة الكاملة تظهر فقط في اللوحة الجانبية.", "Choose a button concept first, then adjust its properties below. The full preview appears in the side panel.")}</p>'),
    ('{BRANDING_BUTTON_STYLE_OPTIONS.map((style) => {', '{localizedButtonStyleOptions.map((style) => {'),
    ('<NumberTokenField label="استدارة الزر" note="نصف قطر حواف الزر"', '<NumberTokenField label={identityText("استدارة الزر", "Button radius")} note={identityText("نصف قطر حواف الزر", "Button corner radius")}'),
    ('<NumberTokenField label="ارتفاع الزر" note="الارتفاع الافتراضي للأزرار"', '<NumberTokenField label={identityText("ارتفاع الزر", "Button height")} note={identityText("الارتفاع الافتراضي للأزرار", "Default button height")}'),
    ('<NumberTokenField label="الحشو الأفقي" note="المساحة يمين ويسار النص"', '<NumberTokenField label={identityText("الحشو الأفقي", "Horizontal padding")} note={identityText("المساحة يمين ويسار النص", "Space to the left and right of text")}'),
    ('<NumberTokenField label="الحشو الرأسي" note="المساحة أعلى وأسفل النص"', '<NumberTokenField label={identityText("الحشو الرأسي", "Vertical padding")} note={identityText("المساحة أعلى وأسفل النص", "Space above and below text")}'),
    ('<NumberTokenField label="عرض الحد" note="سمك إطار الزر"', '<NumberTokenField label={identityText("عرض الحد", "Border width")} note={identityText("سمك إطار الزر", "Button border thickness")}'),
    ('<NumberTokenField label="المسافة مع الأيقونة" note="المسافة بين الأيقونة والنص"', '<NumberTokenField label={identityText("المسافة مع الأيقونة", "Icon gap")} note={identityText("المسافة بين الأيقونة والنص", "Space between icon and text")}'),
    ('<h4 className="text-base font-black text-zinc-950 dark:text-white">حالات الأزرار</h4>', '<h4 className="text-base font-black text-zinc-950 dark:text-white">{identityText("حالات الأزرار", "Button states")}</h4>'),
    ('<h4 className="text-base font-black text-zinc-950 dark:text-white">الحجوم والشكل</h4>', '<h4 className="text-base font-black text-zinc-950 dark:text-white">{identityText("الحجوم والشكل", "Sizing & shape")}</h4>'),
    ('<h4 className="text-base font-black text-zinc-950 dark:text-white">حالات حقول الإدخال</h4>', '<h4 className="text-base font-black text-zinc-950 dark:text-white">{identityText("حالات حقول الإدخال", "Input field states")}</h4>'),
    ('              <div className="rounded-[28px] border border-zinc-100 bg-white p-4 shadow-sm dark:border-white/10 dark:bg-zinc-950/40"><h4 className="text-base font-black text-zinc-950 dark:text-white">الكروت والقوائم والرفع</h4><div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">{[["cardBg", "خلفية الكارت"], ["cardBorder", "حد الكارت"], ["menuBg", "خلفية القائمة"], ["menuBorder", "حد القائمة"], ["menuHoverBg", "خلفية القائمة عند المرور"], ["uploadBg", "خلفية الرفع"], ["uploadBorder", "حد الرفع"], ["progressBg", "خلفية مؤشر التقدم"]].map(([fieldKey, label]) => renderColorToken(fieldKey, label, surfaces[fieldKey], (value) => setSurfaceColor(fieldKey, value)))}</div></div>', '              <div className="rounded-[28px] border border-zinc-100 bg-white p-4 shadow-sm dark:border-white/10 dark:bg-zinc-950/40"><h4 className="text-base font-black text-zinc-950 dark:text-white">{identityText("الكروت والقوائم والرفع", "Cards, menus & uploads")}</h4><div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">{[["cardBg", identityText("خلفية الكارت", "Card background")], ["cardBorder", identityText("حد الكارت", "Card border")], ["menuBg", identityText("خلفية القائمة", "Menu background")], ["menuBorder", identityText("حد القائمة", "Menu border")], ["menuHoverBg", identityText("خلفية القائمة عند المرور", "Menu hover background")], ["uploadBg", identityText("خلفية الرفع", "Upload background")], ["uploadBorder", identityText("حد الرفع", "Upload border")], ["progressBg", identityText("خلفية مؤشر التقدم", "Progress background")]].map(([fieldKey, label]) => renderColorToken(fieldKey, label, surfaces[fieldKey], (value) => setSurfaceColor(fieldKey, value)))}</div></div>'),
    ('              <div className="rounded-[28px] border border-zinc-100 bg-white p-4 shadow-sm dark:border-white/10 dark:bg-zinc-950/40"><h4 className="text-base font-black text-zinc-950 dark:text-white">حالات الشارات</h4><div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">{DESIGN_BADGE_STATE_OPTIONS.map((state) => { const values = badgeStates[state.key] || DESIGN_SYSTEM_DEFAULTS.badgeStates[state.key]; return <div key={state.key} className="rounded-3xl border border-zinc-100 bg-zinc-50 p-3 dark:border-white/10 dark:bg-white/[0.03]"><p className="text-sm font-black text-zinc-950 dark:text-white">{state.label}</p><div className="mt-3 grid grid-cols-3 gap-2">{[["bg", identityCopy.colorParts.bg], ["text", identityCopy.colorParts.text], ["border", identityCopy.colorParts.border]].map(([fieldKey, label]) => <label key={fieldKey} className="text-[10px] font-black text-zinc-500">{label}<SafeColorField compact className="mt-1" value={values[fieldKey]} onChangeValue={(value) => setDesignStateColor("badgeStates", state.key, fieldKey, value)} /></label>)}</div></div>; })}</div></div>', '              <div className="rounded-[28px] border border-zinc-100 bg-white p-4 shadow-sm dark:border-white/10 dark:bg-zinc-950/40"><h4 className="text-base font-black text-zinc-950 dark:text-white">{identityText("حالات الشارات", "Badge states")}</h4><div className="mt-4 grid gap-3 md:grid-cols-2 xl:grid-cols-3">{DESIGN_BADGE_STATE_OPTIONS.map((state) => { const values = badgeStates[state.key] || DESIGN_SYSTEM_DEFAULTS.badgeStates[state.key]; return <div key={state.key} className="rounded-3xl border border-zinc-100 bg-zinc-50 p-3 dark:border-white/10 dark:bg-white/[0.03]"><p className="text-sm font-black text-zinc-950 dark:text-white">{state.label}</p><div className="mt-3 grid grid-cols-3 gap-2">{[["bg", identityCopy.colorParts.bg], ["text", identityCopy.colorParts.text], ["border", identityCopy.colorParts.border]].map(([fieldKey, label]) => <label key={fieldKey} className="text-[10px] font-black text-zinc-500">{label}<SafeColorField compact className="mt-1" value={values[fieldKey]} onChangeValue={(value) => setDesignStateColor("badgeStates", state.key, fieldKey, value)} /></label>)}</div></div>; })}</div></div>'),
    ('setError(getErrorMessage(err, "تعذر تحميل إعدادات الهوية."));', 'setError(getErrorMessage(err, identityText("تعذر تحميل إعدادات الهوية.", "Unable to load identity settings.")));'),
    ('setMessage("تم إلغاء التغييرات والرجوع لآخر نسخة محفوظة.");', 'setMessage(identityText("تم إلغاء التغييرات والرجوع لآخر نسخة محفوظة.", "Changes canceled and the last saved version restored."));'),
    ('setMessage("تم استعادة القيم الافتراضية كمسودة فقط. اضغط حفظ لتطبيقها.");', 'setMessage(identityText("تم استعادة القيم الافتراضية كمسودة فقط. اضغط حفظ لتطبيقها.", "Default values restored to the draft only. Save to apply them."));'),
    ('setMessage("هذا التبويب خاص ببيانات الهوية الأساسية؛ استخدم استعادة الكل لو أردت إعادة كل القيم الافتراضية.");', 'setMessage(identityText("هذا التبويب خاص ببيانات الهوية الأساسية؛ استخدم استعادة الكل لو أردت إعادة كل القيم الافتراضية.", "This tab contains core identity data; use Restore all to reset every value."));'),
    ('setMessage("تم استعادة قيم التبويب الحالي كمسودة فقط. اضغط حفظ لتطبيقها.");', 'setMessage(identityText("تم استعادة قيم التبويب الحالي كمسودة فقط. اضغط حفظ لتطبيقها.", "Current tab values restored to the draft only. Save to apply them."));'),
    ('setMessage("تم تجهيز ملف تصدير نظام التصميم من المسودة الحالية.");', 'setMessage(identityText("تم تجهيز ملف تصدير نظام التصميم من المسودة الحالية.", "Design-system export prepared from the current draft."));'),
    ('setError(getErrorMessage(err, "تعذر تصدير نظام التصميم."));', 'setError(getErrorMessage(err, identityText("تعذر تصدير نظام التصميم.", "Unable to export the design system.")));'),
    ('setMessage("تم استيراد نظام التصميم كمسودة فقط. راجع المعاينة ثم اضغط حفظ.");', 'setMessage(identityText("تم استيراد نظام التصميم كمسودة فقط. راجع المعاينة ثم اضغط حفظ.", "Design system imported as a draft only. Review the preview, then save."));'),
    ('setError(getErrorMessage(err, "ملف الاستيراد غير صالح أو لا يحتوي إعدادات نظام التصميم."));', 'setError(getErrorMessage(err, identityText("ملف الاستيراد غير صالح أو لا يحتوي إعدادات نظام التصميم.", "The import file is invalid or does not contain design-system settings.")));'),
    ('async function saveBranding(successMessage = "تم حفظ إعدادات الواجهة والهوية.", overrideForm = null) {', 'async function saveBranding(successMessage = identityText("تم حفظ إعدادات الواجهة والهوية.", "Interface and identity settings saved."), overrideForm = null) {'),
    ('const message = getErrorMessage(err, "تعذر حفظ إعدادات الهوية فقط. راجع القيم ثم أعد المحاولة.");', 'const message = getErrorMessage(err, identityText("تعذر حفظ إعدادات الهوية فقط. راجع القيم ثم أعد المحاولة.", "Unable to save identity settings. Review the values and try again."));'),
    ('setError("ارفع صورة شعار أو أيقونة بصيغة PNG أو JPG أو WEBP أو GIF.");', 'setError(identityText("ارفع صورة شعار أو أيقونة بصيغة PNG أو JPG أو WEBP أو GIF.", "Upload a logo or icon as PNG, JPG, WEBP, or GIF."));'),
    ('if (!imageUrl) throw new Error("لم يرجع السيرفر رابط صالح للصورة.");', 'if (!imageUrl) throw new Error(identityText("لم يرجع السيرفر رابط صالح للصورة.", "The server did not return a valid image URL."));'),
    ('setMessage(kind === "logo" ? "تم رفع الشعار كمسودة. اضغط حفظ التغييرات لتطبيقه على النظام." : "تم رفع الأيقونة كمسودة. اضغط حفظ التغييرات لتطبيقها على النظام.");', 'setMessage(kind === "logo" ? identityText("تم رفع الشعار كمسودة. اضغط حفظ التغييرات لتطبيقه على النظام.", "Logo uploaded to the draft. Save changes to apply it to the system.") : identityText("تم رفع الأيقونة كمسودة. اضغط حفظ التغييرات لتطبيقها على النظام.", "Icon uploaded to the draft. Save changes to apply it to the system."));'),
    ('setError(getErrorMessage(err, "تعذر رفع ملف الهوية."));', 'setError(getErrorMessage(err, identityText("تعذر رفع ملف الهوية.", "Unable to upload the identity asset.")));'),
    ('<p className="text-[10px] font-black" style={{ color: designColors.textMuted }}>{token.label}</p><p className="mt-2 break-words" style={identityTypographyStyle(token)}>نص معاينة مباشر</p>', '<p className="text-[10px] font-black" style={{ color: designColors.textMuted }}>{identityLang === "en" ? (typographyLabelsEn[tokenKey] || token.label) : token.label}</p><p className="mt-2 break-words" style={identityTypographyStyle(token)}>{identityText("نص معاينة مباشر", "Live preview text")}</p>'),
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
        die("usage: generate_phase5_3_3a_identity_nested_residual.py REPO_ROOT OUTPUT_PATCH", 2)

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

    tmp = Path(tempfile.mkdtemp(prefix="tos-phase5-3-3a-"))
    try:
        run(["git", "init", "-q"], tmp)
        run(["git", "config", "user.email", "phase5-3-3a@tos.local"], tmp)
        run(["git", "config", "user.name", "TOS Phase 5.3.3A Generator"], tmp)
        tmp_target = tmp / TARGET
        tmp_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(target, tmp_target)
        run(["git", "add", "--", TARGET], tmp)
        run(["git", "commit", "-qm", "exact phase 5.3.3a baseline"], tmp)

        encoded = text.encode("utf-8")
        if terminal_newline and not encoded.endswith(b"\n"):
            encoded += b"\n"
        elif not terminal_newline and encoded.endswith(b"\n"):
            encoded = encoded[:-1]
        tmp_target.write_bytes(encoded)

        diff = subprocess.run(
            ["git", "diff", "--binary", "--full-index", "--", TARGET],
            cwd=tmp, text=True, capture_output=True
        )
        if diff.returncode or not diff.stdout.strip():
            die("failed to generate patch", 90)

        output.write_text(diff.stdout, encoding="utf-8", newline="\n")
        print(f"GENERATED_PATCH_SHA256={hashlib.sha256(output.read_bytes()).hexdigest()}")

        numstat = run(["git", "apply", "--numstat", str(output)], root).stdout.strip().splitlines()
        paths = {row.split("\t")[-1] for row in numstat if row.strip()}
        if paths != {TARGET}:
            die(f"unexpected patch paths: {sorted(paths)}", 91)

        print("PARSER=PASS")
        run(["git", "apply", "--check", str(output)], root)
        print("APPLY_CHECK=PASS")
        print("GENERATION_MODE=FULL_FILE_EXACT_BLOB_IDENTITY_RESIDUAL")
        print("PHASE5_3_3A_IDENTITY_NESTED_RESIDUAL_GENERATOR=PASS")
        print(f"OUTPUT={output}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
