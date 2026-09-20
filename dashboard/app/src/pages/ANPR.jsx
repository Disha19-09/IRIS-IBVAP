import { ScanLine, Car, Camera, Clock, ShieldCheck, AlertCircle} from "lucide-react";
import { useAlerts } from "../api/useAlerts.js";
import { getEventTypeLabel } from "../api/api.js";

function ANPR() {
  const { alerts } = useAlerts();
  
  // Filter for alerts with plate numbers (ANPR detections)
  const anprAlerts = alerts.filter((alert) => alert.plate_number && alert.plate_number.trim());
  
  // Get vehicle alerts (with or without plates)
  const vehicleAlerts = alerts.filter((alert) => 
    alert.object_type && ['car', 'truck', 'bus', 'motorcycle'].includes(alert.object_type.toLowerCase())
  );
  
  const latestPlate = anprAlerts[0];

  function formatDateTime(timestamp) {
    const date = new Date(timestamp);
    if (!Number.isFinite(date.getTime())) return "Unknown time";
    return date.toLocaleString();
  }

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
            <strong>{anprAlerts.length}</strong>
            <small>Successfully recognized</small>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">
            <Car size={18} />
          </div>

          <div>
            <span className="stat-label">VEHICLES DETECTED</span>
            <strong>{vehicleAlerts.length}</strong>
            <small>All vehicle types</small>
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
            <strong>{anprAlerts.length > 0 ? "ACTIVE" : "READY"}</strong>
            <small>{anprAlerts.length > 0 ? "Processing detections" : "Waiting for vehicles"}</small>
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
              <small>{formatDateTime(latestPlate.timestamp)}</small>
              <small style={{marginTop: '8px', color: '#888'}}>
                {latestPlate.object_type?.toUpperCase()} · Track #{latestPlate.track_id}
              </small>
            </> : <>
              <Car size={42} />
              <span>No plate detected</span>
              <small>License plates will appear when recognized.</small>
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
            {latestPlate ? (
              <>
                <ScanLine size={26} />
                <p style={{fontSize: '24px', fontWeight: 'bold', margin: '16px 0'}}>{latestPlate.plate_number}</p>
                <span>Vehicle Type: {latestPlate.object_type?.toUpperCase() || 'Unknown'}</span>
                <span>Track ID: #{latestPlate.track_id || 'N/A'}</span>
                <span>Confidence: {latestPlate.confidence ? `${(latestPlate.confidence * 100).toFixed(1)}%` : 'Unknown'}</span>
                <span>Time: {formatDateTime(latestPlate.timestamp)}</span>
              </>
            ) : (
              <>
                <ScanLine size={26} />
                <p>No ANPR result available</p>
                <span>License plate details will appear when a vehicle with readable plate is detected.</span>
              </>
            )}
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

        {anprAlerts.length > 0 ? (
          <div style={{padding: '20px'}}>
            <table style={{width: '100%', borderCollapse: 'collapse'}}>
              <thead>
                <tr style={{borderBottom: '1px solid #333'}}>
                  <th style={{textAlign: 'left', padding: '12px'}}>Plate Number</th>
                  <th style={{textAlign: 'left', padding: '12px'}}>Vehicle</th>
                  <th style={{textAlign: 'left', padding: '12px'}}>Event</th>
                  <th style={{textAlign: 'left', padding: '12px'}}>Time</th>
                  <th style={{textAlign: 'left', padding: '12px'}}>Track ID</th>
                </tr>
              </thead>
              <tbody>
                {anprAlerts.slice(0, 20).map((alert, idx) => (
                  <tr key={alert.id || idx} style={{borderBottom: '1px solid #222'}}>
                    <td style={{padding: '12px', fontWeight: 'bold', color: '#00ff88'}}>
                      {alert.plate_number}
                    </td>
                    <td style={{padding: '12px'}}>
                      {alert.object_type?.toUpperCase() || 'Vehicle'}
                    </td>
                    <td style={{padding: '12px', fontSize: '14px'}}>
                      {getEventTypeLabel(alert.event_type, alert.event_description)}
                    </td>
                    <td style={{padding: '12px', fontSize: '14px', color: '#888'}}>
                      {formatDateTime(alert.timestamp)}
                    </td>
                    <td style={{padding: '12px'}}>
                      #{alert.track_id || 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="anpr-log-empty">
            <span>No license plate detections recorded in this session.</span>
            <span style={{marginTop: '8px', fontSize: '14px', color: '#666'}}>
              {vehicleAlerts.length > 0 
                ? `${vehicleAlerts.length} vehicle(s) detected, but no plates recognized yet.` 
                : 'Waiting for vehicle detections with ANPR enabled...'}
            </span>
          </div>
        )}
      </section>
    </div>
  );
}

export default ANPR;