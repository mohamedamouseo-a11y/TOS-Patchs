import { randomUUID } from "node:crypto";

const REQUEST_ID_PATTERN = /^[A-Za-z0-9._:-]{8,128}$/;

function boundedText(value, maxLength) {
  if (value === null || value === undefined) return null;
  const text = String(value).trim();
  if (!text) return null;
  return text.slice(0, maxLength);
}

export function sanitizeRequestId(value) {
  const candidate = Array.isArray(value) ? value[0] : value;
  const text = boundedText(candidate, 128);
  return text && REQUEST_ID_PATTERN.test(text) ? text : null;
}

export function requestPathOnly(req) {
  const raw = String(req?.originalUrl || req?.url || "");
  return boundedText(raw.split("?", 1)[0], 1024);
}

export function requestContextMiddleware(req, res, next) {
  const incomingRequestId = sanitizeRequestId(req?.headers?.["x-request-id"]);
  const requestId = incomingRequestId || randomUUID();
  const userAgent = boundedText(req?.headers?.["user-agent"], 1024);
  const ipAddress = boundedText(req?.ip || req?.socket?.remoteAddress, 128);
  const httpMethod = boundedText(req?.method, 16)?.toUpperCase() || null;

  req.auditContext = Object.freeze({
    requestId,
    ipAddress,
    userAgent,
    httpMethod,
    route: requestPathOnly(req),
  });

  res?.setHeader?.("X-Request-Id", requestId);
  next();
}
