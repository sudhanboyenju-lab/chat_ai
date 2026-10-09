"""
Project-specific config for Hospital.
Same generic ai_engine as LocalGov and Restro - only this file changes per project.
"""

import os
from functools import partial

from dotenv import load_dotenv

load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from ai_engine.config import EngineConfig
from ai_engine.connectors import MySQLConnector
from ai_engine.orchestrator import Engine
from db import get_connection

if not (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")):
    raise RuntimeError(
        "GOOGLE_API_KEY (or GEMINI_API_KEY) is not set. "
        "Add it to your .env file or export it in your shell."
    )

config = EngineConfig(
    project_name="hospital",
    entity_table="doctors",
    entity_id_field="doctor_id",
    entity_name_field="doctor_name",
    detail_fields=["specialization", "department", "fee", "availability"],
    child_table="doctor_qualifications",
    child_fk_field="doctor_id",
    child_value_field="qualification",

    # Bound to its own "hospital" database, same pattern as Restro -> "restro".
    db_connector=MySQLConnector(partial(get_connection, database="hospital")),

    embeddings_model=GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001"),
    llm=ChatGoogleGenerativeAI(model="gemini-3.6-flash", temperature=0.2),

    fallback_message_en="We don't have information about that doctor. Please contact the hospital reception.",
    fallback_message_native="त्यो डाक्टरको बारेमा हामीसँग जानकारी छैन। कृपया अस्पतालको रिसेप्सनमा सम्पर्क गर्नुहोस्।",
    apply_intent_phrases=[
        "book an appointment",
        "i want to see a doctor",
        "schedule an appointment",
        "अपोइन्टमेन्ट लिन चाहन्छु",
    ],
)

engine = Engine(config, persist_dir="./chroma_hospital")
