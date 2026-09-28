// IMPORTANT: use the SAME hostname style as your browser uses for the frontend.
// If you open React at http://localhost:5173, this must say "localhost", not "127.0.0.1"
// (browsers treat those as different origins for cookies, even on the same machine).
const BASE_URL = "http://localhost:5002";

// Tells the "Top 5 questions" panel to reload right away
// (after login, logout, or a new question) instead of waiting for its timer.
const refreshTopQuestions = () =>
    window.dispatchEvent(new Event("topquestions:refresh"));

async function request(path, options = {}) {
    const res = await fetch(BASE_URL + path, {
        credentials: "include", // required so the session cookie is sent/stored
        headers: { "Content-Type": "application/json" },
        ...options,
    });
    return res.json();
}

export const api = {
    login: async (username, password) => {
        const data = await request("/login", {
            method: "POST",
            body: JSON.stringify({ username, password }),
        });
        refreshTopQuestions();
        return data;
    },

    register: (username, password) =>
        request("/register", { method: "POST", body: JSON.stringify({ username, password }) }),

    logout: async () => {
        const data = await request("/logout", { method: "POST" });
        refreshTopQuestions();
        return data;
    },

    ask: async (question) => {
        const data = await request("/ask", {
            method: "POST",
            body: JSON.stringify({ question }),
        });
        refreshTopQuestions();
        return data;
    },

    askBatch: async (questions) => {
        const data = await request("/ask-batch", {
            method: "POST",
            body: JSON.stringify({ questions }),
        });
        refreshTopQuestions();
        return data;
    },

    // Asks the server if the session cookie is still valid (used on page refresh)
    me: () => request("/me", { method: "GET" }),

    topQuestions: () => request("/top-questions", { method: "GET" }),

    adminListServices: () => request("/admin/services", { method: "GET" }),

    adminAddService: (service) =>
        request("/admin/services", { method: "POST", body: JSON.stringify(service) }),

    adminUpdateService: (serviceId, service) =>
        request(`/admin/services/${serviceId}`, { method: "PUT", body: JSON.stringify(service) }),

    adminDeleteService: (serviceId) =>
        request(`/admin/services/${serviceId}`, { method: "DELETE" }),
};
