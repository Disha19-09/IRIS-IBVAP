import { useEffect, useRef, useState } from "react";

import { clearAuthToken, getAlerts, getAlertsWebSocketUrl } from "./api.js";

export function useAlerts(limit = 100) {
  const [alerts, setAlerts] = useState([]);
  const [mockAlerts, setMockAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [connected, setConnected] = useState(false);
  const mockIndex = useRef(0);

  useEffect(() => {
    let active = true;
    let socket;
    let reconnectTimer;
    let pollTimer;
    let mockTimer;

    const mockTemplates = [
      { event_type: "virtual_fence_crossing", object_type: "person", track_id: 201 },
      { event_type: "loitering", object_type: "person", track_id: 202 },
      { event_type: "virtual_fence_crossing", object_type: "car", track_id: 203 },
      { event_type: "night_movement_crossing", object_type: "person", track_id: 204 },
    ];

    const hasRecentSecurityEvent = (incomingAlerts) => incomingAlerts.some((alert) => (
      alert.event_type !== "tracking_update"
      && Date.now() - new Date(alert.timestamp).getTime() <= 60 * 1000
    ));

    const addMockAlert = () => {
      const template = mockTemplates[mockIndex.current % mockTemplates.length];
      mockIndex.current += 1;
      setMockAlerts((currentAlerts) => [
        ...currentAlerts,
        {
          ...template,
          id: `mock-${Date.now()}`,
          camera_id: "CAM_01",
          confidence: 0.88,
          timestamp: new Date().toISOString(),
          is_mock: true,
        },
      ].slice(-limit));
    };

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
        if (hasRecentSecurityEvent(incomingAlerts)) {
          setMockAlerts([]);
        }
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

    refreshAlerts();
    pollTimer = window.setInterval(refreshAlerts, 1000);
    mockTimer = window.setInterval(addMockAlert, 5000);
    const firstMockTimer = window.setTimeout(addMockAlert, 1500);

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
          if (!active) return;
          mergeAlerts([alert]);
          if (alert.event_type !== "tracking_update") {
            setMockAlerts([]);
          }
        };
      } catch {
        reconnectTimer = window.setTimeout(connect, 2000);
      }
    };

    connect();

    return () => {
      active = false;
      window.clearInterval(pollTimer);
      window.clearInterval(mockTimer);
      window.clearTimeout(firstMockTimer);
      window.clearTimeout(reconnectTimer);
      socket?.close();
    };
  }, [limit]);

  return { alerts: [...alerts, ...mockAlerts].sort((left, right) => new Date(right.timestamp) - new Date(left.timestamp)), loading, connected };
}