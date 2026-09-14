from werkzeug.security import check_password_hash, generate_password_hash

from db import create_user, get_user


def register_user(username, password, role="citizen"):
    if get_user(username):
        return False, "Username already exists"

    password_hash = generate_password_hash(password)
    create_user(username, password_hash, role)
    return True, "Registered successfully"


def verify_user(username, password):
    user = get_user(username)
    if user is None:
        return False, None

    if check_password_hash(user["password_hash"], password):
        return True, user["role"]
    return False, None