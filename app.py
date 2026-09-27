from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import wraps

from flask import Flask, jsonify, request, session
from flask_cors import CORS

<<<<<<< HEAD
from ai_engine.orchestrator import route_question
from auth import register_user, verify_user
from localgov_config import (  # <-- was: setup_orchestrator() from orchestrator.py
    config,
    engine,
)

app = Flask(__name__)
# CORS(app, supports_credentials=True, origins=["http://192.168.1.6:5173"])
CORS(app, supports_credentials=True, origins=["http://localhost:5173"])


=======
from auth import register_user, verify_user
from db import add_service, delete_service, load_services_from_db, update_service
from orchestrator import orchestrate, route_question, setup_orchestrator

app = Flask(__name__)
CORS(app, supports_credentials=True, origins=["http://localhost:5173"])
>>>>>>> 3c38c0001fdb7593b786e29037d23d635bdb7bab
app.secret_key = "dev-secret-key-change-this-later"  # TODO: move to .env before deploying

app.config.update(
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False,
<<<<<<< HEAD
    SESSION_COOKIE_NAME="localgov_session"
)


# --- Auth guards ---
=======
)

# --- One-time setup, runs when the server starts ---
services, vectorstore, llm, service_embeddings, embeddings_model = setup_orchestrator()


# --- Auth guard decorator ---
>>>>>>> 3c38c0001fdb7593b786e29037d23d635bdb7bab
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "username" not in session:
            return jsonify({"error": "Not logged in"}), 401
        return f(*args, **kwargs)
    return decorated


<<<<<<< HEAD
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "username" not in session:
            return jsonify({"error": "Not logged in"}), 401
        if session.get("role") != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated


=======
>>>>>>> 3c38c0001fdb7593b786e29037d23d635bdb7bab
# --- Health check ---
@app.route("/")
def home():
    return jsonify({"status": "API running"})


<<<<<<< HEAD
# --- Auth routes (unchanged) ---
=======
# --- Auth routes ---
>>>>>>> 3c38c0001fdb7593b786e29037d23d635bdb7bab
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


# --- Shared per-question logic, used by both /ask and /ask-batch ---
<<<<<<< HEAD
def answer_one(question, history=None):
    # engine.entities / engine.entity_embeddings are the same cached data
    # the Engine used internally - we just re-run the same routing call
    # here to surface `route` and `service_id` in the API response, same
    # as your old app.py did.
    route, entity_id = route_question(question, engine.entities, engine.entity_embeddings, engine.config)
    answer, sources, action = engine.ask(question, history=history)
=======
def answer_one(question, services, vectorstore, llm, service_embeddings, embeddings_model, history=None):
    route, service_id = route_question(question, services, service_embeddings, embeddings_model)
    answer, sources, action = orchestrate(
        question, services, vectorstore, llm, service_embeddings, embeddings_model, history=history
    )
>>>>>>> 3c38c0001fdb7593b786e29037d23d635bdb7bab
    return {
        "question": question,
        "answer": answer,
        "sources": sources,
        "action": action,
        "route": route,
<<<<<<< HEAD
        "service_id": entity_id,
=======
        "service_id": service_id,
>>>>>>> 3c38c0001fdb7593b786e29037d23d635bdb7bab
    }


# --- Single question ---
@app.route("/ask", methods=["POST"])
@login_required
def ask_endpoint():
    data = request.json
    question = data.get("question", "")

    history = session.get("history", [])
<<<<<<< HEAD
    result = answer_one(question, history=history)
=======
    result = answer_one(question, services, vectorstore, llm, service_embeddings, embeddings_model, history=history)
>>>>>>> 3c38c0001fdb7593b786e29037d23d635bdb7bab

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
<<<<<<< HEAD
        futures = [executor.submit(answer_one, q) for q in questions]
=======
        futures = [
            executor.submit(answer_one, q, services, vectorstore, llm, service_embeddings, embeddings_model)
            for q in questions
        ]
>>>>>>> 3c38c0001fdb7593b786e29037d23d635bdb7bab
        for future in as_completed(futures):
            results.append(future.result())

    return jsonify({"results": results})

<<<<<<< HEAD

# --- Admin CRUD - now generic via config.db_connector instead of db.py's
#     service-specific add_service/update_service/delete_service/load_services_from_db ---
@app.route("/admin/services", methods=["GET"])
@admin_required
def admin_list_services():
    current_entities = config.db_connector.get_all_entities(config)
    return jsonify({"services": current_entities})
=======
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "username" not in session:
            return jsonify({"error": "Not logged in"}), 401
        if session.get("role") != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated


@app.route("/admin/services", methods=["GET"])
@admin_required
def admin_list_services():
    current_services = load_services_from_db()
    return jsonify({"services": current_services})
>>>>>>> 3c38c0001fdb7593b786e29037d23d635bdb7bab


@app.route("/admin/services", methods=["POST"])
@admin_required
def admin_add_service():
    data = request.json
<<<<<<< HEAD
    entity_id = data["service_id"]
    fields = {
        config.entity_name_field: data["name"],
        "fee": data["fee"],
        "office": data["office"],
        "hours": data["hours"],
    }
    config.db_connector.add_entity(config, entity_id, fields, data.get("documents", []))
    engine.refresh()
=======
    add_service(
        data["service_id"], data["name"], data["fee"],
        data["office"], data["hours"], data["documents"]
    )
>>>>>>> 3c38c0001fdb7593b786e29037d23d635bdb7bab
    return jsonify({"success": True, "message": "Service added"})


@app.route("/admin/services/<service_id>", methods=["PUT"])
@admin_required
def admin_update_service(service_id):
    data = request.json
<<<<<<< HEAD
    fields = {
        config.entity_name_field: data["name"],
        "fee": data["fee"],
        "office": data["office"],
        "hours": data["hours"],
    }
    config.db_connector.update_entity(config, service_id, fields, data.get("documents", []))
    engine.refresh()
=======
    update_service(
        service_id, data["name"], data["fee"],
        data["office"], data["hours"], data["documents"]
    )
>>>>>>> 3c38c0001fdb7593b786e29037d23d635bdb7bab
    return jsonify({"success": True, "message": "Service updated"})


@app.route("/admin/services/<service_id>", methods=["DELETE"])
@admin_required
def admin_delete_service(service_id):
<<<<<<< HEAD
    config.db_connector.delete_entity(config, service_id)
    engine.refresh()
=======
    delete_service(service_id)
>>>>>>> 3c38c0001fdb7593b786e29037d23d635bdb7bab
    return jsonify({"success": True, "message": "Service deleted"})


if __name__ == "__main__":
<<<<<<< HEAD
    app.run(debug=True, port=5002, host="0.0.0.0")
=======
    app.run(debug=True, port=5002, host="localhost")
>>>>>>> 3c38c0001fdb7593b786e29037d23d635bdb7bab
