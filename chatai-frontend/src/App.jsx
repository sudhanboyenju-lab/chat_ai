import { useEffect, useState } from "react";
import { AuthProvider, useAuth } from "./context/AuthContext";
import Login from "./components/Login";
import Register from "./components/Register";
import ChatWindow from "./components/ChatWindow";
import BatchAsk from "./components/BatchAsk";
import ModeToggle from "./components/ModeToggle";
import AdminPanel from "./components/AdminPanel";
import { api } from "./api/client";
import "./App.css";

function AppContent() {
    const { isLoggedIn, setIsLoggedIn, role, setRole } = useAuth();
    const [authView, setAuthView] = useState("login");
    const [mode, setMode] = useState("single");
    const [view, setView] = useState("chat"); // "chat" | "admin"
    const [checkingSession, setCheckingSession] = useState(true);

    // On page load / refresh, ask the server if the session cookie is still valid
    // and restore the login instead of dropping the user back on the login screen.
    useEffect(() => {
        api.me()
            .then((res) => {
                if (res && res.logged_in) {
                    if (typeof setRole === "function") setRole(res.role);
                    setIsLoggedIn(true);
                }
            })
            .catch(() => {
                // server unreachable -> just show the login screen
            })
            .finally(() => setCheckingSession(false));
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    async function handleLogout() {
        await api.logout();
        setIsLoggedIn(false);
    }

    // Don't flash the login form while we're still checking the session
    if (checkingSession) return null;

    if (!isLoggedIn) {
        return (
            <div className="container auth-container">
                <h1>Citizen AI</h1>
                <p className="subtitle">
                    Government services made simple — ask in Nepali or English.
                </p>
                {authView === "login" ? (
                    <Login onSwitchToRegister={() => setAuthView("register")} />
                ) : (
                    <Register onSwitchToLogin={() => setAuthView("login")} />
                )}
            </div>
        );
    }

    return (
        <div className="container">
            <button className="logout-btn" onClick={handleLogout}>
                Log out
            </button>
            <h1>Citizen AI</h1>
            <p className="subtitle">
                Ask about birth registration, map approval, tax payment, and other municipal services.
            </p>
    
            <div style={{ display: "flex", gap: 10, flexWrap: "wrap" }}>
                {view === "chat" && <ModeToggle mode={mode} setMode={setMode} />}
    
                {role === "admin" && (
                    <button
                        className="mode-toggle-btn"
                        onClick={() => setView(view === "chat" ? "admin" : "chat")}
                    >
                        {view === "chat" ? "⚙ Admin Panel" : "← Back to Chat"}
                    </button>
                )}
            </div>
    
            {view === "admin"
                ? <AdminPanel />
                : (mode === "single" ? <ChatWindow /> : <BatchAsk />)}
        </div>
    );
}

export default function App() {
    return (
        <AuthProvider>
            <AppContent />
        </AuthProvider>
    );
}
