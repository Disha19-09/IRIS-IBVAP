export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export async function getAlerts(limit = 100) {
  const response = await fetch(`${API_BASE_URL}/alerts?limit=${limit}`, { cache: "no-store" });

  if (!response.ok) {
    throw new Error("Failed to fetch alerts");
  }

  return response.json();
}

export async function getAlertCount() {
  const response = await fetch(`${API_BASE_URL}/alerts/count`, { cache: "no-store" });

  if (!response.ok) {
    throw new Error("Failed to fetch alert count");
  }

  return response.json();
}

export function getSnapshotUrl(snapshotPath, version) {
  if (!snapshotPath) return null;

  const url = new URL(`${API_BASE_URL}/snapshots/${snapshotPath.replace(/^[/\\]+/, "")}`);
  if (version) url.searchParams.set("v", version);
  return url.toString();
}

export function getAlertsWebSocketUrl() {
  const url = new URL(API_BASE_URL);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  url.pathname = "/ws/alerts";
  return url.toString();
}

export function getEventTypeLabel(eventType) {
  const labels = {
    virtual_fence_crossing: "Virtual Fence Crossing",
    loitering: "Loitering",
    night_movement_crossing: "Night Movement",
  };

  return labels[eventType] || eventType;
}