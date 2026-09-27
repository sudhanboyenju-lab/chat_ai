import { useEffect, useState } from "react";
import { api } from "../api/client";

const emptyForm = {
  doctor_id: "",
  doctor_name: "",
  specialization: "",
  department: "",
  fee: "",
  availability: "",
  qualifications: "",
};

export default function AdminPanel() {
  const [doctors, setDoctors] = useState({});
  const [form, setForm] = useState(emptyForm);
  const [editingId, setEditingId] = useState(null);
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const result = await api.adminListDoctors();
      setDoctors(result.doctors || {});
    } catch (err) {
      setStatus(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const startEdit = (doctorId, data) => {
    setEditingId(doctorId);
    setForm({
      doctor_id: doctorId,
      doctor_name: data.doctor_name || "",
      specialization: data.specialization || "",
      department: data.department || "",
      fee: data.fee || "",
      availability: data.availability || "",
      qualifications: (data.documents || []).join(", "),
    });
  };

  const resetForm = () => {
    setEditingId(null);
    setForm(emptyForm);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus("");
    const payload = {
      doctor_name: form.doctor_name,
      specialization: form.specialization,
      department: form.department,
      fee: form.fee,
      availability: form.availability,
      qualifications: form.qualifications
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean),
    };

    try {
      if (editingId) {
        await api.adminUpdateDoctor(editingId, payload);
        setStatus(`Updated ${form.doctor_name}.`);
      } else {
        await api.adminAddDoctor({ doctor_id: form.doctor_id, ...payload });
        setStatus(`Added ${form.doctor_name}.`);
      }
      resetForm();
      load();
    } catch (err) {
      setStatus(err.message);
    }
  };

  const handleDelete = async (doctorId, name) => {
    if (!window.confirm(`Remove ${name} from the directory?`)) return;
    try {
      await api.adminDeleteDoctor(doctorId);
      setStatus(`Removed ${name}.`);
      load();
    } catch (err) {
      setStatus(err.message);
    }
  };

  return (
    <div className="admin-panel">
      <section className="admin-form-section">
        <h2>{editingId ? "Edit doctor" : "Add a doctor"}</h2>
        <form onSubmit={handleSubmit} className="admin-form">
          <label>
            Doctor ID
            <input
              value={form.doctor_id}
              onChange={(e) => setForm({ ...form, doctor_id: e.target.value })}
              disabled={!!editingId}
              required
            />
          </label>
          <label>
            Name
            <input
              value={form.doctor_name}
              onChange={(e) => setForm({ ...form, doctor_name: e.target.value })}
              required
            />
          </label>
          <label>
            Specialization
            <input
              value={form.specialization}
              onChange={(e) => setForm({ ...form, specialization: e.target.value })}
            />
          </label>
          <label>
            Department
            <input
              value={form.department}
              onChange={(e) => setForm({ ...form, department: e.target.value })}
            />
          </label>
          <label>
            Fee
            <input
              value={form.fee}
              onChange={(e) => setForm({ ...form, fee: e.target.value })}
            />
          </label>
          <label>
            Availability
            <input
              value={form.availability}
              onChange={(e) => setForm({ ...form, availability: e.target.value })}
              placeholder="Sun-Fri, 10am-2pm"
            />
          </label>
          <label className="full-width">
            Qualifications (comma separated)
            <input
              value={form.qualifications}
              onChange={(e) => setForm({ ...form, qualifications: e.target.value })}
            />
          </label>

          <div className="admin-form-actions">
            <button type="submit" className="primary-btn">
              {editingId ? "Save changes" : "Add doctor"}
            </button>
            {editingId && (
              <button type="button" className="text-btn" onClick={resetForm}>
                Cancel
              </button>
            )}
          </div>
        </form>
        {status && <p className="admin-status">{status}</p>}
      </section>

      <section className="admin-table-section">
        <h2>Current doctors</h2>
        {loading ? (
          <p>Loading…</p>
        ) : (
          <table className="admin-table">
            <thead>
              <tr>
                <th>Name</th>
                <th>Specialization</th>
                <th>Department</th>
                <th>Fee</th>
                <th>Availability</th>
                <th>Qualifications</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(doctors).map(([doctorId, data]) => (
                <tr key={doctorId}>
                  <td>{data.doctor_name}</td>
                  <td>{data.specialization}</td>
                  <td>{data.department}</td>
                  <td>{data.fee}</td>
                  <td>{data.availability}</td>
                  <td>{(data.documents || []).join(", ")}</td>
                  <td className="row-actions">
                    <button className="text-btn" onClick={() => startEdit(doctorId, data)}>
                      Edit
                    </button>
                    <button
                      className="text-btn danger"
                      onClick={() => handleDelete(doctorId, data.doctor_name)}
                    >
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
