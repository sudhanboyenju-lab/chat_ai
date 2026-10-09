import os
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import wraps

from flask import Flask, jsonify, request, session
from flask_cors import CORS

from ai_engine.analytics import ensure_log_table, get_top_questions, log_question
from ai_engine.asr import transcribe
from ai_engine.cache import ensure_cache_table
from ai_engine.guidance import ensure_dependency_table
from ai_engine.ocr import (
    ALLOWED_MIME_TYPES,
    MAX_IMAGE_BYTES,
    extract_text,
    identify_document,
)
from ai_engine.orchestrator import route_question
from auth import register_user, verify_user
from citizens import (
    DuplicateCitizen,
    delete_citizen,
    ensure_citizen_table,
    extract_card_fields,
    field_schema,
    get_citizen,
    insert_citizen,
    list_citizens,
)
from localgov_config import config, engine

app = Flask(__name__)
# CORS(app, supports_credentials=True, origins=["http://192.168.1.6:5173"])
CORS(app, supports_credentials=True, origins=["http://localhost:5173"])

app.secret_key = "dev-secret-key-change-this-later"  # TODO: move to .env before deploying

app.config.update(
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_NAME="localgov_session",
)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # reject huge uploads (voice/OCR) early

ensure_log_table(config.db_connector)
ensure_cache_table(config.db_connector)
ensure_dependency_table(config.db_connector, config)
ensure_citizen_table(config.db_connector)


# --- Auth guards ---
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


# --- Shared per-question logic, used by /ask, /ask-batch and /ask-voice ---
def answer_one(question, history=None):
    # engine.entities / engine.entity_embeddings are the same cached data
    # the Engine uses internally - we re-run the routing call here only to
    # surface `route` and `service_id` in the API response.
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


# --- Single question ---
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
        futures = [executor.submit(answer_one, q) for q in questions]
        for future in as_completed(futures):
            results.append(future.result())

    return jsonify({"results": results})


# --- Voice question: audio in, transcript + answer out ---
@app.route("/ask-voice", methods=["POST"])
@login_required
def ask_voice():
    f = request.files.get("audio")
    if not f:
        return jsonify({"error": "No audio received"}), 400

    suffix = os.path.splitext(f.filename or "")[1] or ".webm"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        f.save(tmp.name)
        path = tmp.name

    try:
        question = transcribe(path, config, language_hint="Nepali or English")
    except Exception as e:  # noqa: BLE001 - any ASR failure must return a clean error, not a 500
        print(f"[asr] failed: {type(e).__name__}: {e}")
        return jsonify({"error": "Could not process the audio"}), 500
    finally:
        os.remove(path)  # never keep recordings

    if not question:
        return jsonify({"error": "No speech detected"}), 422

    history = session.get("history", [])
    try:
        result = answer_one(question, history=history)  # also logs the question for Top 5
    except Exception as e:  # noqa: BLE001 - keep the transcript visible even if answering fails
        print(f"[ask-voice] answering failed: {type(e).__name__}: {e}")
        return jsonify({"error": f'I heard "{question}", but could not answer right now.'}), 500

    history.append({"question": question, "answer": result["answer"]})
    session["history"] = history

    return jsonify({
        "question": question,
        "answer": result["answer"],
        "sources": result["sources"],
        "route": result["route"],
        "action": result["action"],
    })


# --- Document upload: image in, extracted text + detected document type out ---
@app.route("/ocr", methods=["POST"])
@login_required
def ocr_endpoint():
    f = request.files.get("image")
    if not f:
        return jsonify({"error": "No image received"}), 400

    if f.mimetype not in ALLOWED_MIME_TYPES:
        return jsonify({"error": "Please upload a JPG, PNG or WebP photo."}), 415

    image_bytes = f.read()  # kept in memory only - nothing is saved to disk
    if len(image_bytes) > MAX_IMAGE_BYTES:
        return jsonify({"error": "The image is too large (maximum 8 MB)."}), 413

    try:
        text = extract_text(image_bytes, f.mimetype, config)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:  # noqa: BLE001 - any OCR failure must return a clean error, not a 500
        # Deliberately NOT printing the image or extracted text (personal data).
        print(f"[ocr] failed: {type(e).__name__}: {e}")
        return jsonify({"error": "Could not read the document"}), 500

    if not text:
        return jsonify({"error": "No text found. Try a clearer, well-lit photo."}), 422

    document, service_ids = identify_document(text, engine.entities, config)
    needed_for = [
        {"service_id": sid, "name": engine.entities[sid][config.entity_name_field]}
        for sid in service_ids
    ]
    return jsonify({"text": text, "document": document, "needed_for": needed_for})


# --- Citizen records (admin only): read a citizenship card, confirm, store, list ---
@app.route("/citizens/schema", methods=["GET"])
@admin_required
def citizens_schema():
    return jsonify({"schema": field_schema()})


@app.route("/citizens/extract", methods=["POST"])
@admin_required
def citizens_extract():
    f = request.files.get("image")
    if not f:
        return jsonify({"error": "No image received"}), 400
    if f.mimetype not in ALLOWED_MIME_TYPES:
        return jsonify({"error": "Please upload a JPG, PNG or WebP photo."}), 415

    image_bytes = f.read()  # memory only - the photo is never saved
    if len(image_bytes) > MAX_IMAGE_BYTES:
        return jsonify({"error": "The image is too large (maximum 8 MB)."}), 413

    try:
        fields = extract_card_fields(image_bytes, f.mimetype, config)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:  # noqa: BLE001 - any failure must return a clean error, not a 500
        # Deliberately not printing field values (personal data).
        print(f"[citizens] extract failed: {type(e).__name__}: {e}")
        return jsonify({"error": "Could not read the card"}), 500

    if not any(fields.values()):
        return jsonify({"error": "Could not find card details. Try a clearer, well-lit photo."}), 422
    return jsonify({"fields": fields})


@app.route("/citizens", methods=["POST"])
@admin_required
def citizens_create():
    data = request.json or {}
    try:
        citizen_id = insert_citizen(config.db_connector, data, session["username"])
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except DuplicateCitizen:
        return jsonify({"error": "A record with this certificate number and district already exists."}), 409
    except Exception as e:  # noqa: BLE001
        print(f"[citizens] save failed: {type(e).__name__}: {e}")
        return jsonify({"error": "Could not save the record"}), 500
    print(f"[audit] {session['username']} added citizen id={citizen_id}")
    return jsonify({"success": True, "id": citizen_id}), 201


@app.route("/citizens", methods=["GET"])
@admin_required
def citizens_list():
    q = request.args.get("q", "")
    return jsonify({"citizens": list_citizens(config.db_connector, q)})


@app.route("/citizens/<int:citizen_id>", methods=["GET"])
@admin_required
def citizens_detail(citizen_id):
    citizen = get_citizen(config.db_connector, citizen_id)
    if not citizen:
        return jsonify({"error": "Record not found"}), 404
    print(f"[audit] {session['username']} viewed citizen id={citizen_id}")
    return jsonify({"citizen": citizen})


@app.route("/citizens/<int:citizen_id>", methods=["DELETE"])
@admin_required
def citizens_delete(citizen_id):
    if not delete_citizen(config.db_connector, citizen_id):
        return jsonify({"error": "Record not found"}), 404
    print(f"[audit] {session['username']} deleted citizen id={citizen_id}")
    return jsonify({"success": True})


# --- Top questions panel ---
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