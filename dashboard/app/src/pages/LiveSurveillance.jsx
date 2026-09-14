import { Video, Radio, Users, Car, ShieldAlert,} from "lucide-react";

function LiveSurveillance() {
  return (
    <div className="surveillance-page">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <span className="eyebrow">VIDEO MONITORING</span>
          <h1>Live Surveillance</h1>
          <p>
            Monitor the active CCTV stream with real-time AI detections.
          </p>
        </div>

        <div className="system-badge">
          <span className="status-dot"></span>
          CAM-01 ACTIVE
        </div>
      </div>

      {/* Camera Header */}
      <section className="surveillance-layout">
        <div className="panel surveillance-panel">
          <div className="panel-header">
            <div>
              <span className="panel-kicker">ACTIVE CAMERA</span>
              <h2>CAM-01</h2>
            </div>

            <div className="live-status">
              <Radio size={13} />
              RTSP LIVE
            </div>
          </div>

          {/* Video Area */}
          <div className="surveillance-video">
            <div className="video-corner top-left"></div>
            <div className="video-corner top-right"></div>
            <div className="video-corner bottom-left"></div>
            <div className="video-corner bottom-right"></div>

            <Video size={48} />

            <span>Live surveillance feed</span>
            <small>Video stream will be connected here</small>

            <div className="video-overlay-label">
              CAM-01 / RTSP
            </div>
          </div>

          {/* Camera Info */}
          <div className="camera-info">
            <span>CAM-01</span>
            <span>RTSP STREAM</span>
            <span>AI PROCESSING</span>
          </div>
        </div>

        {/* Detection Panel */}
        <div className="panel detection-panel">
          <div className="panel-header">
            <div>
              <span className="panel-kicker">AI ANALYTICS</span>
              <h2>Live Detections</h2>
            </div>
          </div>

          <div className="detection-item">
            <div className="detection-icon">
              <Users size={18} />
            </div>

            <div>
              <span>Persons</span>
              <small>YOLOv8 detection</small>
            </div>

            <strong>—</strong>
          </div>

          <div className="detection-item">
            <div className="detection-icon">
              <Car size={18} />
            </div>

            <div>
              <span>Vehicles</span>
              <small>Vehicle classification</small>
            </div>

            <strong>—</strong>
          </div>

          <div className="detection-item">
            <div className="detection-icon">
              <ShieldAlert size={18} />
            </div>

            <div>
              <span>Security Events</span>
              <small>Fence / loitering / night</small>
            </div>

            <strong>—</strong>
          </div>
        </div>
      </section>
    </div>
  );
}

export default LiveSurveillance;