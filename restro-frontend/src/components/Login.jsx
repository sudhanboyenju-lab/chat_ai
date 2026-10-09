import { useState } from "react";
import { api } from "../api";

export default function Login({ onLoggedIn }) {
  const [mode, setMode] = useState("login"); // "login" | "register"
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage("");
    setBusy(true);
    try {
      if (mode === "login") {
        const result = await api.login(username, password);
        if (result.success) {
          onLoggedIn({ username, role: result.role });
        } else {
          setMessage(result.message || "Invalid username or password.");
        }
      } else {
        const result = await api.register(username, password);
        if (result.success) {
          setMessage("Account created. You can sign in now.");
          setMode("login");
        } else {
          setMessage(result.message || "Could not create that account.");
        }
      }
    } catch (err) {
      setMessage(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="auth-screen">
      <div className="auth-card">
        <div className="brand-mark large">TB</div>
        <h1>Thakali Bhansa</h1>
        <p className="auth-subtitle">
          {mode === "login"
            ? "Sign in to ask about today's menu."
            : "Create an account to get started."}
        </p>

        <form onSubmit={handleSubmit} className="auth-form">
          <label>
            Username
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              autoComplete="username"
              required
            />
          </label>
          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete={mode === "login" ? "current-password" : "new-password"}
              required
            />
          </label>

          {message && <p className="auth-message">{message}</p>}

          <button type="submit" className="primary-btn" disabled={busy}>
            {busy ? "Please wait…" : mode === "login" ? "Sign in" : "Create account"}
          </button>
        </form>

        <button
          className="text-btn switch-mode"
          onClick={() => {
            setMode(mode === "login" ? "register" : "login");
            setMessage("");
          }}
        >
          {mode === "login" ? "Need an account? Register" : "Already have an account? Sign in"}
        </button>
      </div>
    </div>
  );
}
