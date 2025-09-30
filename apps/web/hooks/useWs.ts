"use client";

import { useEffect, useRef, useState } from "react";

type UseWsResult = {
  socket: WebSocket | null;
  connected: boolean;
};

export function useWs(path: string): UseWsResult {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const retryRef = useRef(0);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    let cancelled = false;

    const open = () => {
      if (cancelled) {
        return;
      }
      const isHttps = window.location.protocol === "https:";
      const scheme = isHttps ? "wss://" : "ws://";
      const base = scheme + window.location.host;
      const url = new URL(path, base).toString();
      const ws = new WebSocket(url);
      socketRef.current = ws;
      setSocket(ws);

      ws.onopen = () => {
        if (cancelled) return;
        setConnected(true);
        retryRef.current = 0;
      };

      ws.onclose = () => {
        if (cancelled) return;
        setConnected(false);
        const delay = Math.min(1000 * 2 ** retryRef.current, 15000);
        retryRef.current += 1;
        timerRef.current = setTimeout(open, delay);
      };

      ws.onerror = () => {
        ws.close();
      };
    };

    open();

    return () => {
      cancelled = true;
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
      const current = socketRef.current;
      if (current && current.readyState === WebSocket.OPEN) {
        current.close();
      }
      setSocket(null);
      setConnected(false);
    };
  }, [path]);

  return { socket, connected };
}
