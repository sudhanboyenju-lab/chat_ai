import json

import mysql.connector

with open("services_db.json", "r", encoding="utf-8") as f:
    services = json.load(f)

conn = mysql.connector.connect(
    host="localhost",
    port=3306,
    user="root",
    password="",
    database="chatai"
)
cursor = conn.cursor()

for service_id, data in services.items():
    cursor.execute(
        "INSERT INTO services (service_id, name, fee, office, hours) VALUES (%s, %s, %s, %s, %s)",
        (service_id, data["name"], data["fee"], data["office"], data["hours"])
    )
    for doc in data["documents"]:
        cursor.execute(
            "INSERT INTO service_documents (service_id, document_name) VALUES (%s, %s)",
            (service_id, doc)
        )

conn.commit()
cursor.close()
conn.close()

print(f"Migrated {len(services)} services to MySQL.")
