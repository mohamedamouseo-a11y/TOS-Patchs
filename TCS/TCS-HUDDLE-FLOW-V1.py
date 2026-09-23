#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime
import shutil
import sys

PATCH = "TCS-HUDDLE-FLOW-V1"
ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "/var/www/TOS").resolve()
HOOK = ROOT / "frontend/src/hooks/useHuddleWebRTC.js"
CHAT = ROOT / "frontend/src/components/ChatPanel.jsx"
SOCKETS = ROOT / "backend/src/sockets.js"
CHAT_ROUTE = ROOT / "backend/src/routes/chat.routes.js"

for path in (HOOK, CHAT, SOCKETS, CHAT_ROUTE):
    if not path.exists():
        raise SystemExit(f"{PATCH}: missing {path}")

backup = Path("/tmp") / f"{PATCH}-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
backup.mkdir(parents=True, exist_ok=True)
for path in (HOOK, CHAT, SOCKETS, CHAT_ROUTE):
    shutil.copy2(path, backup / path.name)

hook = r'''import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { connectSocket, getSocket } from "../lib/socket";

const ICE_SERVERS = [
  { urls: "stun:stun.l.google.com:19302" },
  { urls: "stun:stun1.l.google.com:19302" },
];

const HUDDLE_JOIN_TIMEOUT_MS = 12000;

function targetKey(target = {}) {
  if (target.conversationId) return "conversation:" + target.conversationId;
  if (target.channelId) return "channel:" + target.channelId;
  if (target.projectId) return "project:" + target.projectId + ":general";
  return "";
}

function upsertParticipant(list = [], participant = {}) {
  if (!participant?.socketId) return list;
  return list.some((item) => item.socketId === participant.socketId)
    ? list.map((item) => (item.socketId === participant.socketId ? { ...item, ...participant } : item))
    : [...list, participant];
}

function isDeviceNotFound(error) {
  return ["NotFoundError", "DevicesNotFoundError"].includes(error?.name) || /device not found/i.test(error?.message || "");
}

function currentHuddleLang() {
  if (typeof document !== "undefined" && document.documentElement?.lang === "en") return "en";
  try { return window.localStorage.getItem("tamiyouz-language") === "en" ? "en" : "ar"; } catch { return "ar"; }
}

function huddleText(ar, en) {
  return currentHuddleLang() === "en" ? en : ar;
}

function localizedHuddleDeviceLabel(deviceLabel = "الجهاز") {
  if (currentHuddleLang() !== "en") return deviceLabel;
  if (deviceLabel === "الميكروفون") return "microphone";
  if (deviceLabel === "الكاميرا") return "camera";
  if (deviceLabel === "الجهاز") return "device";
  return deviceLabel;
}

function mediaErrorMessage(error, deviceLabel = "الجهاز") {
  const localizedDevice = localizedHuddleDeviceLabel(deviceLabel);
  if (isDeviceNotFound(error)) return huddleText(
    "لم يتم العثور على " + deviceLabel + ". وصّل الجهاز أو فعّله من إعدادات المتصفح ثم جرّب مرة أخرى.",
    localizedDevice + " was not found. Connect or enable it in browser settings, then try again.",
  );
  if (error?.name === "NotAllowedError" || error?.name === "PermissionDeniedError") return huddleText(
    "تم رفض صلاحية " + deviceLabel + ". اسمح للمتصفح باستخدامه ثم حاول مرة أخرى.",
    localizedDevice + " permission was denied. Allow browser access, then try again.",
  );
  if (error?.name === "NotReadableError" || error?.name === "TrackStartError") return huddleText(
    deviceLabel + " مستخدم من برنامج آخر أو غير متاح الآن.",
    localizedDevice + " is in use by another application or is unavailable right now.",
  );
  if (error?.name === "SecurityError") return huddleText(
    "تشغيل Huddle يحتاج HTTPS وصلاحيات متصفح صحيحة.",
    "Huddle requires HTTPS and valid browser permissions.",
  );
  return error?.message || huddleText("تعذر تشغيل " + deviceLabel + ".", "Could not start " + localizedDevice + ".");
}

function createEmptyMediaStream() {
  if (typeof MediaStream !== "undefined") return new MediaStream();
  return null;
}

export function useHuddleWebRTC({ target, currentUserId = "", onError = null } = {}) {
  const [joined, setJoined] = useState(false);
  const [joining, setJoining] = useState(false);
  const [mediaBusy, setMediaBusy] = useState(false);
  const [micOn, setMicOn] = useState(true);
  const [cameraOn, setCameraOn] = useState(false);
  const [screenOn, setScreenOn] = useState(false);
  const [participants, setParticipants] = useState([]);
  const [remoteStreams, setRemoteStreams] = useState({});
  const [status, setStatus] = useState(huddleText("جاهز للانضمام", "Ready to join"));
  const [mediaError, setMediaError] = useState("");

  const localVideoRef = useRef(null);
  const localStreamRef = useRef(null);
  const screenStreamRef = useRef(null);
  const peersRef = useRef(new Map());
  const pendingCandidatesRef = useRef(new Map());
  const pendingRenegotiationRef = useRef(new Set());
  const roomRef = useRef("");
  const targetRef = useRef(target || {});
  const desiredJoinedRef = useRef(false);
  const joinTimeoutRef = useRef(null);
  const mediaActionRef = useRef(false);
  const micOnRef = useRef(true);
  const cameraOnRef = useRef(false);
  const screenOnRef = useRef(false);
  const cameraBeforeScreenRef = useRef(false);

  const key = useMemo(() => targetKey(target), [target?.projectId, target?.channelId, target?.conversationId]);

  useEffect(() => {
    targetRef.current = target || {};
  }, [target?.projectId, target?.channelId, target?.conversationId]);

  useEffect(() => { micOnRef.current = micOn; }, [micOn]);
  useEffect(() => { cameraOnRef.current = cameraOn; }, [cameraOn]);
  useEffect(() => { screenOnRef.current = screenOn; }, [screenOn]);

  const reportError = useCallback((message, { blocking = true } = {}) => {
    setMediaError(message);
    if (blocking) setStatus(huddleText("تعذر الاتصال", "Connection failed"));
    if (typeof onError === "function") onError(message);
  }, [onError]);

  function clearJoinTimeout() {
    if (joinTimeoutRef.current) window.clearTimeout(joinTimeoutRef.current);
    joinTimeoutRef.current = null;
  }

  function attachLocalVideo() {
    if (localVideoRef.current) localVideoRef.current.srcObject = localStreamRef.current || null;
  }

  function stopScreenStream() {
    if (screenStreamRef.current) {
      screenStreamRef.current.getTracks().forEach((track) => {
        try { track.stop(); } catch { /* noop */ }
      });
    }
    screenStreamRef.current = null;
  }

  function closePeer(socketId) {
    const pc = peersRef.current.get(socketId);
    if (pc) pc.close();
    peersRef.current.delete(socketId);
    pendingCandidatesRef.current.delete(socketId);
    pendingRenegotiationRef.current.delete(socketId);
    setRemoteStreams((prev) => {
      const next = { ...prev };
      delete next[socketId];
      return next;
    });
  }

  function closeAllPeers() {
    peersRef.current.forEach((pc) => pc.close());
    peersRef.current.clear();
    pendingCandidatesRef.current.clear();
    pendingRenegotiationRef.current.clear();
    setRemoteStreams({});
  }

  function stopLocalStream() {
    stopScreenStream();
    if (localStreamRef.current) {
      localStreamRef.current.getTracks().forEach((track) => {
        try { track.stop(); } catch { /* noop */ }
      });
    }
    localStreamRef.current = null;
    attachLocalVideo();
  }

  function startJoinTimeout() {
    clearJoinTimeout();
    joinTimeoutRef.current = window.setTimeout(() => {
      if (!desiredJoinedRef.current || roomRef.current) return;
      desiredJoinedRef.current = false;
      setJoining(false);
      setJoined(false);
      getSocket()?.emit("huddle:leave");
      closeAllPeers();
      stopLocalStream();
      reportError(huddleText("انتهت مهلة الاتصال بالـ Huddle. حاول مرة أخرى.", "Huddle connection timed out. Try again."));
    }, HUDDLE_JOIN_TIMEOUT_MS);
  }

  function emitSignal(targetSocketId, type, data) {
    const socket = getSocket();
    if (!socket || !targetSocketId) return;
    socket.emit("huddle:signal", { targetSocketId, type, data });
  }

  function emitJoin(socket = getSocket()) {
    if (!socket || !desiredJoinedRef.current || !targetKey(targetRef.current)) return;
    socket.emit("huddle:join", {
      ...targetRef.current,
      micOn: micOnRef.current,
      cameraOn: cameraOnRef.current,
      screenOn: screenOnRef.current,
    });
    startJoinTimeout();
  }

  async function ensureLocalStream({ audio = false } = {}) {
    if (localStreamRef.current) return localStreamRef.current;
    if (audio) {
      if (!navigator.mediaDevices?.getUserMedia) throw new Error(huddleText("المتصفح لا يدعم تشغيل الميكروفون والكاميرا.", "This browser does not support microphone and camera access."));
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
      localStreamRef.current = stream;
      attachLocalVideo();
      return stream;
    }
    const emptyStream = createEmptyMediaStream();
    if (!emptyStream) throw new Error(huddleText("المتصفح لا يدعم تشغيل Huddle.", "This browser does not support Huddle."));
    localStreamRef.current = emptyStream;
    attachLocalVideo();
    return emptyStream;
  }

  async function setOutgoingAudioTrack(audioTrack = null) {
    const stream = await ensureLocalStream({ audio: false });
    stream.getAudioTracks().forEach((track) => {
      if (track !== audioTrack) {
        stream.removeTrack(track);
        try { track.stop(); } catch { /* noop */ }
      }
    });
    if (audioTrack && !stream.getAudioTracks().includes(audioTrack)) stream.addTrack(audioTrack);
    const updates = [];
    peersRef.current.forEach((pc) => {
      const sender = pc.getSenders().find((item) => item.track?.kind === "audio" || item._tosHuddleAudioSender);
      if (sender) {
        sender._tosHuddleAudioSender = true;
        updates.push(sender.replaceTrack(audioTrack));
      } else if (audioTrack) {
        const newSender = pc.addTrack(audioTrack, stream);
        newSender._tosHuddleAudioSender = true;
      }
    });
    await Promise.all(updates);
    await renegotiateAllPeers();
  }

  async function enableAudioTrack() {
    if (!navigator.mediaDevices?.getUserMedia) throw new Error(huddleText("المتصفح لا يدعم تشغيل الميكروفون.", "This browser does not support microphone access."));
    const audioStream = await navigator.mediaDevices.getUserMedia({ audio: true, video: false });
    const [audioTrack] = audioStream.getAudioTracks();
    if (!audioTrack) return null;
    await setOutgoingAudioTrack(audioTrack);
    return audioTrack;
  }

  async function setOutgoingVideoTrack(videoTrack = null) {
    const stream = await ensureLocalStream({ audio: false });
    stream.getVideoTracks().forEach((track) => {
      if (track !== videoTrack) {
        stream.removeTrack(track);
        try { track.stop(); } catch { /* noop */ }
      }
    });
    if (videoTrack && !stream.getVideoTracks().includes(videoTrack)) stream.addTrack(videoTrack);
    attachLocalVideo();
    const updates = [];
    peersRef.current.forEach((pc) => {
      const sender = pc.getSenders().find((item) => item.track?.kind === "video" || item._tosHuddleVideoSender);
      if (sender) {
        sender._tosHuddleVideoSender = true;
        updates.push(sender.replaceTrack(videoTrack));
      } else if (videoTrack) {
        const newSender = pc.addTrack(videoTrack, stream);
        newSender._tosHuddleVideoSender = true;
      }
    });
    await Promise.all(updates);
    await renegotiateAllPeers();
  }

  async function enableCameraTrack() {
    if (!navigator.mediaDevices?.getUserMedia) throw new Error(huddleText("المتصفح لا يدعم تشغيل الكاميرا.", "This browser does not support camera access."));
    const videoStream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
    const [videoTrack] = videoStream.getVideoTracks();
    if (!videoTrack) return null;
    await setOutgoingVideoTrack(videoTrack);
    return videoTrack;
  }

  async function flushCandidates(socketId, pc) {
    if (!pc?.remoteDescription) return;
    const queued = pendingCandidatesRef.current.get(socketId) || [];
    pendingCandidatesRef.current.delete(socketId);
    for (const candidate of queued) {
      try { await pc.addIceCandidate(new RTCIceCandidate(candidate)); } catch { /* stale candidate */ }
    }
  }

  function createPeerConnection(socketId) {
    if (!socketId) return null;
    const existing = peersRef.current.get(socketId);
    if (existing) return existing;
    if (typeof RTCPeerConnection === "undefined") {
      reportError(huddleText("المتصفح لا يدعم WebRTC.", "This browser does not support WebRTC."));
      return null;
    }

    const pc = new RTCPeerConnection({ iceServers: ICE_SERVERS });
    peersRef.current.set(socketId, pc);

    localStreamRef.current?.getTracks().forEach((track) => {
      const sender = pc.addTrack(track, localStreamRef.current);
      if (track.kind === "audio") sender._tosHuddleAudioSender = true;
      if (track.kind === "video") sender._tosHuddleVideoSender = true;
    });

    pc.onicecandidate = (event) => {
      if (event.candidate) emitSignal(socketId, "candidate", event.candidate);
    };
    pc.ontrack = (event) => {
      const [stream] = event.streams;
      if (stream) setRemoteStreams((prev) => ({ ...prev, [socketId]: stream }));
    };
    pc.onsignalingstatechange = () => {
      if (pc.signalingState === "stable" && pendingRenegotiationRef.current.has(socketId)) {
        pendingRenegotiationRef.current.delete(socketId);
        createOffer(socketId).catch(() => null);
      }
    };
    pc.onconnectionstatechange = () => {
      if (pc.connectionState === "failed") {
        reportError(huddleText("تعذر اتصال الوسائط مع أحد المشاركين. سيستمر Huddle ويمكن إعادة المحاولة.", "Media connection to a participant failed. Huddle remains open and can retry."), { blocking: false });
        closePeer(socketId);
      } else if (pc.connectionState === "closed") {
        closePeer(socketId);
      }
    };
    return pc;
  }

  async function createOffer(socketId) {
    const pc = createPeerConnection(socketId);
    if (!pc) return false;
    if (pc.signalingState !== "stable") {
      pendingRenegotiationRef.current.add(socketId);
      return false;
    }
    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);
    emitSignal(socketId, "offer", offer);
    return true;
  }

  async function renegotiateAllPeers() {
    const ids = Array.from(peersRef.current.keys());
    await Promise.all(ids.map((socketId) => createOffer(socketId).catch(() => false)));
  }

  async function handleSignal({ fromSocketId, participant, type, data } = {}) {
    if (!fromSocketId || !["offer", "answer", "candidate"].includes(type)) return;
    if (participant?.socketId) setParticipants((prev) => upsertParticipant(prev, participant));
    try {
      const pc = createPeerConnection(fromSocketId);
      if (!pc) return;
      if (type === "candidate" && data) {
        if (!pc.remoteDescription) {
          const queued = pendingCandidatesRef.current.get(fromSocketId) || [];
          pendingCandidatesRef.current.set(fromSocketId, [...queued, data]);
          return;
        }
        await pc.addIceCandidate(new RTCIceCandidate(data));
        return;
      }
      if (type === "offer") {
        if (pc.signalingState !== "stable") await pc.setLocalDescription({ type: "rollback" }).catch(() => null);
        await pc.setRemoteDescription(new RTCSessionDescription(data));
        await flushCandidates(fromSocketId, pc);
        const answer = await pc.createAnswer();
        await pc.setLocalDescription(answer);
        emitSignal(fromSocketId, "answer", answer);
        return;
      }
      if (type === "answer") {
        if (pc.signalingState !== "have-local-offer") return;
        await pc.setRemoteDescription(new RTCSessionDescription(data));
        await flushCandidates(fromSocketId, pc);
      }
    } catch {
      reportError(huddleText("تعذر إنشاء اتصال Huddle مع أحد المشاركين.", "Could not establish a Huddle connection with a participant."), { blocking: false });
    }
  }

  const leave = useCallback(() => {
    desiredJoinedRef.current = false;
    clearJoinTimeout();
    getSocket()?.emit("huddle:leave");
    roomRef.current = "";
    closeAllPeers();
    stopLocalStream();
    cameraBeforeScreenRef.current = false;
    mediaActionRef.current = false;
    setMediaBusy(false);
    setJoining(false);
    setJoined(false);
    setMicOn(true);
    setCameraOn(false);
    setScreenOn(false);
    micOnRef.current = true;
    cameraOnRef.current = false;
    screenOnRef.current = false;
    setParticipants([]);
    setMediaError("");
    setStatus(huddleText("جاهز للانضمام", "Ready to join"));
  }, []);

  const join = useCallback(async () => {
    if (joined || joining || desiredJoinedRef.current) return true;
    if (!key) {
      reportError(huddleText("اختر محادثة صحيحة قبل فتح Huddle.", "Choose a valid conversation before opening Huddle."));
      return false;
    }
    desiredJoinedRef.current = true;
    setJoining(true);
    let joinMicOn = true;
    try {
      setMediaError("");
      setStatus(huddleText("طلب صلاحية الميكروفون...", "Requesting microphone permission..."));
      await ensureLocalStream({ audio: true });
      localStreamRef.current?.getAudioTracks().forEach((track) => { track.enabled = true; });
    } catch (error) {
      joinMicOn = false;
      await ensureLocalStream({ audio: false }).catch(() => null);
      reportError(mediaErrorMessage(error, "الميكروفون") + " " + huddleText("تم الانضمام بدون ميكروفون.", "Joined without a microphone."), { blocking: false });
    }

    try {
      localStreamRef.current?.getVideoTracks().forEach((track) => { track.enabled = false; });
      setMicOn(joinMicOn);
      micOnRef.current = joinMicOn;
      setCameraOn(false);
      cameraOnRef.current = false;
      setScreenOn(false);
      screenOnRef.current = false;
      const socket = connectSocket();
      setStatus(joinMicOn ? huddleText("جاري الاتصال...", "Connecting...") : huddleText("جاري الاتصال بدون ميكروفون...", "Connecting without a microphone..."));
      startJoinTimeout();
      if (socket.connected) emitJoin(socket);
      return true;
    } catch (error) {
      desiredJoinedRef.current = false;
      setJoining(false);
      reportError(mediaErrorMessage(error, "Huddle"));
      stopLocalStream();
      return false;
    }
  }, [key, joined, joining, reportError]);

  const toggleMic = useCallback(async () => {
    if (!joined || mediaActionRef.current) return;
    mediaActionRef.current = true;
    setMediaBusy(true);
    const next = !micOnRef.current;
    try {
      if (next) {
        const audioTracks = localStreamRef.current?.getAudioTracks() || [];
        if (audioTracks.length === 0) await enableAudioTrack();
        else audioTracks.forEach((track) => { track.enabled = true; });
      } else {
        localStreamRef.current?.getAudioTracks().forEach((track) => { track.enabled = false; });
      }
      setMediaError("");
      setMicOn(next);
      micOnRef.current = next;
      getSocket()?.emit("huddle:state", { micOn: next, cameraOn: cameraOnRef.current, screenOn: screenOnRef.current });
    } catch (error) {
      setMicOn(false);
      micOnRef.current = false;
      getSocket()?.emit("huddle:state", { micOn: false, cameraOn: cameraOnRef.current, screenOn: screenOnRef.current });
      reportError(mediaErrorMessage(error, "الميكروفون"), { blocking: false });
    } finally {
      mediaActionRef.current = false;
      setMediaBusy(false);
    }
  }, [joined, reportError]);

  const stopScreenShare = useCallback(async ({ emit = true, restoreCamera = true } = {}) => {
    stopScreenStream();
    const shouldRestoreCamera = restoreCamera && cameraBeforeScreenRef.current;
    setScreenOn(false);
    screenOnRef.current = false;
    if (shouldRestoreCamera) {
      try {
        await enableCameraTrack();
        setCameraOn(true);
        cameraOnRef.current = true;
      } catch (error) {
        await setOutgoingVideoTrack(null);
        setCameraOn(false);
        cameraOnRef.current = false;
        reportError(mediaErrorMessage(error, "الكاميرا"), { blocking: false });
      }
    } else {
      await setOutgoingVideoTrack(null);
      setCameraOn(false);
      cameraOnRef.current = false;
    }
    cameraBeforeScreenRef.current = false;
    if (emit) getSocket()?.emit("huddle:state", { micOn: micOnRef.current, cameraOn: cameraOnRef.current, screenOn: false });
  }, [reportError]);

  const toggleCamera = useCallback(async () => {
    if (!joined || mediaActionRef.current) return;
    mediaActionRef.current = true;
    setMediaBusy(true);
    const next = !cameraOnRef.current;
    try {
      if (next) {
        if (screenOnRef.current) await stopScreenShare({ emit: false, restoreCamera: false });
        await enableCameraTrack();
      } else {
        await setOutgoingVideoTrack(null);
      }
      cameraBeforeScreenRef.current = false;
      setMediaError("");
      setCameraOn(next);
      cameraOnRef.current = next;
      setScreenOn(false);
      screenOnRef.current = false;
      getSocket()?.emit("huddle:state", { micOn: micOnRef.current, cameraOn: next, screenOn: false });
    } catch (error) {
      setCameraOn(false);
      cameraOnRef.current = false;
      getSocket()?.emit("huddle:state", { micOn: micOnRef.current, cameraOn: false, screenOn: false });
      reportError(mediaErrorMessage(error, "الكاميرا"), { blocking: false });
    } finally {
      mediaActionRef.current = false;
      setMediaBusy(false);
    }
  }, [joined, reportError, stopScreenShare]);

  const toggleScreen = useCallback(async () => {
    if (!joined || mediaActionRef.current) return;
    mediaActionRef.current = true;
    setMediaBusy(true);
    try {
      if (screenOnRef.current) {
        await stopScreenShare({ emit: true, restoreCamera: true });
        setStatus(huddleText("متصل الآن", "Connected now"));
        return;
      }
      if (!navigator.mediaDevices?.getDisplayMedia) {
        reportError(huddleText("المتصفح لا يدعم مشاركة الشاشة.", "This browser does not support screen sharing."), { blocking: false });
        return;
      }
      setMediaError("");
      setStatus(huddleText("جاري بدء مشاركة الشاشة...", "Starting screen share..."));
      cameraBeforeScreenRef.current = cameraOnRef.current;
      const displayStream = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: false });
      const [screenTrack] = displayStream.getVideoTracks();
      if (!screenTrack) throw new Error(huddleText("تعذر الحصول على شاشة للمشاركة.", "Could not obtain a screen to share."));
      screenStreamRef.current = displayStream;
      screenTrack.onended = () => {
        if (!screenOnRef.current) return;
        stopScreenShare({ emit: true, restoreCamera: true }).catch(() => null);
      };
      await setOutgoingVideoTrack(screenTrack);
      setCameraOn(false);
      cameraOnRef.current = false;
      setScreenOn(true);
      screenOnRef.current = true;
      setStatus(huddleText("متصل الآن", "Connected now"));
      getSocket()?.emit("huddle:state", { micOn: micOnRef.current, cameraOn: false, screenOn: true });
    } catch (error) {
      cameraBeforeScreenRef.current = false;
      const message = error?.name === "NotAllowedError"
        ? huddleText("تم رفض صلاحية مشاركة الشاشة. اسمح للمتصفح بالمشاركة ثم حاول مرة أخرى.", "Screen-sharing permission was denied. Allow browser sharing, then try again.")
        : (error?.message || huddleText("تعذر بدء مشاركة الشاشة.", "Could not start screen sharing."));
      reportError(message, { blocking: false });
    } finally {
      mediaActionRef.current = false;
      setMediaBusy(false);
    }
  }, [joined, reportError, stopScreenShare]);

  useEffect(() => {
    if (!key) return undefined;
    const socket = connectSocket();

    const onJoined = ({ room, participants: existingParticipants = [] } = {}) => {
      clearJoinTimeout();
      roomRef.current = room || key;
      desiredJoinedRef.current = true;
      setJoining(false);
      setJoined(true);
      setMediaError("");
      setStatus(huddleText("متصل الآن", "Connected now"));
      setParticipants(existingParticipants.filter((participant) => participant.socketId !== socket.id));
      existingParticipants
        .filter((participant) => participant.socketId && participant.socketId !== socket.id)
        .forEach((participant) => createOffer(participant.socketId).catch(() => null));
    };

    const onPeerJoined = ({ participant } = {}) => {
      if (!participant?.socketId || participant.socketId === socket.id) return;
      setParticipants((prev) => upsertParticipant(prev, participant));
    };
    const onPeerLeft = ({ socketId } = {}) => {
      if (!socketId) return;
      closePeer(socketId);
      setParticipants((prev) => prev.filter((participant) => participant.socketId !== socketId));
    };
    const onPeerState = ({ participant } = {}) => {
      if (!participant?.socketId || participant.socketId === socket.id) return;
      setParticipants((prev) => upsertParticipant(prev, participant));
    };
    const onSignal = (payload) => handleSignal(payload);
    const onHuddleError = ({ message } = {}) => {
      clearJoinTimeout();
      desiredJoinedRef.current = false;
      roomRef.current = "";
      setJoining(false);
      setJoined(false);
      closeAllPeers();
      stopLocalStream();
      reportError(message || huddleText("تعذر الاتصال بالـ Huddle.", "Could not connect to Huddle."));
    };
    const onAccessRevoked = () => {
      desiredJoinedRef.current = false;
      clearJoinTimeout();
      roomRef.current = "";
      closeAllPeers();
      stopLocalStream();
      setJoining(false);
      setJoined(false);
      setParticipants([]);
      reportError(huddleText("تم إنهاء Huddle لأن صلاحية المحادثة تغيرت.", "Huddle ended because chat access changed."));
    };
    const onDisconnect = () => {
      if (!desiredJoinedRef.current) return;
      roomRef.current = "";
      closeAllPeers();
      setJoined(false);
      setJoining(true);
      setStatus(huddleText("انقطع الاتصال. جاري إعادة الاتصال...", "Connection lost. Reconnecting..."));
    };
    const onConnect = () => {
      if (!desiredJoinedRef.current || roomRef.current) return;
      setJoining(true);
      setStatus(huddleText("جاري إعادة الاتصال...", "Reconnecting..."));
      emitJoin(socket);
    };

    socket.on("huddle:joined", onJoined);
    socket.on("huddle:peer-joined", onPeerJoined);
    socket.on("huddle:peer-left", onPeerLeft);
    socket.on("huddle:peer-state", onPeerState);
    socket.on("huddle:signal", onSignal);
    socket.on("huddle:error", onHuddleError);
    socket.on("huddle:access-revoked", onAccessRevoked);
    socket.on("disconnect", onDisconnect);
    socket.on("connect", onConnect);

    return () => {
      socket.off("huddle:joined", onJoined);
      socket.off("huddle:peer-joined", onPeerJoined);
      socket.off("huddle:peer-left", onPeerLeft);
      socket.off("huddle:peer-state", onPeerState);
      socket.off("huddle:signal", onSignal);
      socket.off("huddle:error", onHuddleError);
      socket.off("huddle:access-revoked", onAccessRevoked);
      socket.off("disconnect", onDisconnect);
      socket.off("connect", onConnect);
    };
  }, [key, reportError]);

  useEffect(() => () => leave(), [leave]);

  useEffect(() => {
    if (desiredJoinedRef.current) leave();
  }, [key]);

  return {
    joined,
    joining,
    mediaBusy,
    micOn,
    cameraOn,
    screenOn,
    participants,
    remoteStreams,
    localVideoRef,
    status,
    mediaError,
    join,
    leave,
    toggleMic,
    toggleCamera,
    toggleScreen,
  };
}
'''
HOOK.write_text(hook, encoding="utf-8")

chat = CHAT.read_text(encoding="utf-8")
old_sig = 'function HuddlePanel({ open, roomLabel, userName, joined, micOn, cameraOn, screenOn, participants = [], remoteStreams = {}, localVideoRef = null, connectionStatus = "", mediaError = "", onClose, onJoin, onLeave, onToggleMic, onToggleCamera, onToggleScreen, contained = false }) {'
new_sig = 'function HuddlePanel({ open, roomLabel, userName, joined, joining = false, mediaBusy = false, micOn, cameraOn, screenOn, participants = [], remoteStreams = {}, localVideoRef = null, connectionStatus = "", mediaError = "", onClose, onJoin, onLeave, onToggleMic, onToggleCamera, onToggleScreen, contained = false }) {'
if old_sig in chat:
    chat = chat.replace(old_sig, new_sig, 1)

panel_root = '    <div className={contained ? "tcs-v5-contained-huddle absolute bottom-2.5 left-2.5 z-40 w-[340px] max-w-[calc(100%-20px)]" : "fixed inset-x-2.5 bottom-2.5 z-40 sm:inset-x-auto sm:left-5 sm:w-[340px]"} dir={huddleLang === "en" ? "ltr" : "rtl"}>'
panel_root_new = '    <div data-tcs-huddle-flow="v1" className={contained ? "tcs-v5-contained-huddle absolute bottom-2.5 left-2.5 z-40 w-[340px] max-w-[calc(100%-20px)]" : "fixed inset-x-2.5 bottom-2.5 z-40 sm:inset-x-auto sm:left-5 sm:w-[340px]"} dir={huddleLang === "en" ? "ltr" : "rtl"}>'
if 'data-tcs-huddle-flow="v1"' not in chat:
    if panel_root not in chat:
        raise SystemExit(f"{PATCH}: Huddle root anchor missing")
    chat = chat.replace(panel_root, panel_root_new, 1)

h_start = chat.find("function HuddlePanel(")
h_end = chat.find("const failedImagePreviewIds", h_start)
if h_start < 0 or h_end < 0:
    raise SystemExit(f"{PATCH}: HuddlePanel bounds missing")
huddle_panel = chat[h_start:h_end]
huddle_panel = huddle_panel.replace("disabled={!joined}", "disabled={!joined || mediaBusy}")

join_old = '''              <button type="button" onClick={onJoin} className="inline-flex flex-1 items-center justify-center gap-2 rounded-xl bg-zinc-950 px-3.5 py-2.5 text-sm font-black text-white hover:bg-zinc-800 dark:bg-white dark:text-zinc-950">
                <Phone size={16} /> {huddleLang === "en" ? "Join Huddle" : "انضم إلى Huddle"}
              </button>'''
join_new = '''              <button type="button" onClick={onJoin} disabled={joining} className="inline-flex flex-1 items-center justify-center gap-2 rounded-xl bg-zinc-950 px-3.5 py-2.5 text-sm font-black text-white hover:bg-zinc-800 disabled:cursor-wait disabled:opacity-60 dark:bg-white dark:text-zinc-950">
                <Phone size={16} /> {joining ? (huddleLang === "en" ? "Connecting..." : "جاري الاتصال...") : (huddleLang === "en" ? "Join Huddle" : "انضم إلى Huddle")}
              </button>'''
if "disabled={joining}" not in huddle_panel:
    if join_old not in huddle_panel:
        raise SystemExit(f"{PATCH}: Huddle join button anchor missing")
    huddle_panel = huddle_panel.replace(join_old, join_new, 1)
chat = chat[:h_start] + huddle_panel + chat[h_end:]

destruct = '''    joined: huddleJoined,
    micOn: huddleMicOn,'''
destruct_new = '''    joined: huddleJoined,
    joining: huddleJoining,
    mediaBusy: huddleMediaBusy,
    micOn: huddleMicOn,'''
if "joining: huddleJoining" not in chat:
    if destruct not in chat:
        raise SystemExit(f"{PATCH}: Huddle destructure anchor missing")
    chat = chat.replace(destruct, destruct_new, 1)

call = '''        joined={huddleJoined}
        micOn={huddleMicOn}'''
call_new = '''        joined={huddleJoined}
        joining={huddleJoining}
        mediaBusy={huddleMediaBusy}
        micOn={huddleMicOn}'''
if "joining={huddleJoining}" not in chat:
    if call not in chat:
        raise SystemExit(f"{PATCH}: Huddle call anchor missing")
    chat = chat.replace(call, call_new, 1)

CHAT.write_text(chat, encoding="utf-8")

sockets = SOCKETS.read_text(encoding="utf-8")
helper_anchor = "function huddleParticipant(socket) {"
helper_new = '''const HUDDLE_SIGNAL_TYPES = new Set(["offer", "answer", "candidate"]);

async function assertCurrentHuddleAccess(socket) {
  const room = socket.data?.huddleRoom;
  const context = socket.data?.huddleContext;
  if (!room || !context) throw new Error("No active Huddle");
  const now = Date.now();
  if (socket.data?.huddleAccessCheckedAt && now - socket.data.huddleAccessCheckedAt < 5000) return { room, context };
  const resolved = await assertHuddleAccess(socket.user, context);
  if (resolved.room !== room) throw new Error("Huddle scope changed");
  socket.data.huddleAccessCheckedAt = now;
  return resolved;
}

function huddleParticipant(socket) {'''
if "async function assertCurrentHuddleAccess(" not in sockets:
    if helper_anchor not in sockets:
        raise SystemExit(f"{PATCH}: socket helper anchor missing")
    sockets = sockets.replace(helper_anchor, helper_new, 1)

join_state_anchor = '''        socket.data.huddleContext = context;
        socket.data.huddleState = {'''
join_state_new = '''        socket.data.huddleContext = context;
        socket.data.huddleAccessCheckedAt = Date.now();
        socket.data.huddleState = {'''
if "huddleAccessCheckedAt = Date.now()" not in sockets:
    if join_state_anchor not in sockets:
        raise SystemExit(f"{PATCH}: socket join state anchor missing")
    sockets = sockets.replace(join_state_anchor, join_state_new, 1)

state_start = sockets.find('    socket.on("huddle:state", (state = {}) => {')
tws_start = sockets.find('    // TWS Phase 5 collaboration', state_start)
if state_start < 0 or tws_start < 0:
    raise SystemExit(f"{PATCH}: socket handler bounds missing")
new_handlers = '''    socket.on("huddle:state", async (state = {}) => {
      try {
        await assertCurrentHuddleAccess(socket);
        const room = socket.data.huddleRoom;
        socket.data.huddleState = {
          micOn: state.micOn !== false,
          cameraOn: Boolean(state.cameraOn),
          screenOn: Boolean(state.screenOn),
        };
        socket.to(room).emit("huddle:peer-state", { participant: huddleParticipant(socket) });
      } catch {
        leaveHuddleRoom(io, socket);
        socket.emit("huddle:access-revoked");
      }
    });

    socket.on("huddle:signal", async ({ targetSocketId, type, data } = {}) => {
      try {
        await assertCurrentHuddleAccess(socket);
        const room = socket.data.huddleRoom;
        if (!targetSocketId || !HUDDLE_SIGNAL_TYPES.has(type)) return;
        let signalSize = 0;
        try { signalSize = JSON.stringify(data ?? null).length; } catch { return; }
        if (signalSize > 200000) return;
        const targetSocket = io.sockets.sockets.get(targetSocketId);
        if (!targetSocket || targetSocket.data?.huddleRoom !== room) return;
        io.to(targetSocketId).emit("huddle:signal", {
          fromSocketId: socket.id,
          participant: huddleParticipant(socket),
          type,
          data,
        });
      } catch {
        leaveHuddleRoom(io, socket);
        socket.emit("huddle:access-revoked");
      }
    });

'''
sockets = sockets[:state_start] + new_handlers + sockets[tws_start:]

leave_cleanup = '''  socket.data.huddleState = null;
}'''
leave_cleanup_new = '''  socket.data.huddleState = null;
  socket.data.huddleAccessCheckedAt = null;
}'''
if "socket.data.huddleAccessCheckedAt = null;" not in sockets:
    sockets = sockets.replace(leave_cleanup, leave_cleanup_new, 1)

SOCKETS.write_text(sockets, encoding="utf-8")

route = CHAT_ROUTE.read_text(encoding="utf-8")
block_start = route.find("  for (const userId of removedMemberIds) {")
block_end = route.find("  for (const member of updated.members)", block_start)
if block_start < 0 or block_end < 0:
    raise SystemExit(f"{PATCH}: group revoke block missing")
old_block = route[block_start:block_end]
if 'huddle:access-revoked' not in old_block:
    new_block = '''  for (const userId of removedMemberIds) {
    emitToRoom(req, "user:" + userId, "conversation:removed", { id: conversationId });
    const userRoom = "user:" + userId;
    const conversationRoom = "conversation:" + conversationId;
    const huddleRoom = "huddle:conversation:" + conversationId;
    const revokedSockets = io ? await io.in(userRoom).fetchSockets() : [];
    for (const memberSocket of revokedSockets) {
      if (memberSocket.data?.huddleRoom === huddleRoom) {
        io.to(huddleRoom).except(memberSocket.id).emit("huddle:peer-left", { socketId: memberSocket.id, userId });
        memberSocket.emit("huddle:access-revoked");
        await memberSocket.leave(huddleRoom);
      }
      await memberSocket.leave(conversationRoom);
    }
  }
'''
    route = route[:block_start] + new_block + route[block_end:]

CHAT_ROUTE.write_text(route, encoding="utf-8")

print(f"PATCH={PATCH}")
print("JOIN_GUARD=YES")
print("JOIN_TIMEOUT=YES")
print("SOCKET_RECONNECT=YES")
print("ICE_CANDIDATE_QUEUE=YES")
print("SIGNAL_RACE_GUARD=YES")
print("MEDIA_ACTION_GUARD=YES")
print("SCREEN_CAMERA_RESTORE=YES")
print("ACCESS_REVALIDATION=YES")
print("GROUP_REMOVAL_HUDDLE_REVOKE=YES")
print("DB_SCHEMA_UNCHANGED=YES")
print(f"BACKUP={backup}")
print("NEXT=BUILD_RESTART_BACKEND_DEPLOY")
