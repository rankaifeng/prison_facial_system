import { useEffect, useRef, useCallback, useState } from 'react';

const RECONNECT_DELAY = 3000;

const useDoorEvents = ({ onEvent }) => {
  const wsRef = useRef(null);
  const reconnectTimer = useRef(null);
  const [connected, setConnected] = useState(false);

  const getWsUrl = () => {
    const base = window.location.hostname || '127.0.0.1';
    return `ws://${base}:8000/ws/door-events/`;
  };

  const connect = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState <= 1) return;

    const ws = new WebSocket(getWsUrl());
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      console.log('[WebSocket] 已连接大华事件服务');
    };

    ws.onmessage = (e) => {
      try {
        const data = JSON.parse(e.data);
        if (data?.UserID) {
          console.log('[WebSocket] 收到事件:', data?.UserID);
          onEvent?.(data?.UserID);
        }

      } catch (err) {
        console.warn('[WebSocket] 解析消息失败:', e.data);
      }
    };

    ws.onclose = () => {
      setConnected(false);
      console.log('[WebSocket] 连接断开，自动重连...');
      reconnectTimer.current = setTimeout(connect, RECONNECT_DELAY);
    };

    ws.onerror = (err) => {
      console.error('[WebSocket] 错误:', err);
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
