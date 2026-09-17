import { Radio, CheckCircle2, Server, Cpu } from "lucide-react";
import { useAlerts } from "../api/useAlerts.js";
import { clearAuthToken } from "../api/api.js";
import { useNavigate } from "react-router-dom";

function Topbar() {
  const { connected } = useAlerts();
  const navigate = useNavigate();

  function handleLogout() {
    clearAuthToken();
    navigate("/login", { replace: true });
  }

  return (
    <header className="topbar">
      <div className="topbar-section">
        <span className="topbar-label">BORDER-SEC</span>
        <span className="topbar-divider">/</span>
        <span className="topbar-system">SYSTEM</span>
      </div>

      <div className="topbar-status">
        <div className="status-item live">
          <Radio size={13} />
          <span>CAM-01</span>
          <span className="status-sub">RTSP LIVE</span>
        </div>

        <div className="status-item online">
          <CheckCircle2 size={13} />
          <span>SYSTEM</span>
          <span className="status-sub">ONLINE</span>
        </div>

        <div className="status-item connected">
          <Server size={13} />
          <span>FASTAPI</span>
          <span className="status-sub">{connected ? "CONNECTED" : "OFFLINE"}</span>
        </div>

        <div className="status-item pipeline">
          <Cpu size={13} />
          <span>PIPELINE</span>
          <span className="status-sub">ACTIVE</span>
        </div>
      </div>

      <div className="topbar-session">
        <span className="session-label">IBVAP</span>
        <span className="session-status">ACTIVE SESSION</span>
        <button type="button" className="logout-button" onClick={handleLogout}>
          Sign out
        </button>
      </div>
    </header>
  );
}

export default Topbar;