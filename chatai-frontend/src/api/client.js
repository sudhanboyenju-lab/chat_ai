// Where the API lives.
//
// Default is the relative path "/api": the browser calls the SAME site it loaded
// the page from, and a proxy forwards "/api/*" to Flask:
//   - development: Vite's dev-server proxy (see vite.config.js)
//   - production:  nginx / your host (see nginx.conf.example)
// Same origin means no hardcoded host or port, no CORS problems, and the login
// cookie works without the localhost-vs-127.0.0.1 trap.
//
// If the API is on a different domain, set VITE_API_URL at build time instead,
// e.g. VITE_API_URL=https://api.example.com  (then Flask must allow that origin in CORS).
export const BASE_URL = import.meta.env.VITE_API_URL ?? "/api";

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

// Shared by every file upload (voice, documents): multipart FormData in, JSON out.
// No Content-Type header on purpose - the browser sets it itself, with the
// boundary marker that multipart uploads require.
async function uploadForm(path, form) {
    const res = await fetch(BASE_URL + path, {
        method: "POST",
        credentials: "include",
        body: form,
    });

    // Read as text first: server error pages are HTML, not JSON.
    const text = await res.text();
    let data;
    try {
        data = JSON.parse(text);
    } catch {
        if (res.status === 413) throw new Error("That file is too large.");
        throw new Error(`Server returned ${res.status} (not JSON). Check the Flask terminal.`);
    }
    if (!res.ok) throw new Error(data.error || "Upload failed");
    return data;
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

    // Voice question: uploads a recording, returns { question, answer, sources, route, action }.
    askVoice: async (blob, filename = "question.webm") => {
        const form = new FormData();
        form.append("audio", blob, filename);
        const data = await uploadForm("/ask-voice", form);
        refreshTopQuestions();
        return data;
    },

    // Document photo: returns { text, document, needed_for }.
    uploadDocument: async (file) => {
        const form = new FormData();
        form.append("image", file, file.name);
        return uploadForm("/ocr", form);
    },

    // --- Citizen records (admin only) ---
    citizenSchema: () => request("/citizens/schema", { method: "GET" }),

    // Photo of a citizenship card -> { fields } (suggestions only, nothing is saved)
    extractCitizenCard: (file) => {
        const form = new FormData();
        form.append("image", file, file.name);
        return uploadForm("/citizens/extract", form);
    },

    saveCitizen: (fields) =>
        request("/citizens", { method: "POST", body: JSON.stringify(fields) }),

    listCitizens: (q = "") =>
        request(`/citizens?q=${encodeURIComponent(q)}`, { method: "GET" }),

    getCitizen: (id) => request(`/citizens/${id}`, { method: "GET" }),

    deleteCitizen: (id) => request(`/citizens/${id}`, { method: "DELETE" }),

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