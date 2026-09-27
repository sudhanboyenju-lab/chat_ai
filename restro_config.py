"""
Project-specific config for Restro.
Same generic ai_engine as LocalGov - only this file changes per project.
"""

import os
from functools import partial

from dotenv import load_dotenv

load_dotenv()

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings

from ai_engine.config import EngineConfig
from ai_engine.connectors import MySQLConnector
from ai_engine.orchestrator import Engine
from db import get_connection  # your existing connection function

if not (os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")):
    raise RuntimeError(
        "GOOGLE_API_KEY (or GEMINI_API_KEY) is not set. "
        "Add it to your .env file or export it in your shell."
    )

config = EngineConfig(
    project_name="restro",
    entity_table="menu_items",
    entity_id_field="item_id",
    entity_name_field="dish_name",
    detail_fields=["price", "category", "spice_level"],
    child_table="menu_item_ingredients",
    child_fk_field="item_id",
    child_value_field="ingredient_name",

    # Bound to the "restro" database specifically, so this never touches
    # LocalGov's "chatai" tables. LocalGov's own config keeps calling
    # get_connection() with no argument, which still defaults to "chatai".
    db_connector=MySQLConnector(partial(get_connection, database="restro")),

    embeddings_model=GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001"),
    llm=ChatGoogleGenerativeAI(model="gemini-3.6-flash", temperature=0.2),

    fallback_message_en="We don't have information about that dish. Please ask our staff.",
    fallback_message_native="यो परिकारको बारेमा हामीसँग जानकारी छैन। कृपया हाम्रो कर्मचारीलाई सोध्नुहोस्।",
    apply_intent_phrases=["i want to order", "add to cart", "order this", "म यो अर्डर गर्न चाहन्छु"],
)

engine = Engine(config, persist_dir="./chroma_restro")