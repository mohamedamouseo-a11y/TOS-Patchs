export const AUDIT_REDACTED = "[REDACTED]";
export const AUDIT_CIRCULAR = "[CIRCULAR]";
export const AUDIT_MAX_DEPTH = "[MAX_DEPTH]";

const SENSITIVE_EXACT = new Set([
  "authorization",
  "proxyauthorization",
  "cookie",
  "setcookie",
  "password",
  "passwd",
  "pwd",
  "secret",
  "clientsecret",
  "apikey",
  "xapikey",
  "accesstoken",
  "refreshtoken",
  "idtoken",
  "authtoken",
  "token",
  "jwt",
  "csrf",
  "csrftoken",
  "xsrf",
  "xsrftoken",
  "otp",
  "onetimepassword",
  "session",
  "sessionid",
  "sessiontoken",
  "credential",
  "credentials",
  "privatekey",
  "privatekeydata",
  "signingkey",
]);

const SENSITIVE_FRAGMENTS = [
  "password",
  "passwd",
  "secret",
  "token",
  "apikey",
  "authorization",
  "cookie",
  "csrf",
  "xsrf",
  "otp",
  "session",
  "credential",
  "privatekey",
  "signingkey",
];

function normalizedKey(key) {
  return String(key || "").toLowerCase().replace(/[^a-z0-9]/g, "");
}

export function isSensitiveAuditKey(key) {
  const normalized = normalizedKey(key);
  if (!normalized) return false;
  if (SENSITIVE_EXACT.has(normalized)) return true;
  return SENSITIVE_FRAGMENTS.some((fragment) => normalized.includes(fragment));
}

export function redactAuditString(value, maxLength = 8192) {
  let output = String(value ?? "");
  output = output
    .replace(/\bBearer\s+[A-Za-z0-9._~+/=-]+/gi, `Bearer ${AUDIT_REDACTED}`)
    .replace(/\b[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b/g, AUDIT_REDACTED)
    .replace(/\b(password|passwd|access[_-]?token|refresh[_-]?token|api[_-]?key|client[_-]?secret|authorization)\s*[:=]\s*[^\s,;]+/gi, (_match, key) => `${key}=${AUDIT_REDACTED}`);
  if (output.length > maxLength) return `${output.slice(0, maxLength)}...[TRUNCATED]`;
  return output;
}

export function redactAuditValue(value, options = {}) {
  const maxDepth = Number.isInteger(options.maxDepth) ? options.maxDepth : 8;
  const maxArrayLength = Number.isInteger(options.maxArrayLength) ? options.maxArrayLength : 100;
  const maxObjectKeys = Number.isInteger(options.maxObjectKeys) ? options.maxObjectKeys : 200;
  const maxStringLength = Number.isInteger(options.maxStringLength) ? options.maxStringLength : 8192;
  const seen = new WeakSet();

  function visit(current, depth) {
    if (current === null) return null;
    if (current === undefined || typeof current === "function" || typeof current === "symbol") return null;
    if (typeof current === "string") return redactAuditString(current, maxStringLength);
    if (typeof current === "number" || typeof current === "boolean") return current;
    if (typeof current === "bigint") return current.toString();
    if (current instanceof Date) return Number.isNaN(current.getTime()) ? null : current.toISOString();
    if (current instanceof Error) {
      return {
        name: redactAuditString(current.name, 256),
        message: redactAuditString(current.message, maxStringLength),
      };
    }
    if (typeof current !== "object") return redactAuditString(current, maxStringLength);
    if (depth >= maxDepth) return AUDIT_MAX_DEPTH;
    if (seen.has(current)) return AUDIT_CIRCULAR;

    seen.add(current);
    try {
      if (Array.isArray(current)) {
        const result = current.slice(0, maxArrayLength).map((item) => visit(item, depth + 1));
        if (current.length > maxArrayLength) result.push(`[TRUNCATED ${current.length - maxArrayLength} ITEMS]`);
        return result;
      }

      const result = {};
      const entries = Object.entries(current);
      for (const [key, item] of entries.slice(0, maxObjectKeys)) {
        result[key] = isSensitiveAuditKey(key) ? AUDIT_REDACTED : visit(item, depth + 1);
      }
      if (entries.length > maxObjectKeys) result.__auditTruncatedKeys = entries.length - maxObjectKeys;
      return result;
    } finally {
      seen.delete(current);
    }
  }

  return visit(value, 0);
}
