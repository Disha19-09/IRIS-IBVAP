import { Settings as SettingsIcon, Video, SlidersHorizontal, Shield, Clock, Server, } from "lucide-react";
import { useAlerts } from "../api/useAlerts.js";

function Settings() {
  const { connected } = useAlerts();

  return (
    <div className="settings-page">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <span className="eyebrow">SYSTEM CONFIGURATION</span>
          <h1>Settings</h1>
          <p>
            Configure surveillance and AI analytics parameters.
          </p>
        </div>

        <div className="system-badge">
          <span className="status-dot"></span>
          SYSTEM CONFIGURATION
        </div>
      </div>

      {/* Camera Configuration */}
      <section className="settings-section">
        <div className="settings-section-header">
          <div>
            <span className="panel-kicker">VIDEO SOURCE</span>
            <h2>Camera Configuration</h2>
          </div>

          <Video size={18} />
        </div>

        <div className="settings-grid">
          <div className="setting-card">
            <div className="setting-card-icon">
              <Video size={17} />
            </div>

            <div className="setting-content">
              <span>ACTIVE CAMERA</span>
              <strong>CAM-01</strong>
              <small>Current surveillance source</small>
            </div>
          </div>

          <div className="setting-card">
            <div className="setting-card-icon">
              <Server size={17} />
            </div>

            <div className="setting-content">
              <span>STREAM TYPE</span>
              <strong>RTSP</strong>
              <small>IP camera video stream</small>
            </div>
          </div>
        </div>
      </section>

      {/* Detection Configuration */}
      <section className="settings-section">
        <div className="settings-section-header">
          <div>
            <span className="panel-kicker">AI ANALYTICS</span>
            <h2>Detection Configuration</h2>
          </div>

          <SlidersHorizontal size={18} />
        </div>

        <div className="settings-grid">
          <div className="setting-card">
            <div className="setting-card-icon">
              <SlidersHorizontal size={17} />
            </div>

            <div className="setting-content">
              <span>OBJECT DETECTION</span>
              <strong>YOLOv8</strong>
              <small>Person and vehicle detection</small>
            </div>
          </div>

          <div className="setting-card">
            <div className="setting-card-icon">
              <Shield size={17} />
            </div>

            <div className="setting-content">
              <span>TRACKING</span>
              <strong>ByteTrack</strong>
              <small>Object tracking across frames</small>
            </div>
          </div>
        </div>
      </section>

      {/* Security Configuration */}
      <section className="settings-section">
        <div className="settings-section-header">
          <div>
            <span className="panel-kicker">SECURITY EVENTS</span>
            <h2>Event Configuration</h2>
          </div>

          <Shield size={18} />
        </div>

        <div className="settings-grid">
          <div className="setting-card">
            <div className="setting-card-icon">
              <Shield size={17} />
            </div>

            <div className="setting-content">
              <span>VIRTUAL FENCE</span>
              <strong>ENABLED</strong>
              <small>Directional crossing detection</small>
            </div>
          </div>

          <div className="setting-card">
            <div className="setting-card-icon">
              <Clock size={17} />
            </div>

            <div className="setting-content">
              <span>LOITERING THRESHOLD</span>
              <strong>5 SECONDS</strong>
              <small>Configured event threshold</small>
            </div>
          </div>

          <div className="setting-card">
            <div className="setting-card-icon">
              <Clock size={17} />
            </div>

            <div className="setting-content">
              <span>NIGHT PERIOD</span>
              <strong>19:00 – 06:00</strong>
              <small>Person movement classification</small>
            </div>
          </div>

          <div className="setting-card">
            <div className="setting-card-icon">
              <Shield size={17} />
            </div>

            <div className="setting-content">
              <span>ALERT EVIDENCE</span>
              <strong>SNAPSHOT</strong>
              <small>Capture evidence on detected events</small>
            </div>
          </div>
        </div>
      </section>

      {/* System Status */}
      <section className="panel system-status-panel">
        <div className="panel-header">
          <div>
            <span className="panel-kicker">SYSTEM</span>
            <h2>System Status</h2>
          </div>

          <Server size={18} />
        </div>

        <div className="system-status-grid">
          <div>
            <span>VIDEO INGESTION</span>
            <strong>READY</strong>
          </div>

          <div>
            <span>AI PIPELINE</span>
            <strong>READY</strong>
          </div>

          <div>
            <span>EVENT LOGGING</span>
            <strong>READY</strong>
          </div>

          <div>
            <span>BACKEND</span>
            <strong>{connected ? "CONNECTED" : "OFFLINE"}</strong>
          </div>
        </div>
      </section>
    </div>
  );
}

export default Settings;