import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api/client";

const MAX_BYTES = 8 * 1024 * 1024; // keep in sync with MAX_IMAGE_BYTES on the server

const box = {
  border: "1px solid #d7d9ef",
  borderRadius: 12,
  padding: 16,
  marginTop: 16,
  background: "#fff",
  textAlign: "left",
};

/**
 * Admin screen: upload a citizenship card photo -> review/edit the extracted fields ->
 * save -> see everyone in a searchable list.
 * Nothing is saved until the person clicks "Save record".
 */
export default function CitizenManager() {
  const fileRef = useRef(null);
  const [schema, setSchema] = useState([]);
  const [draft, setDraft] = useState(null); // field values under review, or null
  const [citizens, setCitizens] = useState([]);
  const [query, setQuery] = useState("");
  const [detail, setDetail] = useState(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState({ type: "", text: "" });

  const showError = (text) => setMessage({ type: "error", text });
  const showOk = (text) => setMessage({ type: "ok", text });

  const loadList = useCallback(async (q) => {
    try {
      const data = await api.listCitizens(q);
      if (data.error) throw new Error(data.error);
      setCitizens(data.citizens);
    } catch (e) {
      setMessage({ type: "error", text: e.message || "Could not load the list." });
    }
  }, []);

  useEffect(() => {
    api
      .citizenSchema()
      .then((data) => data.schema && setSchema(data.schema))
      .catch(() => {});
    loadList("");
  }, [loadList]);

  const emptyDraft = () => Object.fromEntries(schema.map((f) => [f.key, ""]));

  async function handleFile(e) {
    const file = e.target.files?.[0];
    e.target.value = ""; // allows picking the same file again
    if (!file) return;

    setMessage({ type: "", text: "" });
    if (!["image/jpeg", "image/png", "image/webp"].includes(file.type)) {
      showError("Please choose a JPG, PNG or WebP photo.");
      return;
    }
    if (file.size > MAX_BYTES) {
      showError("That image is too large (maximum 8 MB).");
      return;
    }

    setBusy(true);
    try {
      const data = await api.extractCitizenCard(file);
      setDraft(data.fields);
      showOk("Please check every field against the card before saving.");
    } catch (err) {
      showError(err.message || "Could not read the card.");
    } finally {
      setBusy(false);
    }
  }

  async function handleSave() {
    const missing = schema.filter((f) => f.required && !draft[f.key]?.trim());
    if (missing.length > 0) {
      showError(`Please fill in: ${missing.map((f) => f.label).join(", ")}`);
      return;
    }
    setBusy(true);
    try {
      const data = await api.saveCitizen(draft);
      if (data.error) throw new Error(data.error);
      setDraft(null);
      showOk("Record saved.");
      await loadList(query);
    } catch (err) {
      showError(err.message || "Could not save the record.");
    } finally {
      setBusy(false);
    }
  }

  async function handleView(id) {
    try {
      const data = await api.getCitizen(id);
      if (data.error) throw new Error(data.error);
      setDetail(data.citizen);
    } catch (err) {
      showError(err.message || "Could not open the record.");
    }
  }

  async function handleDelete(id) {
    if (!window.confirm("Delete this record permanently?")) return;
    try {
      const data = await api.deleteCitizen(id);
      if (data.error) throw new Error(data.error);
      if (detail && detail.id === id) setDetail(null);
      showOk("Record deleted.");
      await loadList(query);
    } catch (err) {
      showError(err.message || "Could not delete the record.");
    }
  }

  return (
    <div className="panel">
      <h2>Citizen records</h2>

      <div style={box}>
        <input
          ref={fileRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          onChange={handleFile}
          style={{ display: "none" }}
        />
        <button type="button" onClick={() => fileRef.current?.click()} disabled={busy}>
          {busy ? "Working…" : "📄 Upload citizenship card"}
        </button>{" "}
        <button type="button" onClick={() => setDraft(emptyDraft())} disabled={busy || !schema.length}>
          ＋ Add manually
        </button>
        <p style={{ fontSize: 13, color: "#555", marginBottom: 0 }}>
          The photo is read and discarded. Only the fields you confirm below are saved.
        </p>
      </div>

      {message.text && (
        <div style={{ color: message.type === "error" ? "#b00020" : "#1b6e3c", marginTop: 12 }}>
          {message.text}
        </div>
      )}

      {draft && (
        <div style={box}>
          <h3 style={{ marginTop: 0 }}>Review before saving</h3>
          {schema.map((f) => (
            <label key={f.key} style={{ display: "block", marginBottom: 10, fontSize: 14 }}>
              {f.label}
              {f.required ? " *" : ""}
              <input
                value={draft[f.key] ?? ""}
                onChange={(e) => setDraft({ ...draft, [f.key]: e.target.value })}
                style={{ display: "block", width: "100%", boxSizing: "border-box", padding: 8 }}
              />
            </label>
          ))}
          <button type="button" onClick={handleSave} disabled={busy}>
            Save record
          </button>{" "}
          <button type="button" onClick={() => setDraft(null)} disabled={busy}>
            Cancel
          </button>
        </div>
      )}

      <div style={box}>
        <h3 style={{ marginTop: 0 }}>Citizen list ({citizens.length})</h3>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            loadList(query);
          }}
          style={{ marginBottom: 12 }}
        >
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by name or certificate no."
            style={{ padding: 8, width: "60%" }}
          />{" "}
          <button type="submit">Search</button>
        </form>

        {citizens.length === 0 ? (
          <p>No records yet.</p>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 14 }}>
              <thead>
                <tr style={{ textAlign: "left", borderBottom: "1px solid #ddd" }}>
                  <th>Name</th>
                  <th>Certificate no.</th>
                  <th>Municipality</th>
                  <th>District</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {citizens.map((c) => (
                  <tr key={c.id} style={{ borderBottom: "1px solid #eee" }}>
                    <td>{c.full_name}</td>
                    <td>{c.citizenship_no}</td>
                    <td>{c.permanent_municipality}</td>
                    <td>{c.permanent_district}</td>
                    <td style={{ whiteSpace: "nowrap" }}>
                      <button type="button" onClick={() => handleView(c.id)}>View</button>{" "}
                      <button type="button" onClick={() => handleDelete(c.id)}>Delete</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {detail && (
        <div style={box}>
          <h3 style={{ marginTop: 0 }}>Record #{detail.id}</h3>
          {schema.map((f) => (
            <div key={f.key} style={{ fontSize: 14, marginBottom: 4 }}>
              <strong>{f.label}:</strong> {detail[f.key] || "—"}
            </div>
          ))}
          <div style={{ fontSize: 12, color: "#666", marginTop: 8 }}>
            Added by {detail.created_by || "unknown"} on {detail.created_at}
          </div>
          <button type="button" onClick={() => setDetail(null)} style={{ marginTop: 10 }}>
            Close
          </button>
        </div>
      )}
    </div>
  );
}
