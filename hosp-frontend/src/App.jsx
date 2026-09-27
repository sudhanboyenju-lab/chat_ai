import { useState } from "react";
import Login from "./components/Login";
import Chat from "./components/Chat";
import AdminPanel from "./components/AdminPanel";
import { api } from "./api/client";
import "./App.css";

export default function App() {
  const [user, setUser] = useState(null); // { username, role }
  const [view, setView] = useState("chat"); // "chat" | "admin"

  const handleLogout = async () => {
    try {
      await api.logout();
    } catch {
      // ignore network errors on logout - clear local state regardless
    }
    setUser(null);
  };

  if (!user) {
    return <Login onLoggedIn={setUser} />;
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="brand">
          <span className="brand-mark">SH</span>
          <span className="brand-name">Sunrise Hospital</span>
        </div>

        <nav className="app-nav">
          <button
            className={view === "chat" ? "nav-btn active" : "nav-btn"}
            onClick={() => setView("chat")}
          >
            Ask about doctors
          </button>
          {user.role === "admin" && (
            <button
              className={view === "admin" ? "nav-btn active" : "nav-btn"}
              onClick={() => setView("admin")}
            >
              Manage doctors
            </button>
          )}
        </nav>

        <div className="session-info">
          <span className="session-user">{user.username}</span>
          <button className="text-btn" onClick={handleLogout}>
            Sign out
          </button>
        </div>
      </header>

      <main className="app-main">{view === "chat" ? <Chat /> : <AdminPanel />}</main>
    </div>
  );
}
