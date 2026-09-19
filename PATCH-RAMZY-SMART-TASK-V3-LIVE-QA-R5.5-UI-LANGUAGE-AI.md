# Ramzy Smart Task V3 — Live QA R5.5: Enforce UI Language for AI Title + Description

Baseline TOS:
`85ddc87f691637ffd95a5ae4c269e15dad5eb59a`

Scope ONLY:
Make Smart Task AI writing obey the current TOS UI language for BOTH:
- Write/Improve Title
- Write/Improve Description

Current frontend is already correct:
`language: isEnglish ? "en" : "ar"`

Current backend routes are already correct:
`const language = req.body?.language === "ar" ? "ar" : "en";`

The weakness is prompt/output enforcement: the model may follow the input text language instead of the requested UI language.

## Required behavior

Source of truth = TOS UI language sent in `language`.

- If `language === "ar"`:
  - final AI title MUST be Arabic
  - final AI description MUST be Arabic
- If `language === "en"`:
  - final AI title MUST be English
  - final AI description MUST be English

Do NOT infer response language from the user's typed title/description.

Examples:
- Arabic UI + English rough input => return Arabic suggestion.
- English UI + Arabic rough input => return English suggestion.

Allowed exception:
- preserve unavoidable brand names, product names, URLs, acronyms, technical identifiers, or proper nouns in their original form when translating them would be wrong.
- Do not produce mixed-language prose otherwise.

## Prompt hardening

Update BOTH `taskTitlePrompt()` and `taskDescriptionPrompt()` in:
`backend/src/agency-operator/services/ramzySmartTask.service.js`

Make the instruction explicit and high-priority.

For Arabic:
- "The required output language is Arabic because the user's TOS UI is Arabic."
- "Write all normal prose in Arabic even if the source text is English."
- "Do not answer in English except unavoidable brand names, URLs, acronyms, technical identifiers, or proper nouns."
- "Return only the requested title/description."

For English:
- same inverse rule.
- "Write all normal prose in English even if the source text is Arabic."
- Arabic may remain only where it is an unavoidable proper name/brand.

## Robustness

Add a small language guard in the Smart Task AI service after generation.

The guard must detect ONLY clearly wrong-language prose; do not reject normal mixed technical terms.

If output is clearly in the wrong language:
- retry ONCE using the same configured Ramzy provider/model
- retry instruction must explicitly say to rewrite the generated result in the requested UI language
- preserve meaning and allowed brand/proper/technical names
- no additional provider/key/fallback
- maximum one retry; no loop

If the second result still clearly violates the requested language:
- return the safer second result only if it has meaningful requested-language content
- otherwise fail with a controlled AI-generation error rather than silently returning fully wrong-language prose

Keep existing title/description length limits.

## Do NOT touch

- frontend language source (`isEnglish`) except tests if needed
- project picker
- assignees
- feature tip
- approval/task creation
- permissions
- provider/model/API key configuration
- unrelated Ramzy prompts/chat

## Regression tests

Add focused tests proving:
1. frontend still sends `ar` for Arabic UI and `en` for English UI.
2. Arabic prompt explicitly requires Arabic regardless of source text language.
3. English prompt explicitly requires English regardless of source text language.
4. title and description use the same rule.
5. clearly wrong-language model output triggers at most ONE retry.
6. brand names / URLs / acronyms are allowed without causing false failure.
7. no provider/model change.

## Verify

- `npm --prefix backend run test:ramzy`
- frontend build only if frontend changed
- restart/reload backend because prompt/service changes
- authenticated live smoke:
  - Arabic request with English input => Arabic output
  - English request with Arabic input => English output
  for title and description when provider is available
- deploy
- commit + push exact changes to TOS main

Return only:
```
PATCH=RAMZY-SMART-TASK-V3-LIVE-QA-R5.5
PASS/FAIL=
AR_TITLE=PASS/FAIL
AR_DESCRIPTION=PASS/FAIL
EN_TITLE=PASS/FAIL
EN_DESCRIPTION=PASS/FAIL
LANGUAGE_RETRY=PASS/FAIL
PROVIDER_UNCHANGED=PASS/FAIL
BACKEND_TEST=PASS/FAIL
FRONTEND_BUILD=PASS/FAIL/NOT_NEEDED
LIVE_DEPLOY=PASS/FAIL
COMMIT=
PUSH=YES/NO
ERROR=
```
