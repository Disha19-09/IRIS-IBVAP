import { BrowserRouter, Routes, Route } from "react-router-dom";

import Sidebar from "./components/Sidebar.jsx";
import Topbar from "./components/Topbar.jsx";

import Dashboard from "./pages/Dashboard.jsx";
import LiveSurveillance from "./pages/LiveSurveillance.jsx";
import SecurityEvents from "./pages/SecurityEvents.jsx";
import ANPR from "./pages/ANPR.jsx";
import Evidence from "./pages/Evidence.jsx";
import Settings from "./pages/Settings.jsx";

import "./App.css";

function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <Sidebar />

        <div className="content-area">
          <Topbar />

          <main className="main-content">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/live" element={<LiveSurveillance />} />
              <Route path="/events" element={<SecurityEvents />} />
              <Route path="/anpr" element={<ANPR />} />
              <Route path="/evidence" element={<Evidence />} />
              <Route path="/settings" element={<Settings />} />
            </Routes>
          </main>
        </div>
      </div>
    </BrowserRouter>
  );
}

export default App;