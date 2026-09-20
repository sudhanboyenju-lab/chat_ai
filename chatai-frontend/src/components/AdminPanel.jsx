import { useState, useEffect } from "react";
import { api } from "../api/client";

export default function AdminPanel() {
    const [services, setServices] = useState({});
    const [editingId, setEditingId] = useState(null);
    const [form, setForm] = useState({
        service_id: "", name: "", fee: "", office: "", hours: "", documents: ""
    });
    const [message, setMessage] = useState("");

    async function loadServices() {
        const data = await api.adminListServices();
        setServices(data.services || {});
    }

    useEffect(() => {
        loadServices();
    }, []);

    function resetForm() {
        setForm({ service_id: "", name: "", fee: "", office: "", hours: "", documents: "" });
        setEditingId(null);
    }

    function startEdit(serviceId) {
        const s = services[serviceId];
        setForm({
            service_id: serviceId,
            name: s.name,
            fee: s.fee,
            office: s.office,
            hours: s.hours,
            documents: s.documents.join("\n"),
        });
        setEditingId(serviceId);
    }

    async function handleSubmit() {
        const payload = {
            service_id: form.service_id.trim(),
            name: form.name.trim(),
            fee: form.fee.trim(),
            office: form.office.trim(),
            hours: form.hours.trim(),
            documents: form.documents.split("\n").map(d => d.trim()).filter(Boolean),
        };

        if (!payload.service_id || !payload.name) {
            setMessage("Service ID and name are required.");
            return;
        }

        try {
            if (editingId) {
                await api.adminUpdateService(editingId, payload);
                setMessage(`Updated "${payload.name}"`);
            } else {
                await api.adminAddService(payload);
                setMessage(`Added "${payload.name}"`);
            }
            resetForm();
            loadServices();
        } catch (err) {
            setMessage("Something went wrong. Check the service ID isn't already taken.");
        }
    }

    async function handleDelete(serviceId) {
        if (!confirm(`Delete "${services[serviceId].name}"? This cannot be undone.`)) return;
        await api.adminDeleteService(serviceId);
        loadServices();
        if (editingId === serviceId) resetForm();
    }

    return (
        <div className="panel">
            <h3>{editingId ? `Editing: ${form.name}` : "Add a new service"}</h3>

            <input
                placeholder="service_id (e.g. birth_registration)"
                value={form.service_id}
                onChange={(e) => setForm({ ...form, service_id: e.target.value })}
                disabled={!!editingId}
            />
            <input
                placeholder="Service name"
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
            />
            <input
                placeholder="Fee"
                value={form.fee}
                onChange={(e) => setForm({ ...form, fee: e.target.value })}
            />
            <input
                placeholder="Office"
                value={form.office}
                onChange={(e) => setForm({ ...form, office: e.target.value })}
            />
            <input
                placeholder="Hours"
                value={form.hours}
                onChange={(e) => setForm({ ...form, hours: e.target.value })}
            />
            <textarea
                rows={4}
                placeholder="Documents required, one per line"
                value={form.documents}
                onChange={(e) => setForm({ ...form, documents: e.target.value })}
            />

            <button onClick={handleSubmit}>
                {editingId ? "Save Changes" : "Add Service"}
            </button>
            {editingId && (
                <button onClick={resetForm} style={{ background: "#8592ab", marginTop: 8 }}>
                    Cancel Edit
                </button>
            )}

            {message && <div className="hint">{message}</div>}

            <h3 style={{ marginTop: 24 }}>Existing services</h3>
            {Object.entries(services).map(([id, s]) => (
                <div key={id} className="bubble ai batch-result" style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <div>
                        <strong>{s.name}</strong>
                        <div className="hint">{id} — {s.documents.length} documents</div>
                    </div>
                    <div style={{ display: "flex", gap: 6 }}>
                        <button onClick={() => startEdit(id)} style={{ padding: "6px 14px", fontSize: 12 }}>Edit</button>
                        <button onClick={() => handleDelete(id)} style={{ padding: "6px 14px", fontSize: 12, background: "#c0392b" }}>Delete</button>
                    </div>
                </div>
            ))}
        </div>
    );
}