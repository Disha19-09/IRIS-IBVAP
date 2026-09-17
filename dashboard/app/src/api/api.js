export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const AUTH_TOKEN_KEY = "iris_ibvap_access_token";
const REFRESH_TOKEN_KEY = "iris_ibvap_refresh_token";

export function setAuthToken(accessToken, refreshToken) {
  localStorage.setItem(AUTH_TOKEN_KEY, accessToken || "");
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken || "");
}

export function getAuthToken() {
  return localStorage.getItem(AUTH_TOKEN_KEY) || "";
}

export function clearAuthToken() {
  localStorage.removeItem(AUTH_TOKEN_KEY);
  localStorage.removeItem(REFRESH_TOKEN_KEY);
}

export function getAuthHeaders(additionalHeaders = {}) {
  const token = getAuthToken();
  return {
    ...additionalHeaders,
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

export async function getAlerts(limit = 100) {
  const response = await fetch(`${API_BASE_URL}/alerts?limit=${limit}`, {
    cache: "no-store",
    headers: getAuthHeaders(),
  });

  if (!response.ok) {
    if (response.status === 401 || response.status === 403) {
      throw new Error("AUTH_REQUIRED");
    }
    throw new Error("Failed to fetch alerts");
  }

  return response.json();
}

export async function getAlertCount() {
  const response = await fetch(`${API_BASE_URL}/alerts/count`, {
    cache: "no-store",
    headers: getAuthHeaders(),
  });

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
    night_movement_crossing: "Person Movement",
  };

  return labels[eventType] || eventType;
}