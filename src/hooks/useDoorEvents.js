import { useEffect, useRef, useCallback, useState } from 'react';

const RECONNECT_DELAY = 3000;

const useDoorEvents = ({ onEvent }) => {
  const wsRef = useRef(null);
  const reconnectTimer = useRef(null);
  const [connected, setConnected] = useState(false);

  const getWsUrl = () => {
    const base = window.location.hostname || '127.0.0.1';
    // 开发环境连后端 8000 端口，生产环境通过 Nginx 代理（同端口）
    if (import.meta.env.DEV) {
      return `ws://${base}:8000/ws/door-events/`;
    }
    const port = window.location.port;
    const portStr = port ? `:${port}` : '';
    return `ws://${base}${portStr}/ws/door-events/`;
  };

  const connect = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState <= 1) return;

    const ws = new WebSocket(getWsUrl());
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
    };

    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        onEvent?.(data);
      } catch (err) {
      }
    };

    ws.onclose = () => {
      setConnected(false);
      reconnectTimer.current = setTimeout(connect, RECONNECT_DELAY);
    };

    ws.onerror = (err) => {
      ws.close();
    };
  }, [onEvent]);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return { connected };
};

export default useDoorEvents;
