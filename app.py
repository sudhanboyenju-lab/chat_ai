from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import wraps

from flask import Flask, jsonify, request, session
from flask_cors import CORS

from auth import register_user, verify_user
from orchestrator import orchestrate, route_question, setup_orchestrator

app = Flask(__name__)
CORS(app, supports_credentials=True, origins=["http://localhost:5173"])
app.secret_key = "dev-secret-key-change-this-later"  # TODO: move to .env before deploying

app.config.update(
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False,
)

# --- One-time setup, runs when the server starts ---
services, vectorstore, llm, service_embeddings, embeddings_model = setup_orchestrator()


# --- Auth guard decorator ---
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "username" not in session:
            return jsonify({"error": "Not logged in"}), 401
        return f(*args, **kwargs)
    return decorated


# --- Health check ---
@app.route("/")
def home():
    return jsonify({"status": "API running"})


# --- Auth routes ---
@app.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"success": False, "message": "Username and password required"})

    success, message = register_user(username, password)
    return jsonify({"success": success, "message": message})


@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username", "").strip()
    password = data.get("password", "")

    valid, role = verify_user(username, password)
    if valid:
        session["username"] = username
        session["role"] = role
        session["history"] = []
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "Invalid username or password"})


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True})


# --- Shared per-question logic, used by both /ask and /ask-batch ---
def answer_one(question, services, vectorstore, llm, service_embeddings, embeddings_model, history=None):
    route, service_id = route_question(question, services, service_embeddings, embeddings_model)
    answer, sources, action = orchestrate(
        question, services, vectorstore, llm, service_embeddings, embeddings_model, history=history
    )
    return {
        "question": question,
        "answer": answer,
        "sources": sources,
        "action": action,
        "route": route,
        "service_id": service_id,
    }


# --- Single question ---
@app.route("/ask", methods=["POST"])
@login_required
def ask_endpoint():
    data = request.json
    question = data.get("question", "")

    history = session.get("history", [])
    result = answer_one(question, services, vectorstore, llm, service_embeddings, embeddings_model, history=history)

    history.append({"question": question, "answer": result["answer"]})
    session["history"] = history

    return jsonify({
        "answer": result["answer"],
        "sources": result["sources"],
        "route": result["route"],
        "action": result["action"],
    })


# --- Multiple questions, processed concurrently ---
@app.route("/ask-batch", methods=["POST"])
@login_required
def ask_batch_endpoint():
    data = request.json
    questions = [q.strip() for q in data.get("questions", []) if q.strip()]

    if not questions:
        return jsonify({"results": []})

    results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(answer_one, q, services, vectorstore, llm, service_embeddings, embeddings_model)
            for q in questions
        ]
        for future in as_completed(futures):
            results.append(future.result())

    return jsonify({"results": results})


if __name__ == "__main__":
    app.run(debug=True, port=5002, host="localhost")