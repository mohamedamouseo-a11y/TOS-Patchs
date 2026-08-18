# TOS — Ramzy Gemini Primary / Agnes Fallback V1

## الهدف
تعديل مزود الذكاء الاصطناعي الخاص بـ Ramzy فقط بحيث يكون:

1. **Gemini** هو المزود الأساسي.
2. **Agnes** هو المزود الاحتياطي التلقائي عند فشل Gemini وفق قواعد الـ fallback أدناه.

هذا الباتش لا يحتوي على أي API keys ولا يعدّل قاعدة البيانات ولا يغيّر صلاحيات Ramzy أو أدواته أو مسار الموافقات.

## ملاحظة مهمة عن Base Source
تمت مراجعة الفرع `main` في المستودع:

`mohamedamouseo-a11y/TOS`

لكن نسخة GitHub الحالية لا تحتوي على بصمات نسخة Ramzy الموجودة على النظام الحي مثل:

- `Mastra Agency Operator`
- `AGENT_SETTINGS_ENCRYPTION_KEY`
- `gpt-4.1-mini`
- `OpenAI API key is not configured`

لذلك الباتش **Guarded / Fail-Closed**: لا يقوم بتخمين ملفات أو استبدالات على Source غير مطابق. يجب تشغيل `apply.mjs` أولاً على `/var/www/TOS`. إذا لم يجد بصمات Ramzy المطلوبة فسيعيد `PATCH_BASE_MISMATCH` بدون تعديل أي ملف.

## Environment Variables
يجب أن تبقى الأسرار Server-side فقط:

```env
GEMINI_API_KEY=...
AGNES_API_KEY=...
```

إذا كانت نسخة Ramzy الحالية تستخدم تشفير إعدادات المزود عبر `AGENT_SETTINGS_ENCRYPTION_KEY` فيجب الحفاظ على نفس الآلية وعدم تجاوزها.

## Provider Order

- Primary: `gemini`
- Fallback: `agnes`
- Agnes base URL: `https://apihub.agnes-ai.com/v1`
- Agnes chat endpoint: `/chat/completions`
- Agnes model default for this patch: `agnes-2.0-flash`

> ملاحظة: الـ base URL يحتوي `/v1` بالفعل، لذلك المسار الكامل يصبح `/v1/chat/completions`.

## Fallback Rules
يُسمح بالتحويل من Gemini إلى Agnes فقط **قبل بدء أي side effects أو tool/action execution** في الطلب الحالي.

Fallback عند:

- عدم وجود Gemini configuration/key.
- HTTP `429` من Gemini.
- HTTP `5xx` من Gemini.
- network error / timeout / provider unavailable.

عند `401/403` من Gemini:

- يجب تسجيل خطأ المصادقة بوضوح في audit log.
- يجوز استخدام Agnes لإبقاء Ramzy متاحاً فقط إذا لم تبدأ أي side effects بعد، مع الاحتفاظ بسجل سبب الـ fallback.

ممنوع إعادة تنفيذ request على Agnes بعد بدء tool/action side effects لتجنب duplicate actions.

## ما يجب الحفاظ عليه 1:1

- Ramzy permissions.
- workspace access.
- role access.
- read-only / proposals mode.
- approval workflow.
- memory behavior.
- daily limits.
- tool-call limits.
- existing tools / function calling.
- audit logging.

## طريقة التطبيق

1. انسخ/clone هذا المجلد فقط إلى بيئة التطبيق.
2. شغّل:

```bash
node apply.mjs /var/www/TOS
```

3. إذا ظهر `PATCH_BASE_MISMATCH` توقف ولا تعدّل شيئاً.
4. إذا ظهر `PATCH_BASE_MATCH` استخدم الملفات التي يعرضها التقرير كـ scope وحيد للتعديل، وطبّق العقد الموجود في `RAMZY_PROVIDER_SPEC.md`.
5. نفّذ build/check الموجود فعلياً في نسخة الإنتاج، ثم restart لنفس Process الخاص بـ TOS فقط.

راجع `REPLIT_APPLY_PROMPT.txt` للتطبيق بأقل تغييرات ممكنة.
