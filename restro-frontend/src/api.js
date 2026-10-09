// const API_BASE = "http://192.168.1.6:5003"; // Flask (restro) server - update per environment
const API_BASE = "http://localhost:5003";

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    credentials: "include",
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
  register: (username, password) =>
    request("/register", { method: "POST", body: JSON.stringify({ username, password }) }),

  login: (username, password) =>
    request("/login", { method: "POST", body: JSON.stringify({ username, password }) }),

  logout: () => request("/logout", { method: "POST" }),

  ask: (question) =>
    request("/ask", { method: "POST", body: JSON.stringify({ question }) }),

  askBatch: (questions) =>
    request("/ask-batch", { method: "POST", body: JSON.stringify({ questions }) }),

  listMenuItems: () => request("/admin/menu-items"),

  addMenuItem: (item) =>
    request("/admin/menu-items", { method: "POST", body: JSON.stringify(item) }),

  updateMenuItem: (itemId, item) =>
    request(`/admin/menu-items/${itemId}`, { method: "PUT", body: JSON.stringify(item) }),

  deleteMenuItem: (itemId) =>
    request(`/admin/menu-items/${itemId}`, { method: "DELETE" }),
};
