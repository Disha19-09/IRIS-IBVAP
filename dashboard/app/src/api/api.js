const API_BASE_URL = "http://127.0.0.1:8000";

export async function getAlerts(limit = 100) {
  const response = await fetch(`${API_BASE_URL}/alerts?limit=${limit}`);

  if (!response.ok) {
    throw new Error("Failed to fetch alerts");
  }

  return response.json();
}

export async function getAlertCount() {
  const response = await fetch(`${API_BASE_URL}/alerts/count`);

  if (!response.ok) {
    throw new Error("Failed to fetch alert count");
  }

  return response.json();
}

export function getSnapshotUrl(snapshotPath) {
  if (!snapshotPath) return null;

  return `${API_BASE_URL}/snapshots/${snapshotPath}`;
}

export function getEventTypeLabel(eventType) {
  const labels = {
    virtual_fence_crossing: "Virtual Fence Crossing",
    loitering: "Loitering",
    night_movement_crossing: "Night Movement",
  };

  return labels[eventType] || eventType;
}