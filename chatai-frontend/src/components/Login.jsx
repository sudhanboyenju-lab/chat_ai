import { useState } from "react";
import { api } from "../api/client";
import { useAuth } from "../context/AuthContext";

export default function Login({ onSwitchToRegister }) {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);
    const { setIsLoggedIn } = useAuth();

    async function handleLogin() {
        if (!username.trim() || !password) return;
        setLoading(true);
        setError("");

        try {
            const data = await api.login(username.trim(), password);
            if (data.success) {
                setIsLoggedIn(true);
            } else {
                setError(data.message || "Login failed");
            }
        } catch (err) {
            setError("Could not reach the server. Is Flask running?");
        } finally {
            setLoading(false);
        }
    }

    function handleKeyPress(e) {
        if (e.key === "Enter") handleLogin();
    }

    return (
        <div className="panel">
            <h3>Log in</h3>
            <input
                placeholder="Username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                onKeyPress={handleKeyPress}
            />
            <input
                type="password"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                onKeyPress={handleKeyPress}
            />
            <button onClick={handleLogin} disabled={loading}>
                {loading ? "Logging in..." : "Log In"}
            </button>
            <div className="switch" onClick={onSwitchToRegister}>
                Don't have an account? Register
            </div>
            {error && <div className="error">{error}</div>}
        </div>
    );
}
