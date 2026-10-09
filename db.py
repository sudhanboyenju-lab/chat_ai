from typing import Any

import mysql.connector


def get_connection(database="chatai"):
    return mysql.connector.connect(
        host="localhost",
        port=3306,
        user="root",
        password="",
        database=database
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


def add_service(service_id, name, fee, office, hours, documents):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO services (service_id, name, fee, office, hours) VALUES (%s, %s, %s, %s, %s)",
        (service_id, name, fee, office, hours)
    )

    for doc in documents:
        cursor.execute(
            "INSERT INTO service_documents (service_id, document_name) VALUES (%s, %s)",
            (service_id, doc)
        )

    conn.commit()
    cursor.close()
    conn.close()


def update_service(service_id, name, fee, office, hours, documents):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE services SET name=%s, fee=%s, office=%s, hours=%s WHERE service_id=%s",
        (name, fee, office, hours, service_id)
    )

    # Simplest approach: delete old documents, insert the new full list
    cursor.execute("DELETE FROM service_documents WHERE service_id=%s", (service_id,))
    for doc in documents:
        cursor.execute(
            "INSERT INTO service_documents (service_id, document_name) VALUES (%s, %s)",
            (service_id, doc)
        )

    conn.commit()
    cursor.close()
    conn.close()


def delete_service(service_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM service_documents WHERE service_id=%s", (service_id,))
    cursor.execute("DELETE FROM services WHERE service_id=%s", (service_id,))
    conn.commit()
    cursor.close()
    conn.close()