from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import wraps

from flask import Flask, jsonify, request, session
from flask_cors import CORS

from ai_engine.analytics import ensure_log_table, get_top_questions, log_question
from ai_engine.cache import ensure_cache_table
from ai_engine.guidance import ensure_dependency_table
from ai_engine.orchestrator import route_question
from auth import register_user, verify_user
from localgov_config import config, engine

app = Flask(__name__)
CORS(app, supports_credentials=True, origins=["http://localhost:5173"])

app.secret_key = "dev-secret-key-change-this-later"  # TODO: move to .env before deploying

app.config.update(
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_NAME="localgov_session",
)

ensure_log_table(config.db_connector)
ensure_cache_table(config.db_connector)
ensure_dependency_table(config.db_connector, config)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "username" not in session:
            return jsonify({"error": "Not logged in"}), 401
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "username" not in session:
            return jsonify({"error": "Not logged in"}), 401
        if session.get("role") != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated


@app.route("/")
def home():
    return jsonify({"status": "API running"})


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
        return jsonify({"success": True, "role": role})
    return jsonify({"success": False, "message": "Invalid username or password"})


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True})


@app.route("/me", methods=["GET"])
def me():
    """Lets the frontend ask 'am I still logged in?' after a page refresh."""
    if "username" not in session:
        return jsonify({"logged_in": False})
    return jsonify({
        "logged_in": True,
        "username": session["username"],
        "role": session.get("role"),
    })


def answer_one(question, history=None):
    route, entity_id = route_question(question, engine.entities, engine.entity_embeddings, engine.config)
    answer, sources, action = engine.ask(question, history=history)
    log_question(config.db_connector, question, answer)
    return {
        "question": question,
        "answer": answer,
        "sources": sources,
        "action": action,
        "route": route,
        "service_id": entity_id,
    }


@app.route("/ask", methods=["POST"])
@login_required
def ask_endpoint():
    data = request.json
    question = data.get("question", "")

    history = session.get("history", [])
    result = answer_one(question, history=history)

    history.append({"question": question, "answer": result["answer"]})
    session["history"] = history

    return jsonify({
        "answer": result["answer"],
        "sources": result["sources"],
        "route": result["route"],
        "action": result["action"],
    })


@app.route("/ask-batch", methods=["POST"])
@login_required
def ask_batch_endpoint():
    data = request.json
    questions = [q.strip() for q in data.get("questions", []) if q.strip()]

    if not questions:
        return jsonify({"results": []})

    results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(answer_one, q) for q in questions]
        for future in as_completed(futures):
            results.append(future.result())

    return jsonify({"results": results})


@app.route("/top-questions", methods=["GET"])
@login_required
def top_questions_endpoint():
    top = get_top_questions(config.db_connector, limit=5)
    return jsonify({"top_questions": top})


# --- Admin CRUD - via config.db_connector, not db.py's service-specific functions ---
@app.route("/admin/services", methods=["GET"])
@admin_required
def admin_list_services():
    current_entities = config.db_connector.get_all_entities(config)
    return jsonify({"services": current_entities})


@app.route("/admin/services", methods=["POST"])
@admin_required
def admin_add_service():
    data = request.json
    entity_id = data["service_id"]
    fields = {
        config.entity_name_field: data["name"],
        "fee": data["fee"],
        "office": data["office"],
        "hours": data["hours"],
    }
    config.db_connector.add_entity(config, entity_id, fields, data.get("documents", []))
    engine.refresh()
    return jsonify({"success": True, "message": "Service added"})


@app.route("/admin/services/<service_id>", methods=["PUT"])
@admin_required
def admin_update_service(service_id):
    data = request.json
    fields = {
        config.entity_name_field: data["name"],
        "fee": data["fee"],
        "office": data["office"],
        "hours": data["hours"],
    }
    config.db_connector.update_entity(config, service_id, fields, data.get("documents", []))
    engine.refresh()
    return jsonify({"success": True, "message": "Service updated"})


@app.route("/admin/services/<service_id>", methods=["DELETE"])
@admin_required
def admin_delete_service(service_id):
    config.db_connector.delete_entity(config, service_id)
    engine.refresh()
    return jsonify({"success": True, "message": "Service deleted"})


if __name__ == "__main__":
    app.run(debug=True, port=5002, host="0.0.0.0")
