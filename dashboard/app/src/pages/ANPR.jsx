import { ScanLine, Car, Camera, Clock, ShieldCheck,} from "lucide-react";
import { useAlerts } from "../api/useAlerts.js";

function ANPR() {
  const { alerts } = useAlerts();
  const plates = alerts.filter((alert) => alert.plate_number);
  const latestPlate = plates[0];

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
            <strong>{plates.length}</strong>
            <small>Current session</small>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">
            <Car size={18} />
          </div>

          <div>
            <span className="stat-label">VEHICLES ANALYZED</span>
            <strong>{alerts.filter((alert) => alert.object_type === "car").length}</strong>
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
            <strong>{latestPlate ? "READY" : "WAITING"}</strong>
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
            {latestPlate ? <>
              <Car size={42} />
              <span>{latestPlate.plate_number}</span>
              <small>{new Date(latestPlate.timestamp).toLocaleString()}</small>
            </> : <>
              <Car size={42} />
              <span>No vehicle plate detected</span>
              <small>Recognized number plates will appear here.</small>
            </>}
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
            <p>{latestPlate ? latestPlate.plate_number : "No ANPR result available."}</p>
            <span>{latestPlate ? `Confidence: ${latestPlate.confidence ?? "unknown"}` : "Plate number and recognition confidence will appear when detected."}</span>
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
          <span>{plates.length ? `${plates.length} number plate detection${plates.length === 1 ? "" : "s"} recorded.` : "No number plate detections recorded in this session."}</span>
        </div>
      </section>
    </div>
  );
}

export default ANPR;