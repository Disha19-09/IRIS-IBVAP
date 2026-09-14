import { ShieldAlert, Clock, Camera, User, Car, MapPin,} from "lucide-react";

function SecurityEvents() {
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
          EVENT MONITORING ACTIVE
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
            <strong>—</strong>
            <small>Current session</small>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">
            <User size={18} />
          </div>

          <div>
            <span className="stat-label">LOITERING</span>
            <strong>—</strong>
            <small>Detected events</small>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">
            <MapPin size={18} />
          </div>

          <div>
            <span className="stat-label">FENCE CROSSINGS</span>
            <strong>—</strong>
            <small>Virtual fence</small>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">
            <Clock size={18} />
          </div>

          <div>
            <span className="stat-label">NIGHT EVENTS</span>
            <strong>—</strong>
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

        <div className="events-empty">
          <ShieldAlert size={28} />

          <p>No security events recorded.</p>

          <span>
            AI-detected fence crossings, loitering, and night movement events
            will appear here.
          </span>
        </div>
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
            <h3>Night Movement</h3>
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