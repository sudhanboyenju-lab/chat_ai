import json
import os

from werkzeug.security import check_password_hash, generate_password_hash

USERS_FILE = "users.json"

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)

def register_user(username, password, role="citizen"):
    users = load_users()
    if username in users:
        return False, "Username already exists"

    users[username] = {
        "password_hash": generate_password_hash(password),
        "role": role
    }
    save_users(users)
    return True, "Registered successfully"

def verify_user(username, password):
    users = load_users()
    if username not in users:
        return False, None

    user = users[username]
    if check_password_hash(user["password_hash"], password):
        return True, user["role"]
    return False, None