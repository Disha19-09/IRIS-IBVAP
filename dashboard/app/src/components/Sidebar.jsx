import { NavLink } from "react-router-dom";
import { LayoutDashboard, Video, ShieldAlert, ScanLine, Image, Settings,} from "lucide-react";

function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <div className="logo-mark">I</div>

        <div>
          <h1>IBVAP</h1>
          <span>INTELLIGENT VIDEO ANALYTICS</span>
        </div>
      </div>

      <nav className="sidebar-nav">
        <NavLink
          to="/"
          className={({ isActive }) =>
            `nav-item ${isActive ? "active" : ""}`
          }
        >
          <LayoutDashboard size={18} />
          <span>Overview</span>
        </NavLink>

        <NavLink
          to="/live"
          className={({ isActive }) =>
            `nav-item ${isActive ? "active" : ""}`
          }
        >
          <Video size={18} />
          <span>Live Surveillance</span>
        </NavLink>

        <NavLink
          to="/events"
          className={({ isActive }) =>
            `nav-item ${isActive ? "active" : ""}`
          }
        >
          <ShieldAlert size={18} />
          <span>Security Events</span>
        </NavLink>

        <NavLink
          to="/anpr"
          className={({ isActive }) =>
            `nav-item ${isActive ? "active" : ""}`
          }
        >
          <ScanLine size={18} />
          <span>ANPR</span>
        </NavLink>

        <NavLink
          to="/evidence"
          className={({ isActive }) =>
            `nav-item ${isActive ? "active" : ""}`
          }
        >
          <Image size={18} />
          <span>Evidence</span>
        </NavLink>
      </nav>

      <div className="sidebar-bottom">
        <NavLink
          to="/settings"
          className={({ isActive }) =>
            `nav-item ${isActive ? "active" : ""}`
          }
        >
          <Settings size={18} />
          <span>Settings</span>
        </NavLink>
      </div>
    </aside>
  );
}

export default Sidebar;