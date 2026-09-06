#!/usr/bin/env python3
from pathlib import Path

ROOT = Path('/var/www/TOS')


def read(rel):
    return (ROOT / rel).read_text(encoding='utf-8')


def write(rel, text):
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def ensure_replace(text, old, new, label):
    if new in text:
        return text
    if old not in text:
        raise SystemExit(f'PHASE11_PATCH_ERROR={label}_STATE_UNKNOWN')
    return text.replace(old, new, 1)


VOICE_SERVICE = r'''const VOICE_VERSION = "RAMZY_VOICE_IO_V1";
const DEFAULT_MAX_AUDIO_BYTES = 12 * 1024 * 1024;
const SAFE_AUDIO_TYPES = new Set([
  "audio/webm",
  "audio/ogg",
  "audio/mp4",
  "audio/mpeg",
  "audio/wav",
  "audio/x-wav",
  "audio/aac",
]);

function envFlag(name, fallback = false) {
  const raw = process.env[name];
  if (raw === undefined) return fallback;
  return ["1", "true", "yes", "on"].includes(String(raw).toLowerCase());
}

function cleanBaseUrl(value) {
  return String(value || "").trim().replace(/\/+$/, "");
}

function normalizeLanguage(value) {
  const language = String(value || "").trim().toLowerCase();
  if (language.startsWith("ar")) return "ar";
  if (language.startsWith("en")) return "en";
  return "";
}

function providerConfig(settings = {}) {
  const envBase = cleanBaseUrl(process.env.RAMZY_VOICE_BASE_URL);
  const envKey = String(process.env.RAMZY_VOICE_API_KEY || "").trim();
  if (envBase && envKey) {
    return {
      enabled: true,
      provider: "custom-openai-compatible",
      baseUrl: envBase,
      apiKey: envKey,
      source: "VOICE_ENV",
    };
  }

  const provider = String(settings.provider || "").toLowerCase();
  if (provider === "openai" && settings.apiKey) {
    return {
      enabled: true,
      provider: "openai",
      baseUrl: "https://api.openai.com/v1",
      apiKey: settings.apiKey,
      source: "PRIMARY_PROVIDER",
    };
  }

  if (provider === "agnes" && envFlag("RAMZY_VOICE_USE_PRIMARY_OPENAI_COMPATIBLE", false)) {
    const key = String(settings.agnesApiKey || settings.apiKey || "").trim();
    const baseUrl = cleanBaseUrl(settings.agnesBaseUrl);
    if (key && baseUrl) {
      return {
        enabled: true,
        provider: "agnes-openai-compatible",
        baseUrl,
        apiKey: key,
        source: "PRIMARY_PROVIDER_OPT_IN",
      };
    }
  }

  return {
    enabled: false,
    provider: provider || "none",
    baseUrl: "",
    apiKey: "",
    source: "BROWSER_FALLBACK",
  };
}

function safeProviderError(status, fallback) {
  const error = new Error(fallback);
  error.status = status;
  error.code = "RAMZY_VOICE_PROVIDER_ERROR";
  return error;
}

async function providerFetch(config, path, options) {
  let response;
  try {
    response = await fetch(`${config.baseUrl}${path}`, options);
  } catch {
    throw safeProviderError(502, "Voice provider is unavailable");
  }
  if (!response.ok) {
    throw safeProviderError(response.status === 404 ? 501 : 502, "Voice provider does not support this operation right now");
  }
  return response;
}

export function getRamzyVoiceCapabilities(settings = {}) {
  const config = providerConfig(settings);
  return {
    version: VOICE_VERSION,
    apiTranscription: Boolean(config.enabled),
    apiSpeech: Boolean(config.enabled),
    provider: config.provider,
    providerSource: config.source,
    browserSpeechRecognitionFallback: true,
    browserSpeechSynthesisFallback: true,
    autoSendAfterTranscription: false,
    actionExecutionFromVoice: false,
  };
}

export function validateRamzyVoiceUpload({ buffer, mimeType }) {
  if (!Buffer.isBuffer(buffer) || !buffer.length) {
    const error = new Error("Audio file is required");
    error.status = 400;
    throw error;
  }
  if (buffer.length > DEFAULT_MAX_AUDIO_BYTES) {
    const error = new Error("Audio file is too large");
    error.status = 413;
    throw error;
  }
  const type = String(mimeType || "").toLowerCase().split(";")[0].trim();
  if (type && !SAFE_AUDIO_TYPES.has(type)) {
    const error = new Error("Unsupported audio format");
    error.status = 415;
    throw error;
  }
  return type || "audio/webm";
}

export async function transcribeRamzyAudio({ settings, buffer, mimeType, filename = "ramzy-voice.webm", language = "" }) {
  const config = providerConfig(settings);
  if (!config.enabled) {
    const error = new Error("API voice transcription is not configured");
    error.status = 501;
    throw error;
  }
  const safeType = validateRamzyVoiceUpload({ buffer, mimeType });
  const form = new FormData();
  form.append("file", new Blob([buffer], { type: safeType }), String(filename || "ramzy-voice.webm").slice(0, 160));
  form.append("model", String(process.env.RAMZY_STT_MODEL || "whisper-1").trim());
  const lang = normalizeLanguage(language);
  if (lang) form.append("language", lang);
  const response = await providerFetch(config, "/audio/transcriptions", {
    method: "POST",
    headers: { Authorization: `Bearer ${config.apiKey}` },
    body: form,
  });
  const payload = await response.json().catch(() => null);
  const text = String(payload?.text || payload?.transcript || "").trim();
  if (!text) throw safeProviderError(502, "Voice provider returned an empty transcription");
  return {
    version: VOICE_VERSION,
    text: text.slice(0, 12_000),
    provider: config.provider,
    language: lang || null,
  };
}

function normalizeVoice(value) {
  const voice = String(value || process.env.RAMZY_TTS_VOICE || "alloy").trim().toLowerCase();
  return /^[a-z0-9_-]{2,40}$/.test(voice) ? voice : "alloy";
}

export async function synthesizeRamzySpeech({ settings, text, voice = "", language = "" }) {
  const config = providerConfig(settings);
  if (!config.enabled) {
    const error = new Error("API speech synthesis is not configured");
    error.status = 501;
    throw error;
  }
  const content = String(text || "").trim();
  if (!content) {
    const error = new Error("Speech text is required");
    error.status = 400;
    throw error;
  }
  if (content.length > 4000) {
    const error = new Error("Speech text is too long");
    error.status = 400;
    throw error;
  }
  const response = await providerFetch(config, "/audio/speech", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${config.apiKey}`,
      "Content-Type": "application/json",
      Accept: "audio/mpeg",
    },
    body: JSON.stringify({
      model: String(process.env.RAMZY_TTS_MODEL || "tts-1").trim(),
      voice: normalizeVoice(voice),
      input: content,
      response_format: "mp3",
    }),
  });
  const arrayBuffer = await response.arrayBuffer();
  if (!arrayBuffer.byteLength) throw safeProviderError(502, "Voice provider returned empty audio");
  return {
    version: VOICE_VERSION,
    buffer: Buffer.from(arrayBuffer),
    contentType: response.headers.get("content-type") || "audio/mpeg",
    provider: config.provider,
    language: normalizeLanguage(language) || null,
  };
}

export function getRamzyVoiceConfig() {
  return {
    version: VOICE_VERSION,
    maxAudioBytes: DEFAULT_MAX_AUDIO_BYTES,
    sttModelDefault: "whisper-1",
    ttsModelDefault: "tts-1",
    actionExecutionFromVoice: false,
    providerSecretsExposedToBrowser: false,
  };
}
'''

VOICE_TEST = r'''import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { getRamzyVoiceCapabilities, getRamzyVoiceConfig } from "../services/ramzyVoice.service.js";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "../..");
const read = (relative) => readFile(path.join(root, relative), "utf8");

test("Phase 11 voice service keeps provider secrets server-side and actions disabled", () => {
  const config = getRamzyVoiceConfig();
  assert.equal(config.version, "RAMZY_VOICE_IO_V1");
  assert.equal(config.actionExecutionFromVoice, false);
  assert.equal(config.providerSecretsExposedToBrowser, false);
  const fallback = getRamzyVoiceCapabilities({ provider: "google" });
  assert.equal(fallback.apiTranscription, false);
  assert.equal(fallback.browserSpeechRecognitionFallback, true);
  assert.equal(fallback.autoSendAfterTranscription, false);
});

test("Phase 11 agent routes keep voice behind auth and enabled-user policy", async () => {
  const routes = await read("routes/agent.routes.js");
  assert.match(routes, /router\.use\(auth\)/);
  assert.match(routes, /\/voice\/status/);
  assert.match(routes, /\/voice\/transcribe/);
  assert.match(routes, /\/voice\/synthesize/);
  assert.match(routes, /assertAgentEnabledForUser\(req\.user\)/);
  assert.match(routes, /getAgentRuntimeSettings/);
});

test("Phase 11 frontend supports API voice plus browser fallbacks without auto-send", async () => {
  const ui = await read("../frontend/src/components/RamzyAssistant.jsx");
  const api = await read("../frontend/src/lib/api.js");
  assert.match(ui, /RAMZY_VOICE_MODE_STORAGE_PREFIX/);
  assert.match(ui, /voice-input/);
  assert.match(ui, /voice-conversation/);
  assert.match(ui, /MediaRecorder/);
  assert.match(ui, /SpeechRecognition/);
  assert.match(ui, /speechSynthesis/);
  assert.match(ui, /transcribeVoice/);
  assert.match(ui, /synthesizeVoice/);
  assert.match(api, /\/api\/agent\/voice\/transcribe/);
  assert.match(api, /\/api\/agent\/voice\/synthesize/);
  assert.doesNotMatch(ui, /transcribeVoice[\s\S]{0,500}sendMessage\(/);
});
'''

VOICE_CSS = r'''.ramzy-voice-mode-select {
  min-width: 138px;
  height: 34px;
  border-radius: 10px;
  border: 1px solid rgba(148, 163, 184, 0.28);
  background: rgba(255, 255, 255, 0.84);
  padding: 0 9px;
  font-size: 11px;
  font-weight: 800;
  color: #334155;
  outline: none;
}
.dark .ramzy-voice-mode-select {
  background: rgba(24, 24, 27, 0.92);
  border-color: rgba(255, 255, 255, 0.11);
  color: #e4e4e7;
}
.ramzy-message-actions .ramzy-speak-button.is-speaking,
.ramzy-mic-button.is-listening {
  color: #b45309;
  background: rgba(245, 158, 11, 0.14);
}
.ramzy-voice-status.is-api {
  color: #047857;
}
.dark .ramzy-voice-status.is-api {
  color: #6ee7b7;
}
@media (max-width: 640px) {
  .ramzy-voice-mode-select { min-width: 116px; max-width: 145px; }
}
'''

# New backend service.
voice_rel = 'backend/src/agency-operator/services/ramzyVoice.service.js'
if (ROOT / voice_rel).exists():
    existing = read(voice_rel)
    if 'RAMZY_VOICE_IO_V1' not in existing:
        raise SystemExit('PHASE11_PATCH_ERROR=VOICE_SERVICE_CONFLICT')
else:
    write(voice_rel, VOICE_SERVICE)

# Static tests.
test_rel = 'backend/src/agency-operator/tests/ramzyVoicePhase11.static.test.js'
if (ROOT / test_rel).exists():
    existing = read(test_rel)
    if 'Phase 11 voice service' not in existing:
        raise SystemExit('PHASE11_PATCH_ERROR=VOICE_TEST_CONFLICT')
else:
    write(test_rel, VOICE_TEST)

# Dedicated CSS.
css_rel = 'frontend/src/components/ramzyVoicePhase11.css'
if (ROOT / css_rel).exists():
    existing = read(css_rel)
    if '.ramzy-voice-mode-select' not in existing:
        raise SystemExit('PHASE11_PATCH_ERROR=VOICE_CSS_CONFLICT')
else:
    write(css_rel, VOICE_CSS)

# backend/src/routes/agent.routes.js
rel = 'backend/src/routes/agent.routes.js'
text = read(rel)
if 'import multer from "multer";' not in text:
    text = ensure_replace(text, 'import rateLimit, { ipKeyGenerator } from "express-rate-limit";\n', 'import rateLimit, { ipKeyGenerator } from "express-rate-limit";\nimport multer from "multer";\n', 'AGENT_ROUTE_MULTER_IMPORT')
text = ensure_replace(
    text,
    '  getAgentSettings,\n  publicAgentSettings,\n  updateAgentSettings,\n} from "../agency-operator/services/agentSettings.service.js";\n',
    '  getAgentRuntimeSettings,\n  getAgentSettings,\n  publicAgentSettings,\n  updateAgentSettings,\n} from "../agency-operator/services/agentSettings.service.js";\n',
    'AGENT_ROUTE_RUNTIME_SETTINGS_IMPORT',
)
if 'from "../agency-operator/services/ramzyVoice.service.js";' not in text:
    anchor = 'import { clearScopedRamzyMemory } from "../agency-operator/services/ramzyMemory.service.js";\n'
    insert = anchor + 'import { getRamzyVoiceCapabilities, synthesizeRamzySpeech, transcribeRamzyAudio } from "../agency-operator/services/ramzyVoice.service.js";\n'
    text = ensure_replace(text, anchor, insert, 'AGENT_ROUTE_VOICE_IMPORT')
if 'const ramzyVoiceUpload = multer({' not in text:
    anchor = 'const APPROVAL_STATUSES = new Set(["PENDING", "EXECUTING", "EXECUTED", "REJECTED", "FAILED", "EXPIRED"]);\n'
    insert = anchor + '''const ramzyVoiceUpload = multer({\n  storage: multer.memoryStorage(),\n  limits: { fileSize: 12 * 1024 * 1024, files: 1 },\n});\n'''
    text = ensure_replace(text, anchor, insert, 'AGENT_ROUTE_VOICE_UPLOAD')
if 'router.get("/voice/status"' not in text:
    anchor = 'router.get("/settings", requireRole("SUPER_ADMIN"), asyncHandler(async (_req, res) => {\n'
    block = '''router.get("/voice/status", asyncHandler(async (req, res) => {\n  await assertAgentEnabledForUser(req.user);\n  const settings = await getAgentRuntimeSettings();\n  res.json(getRamzyVoiceCapabilities(settings));\n}));\n\nrouter.post("/voice/transcribe", ramzyVoiceUpload.single("audio"), asyncHandler(async (req, res) => {\n  await assertAgentEnabledForUser(req.user);\n  if (!req.file?.buffer) throw new AppError("Audio file is required", 400);\n  const settings = await getAgentRuntimeSettings();\n  try {\n    res.json(await transcribeRamzyAudio({\n      settings,\n      buffer: req.file.buffer,\n      mimeType: req.file.mimetype,\n      filename: req.file.originalname,\n      language: req.body?.language,\n    }));\n  } catch (error) {\n    throw new AppError(String(error?.message || "Voice transcription failed"), Number(error?.status || 502));\n  }\n}));\n\nrouter.post("/voice/synthesize", asyncHandler(async (req, res) => {\n  await assertAgentEnabledForUser(req.user);\n  const settings = await getAgentRuntimeSettings();\n  try {\n    const speech = await synthesizeRamzySpeech({\n      settings,\n      text: req.body?.text,\n      voice: req.body?.voice,\n      language: req.body?.language,\n    });\n    res.setHeader("Content-Type", speech.contentType || "audio/mpeg");\n    res.setHeader("Cache-Control", "no-store");\n    res.setHeader("X-Ramzy-Voice-Provider", speech.provider || "api");\n    res.send(speech.buffer);\n  } catch (error) {\n    throw new AppError(String(error?.message || "Speech synthesis failed"), Number(error?.status || 502));\n  }\n}));\n\n'''
    text = ensure_replace(text, anchor, block + anchor, 'AGENT_ROUTE_VOICE_ENDPOINTS')
write(rel, text)

# frontend/src/lib/api.js
rel = 'frontend/src/lib/api.js'
text = read(rel)
if 'async function binaryJsonRequest(' not in text:
    anchor = '\n\nfunction uploadRequest(path, formData, { method = "POST", onProgress } = {}) {\n'
    helper = r'''

async function binaryJsonRequest(path, payload = {}, { signal } = {}) {
  const stateSyncRequestId = createStateSyncRequestId();
  const headers = {
    "Content-Type": "application/json",
    "Accept": "audio/mpeg, audio/*",
    "X-Tamiyouz-Client": "web",
    "x-csrf-token": decodeURIComponent(readCookie("tamiyouz_csrf_token")),
    [STATE_SYNC_REQUEST_HEADER]: stateSyncRequestId,
  };
  let res;
  try {
    res = await fetch(`${API_URL}${path}`, {
      credentials: "include",
      method: "POST",
      headers,
      body: JSON.stringify(payload || {}),
      signal,
    });
  } catch (error) {
    if (error?.name === "AbortError") throw error;
    throw new ApiError("Failed to fetch", 0, { cause: error });
  }
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    const data = normalizeFileNamesInPayload(parseJsonSafely(text));
    if (res.status === 401) notifyAuthExpired(path);
    throw new ApiError(data?.error || data?.message || text || `Request failed with status ${res.status}`, res.status, data);
  }
  notifyMutationFromRequest(path, "POST", { requestId: stateSyncRequestId });
  return res.blob();
}
'''
    text = ensure_replace(text, anchor, helper + anchor, 'API_BINARY_HELPER')
if 'voiceStatus: () => request("/api/agent/voice/status")' not in text:
    anchor = '    insights: (params = {}) => { const query = new URLSearchParams(Object.entries(params).filter(([, value]) => value)); return request(`/api/agent/insights${query.toString() ? `?${query}` : ""}`); },\n'
    addition = anchor + '''    voiceStatus: () => request("/api/agent/voice/status"),\n    transcribeVoice: (blob, language = "") => { const form = new FormData(); form.append("audio", blob, blob?.type?.includes("ogg") ? "ramzy-voice.ogg" : "ramzy-voice.webm"); if (language) form.append("language", language); return uploadRequest("/api/agent/voice/transcribe", form); },\n    synthesizeVoice: (text, options = {}) => binaryJsonRequest("/api/agent/voice/synthesize", { text, voice: options.voice || "", language: options.language || "" }, { signal: options.signal }),\n'''
    text = ensure_replace(text, anchor, addition, 'API_AGENT_VOICE_METHODS')
write(rel, text)

# frontend/src/components/RamzyAssistant.jsx
rel = 'frontend/src/components/RamzyAssistant.jsx'
text = read(rel)
text = ensure_replace(
    text,
    'import { Check, Copy, History, LoaderCircle, MessageCircle, Mic, MicOff, Minus, Plus, RefreshCw, Send, Sparkles, Square, ThumbsDown, ThumbsUp, X } from "lucide-react";\n',
    'import { Check, Copy, History, LoaderCircle, MessageCircle, Mic, MicOff, Minus, Plus, RefreshCw, Send, Sparkles, Square, ThumbsDown, ThumbsUp, Volume2, VolumeX, X } from "lucide-react";\n',
    'RAMZY_VOICE_ICON_IMPORT',
)
if 'import "./ramzyVoicePhase11.css";' not in text:
    anchor = 'import { usePreferences } from "../contexts/PreferencesContext";\n'
    text = ensure_replace(text, anchor, anchor + 'import "./ramzyVoicePhase11.css";\n', 'RAMZY_VOICE_CSS_IMPORT')
if 'const RAMZY_VOICE_MODE_STORAGE_PREFIX' not in text:
    anchor = 'const RAMZY_POSITION_STORAGE_PREFIX = "tos.ramzy.position";\n'
    text = ensure_replace(text, anchor, anchor + 'const RAMZY_VOICE_MODE_STORAGE_PREFIX = "tos.ramzy.voice-mode";\n', 'RAMZY_VOICE_STORAGE_CONST')

# MessageBubble voice action.
text = ensure_replace(
    text,
    'function MessageBubble({ message, onFeedback, onRetry, isEnglish }) {\n',
    'function MessageBubble({ message, onFeedback, onRetry, onSpeak, speaking, isEnglish }) {\n',
    'MESSAGE_BUBBLE_SIGNATURE',
)
old_actions = '''          <button type="button" title={isEnglish ? "Copy" : "نسخ"} aria-label={isEnglish ? "Copy response" : "نسخ الرد"} onClick={() => navigator.clipboard?.writeText(message.content)}><Copy size={13} /></button>\n          {onRetry && <button type="button" title={isEnglish ? "Retry" : "إعادة المحاولة"} aria-label={isEnglish ? "Retry response" : "إعادة محاولة الرد"} onClick={onRetry}><RefreshCw size={13} /></button>}\n'''
new_actions = '''          <button type="button" title={isEnglish ? "Copy" : "نسخ"} aria-label={isEnglish ? "Copy response" : "نسخ الرد"} onClick={() => navigator.clipboard?.writeText(message.content)}><Copy size={13} /></button>\n          {onSpeak && <button type="button" className={`ramzy-speak-button${speaking ? " is-speaking" : ""}`} title={speaking ? (isEnglish ? "Stop voice" : "إيقاف الصوت") : (isEnglish ? "Read response aloud" : "قراءة الرد صوتيًا")} aria-label={speaking ? (isEnglish ? "Stop voice" : "إيقاف الصوت") : (isEnglish ? "Read response aloud" : "قراءة الرد صوتيًا")} onClick={() => onSpeak(message)}>{speaking ? <VolumeX size={13} /> : <Volume2 size={13} />}</button>}\n          {onRetry && <button type="button" title={isEnglish ? "Retry" : "إعادة المحاولة"} aria-label={isEnglish ? "Retry response" : "إعادة محاولة الرد"} onClick={onRetry}><RefreshCw size={13} /></button>}\n'''
text = ensure_replace(text, old_actions, new_actions, 'MESSAGE_BUBBLE_VOICE_ACTION')

# State and refs.
state_anchor = '  const [voiceStatus, setVoiceStatus] = useState("");\n'
if 'const [voiceMode, setVoiceMode]' not in text:
    state_add = state_anchor + '''  const [voiceMode, setVoiceMode] = useState(() => localStorage.getItem(`${RAMZY_VOICE_MODE_STORAGE_PREFIX}.${user?.id || "anonymous"}`) || "voice-input");\n  const [voiceCapabilities, setVoiceCapabilities] = useState(null);\n  const [speakingMessageId, setSpeakingMessageId] = useState("");\n'''
    text = ensure_replace(text, state_anchor, state_add, 'RAMZY_VOICE_STATE')
refs_anchor = '  const voiceHadSpeechRef = useRef(false);\n'
if 'const voiceRecorderRef = useRef(null);' not in text:
    refs_add = refs_anchor + '''  const voiceRecorderRef = useRef(null);\n  const voiceStreamRef = useRef(null);\n  const voiceChunksRef = useRef([]);\n  const voiceAudioRef = useRef(null);\n  const voiceAudioUrlRef = useRef("");\n'''
    text = ensure_replace(text, refs_anchor, refs_add, 'RAMZY_VOICE_REFS')

# Load voice capabilities and persist mode.
status_effect_anchor = '''  useEffect(() => {\n    let alive = true;\n    initializedRef.current = false;\n    api.agent.status().then((data) => { if (alive) setStatus(data); }).catch(() => { if (alive) setStatus({ enabled: false, allowed: false }); });\n    return () => { alive = false; };\n  }, [user?.id]);\n'''
if 'api.agent.voiceStatus()' not in text:
    addition = status_effect_anchor + '''\n  useEffect(() => {\n    if (!status?.allowed) return undefined;\n    let alive = true;\n    api.agent.voiceStatus().then((data) => { if (alive) setVoiceCapabilities(data); }).catch(() => {\n      if (alive) setVoiceCapabilities({ apiTranscription: false, apiSpeech: false, browserSpeechRecognitionFallback: true, browserSpeechSynthesisFallback: true });\n    });\n    return () => { alive = false; };\n  }, [status?.allowed]);\n\n  useEffect(() => {\n    try { localStorage.setItem(`${RAMZY_VOICE_MODE_STORAGE_PREFIX}.${user?.id || "anonymous"}`, voiceMode); } catch { /* optional */ }\n  }, [voiceMode, user?.id]);\n'''
    text = ensure_replace(text, status_effect_anchor, addition, 'RAMZY_VOICE_CAPABILITIES_EFFECT')

# Cleanup.
old_cleanup = '''  useEffect(() => () => {\n    voiceRecognitionRef.current?.stop();\n    voiceRecognitionRef.current = null;\n  }, []);\n'''
new_cleanup = '''  useEffect(() => () => {\n    voiceRecognitionRef.current?.stop();\n    voiceRecognitionRef.current = null;\n    try { voiceRecorderRef.current?.stop(); } catch { /* noop */ }\n    voiceStreamRef.current?.getTracks?.().forEach((track) => track.stop());\n    voiceStreamRef.current = null;\n    voiceAudioRef.current?.pause?.();\n    window.speechSynthesis?.cancel?.();\n    if (voiceAudioUrlRef.current) URL.revokeObjectURL(voiceAudioUrlRef.current);\n  }, []);\n'''
text = ensure_replace(text, old_cleanup, new_cleanup, 'RAMZY_VOICE_CLEANUP')

# Add recording/TTS helpers after browser recognition function.
marker = '  function applyHelpSuggestion() {\n'
if 'async function startApiVoiceRecording()' not in text:
    helpers = r'''  function voiceLanguage() {
    return isEnglish ? "en-US" : "ar-EG";
  }

  function stopVoicePlayback() {
    voiceAudioRef.current?.pause?.();
    voiceAudioRef.current = null;
    if (voiceAudioUrlRef.current) {
      URL.revokeObjectURL(voiceAudioUrlRef.current);
      voiceAudioUrlRef.current = "";
    }
    window.speechSynthesis?.cancel?.();
    setSpeakingMessageId("");
  }

  function speechText(value) {
    return String(value || "")
      .replace(/```[\s\S]*?```/g, " ")
      .replace(/`([^`]+)`/g, "$1")
      .replace(/!\[[^\]]*\]\([^)]*\)/g, " ")
      .replace(/\[([^\]]+)\]\([^)]*\)/g, "$1")
      .replace(/^#{1,6}\s+/gm, "")
      .replace(/[|*_>#-]+/g, " ")
      .replace(/\s+/g, " ")
      .trim()
      .slice(0, 4000);
  }

  async function playAssistantVoice(message) {
    const text = speechText(message?.content);
    if (!text) return;
    if (speakingMessageId === message?.id) {
      stopVoicePlayback();
      return;
    }
    stopVoicePlayback();
    setSpeakingMessageId(message?.id || "speaking");
    const language = voiceLanguage();
    if (voiceCapabilities?.apiSpeech) {
      try {
        const blob = await api.agent.synthesizeVoice(text, { language });
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);
        voiceAudioUrlRef.current = url;
        voiceAudioRef.current = audio;
        audio.onended = stopVoicePlayback;
        audio.onerror = stopVoicePlayback;
        await audio.play();
        return;
      } catch {
        setVoiceStatus(isEnglish ? "API voice unavailable; using browser voice." : "الصوت عبر الـAPI غير متاح حاليًا؛ سيتم استخدام صوت المتصفح.");
      }
    }
    if (window.speechSynthesis && window.SpeechSynthesisUtterance) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = language;
      utterance.onend = () => setSpeakingMessageId("");
      utterance.onerror = () => setSpeakingMessageId("");
      window.speechSynthesis.speak(utterance);
    } else {
      setSpeakingMessageId("");
      setVoiceStatus(isEnglish ? "Speech output is not supported in this browser." : "إخراج الصوت غير مدعوم في هذا المتصفح.");
    }
  }

  async function startApiVoiceRecording() {
    if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") return false;
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      voiceBaseInputRef.current = input;
      voiceChunksRef.current = [];
      voiceStreamRef.current = stream;
      voiceRecorderRef.current = recorder;
      setVoiceStatus(isEnglish ? "Listening through secure API transcription..." : "جاري الاستماع للإملاء عبر الـAPI...");
      recorder.ondataavailable = (event) => { if (event.data?.size) voiceChunksRef.current.push(event.data); };
      recorder.onerror = () => {
        setListening(false);
        setVoiceStatus(isEnglish ? "Could not record audio." : "تعذر تسجيل الصوت.");
      };
      recorder.onstop = async () => {
        setListening(false);
        const chunks = voiceChunksRef.current;
        const mimeType = recorder.mimeType || chunks?.[0]?.type || "audio/webm";
        voiceRecorderRef.current = null;
        voiceStreamRef.current?.getTracks?.().forEach((track) => track.stop());
        voiceStreamRef.current = null;
        if (!chunks.length) {
          setVoiceStatus(isEnglish ? "No speech was captured." : "لم يتم التقاط صوت.");
          return;
        }
        try {
          setVoiceStatus(isEnglish ? "Transcribing..." : "جاري تحويل الصوت إلى نص...");
          const result = await api.agent.transcribeVoice(new Blob(chunks, { type: mimeType }), voiceLanguage());
          const transcript = String(result?.text || "").trim();
          if (transcript) {
            setInput((current) => appendDictation(current || voiceBaseInputRef.current, transcript));
            setVoiceStatus(isEnglish ? "Voice added to the prompt. Review it, then send." : "تمت إضافة كلامك للبرومبت. راجعه ثم اضغط إرسال.");
            setTimeout(() => composerRef.current?.focus(), 0);
          }
        } catch {
          setVoiceStatus(isEnglish ? "API transcription failed. You can use browser dictation instead." : "تعذر تحويل الصوت عبر الـAPI. يمكنك استخدام إملاء المتصفح بدلًا منه.");
        }
      };
      recorder.start();
      setListening(true);
      return true;
    } catch {
      setVoiceStatus(isEnglish ? "Allow microphone access, then try again." : "اسمح باستخدام الميكروفون ثم جرّب مرة أخرى.");
      return false;
    }
  }

  function stopVoiceInput() {
    if (voiceRecorderRef.current && voiceRecorderRef.current.state !== "inactive") {
      voiceRecorderRef.current.stop();
      return;
    }
    stopVoiceRecognition();
  }

  async function startVoiceInput() {
    if (voiceMode === "text") return;
    if (listening) {
      stopVoiceInput();
      return;
    }
    stopVoicePlayback();
    if (voiceCapabilities?.apiTranscription) {
      const started = await startApiVoiceRecording();
      if (started) return;
    }
    startVoiceRecognition();
  }

'''
    text = ensure_replace(text, marker, helpers + marker, 'RAMZY_VOICE_HELPERS')

# Safe send while listening; do not auto-send transcript.
text = ensure_replace(
    text,
    '  async function sendMessage(text = input) {\n    if (listening) stopVoiceRecognition();\n',
    '  async function sendMessage(text = input) {\n    if (listening) { stopVoiceInput(); return; }\n',
    'RAMZY_VOICE_SAFE_SEND',
)
# Auto speak final result only in conversation mode.
if 'if (voiceMode === "voice-conversation" && finalResult?.message)' not in text:
    anchor = '        if (finalResult.approvals?.length) setApprovals((current) => [...current, ...finalResult.approvals.filter((next) => !current.some((item) => item.id === next.id))]);\n'
    addition = anchor + '        if (voiceMode === "voice-conversation" && finalResult?.message) void playAssistantVoice(finalResult.message);\n'
    text = ensure_replace(text, anchor, addition, 'RAMZY_VOICE_AUTO_TTS')

# MessageBubble wiring.
old_bubble = '''                <MessageBubble message={message} isEnglish={isEnglish} onFeedback={feedback} onRetry={message.role === "ASSISTANT" && !message.streaming && !String(message.id).startsWith("streaming-") ? () => retryAssistantMessage(message.id) : null} />\n'''
new_bubble = '''                <MessageBubble message={message} isEnglish={isEnglish} onFeedback={feedback} onSpeak={message.role === "ASSISTANT" && !message.streaming ? playAssistantVoice : null} speaking={speakingMessageId === message.id} onRetry={message.role === "ASSISTANT" && !message.streaming && !String(message.id).startsWith("streaming-") ? () => retryAssistantMessage(message.id) : null} />\n'''
text = ensure_replace(text, old_bubble, new_bubble, 'RAMZY_VOICE_MESSAGE_WIRING')

# Voice mode selector and button.
old_actions = '''            <div className="ramzy-composer-actions">\n              <button type="button" className={`ramzy-mic-button${listening ? " is-listening" : ""}`} aria-label={listening ? (isEnglish ? "Stop voice dictation" : "إيقاف الإملاء الصوتي") : (isEnglish ? "Voice dictation" : "الإملاء الصوتي")} title={listening ? (isEnglish ? "Stop voice dictation" : "إيقاف الإملاء الصوتي") : (isEnglish ? "Voice dictation in Arabic or English" : "الإملاء الصوتي بالعربية أو الإنجليزية")} disabled={typeof window !== "undefined" && !window.SpeechRecognition && !window.webkitSpeechRecognition} onClick={startVoiceRecognition}>{listening ? <MicOff size={19} /> : <Mic size={19} />}</button>\n              <button type="button" className="ramzy-send-button" aria-label={isEnglish ? "Send message" : "إرسال الرسالة"} disabled={!input.trim() || loading} onClick={() => sendMessage()}><Send size={18} /></button>\n            </div>\n'''
new_actions = '''            <div className="ramzy-composer-actions">\n              <select className="ramzy-voice-mode-select" aria-label={isEnglish ? "Voice mode" : "وضع الصوت"} value={voiceMode} onChange={(event) => { stopVoiceInput(); stopVoicePlayback(); setVoiceMode(event.target.value); }}>\n                <option value="text">{isEnglish ? "Text only" : "نص فقط"}</option>\n                <option value="voice-input">{isEnglish ? "Voice input" : "إدخال صوتي"}</option>\n                <option value="voice-conversation">{isEnglish ? "Voice conversation" : "محادثة صوتية"}</option>\n              </select>\n              {voiceMode !== "text" && <button type="button" className={`ramzy-mic-button${listening ? " is-listening" : ""}`} aria-label={listening ? (isEnglish ? "Stop voice input" : "إيقاف الإدخال الصوتي") : (isEnglish ? "Voice input" : "إدخال صوتي")} title={voiceCapabilities?.apiTranscription ? (isEnglish ? "Secure API voice transcription" : "تحويل الصوت إلى نص عبر الـAPI") : (isEnglish ? "Browser voice dictation" : "إملاء صوتي عبر المتصفح")} onClick={startVoiceInput}>{listening ? <MicOff size={19} /> : <Mic size={19} />}</button>}\n              <button type="button" className="ramzy-send-button" aria-label={isEnglish ? "Send message" : "إرسال الرسالة"} disabled={!input.trim() || loading || listening} onClick={() => sendMessage()}><Send size={18} /></button>\n            </div>\n'''
text = ensure_replace(text, old_actions, new_actions, 'RAMZY_VOICE_COMPOSER_ACTIONS')
write(rel, text)

print('PHASE11_RAMZY_VOICE_INPUT_OUTPUT_PATCH=PASS')
