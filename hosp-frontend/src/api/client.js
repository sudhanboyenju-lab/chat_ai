// BASE_URL now comes from .env (VITE_API_BASE), not a hardcoded string here.
// This is the ONE place per project where the frontend/backend pairing lives -
// if you ever change ports, edit .env, not this file.
const BASE_URL = import.meta.env.VITE_API_BASE || "http://localhost:5004";

async function request(path, options = {}) {
  const res = await fetch(BASE_URL + path, {
    credentials: "include", // required so the session cookie is sent/received
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    throw new Error(data.message || data.error || `Request failed (${res.status})`);
  }
  return data;
}

export const api = {
  login: (username, password) =>
    request("/login", { method: "POST", body: JSON.stringify({ username, password }) }),

  register: (username, password) =>
    request("/register", { method: "POST", body: JSON.stringify({ username, password }) }),

  logout: () => request("/logout", { method: "POST" }),

  ask: (question) =>
    request("/ask", { method: "POST", body: JSON.stringify({ question }) }),

  askBatch: (questions) =>
    request("/ask-batch", { method: "POST", body: JSON.stringify({ questions }) }),

  adminListDoctors: () => request("/admin/doctors", { method: "GET" }),

  adminAddDoctor: (doctor) =>
    request("/admin/doctors", { method: "POST", body: JSON.stringify(doctor) }),

  adminUpdateDoctor: (doctorId, doctor) =>
    request(`/admin/doctors/${doctorId}`, { method: "PUT", body: JSON.stringify(doctor) }),

  adminDeleteDoctor: (doctorId) =>
    request(`/admin/doctors/${doctorId}`, { method: "DELETE" }),
};
