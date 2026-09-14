import {
  Users,
  Car,
  ShieldAlert,
  Activity,
  Video,
  Clock,
  AlertTriangle,
  CheckCircle2,
} from "lucide-react";

function Dashboard() {
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
            <span className="stat-label">PERSONS DETECTED</span>
            <strong>—</strong>
            <small>Live stream</small>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">
            <Car size={18} />
          </div>

          <div>
            <span className="stat-label">VEHICLES DETECTED</span>
            <strong>—</strong>
            <small>Live stream</small>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">
            <Activity size={18} />
          </div>

          <div>
            <span className="stat-label">ACTIVE TRACKS</span>
            <strong>—</strong>
            <small>ByteTrack</small>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon alert-icon">
            <ShieldAlert size={18} />
          </div>

          <div>
            <span className="stat-label">SECURITY EVENTS</span>
            <strong>—</strong>
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
              RTSP LIVE
            </div>
          </div>

          <div className="video-placeholder">
            <Video size={42} />
            <span>Live surveillance feed</span>
            <small>Video stream will be connected here</small>
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
              <span className="panel-kicker">SECURITY EVENTS</span>
              <h2>Active Alerts</h2>
            </div>

            <AlertTriangle size={18} />
          </div>

          <div className="empty-state">
            <CheckCircle2 size={26} />
            <p>No active alerts</p>
            <span>
              Real-time events will appear here when detected.
            </span>
          </div>
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
            <span>No events recorded in this session.</span>
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