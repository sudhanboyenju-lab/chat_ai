import { useState } from "react";
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
    const { isLoggedIn, setIsLoggedIn, role } = useAuth();
    const [authView, setAuthView] = useState("login");
    const [mode, setMode] = useState("single");
    const [view, setView] = useState("chat"); // "chat" | "admin"

    async function handleLogout() {
        await api.logout();
        setIsLoggedIn(false);
    }

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
