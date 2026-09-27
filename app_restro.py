from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import wraps

from flask import Flask, jsonify, request, session
from flask_cors import CORS

from ai_engine.orchestrator import route_question
from auth import register_user, verify_user
from restro_config import (  # <-- only line that differs from LocalGov's app.py
    config,
    engine,
)

app = Flask(__name__)
# CORS(app, supports_credentials=True, origins=["http://192.168.1.6:5174"])
CORS(app, supports_credentials=True, origins=["http://localhost:5174"])

app.secret_key = "dev-secret-key-change-this-later"  # TODO: move to .env before deploying

app.config.update(
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_NAME="restro_session"
)


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


def answer_one(question, history=None):
    route, entity_id = route_question(question, engine.entities, engine.entity_embeddings, engine.config)
    answer, sources, action = engine.ask(question, history=history)
    return {
        "question": question,
        "answer": answer,
        "sources": sources,
        "action": action,
        "route": route,
        "item_id": entity_id,   # was "service_id" in LocalGov
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


# --- Admin CRUD for menu items ---
@app.route("/admin/menu-items", methods=["GET"])
@admin_required
def admin_list_menu_items():
    current_entities = config.db_connector.get_all_entities(config)
    return jsonify({"menu_items": current_entities})


@app.route("/admin/menu-items", methods=["POST"])
@admin_required
def admin_add_menu_item():
    data = request.json
    entity_id = data["item_id"]
    fields = {
        config.entity_name_field: data["dish_name"],
        "price": data["price"],
        "category": data["category"],
        "spice_level": data["spice_level"],
    }
    config.db_connector.add_entity(config, entity_id, fields, data.get("ingredients", []))
    engine.refresh()
    return jsonify({"success": True, "message": "Menu item added"})


@app.route("/admin/menu-items/<item_id>", methods=["PUT"])
@admin_required
def admin_update_menu_item(item_id):
    data = request.json
    fields = {
        config.entity_name_field: data["dish_name"],
        "price": data["price"],
        "category": data["category"],
        "spice_level": data["spice_level"],
    }
    config.db_connector.update_entity(config, item_id, fields, data.get("ingredients", []))
    engine.refresh()
    return jsonify({"success": True, "message": "Menu item updated"})


@app.route("/admin/menu-items/<item_id>", methods=["DELETE"])
@admin_required
def admin_delete_menu_item(item_id):
    config.db_connector.delete_entity(config, item_id)
    engine.refresh()
    return jsonify({"success": True, "message": "Menu item deleted"})


if __name__ == "__main__":
    app.run(debug=True, port=5003, host="0.0.0.0")
