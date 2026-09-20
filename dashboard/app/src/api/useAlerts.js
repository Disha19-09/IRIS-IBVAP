import { useEffect, useState } from "react";

import { clearAuthToken, getAlerts, getAlertsWebSocketUrl } from "./api.js";

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

    const replaceAlerts = (incomingAlerts) => {
      setAlerts(
        [...incomingAlerts]
          .sort((left, right) => new Date(right.timestamp) - new Date(left.timestamp))
          .slice(0, limit)
      );
    };

    const refreshAlerts = () => getAlerts(limit)
      .then((incomingAlerts) => {
        if (!active) return;
        replaceAlerts(incomingAlerts);
      })
      .catch((error) => {
        if (error.message === "AUTH_REQUIRED") {
          clearAuthToken();
          window.location.assign("/login");
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    // Initial fetch
    refreshAlerts();
    
    // Poll every 1 second as fallback (reduced from 2 seconds)
    pollTimer = window.setInterval(refreshAlerts, 1000);

    // WebSocket connection for real-time updates
    const connect = () => {
      if (!active) return;

      try {
        socket = new WebSocket(getAlertsWebSocketUrl());
        
        socket.onopen = () => {
          if (active) {
            setConnected(true);
            console.log("[WebSocket] Connected to alerts stream");
          }
        };
        
        socket.onclose = () => {
          if (!active) return;
          setConnected(false);
          console.log("[WebSocket] Disconnected, reconnecting in 1s...");
          reconnectTimer = window.setTimeout(connect, 1000);
        };
        
        socket.onerror = (error) => {
          if (active) {
            setConnected(false);
            console.error("[WebSocket] Error:", error);
          }
        };
        
        socket.onmessage = (message) => {
          if (!active) return;
          try {
            const alert = JSON.parse(message.data);
            console.log("[WebSocket] Received alert:", alert);
            mergeAlerts([alert]);
          } catch (error) {
            console.error("[WebSocket] Failed to parse message:", error);
          }
        };
      } catch (error) {
        console.error("[WebSocket] Connection failed:", error);
        reconnectTimer = window.setTimeout(connect, 1000);
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