import { useState } from "react";
import { AuthProvider, useAuth } from "./context/AuthContext";
import Login from "./components/Login";
import Register from "./components/Register";
import ChatWindow from "./components/ChatWindow";
import BatchAsk from "./components/BatchAsk";
import ModeToggle from "./components/ModeToggle";
import { api } from "./api/client";
import "./App.css";

function AppContent() {
    const { isLoggedIn, setIsLoggedIn } = useAuth();
    const [authView, setAuthView] = useState("login");
    const [mode, setMode] = useState("single");

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
                Ask about birth registration, map apaaproval, tax payment, and other municipal services.
            </p>
            <ModeToggle mode={mode} setMode={setMode} />
            {mode === "single" ? <ChatWindow /> : <BatchAsk />}
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
