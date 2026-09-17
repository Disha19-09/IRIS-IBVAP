import { BrowserRouter, Routes, Route } from "react-router-dom";

import Sidebar from "./components/Sidebar.jsx";
import Topbar from "./components/Topbar.jsx";
import ProtectedRoute from "./components/ProtectedRoute.jsx";

import Dashboard from "./pages/Dashboard.jsx";
import LiveSurveillance from "./pages/LiveSurveillance.jsx";
import SecurityEvents from "./pages/SecurityEvents.jsx";
import ANPR from "./pages/ANPR.jsx";
import Evidence from "./pages/Evidence.jsx";
import Settings from "./pages/Settings.jsx";
import Login from "./pages/Login.jsx";

import "./App.css";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />

        <Route
          path="/"
          element={
            <ProtectedRoute>
              <div className="app">
                <Sidebar />

                <div className="content-area">
                  <Topbar />

                  <main className="main-content">
                    <Dashboard />
                  </main>
                </div>
              </div>
            </ProtectedRoute>
          }
        />

        <Route
          path="/live"
          element={
            <ProtectedRoute>
              <div className="app">
                <Sidebar />

                <div className="content-area">
                  <Topbar />

                  <main className="main-content">
                    <LiveSurveillance />
                  </main>
                </div>
              </div>
            </ProtectedRoute>
          }
        />

        <Route
          path="/events"
          element={
            <ProtectedRoute>
              <div className="app">
                <Sidebar />

                <div className="content-area">
                  <Topbar />

                  <main className="main-content">
                    <SecurityEvents />
                  </main>
                </div>
              </div>
            </ProtectedRoute>
          }
        />

        <Route
          path="/anpr"
          element={
            <ProtectedRoute>
              <div className="app">
                <Sidebar />

                <div className="content-area">
                  <Topbar />

                  <main className="main-content">
                    <ANPR />
                  </main>
                </div>
              </div>
            </ProtectedRoute>
          }
        />

        <Route
          path="/evidence"
          element={
            <ProtectedRoute>
              <div className="app">
                <Sidebar />

                <div className="content-area">
                  <Topbar />

                  <main className="main-content">
                    <Evidence />
                  </main>
                </div>
              </div>
            </ProtectedRoute>
          }
        />

        <Route
          path="/settings"
          element={
            <ProtectedRoute>
              <div className="app">
                <Sidebar />

                <div className="content-area">
                  <Topbar />

                  <main className="main-content">
                    <Settings />
                  </main>
                </div>
              </div>
            </ProtectedRoute>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;