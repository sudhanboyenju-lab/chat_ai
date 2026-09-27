"""
Creates the "restro" database (if it doesn't exist yet) on the same MySQL
server your app connects to, then applies restro_schema.sql to it.

Usage:
    python run_restro_schema.py
"""

from db import get_connection

SCHEMA_FILE = "restro_schema.sql"
DB_NAME = "restro"


def strip_sql_comments(sql_text: str) -> str:
    """Remove '-- comment' text from every line, whether it's a full-line
    comment or trails after real SQL, before we ever split on ';'."""
    cleaned_lines = []
    for line in sql_text.splitlines():
        idx = line.find("--")
        if idx != -1:
            line = line[:idx]
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines)


def ensure_database_exists():
    conn = get_connection(database=None)
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    cursor.close()
    conn.close()
    print(f"Database '{DB_NAME}' is ready.")


def run_schema():
    with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
        raw_sql = f.read()

    sql_text = strip_sql_comments(raw_sql)
    statements = [s.strip() for s in sql_text.split(";") if s.strip()]

    conn = get_connection(database=DB_NAME)
    cursor = conn.cursor()

    for stmt in statements:
        print(f"Running: {stmt.splitlines()[0][:60]}...")
        cursor.execute(stmt)

    conn.commit()
    cursor.close()
    conn.close()
    print(f"Done. Restro schema applied to the '{DB_NAME}' database.")


if __name__ == "__main__":
    ensure_database_exists()
    run_schema()