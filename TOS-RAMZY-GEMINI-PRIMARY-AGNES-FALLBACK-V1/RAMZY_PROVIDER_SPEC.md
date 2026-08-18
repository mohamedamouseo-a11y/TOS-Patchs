# Ramzy Provider Failover Contract

## Scope
This contract applies only to the model-generation layer used by Ramzy.

Do not change:
- authorization
- roles/workspaces
- approval gates
- read-only/proposals behavior
- tool definitions
- tool execution
- memory
- limits
- audit storage/schema
- database schema

## Provider configuration

```ts
export const RAMZY_PROVIDER_CONFIG = {
  primary: {
    provider: "gemini",
    apiKeyEnv: "GEMINI_API_KEY",
  },
  fallback: {
    provider: "agnes",
    apiKeyEnv: "AGNES_API_KEY",
    baseUrl: "https://apihub.agnes-ai.com/v1",
    model: "agnes-2.0-flash",
  },
} as const;
```

Gemini model name must reuse the model already supported by the installed Gemini client/runtime in the production source. Do not introduce a package upgrade merely to select a newer model.

## Required execution contract

Pseudocode:

```ts
async function generateRamzyModelOutput(input, context) {
  assertNoSideEffectsStarted(context);

  try {
    if (!hasGeminiConfiguration()) {
      return generateWithAgnes(input, {
        reason: "GEMINI_NOT_CONFIGURED",
      });
    }

    const result = await generateWithGemini(input);
    auditProviderSuccess("gemini");
    return result;
  } catch (error) {
    const failure = classifyGeminiFailure(error);
    auditProviderFailure("gemini", failure);

    if (context.sideEffectsStarted) {
      throw error;
    }

    if (!isAllowedFallbackFailure(failure)) {
      throw error;
    }

    const result = await generateWithAgnes(input, {
      reason: failure.code,
    });
    auditProviderSuccess("agnes", {
      fallbackFrom: "gemini",
      reason: failure.code,
    });
    return result;
  }
}
```

## Allowed fallback failures

```ts
function isAllowedFallbackFailure(failure) {
  return (
    failure.code === "GEMINI_NOT_CONFIGURED" ||
    failure.code === "GEMINI_RATE_LIMIT" ||
    failure.code === "GEMINI_SERVER_ERROR" ||
    failure.code === "GEMINI_NETWORK_ERROR" ||
    failure.code === "GEMINI_TIMEOUT" ||
    failure.code === "GEMINI_AUTH_ERROR"
  );
}
```

For `GEMINI_AUTH_ERROR` (401/403), audit must retain the authentication error explicitly; fallback must never hide or overwrite that cause.

## Agnes request contract

Use the project's existing HTTP client if one exists. Do not add a dependency just for Agnes.

```ts
const response = await fetch(
  "https://apihub.agnes-ai.com/v1/chat/completions",
  {
    method: "POST",
    headers: {
      "content-type": "application/json",
      authorization: `Bearer ${process.env.AGNES_API_KEY}`,
    },
    body: JSON.stringify({
      model: "agnes-2.0-flash",
      messages,
      tools,
      tool_choice: toolChoice,
    }),
  },
);
```

Map the Agnes response back to the same internal normalized model result currently consumed by Ramzy. Preserve existing function/tool call names and arguments exactly.

## Side-effect safety

The fallback decision must happen inside the model invocation layer and before any of the following begins:

- tool execution
- external API mutation
- DB write caused by a Ramzy action
- task/status update
- notification/send action
- approval execution

If an action has already started, never replay the prompt through Agnes.

## Audit requirements

At minimum, retain/log:

- provider used: `gemini` or `agnes`
- model used
- whether fallback occurred
- fallback source: `gemini`
- fallback reason
- original Gemini auth error when status is 401/403
- terminal provider error when both providers fail

Never log API keys, bearer tokens, decrypted provider secrets, or full authorization headers.

## Error behavior

If both providers fail, return the existing Ramzy provider-error shape used by the application. Do not invent a new API response shape unless required by the existing source.
