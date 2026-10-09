"""
Citizen records: read a Nepali citizenship certificate photo, let staff confirm
the fields, store them, and list them.

Flow (nothing is saved until a person confirms the fields):
  1. extract_card_fields()  - photo -> suggested field values (NOT saved)
  2. staff review and correct the values in a form
  3. insert_citizen()       - saves the confirmed values
  4. list_citizens()        - searchable list, citizenship number masked

PRIVACY (this is personal data - confirm the rules with your seniors):
  - The photo is never written to disk or kept; only confirmed text fields are stored.
  - Every endpoint using this module is admin-only.
  - The list shows a masked citizenship number; the full record needs an explicit view.
  - Never log field values. Log ids only.

This module is MySQL-specific (it uses db_connector.get_connection()).
"""

import base64
import json
import re

from langchain_core.messages import HumanMessage
from mysql.connector import errors as mysql_errors

from ai_engine.ocr import validate_image
from ai_engine.rag import get_response_text

MAX_LEN = 150

# (column name, label shown in the form, required to save?)
FIELDS = [
    ("citizenship_no", "Citizenship certificate no.", True),
    ("full_name", "Full name", True),
    ("gender", "Gender", False),
    ("date_of_birth", "Date of birth (as printed, BS)", False),
    ("permanent_district", "Permanent district", False),
    ("permanent_municipality", "Permanent municipality", False),
    ("permanent_ward", "Ward no.", False),
    ("father_name", "Father's name", False),
    ("mother_name", "Mother's name", False),
    ("issued_district", "Issued district", False),
    ("issued_date", "Issued date (as printed, BS)", False),
]
FIELD_KEYS = [key for key, _label, _required in FIELDS]

_DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")


class DuplicateCitizen(Exception):
    """Same citizenship number and issued district already stored."""


def field_schema():
    return [{"key": k, "label": label, "required": req} for k, label, req in FIELDS]


def normalize_digits(text):
    """Nepali digits (०१२३) -> ASCII (0123), so numbers compare and search reliably."""
    return text.translate(_DEVANAGARI_DIGITS)


def clean_fields(data):
    """Keep only known fields, as trimmed strings. Unknown keys are dropped, so request
    data can never choose column names."""
    cleaned = {}
    for key in FIELD_KEYS:
        value = data.get(key, "") if isinstance(data, dict) else ""
        if value is None:
            value = ""
        if not isinstance(value, str):
            value = str(value)
        cleaned[key] = re.sub(r"\s+", " ", value).strip()[:MAX_LEN]
    # The certificate number is an identifier: store it with ASCII digits and no spaces.
    cleaned["citizenship_no"] = re.sub(r"\s+", "", normalize_digits(cleaned["citizenship_no"]))
    return cleaned


def validate_for_save(fields):
    for key, label, required in FIELDS:
        if required and not fields[key]:
            raise ValueError(f"{label} is required.")


def mask_number(number):
    if len(number) <= 4:
        return "*" * len(number)
    return "*" * (len(number) - 4) + number[-4:]


def _like(text):
    escaped = text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return f"%{escaped}%"


# ---------------------------------------------------------------- extraction

def extract_card_fields(image_bytes, mime_type, config):
    """Photo of a citizenship certificate -> dict of suggested values (all keys present,
    empty string when not found). One LLM call. Does NOT save anything."""
    validate_image(image_bytes, mime_type)
    image_b64 = base64.b64encode(image_bytes).decode()

    prompt = (
        "This is a photo of a Nepali citizenship certificate (नागरिकता प्रमाणपत्र). "
        "Read it and return ONLY a JSON object with exactly these keys:\n"
        "- citizenship_no: certificate number (प्रमाणपत्र नं.)\n"
        "- full_name: full name (नाम, थर)\n"
        "- gender: (लिङ्ग)\n"
        "- date_of_birth: (जन्म मिति), exactly as printed\n"
        "- permanent_district: district of permanent address (स्थायी ठेगाना, जिल्ला)\n"
        "- permanent_municipality: municipality / rural municipality (न.पा. / गा.पा.)\n"
        "- permanent_ward: ward number (वडा नं.)\n"
        "- father_name: (बाबुको नाम, थर)\n"
        "- mother_name: (आमाको नाम, थर)\n"
        "- issued_district: issuing district (जारी गर्ने जिल्ला)\n"
        "- issued_date: (जारी मिति), exactly as printed\n"
        "Rules: copy every value exactly as printed, in the original script (Nepali stays in "
        "Devanagari). Do NOT translate, transliterate, correct, or reformat. Copy digits exactly. "
        "If a field is missing or unreadable, use an empty string. NEVER guess. "
        "Output only the JSON object, no explanation."
    )
    message = HumanMessage(content=[
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": f"data:{mime_type};base64,{image_b64}"},
    ])
    reply = get_response_text(config.llm.invoke([message])).strip()

    match = re.search(r"\{.*\}", reply, re.DOTALL)
    if not match:
        return clean_fields({})
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return clean_fields({})
    return clean_fields(data)


# ------------------------------------------------------------------ database

def ensure_citizen_table(db_connector):
    """Creates the table if it doesn't exist. Safe to call on every startup."""
    columns = ",\n            ".join(f"{key} VARCHAR({MAX_LEN}) NOT NULL DEFAULT ''" for key in FIELD_KEYS)
    conn = db_connector.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS citizens (
                id INT AUTO_INCREMENT PRIMARY KEY,
                {columns},
                created_by VARCHAR(100) NOT NULL DEFAULT '',
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uniq_citizen (citizenship_no, issued_district)
            ) DEFAULT CHARSET=utf8mb4
        """)
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def insert_citizen(db_connector, data, created_by):
    """Validate and save ONE confirmed record. Returns the new id."""
    fields = clean_fields(data)
    validate_for_save(fields)

    columns = ", ".join(FIELD_KEYS)  # from our own allowlist, never from request keys
    placeholders = ", ".join(["%s"] * (len(FIELD_KEYS) + 1))
    values = [fields[key] for key in FIELD_KEYS] + [created_by]

    conn = db_connector.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            f"INSERT INTO citizens ({columns}, created_by) VALUES ({placeholders})", values
        )
        conn.commit()
        return cursor.lastrowid
    except mysql_errors.IntegrityError as e:
        if e.errno == 1062:  # duplicate entry
            raise DuplicateCitizen from None
        raise
    finally:
        cursor.close()
        conn.close()


def list_citizens(db_connector, query="", limit=200):
    """Newest first. Optional search by name or certificate number. Numbers are masked."""
    query = (query or "").strip()
    columns = "id, full_name, citizenship_no, permanent_municipality, permanent_district, created_at"

    conn = db_connector.get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        if query:
            cursor.execute(
                f"SELECT {columns} FROM citizens "
                "WHERE full_name LIKE %s OR citizenship_no LIKE %s ORDER BY id DESC LIMIT %s",
                (_like(query), _like(normalize_digits(query)), limit),
            )
        else:
            cursor.execute(f"SELECT {columns} FROM citizens ORDER BY id DESC LIMIT %s", (limit,))
        rows = cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

    for row in rows:
        row["citizenship_no"] = mask_number(row["citizenship_no"])
        row["created_at"] = str(row["created_at"])
    return rows


def get_citizen(db_connector, citizen_id):
    """Full record (unmasked) or None."""
    conn = db_connector.get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT * FROM citizens WHERE id = %s", (citizen_id,))
        row = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()
    if row:
        row["created_at"] = str(row["created_at"])
    return row


def delete_citizen(db_connector, citizen_id):
    conn = db_connector.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM citizens WHERE id = %s", (citizen_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        cursor.close()
        conn.close()
