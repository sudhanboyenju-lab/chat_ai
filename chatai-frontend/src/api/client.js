// BASE_URL comes from .env (VITE_API_BASE) - the one place per project where
// the frontend/backend pairing lives. Change .env if you ever change ports.
const BASE_URL = import.meta.env.VITE_API_BASE || "http://localhost:5002";

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

  adminListServices: () => request("/admin/services", { method: "GET" }),

  adminAddService: (service) =>
    request("/admin/services", { method: "POST", body: JSON.stringify(service) }),

  adminUpdateService: (serviceId, service) =>
    request(`/admin/services/${serviceId}`, { method: "PUT", body: JSON.stringify(service) }),

  adminDeleteService: (serviceId) =>
    request(`/admin/services/${serviceId}`, { method: "DELETE" }),
};