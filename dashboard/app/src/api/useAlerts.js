import { useEffect, useState } from "react";

import { getAlerts, getAlertsWebSocketUrl } from "./api.js";

export function useAlerts(limit = 100) {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    let active = true;
    let socket;
    let reconnectTimer;
    let pollTimer;

    const mergeAlerts = (incomingAlerts) => {
      setAlerts((currentAlerts) => {
        const byId = new Map(currentAlerts.map((alert) => [alert.id, alert]));
        incomingAlerts.forEach((alert) => byId.set(alert.id, alert));
        return [...byId.values()]
          .sort((left, right) => new Date(right.timestamp) - new Date(left.timestamp))
          .slice(0, limit);
      });
    };

    const refreshAlerts = () => getAlerts(limit)
      .then((incomingAlerts) => {
        if (active) mergeAlerts(incomingAlerts);
      })
      .catch(() => {
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    refreshAlerts();
    pollTimer = window.setInterval(refreshAlerts, 2000);

    const connect = () => {
      if (!active) return;

      try {
        socket = new WebSocket(getAlertsWebSocketUrl());
        socket.onopen = () => active && setConnected(true);
        socket.onclose = () => {
          if (!active) return;
          setConnected(false);
          reconnectTimer = window.setTimeout(connect, 2000);
        };
        socket.onerror = () => active && setConnected(false);
        socket.onmessage = (message) => {
          const alert = JSON.parse(message.data);
          if (active) mergeAlerts([alert]);
        };
      } catch {
        reconnectTimer = window.setTimeout(connect, 2000);
      }
    };

    connect();

    return () => {
      active = false;
      window.clearInterval(pollTimer);
      window.clearTimeout(reconnectTimer);
      socket?.close();
    };
  }, [limit]);

  return { alerts, loading, connected };
}