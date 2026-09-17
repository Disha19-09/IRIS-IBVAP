import { ShieldAlert, Clock, Camera, User, Car, MapPin,} from "lucide-react";
import { useAlerts } from "../api/useAlerts.js";
import { getEventTypeLabel } from "../api/api.js";

function SecurityEvents() {
  const { alerts, connected } = useAlerts();
  const countByType = (types) => alerts.filter((alert) => types.includes(alert.event_type)).length;
  const securityEvents = alerts.filter((alert) => alert.event_type !== "tracking_update");
  return (
    <div className="events-page">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <span className="eyebrow">EVENT MONITORING</span>
          <h1>Security Events</h1>
          <p>
            Review AI-detected security events from the active surveillance stream.
          </p>
        </div>

        <div className="system-badge">
          <span className="status-dot"></span>
          {connected ? "EVENT MONITORING ACTIVE" : "BACKEND OFFLINE"}
        </div>
      </div>

      {/* Event Summary */}
      <section className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon alert-icon">
            <ShieldAlert size={18} />
          </div>

          <div>
            <span className="stat-label">TOTAL EVENTS</span>
            <strong>{securityEvents.length}</strong>
            <small>Current session</small>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">
            <User size={18} />
          </div>

          <div>
            <span className="stat-label">LOITERING</span>
            <strong>{countByType(["loitering", "night_loitering"])}</strong>
            <small>Detected events</small>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">
            <MapPin size={18} />
          </div>

          <div>
            <span className="stat-label">FENCE CROSSINGS</span>
            <strong>{countByType(["virtual_fence_crossing", "night_movement_crossing"])}</strong>
            <small>Virtual fence</small>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">
            <Clock size={18} />
          </div>

          <div>
            <span className="stat-label">NIGHT EVENTS</span>
            <strong>{countByType(["night_movement_crossing", "night_loitering"])}</strong>
            <small>19:00 – 06:00</small>
          </div>
        </div>
      </section>

      {/* Event Log */}
      <section className="panel events-panel">
        <div className="panel-header">
          <div>
            <span className="panel-kicker">SECURITY EVENT LOG</span>
            <h2>Detected Events</h2>
          </div>

          <ShieldAlert size={18} />
        </div>

        {securityEvents.length ? securityEvents.map((alert) => (
          <div className="pipeline-item" key={alert.id}>
            <span>{getEventTypeLabel(alert.event_type)} · {alert.object_type || "unknown"}</span>
            <span className="pipeline-status">{new Date(alert.timestamp).toLocaleTimeString()}</span>
          </div>
        )) : (
          <div className="events-empty">
            <ShieldAlert size={28} />
            <p>No security events recorded.</p>
            <span>AI-detected fence crossings, loitering, and person movement events will appear here.</span>
          </div>
        )}
      </section>

      {/* Event Types */}
      <section className="event-types-grid">
        <div className="panel event-type-card">
          <div className="event-type-icon">
            <MapPin size={18} />
          </div>

          <div>
            <span className="panel-kicker">EVENT TYPE</span>
            <h3>Virtual Fence Crossing</h3>
            <p>
              Directional crossing of the configured virtual security boundary.
            </p>
          </div>
        </div>

        <div className="panel event-type-card">
          <div className="event-type-icon">
            <User size={18} />
          </div>

          <div>
            <span className="panel-kicker">EVENT TYPE</span>
            <h3>Loitering</h3>
            <p>
              Object remains on the configured fence side beyond the defined
              time threshold.
            </p>
          </div>
        </div>

        <div className="panel event-type-card">
          <div className="event-type-icon">
            <Clock size={18} />
          </div>

          <div>
            <span className="panel-kicker">EVENT TYPE</span>
            <h3>Person Movement</h3>
            <p>
              Fence-crossing activity detected during the configured night
              period.
            </p>
          </div>
        </div>

        <div className="panel event-type-card">
          <div className="event-type-icon">
            <Camera size={18} />
          </div>

          <div>
            <span className="panel-kicker">SOURCE</span>
            <h3>CAM-01</h3>
            <p>
              Events generated from the active CCTV / RTSP surveillance stream.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}

export default SecurityEvents;