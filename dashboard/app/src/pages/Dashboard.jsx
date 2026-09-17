import {
  Users,
  Car,
  ShieldAlert,
  Activity,
  Clock,
  AlertTriangle,
  CheckCircle2,
} from "lucide-react";
import { useAlerts } from "../api/useAlerts.js";
import { getEventTypeLabel } from "../api/api.js";
import StreamVideo from "../components/StreamVideo.jsx";

function Dashboard() {
  const { alerts, connected } = useAlerts();
  const people = alerts.filter((alert) => alert.object_type === "person").length;
  const vehicles = alerts.filter((alert) => alert.object_type === "car").length;
  const activeTracks = new Set(alerts.map((alert) => alert.track_id).filter(Boolean)).size;
  const securityEvents = alerts.filter((alert) => alert.event_type !== "tracking_update");
  const activeAlerts = securityEvents.filter((alert) => {
    const timestamp = new Date(alert.timestamp).getTime();
    return Number.isFinite(timestamp) && Date.now() - timestamp <= 60 * 1000;
  });

  function formatAlertTime(timestamp) {
    const date = new Date(timestamp);
    if (!Number.isFinite(date.getTime())) return "TIME UNKNOWN";
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  }

  return (
    <div className="dashboard">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <span className="eyebrow">COMMAND CONSOLE</span>
          <h1>Command Center</h1>
          <p>
            Real-time AI video analytics and security event monitoring.
          </p>
        </div>

        <div className="system-badge">
          <span className="status-dot"></span>
          PROCESSING ACTIVE
        </div>
      </div>

      {/* Detection Summary */}
      <section className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">
            <Users size={18} />
          </div>

          <div>
            <span className="stat-label">PERSONS EVENTS</span>
            <strong>{people}</strong>
            <small>Live stream</small>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">
            <Car size={18} />
          </div>

          <div>
            <span className="stat-label">VEHICLES EVENTS</span>
            <strong>{vehicles}</strong>
            <small>Live stream</small>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">
            <Activity size={18} />
          </div>

          <div>
            <span className="stat-label">TRACKED OBJECTS</span>
            <strong>{activeTracks}</strong>
            <small>ByteTrack </small>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon alert-icon">
            <ShieldAlert size={18} />
          </div>

          <div>
            <span className="stat-label">SECURITY EVENTS</span>
            <strong>{securityEvents.length}</strong>
            <small>Current session</small>
          </div>
        </div>
      </section>

      {/* Main Monitoring Area */}
      <section className="monitoring-grid">
        {/* Live Surveillance */}
        <div className="panel live-panel">
          <div className="panel-header">
            <div>
              <span className="panel-kicker">LIVE SURVEILLANCE</span>
              <h2>CAM-01</h2>
            </div>

            <div className="live-status">
              <span className="status-dot"></span>
              {connected ? "BACKEND LIVE" : "BACKEND OFFLINE"}
            </div>
          </div>

          <div className="video-placeholder">
            <StreamVideo />
          </div>

          <div className="video-footer">
            <span>CAM-01</span>
            <span>RTSP STREAM</span>
            <span>AI PROCESSING</span>
          </div>
        </div>

        {/* Active Alerts */}
        <div className="panel alerts-panel">
          <div className="panel-header">
            <div>
              <span className="panel-kicker">LIVE SECURITY EVENTS</span>
              <h2>Active Alerts</h2>
            </div>

            <AlertTriangle size={18} />
          </div>

          {activeAlerts.length ? activeAlerts.slice(0, 4).map((alert) => (
            <div className="pipeline-item" key={alert.id ?? `${alert.timestamp}-${alert.track_id}`}>
              <span>
                {getEventTypeLabel(alert.event_type) || "Security event"}
                <small className="alert-time">{formatAlertTime(alert.timestamp)}</small>
              </span>
              <span className="pipeline-status">{alert.object_type || "unknown"} · #{alert.track_id ?? "n/a"}</span>
            </div>
          )) : (
            <div className="empty-state">
              <CheckCircle2 size={26} />
              <p>No live alerts</p>
              <span>New events will appear here for 60 seconds.</span>
            </div>
          )}
        </div>
      </section>

      {/* Bottom Section */}
      <section className="bottom-grid">
        {/* Recent Events */}
        <div className="panel">
          <div className="panel-header">
            <div>
              <span className="panel-kicker">EVENT LOG</span>
              <h2>Recent Security Events</h2>
            </div>

            <Clock size={18} />
          </div>

          <div className="event-empty">
            <span>{alerts.length ? `${alerts.length} event${alerts.length === 1 ? "" : "s"} recorded.` : "No events recorded in this session."}</span>
          </div>
        </div>

        {/* Pipeline */}
        <div className="panel pipeline-panel">
          <div className="panel-header">
            <div>
              <span className="panel-kicker">AI PIPELINE</span>
              <h2>Processing Status</h2>
            </div>

            <Activity size={18} />
          </div>

          <div className="pipeline-item">
            <span>Video Ingestion</span>
            <span className="pipeline-status">READY</span>
          </div>

          <div className="pipeline-item">
            <span>YOLOv8 Detection</span>
            <span className="pipeline-status">READY</span>
          </div>

          <div className="pipeline-item">
            <span>ByteTrack</span>
            <span className="pipeline-status">READY</span>
          </div>

          <div className="pipeline-item">
            <span>Event Detection</span>
            <span className="pipeline-status">READY</span>
          </div>
        </div>
      </section>
    </div>
  );
}

export default Dashboard;