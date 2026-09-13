import { useState } from "react";
import { api } from "../api/client";

export default function Register({ onSwitchToLogin }) {
    const [username, setUsername] = useState("");
    const [password, setPassword] = useState("");
    const [message, setMessage] = useState("");
    const [success, setSuccess] = useState(false);
    const [loading, setLoading] = useState(false);

    async function handleRegister() {
        if (!username.trim() || !password) return;
        setLoading(true);

        try {
            const data = await api.register(username.trim(), password);
            setMessage(data.message);
            setSuccess(data.success);
            if (data.success) {
                setTimeout(onSwitchToLogin, 900);
            }
        } catch (err) {
            setMessage("Could not reach the server. Is Flask running?");
            setSuccess(false);
        } finally {
            setLoading(false);
        }
    }

    return (
        <div className="panel">
            <h3>Create an account</h3>
            <input
                placeholder="Choose a username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
            />
            <input
                type="password"
                placeholder="Choose a password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
            />
            <button onClick={handleRegister} disabled={loading}>
                {loading ? "Registering..." : "Register"}
            </button>
            <div className="switch" onClick={onSwitchToLogin}>
                Already have an account? Log in
            </div>
            {message && (
                <div className={success ? "success" : "error"}>{message}</div>
            )}
        </div>
    );
}
