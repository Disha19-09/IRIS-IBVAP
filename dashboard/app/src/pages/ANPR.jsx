import { ScanLine, Car, Camera, Clock, ShieldCheck,} from "lucide-react";

function ANPR() {
  return (
    <div className="anpr-page">
      {/* Page Header */}
      <div className="page-header">
        <div>
          <span className="eyebrow">VEHICLE INTELLIGENCE</span>
          <h1>ANPR</h1>
          <p>
            Automatic number plate recognition from the active surveillance stream.
          </p>
        </div>

        <div className="system-badge">
          <span className="status-dot"></span>
          ANPR MONITORING ACTIVE
        </div>
      </div>

      {/* ANPR Summary */}
      <section className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">
            <ScanLine size={18} />
          </div>

          <div>
            <span className="stat-label">PLATES DETECTED</span>
            <strong>—</strong>
            <small>Current session</small>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">
            <Car size={18} />
          </div>

          <div>
            <span className="stat-label">VEHICLES ANALYZED</span>
            <strong>—</strong>
            <small>AI vehicle detection</small>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">
            <Camera size={18} />
          </div>

          <div>
            <span className="stat-label">SOURCE CAMERA</span>
            <strong>CAM-01</strong>
            <small>Active RTSP stream</small>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">
            <ShieldCheck size={18} />
          </div>

          <div>
            <span className="stat-label">RECOGNITION STATUS</span>
            <strong>—</strong>
            <small>Waiting for results</small>
          </div>
        </div>
      </section>

      {/* ANPR Workspace */}
      <section className="anpr-layout">
        {/* Recognition Preview */}
        <div className="panel anpr-preview-panel">
          <div className="panel-header">
            <div>
              <span className="panel-kicker">PLATE RECOGNITION</span>
              <h2>Latest Detection</h2>
            </div>

            <ScanLine size={18} />
          </div>

          <div className="anpr-preview">
            <Car size={42} />

            <span>No vehicle plate detected</span>

            <small>
              Recognized number plates will appear here.
            </small>
          </div>
        </div>

        {/* Latest Result */}
        <div className="panel anpr-result-panel">
          <div className="panel-header">
            <div>
              <span className="panel-kicker">LATEST RESULT</span>
              <h2>Plate Information</h2>
            </div>

            <ShieldCheck size={18} />
          </div>

          <div className="plate-result-empty">
            <ScanLine size={26} />

            <p>No ANPR result available.</p>

            <span>
              Plate number and recognition confidence will appear when detected.
            </span>
          </div>
        </div>
      </section>

      {/* Recognition Log */}
      <section className="panel anpr-log-panel">
        <div className="panel-header">
          <div>
            <span className="panel-kicker">RECOGNITION LOG</span>
            <h2>Detected Number Plates</h2>
          </div>

          <Clock size={18} />
        </div>

        <div className="anpr-log-empty">
          <span>
            No number plate detections recorded in this session.
          </span>
        </div>
      </section>
    </div>
  );
}

export default ANPR;