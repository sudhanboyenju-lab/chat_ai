// IMPORTANT: use the SAME hostname style as your browser uses for the frontend.
// If you open React at http://localhost:5173, this must say "localhost", not "127.0.0.1"
// (browsers treat those as different origins for cookies, even on the same machine).
const BASE_URL = "http://localhost:5003";
// const BASE_URL = "http://192.168.1.6:5002";

async function request(path, options = {}) {
    const res = await fetch(BASE_URL + path, {
        credentials: "include", // required so the session cookie is sent/stored
        headers: { "Content-Type": "application/json" },
        ...options,
    });
    return res.json();
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
