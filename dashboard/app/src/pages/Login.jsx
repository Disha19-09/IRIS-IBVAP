import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { API_BASE_URL, setAuthToken } from "../api/api.js";

function Login() {
  const navigate = useNavigate();
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("admin123");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ username, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "Login failed");
      }

      setAuthToken(data.access_token, data.refresh_token);
      navigate("/");
    } catch (loginError) {
      setError(loginError.message || "Unable to login");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-page">
      <div className="login-grid" aria-hidden="true" />
      <div className="login-scanline" aria-hidden="true" />

      <div className="login-box">
        <div className="login-kicker">
          <span className="kicker-dot" /> BORDER SECURITY NETWORK
          <span className="kicker-code">NODE 01 / AUTH</span>
        </div>

        <div className="login-header">
          <div className="logo-mark">I</div>
          <div>
            <p className="login-eyebrow">INTELLIGENT VIDEO ANALYTICS</p>
            <h1>IBVAP</h1>
            <span>Secure operations gateway</span>
          </div>
        </div>

        <div className="login-rule" />

        <div className="login-intro">
          <h2>Welcome back</h2>
          <p>Sign in to access live surveillance and incident intelligence.</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          <label className="login-field">
            <span>Operator ID</span>
            <input
              type="text"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              autoComplete="username"
            />
          </label>

          <label className="login-field">
            <span>Access key</span>
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete="current-password"
            />
          </label>

          {error && <div className="login-error">{error}</div>}

          <button type="submit" disabled={loading}>
            <span>{loading ? "Authenticating" : "Enter secure dashboard"}</span>
            <span className="login-arrow">-&gt;</span>
          </button>
        </form>

        <div className="login-footer">
          <span><i /> SYSTEM ONLINE</span>
          <span>JWT ENCRYPTED SESSION</span>
        </div>
      </div>
    </div>
  );
}

export default Login;
