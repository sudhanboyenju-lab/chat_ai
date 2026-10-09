"""
Project-specific config for LocalGov.
This is the ONLY file that knows the word "service" or "birth_registration".
app.py imports `config` and `engine` from here and stays fully generic.
"""

import os

from dotenv import load_dotenv

load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from ai_engine.config import EngineConfig
from ai_engine.connectors import MySQLConnector
from ai_engine.orchestrator import Engine
from db import get_connection  # your existing connection function, unchanged

if not (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")):
    raise RuntimeError(
        "GOOGLE_API_KEY (or GEMINI_API_KEY) is not set. "
        "Add it to your .env file or export it in your shell."
    )

config = EngineConfig(
    project_name="localgov",
    entity_table="services",
    entity_id_field="service_id",
    entity_name_field="name",
    detail_fields=["fee", "office", "hours"],
    child_table="service_documents",
    child_fk_field="service_id",
    child_value_field="document_name",

    db_connector=MySQLConnector(get_connection),

    embeddings_model=GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001"),
    llm=ChatGoogleGenerativeAI(model="gemini-3.6-flash", temperature=0.2),

    fallback_message_en="We don't have information about this service. Please contact your local ward office.",
    fallback_message_native="यो सेवाको बारेमा हामीसँग जानकारी छैन। कृपया आफ्नो स्थानीय वडा कार्यालयमा सम्पर्क गर्नुहोस्।",
    apply_intent_phrases=["i want to apply", "start my application", "apply for", "आवेदन दिन"],

    # Situation-based guidance: lets a citizen describe a real-life situation
    # ("my father passed away and I want to transfer his land") and get back
    # an ordered set of steps, instead of only answering direct questions.
    # The table is auto-created empty on first run - add rows via phpMyAdmin
    # once you know your real service_id values.
    dependency_table="service_dependencies",
    dependency_from_field="service_id",
    dependency_requires_field="requires_service_id",
    dependency_note_field="note",
)

# One-time setup - runs once when the Flask process starts, same as your old
# `setup_orchestrator()` call did.
engine = Engine(config, persist_dir="./chroma_localgov")