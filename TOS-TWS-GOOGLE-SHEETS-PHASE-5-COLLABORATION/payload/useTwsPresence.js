import { useCallback, useEffect, useRef, useState } from "react";
import { getSocket } from "../../lib/socket";

/**
 * TWS document presence + Phase 5 realtime collaboration signals.
 * Persistent sheet mutations still go through authenticated HTTP endpoints;
 * Socket.IO is used for presence, remote selections and fan-out of committed
 * sheet patches so editors do not overwrite each other's unrelated cells.
 */
export function useTwsPresence(documentId, userId, handlers = {}) {
  const [peers, setPeers] = useState([]);
  const [peerSelections, setPeerSelections] = useState({});
  const [lastRemoteChange, setLastRemoteChange] = useState(null);
  const handlersRef = useRef(handlers);
  handlersRef.current = handlers;

  const emitSelection = useCallback((selection = {}) => {
    if (!documentId) return;
    const socket = getSocket();
    if (!socket) return;
    socket.emit("tws-doc:selection", {
      documentId,
      sheetId: selection.sheetId || null,
      anchorRef: selection.anchorRef || null,
      focusRef: selection.focusRef || null,
    });
  }, [documentId]);

  useEffect(() => {
    if (!documentId) return undefined;
    const socket = getSocket();
    if (!socket) return undefined;

    function isSelf(actorId) {
      return actorId && userId && actorId === userId;
    }

    function handleJoined({ peers: initialPeers = [] } = {}) {
      setPeers(initialPeers);
    }
    function handlePeerJoined({ peer } = {}) {
      if (!peer) return;
      setPeers((prev) => (prev.some((item) => item.socketId === peer.socketId) ? prev : [...prev, peer]));
    }
    function handlePeerLeft({ socketId } = {}) {
      setPeers((prev) => prev.filter((item) => item.socketId !== socketId));
      setPeerSelections((prev) => {
        if (!socketId || !Object.prototype.hasOwnProperty.call(prev, socketId)) return prev;
        const next = { ...prev };
        delete next[socketId];
        return next;
      });
    }
    function handleContentUpdated(detail = {}) {
      if (isSelf(detail.actorId)) return;
      setLastRemoteChange({ type: "content", ...detail });
      handlersRef.current.onContentUpdated?.(detail);
    }
    function handleSheetPatch(detail = {}) {
      if (isSelf(detail.actorId)) return;
      setLastRemoteChange({ type: "sheet-patch", ...detail });
      handlersRef.current.onSheetPatch?.(detail);
    }
    function handleSelection(detail = {}) {
      if (isSelf(detail.actorId) || !detail.socketId) return;
      setPeerSelections((prev) => ({
        ...prev,
        [detail.socketId]: {
          socketId: detail.socketId,
          actorId: detail.actorId || detail.peer?.id || null,
          actorName: detail.actorName || detail.peer?.name || "",
          avatarUrl: detail.peer?.avatarUrl || null,
          sheetId: detail.sheetId || null,
          anchorRef: detail.anchorRef || null,
          focusRef: detail.focusRef || null,
          at: detail.at || new Date().toISOString(),
        },
      }));
      handlersRef.current.onSelection?.(detail);
    }
    function handleCommentsUpdated(detail = {}) {
      handlersRef.current.onCommentsUpdated?.(detail);
    }
    function handlePermissionsUpdated(detail = {}) {
      handlersRef.current.onPermissionsUpdated?.(detail);
    }
    function handleShareLinksUpdated(detail = {}) {
      handlersRef.current.onShareLinksUpdated?.(detail);
    }
    function handleMetaUpdated(detail = {}) {
      if (isSelf(detail.actorId)) return;
      handlersRef.current.onMetaUpdated?.(detail);
    }
    function handleTrashed(detail = {}) {
      if (isSelf(detail.actorId)) return;
      handlersRef.current.onTrashed?.(detail);
    }

    socket.emit("tws-doc:join", { documentId });
    socket.on("tws-doc:joined", handleJoined);
    socket.on("tws-doc:peer-joined", handlePeerJoined);
    socket.on("tws-doc:peer-left", handlePeerLeft);
    socket.on("tws-doc:content-updated", handleContentUpdated);
    socket.on("tws-doc:sheet-patch", handleSheetPatch);
    socket.on("tws-doc:selection", handleSelection);
    socket.on("tws-doc:comments-updated", handleCommentsUpdated);
    socket.on("tws-doc:permissions-updated", handlePermissionsUpdated);
    socket.on("tws-doc:share-links-updated", handleShareLinksUpdated);
    socket.on("tws-doc:meta-updated", handleMetaUpdated);
    socket.on("tws-doc:trashed", handleTrashed);

    return () => {
      socket.emit("tws-doc:leave", { documentId });
      socket.off("tws-doc:joined", handleJoined);
      socket.off("tws-doc:peer-joined", handlePeerJoined);
      socket.off("tws-doc:peer-left", handlePeerLeft);
      socket.off("tws-doc:content-updated", handleContentUpdated);
      socket.off("tws-doc:sheet-patch", handleSheetPatch);
      socket.off("tws-doc:selection", handleSelection);
      socket.off("tws-doc:comments-updated", handleCommentsUpdated);
      socket.off("tws-doc:permissions-updated", handlePermissionsUpdated);
      socket.off("tws-doc:share-links-updated", handleShareLinksUpdated);
      socket.off("tws-doc:meta-updated", handleMetaUpdated);
      socket.off("tws-doc:trashed", handleTrashed);
      setPeers([]);
      setPeerSelections({});
    };
  }, [documentId, userId]);

  return { peers, peerSelections, lastRemoteChange, emitSelection };
}
