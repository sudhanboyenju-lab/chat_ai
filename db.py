import mysql.connector
from typing import Any


def get_connection():
    return mysql.connector.connect(
        host="localhost",
        port=3306,
        user="root",
        password="",
        database="chatai"
    )


def load_services_from_db():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM services")
    service_rows: list[dict[str, Any]] = cursor.fetchall()  # type: ignore

    services = {}
    for row in service_rows:
        services[row["service_id"]] = {
            "name": row["name"],
            "fee": row["fee"],
            "office": row["office"],
            "hours": row["hours"],
            "documents": []
        }

    cursor.execute("SELECT service_id, document_name FROM service_documents")
    doc_rows: list[dict[str, Any]] = cursor.fetchall()  # type: ignore

    for row in doc_rows:
        sid = row["service_id"]
        if sid in services:
            services[sid]["documents"].append(row["document_name"])

    cursor.close()
    conn.close()
    return services


def get_user(username):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user: dict[str, Any] = cursor.fetchone()  # type: ignore
    cursor.close()
    conn.close()
    return user


def create_user(username, password_hash, role="citizen"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
        (username, password_hash, role)
    )
    conn.commit()
    cursor.close()
    conn.close()