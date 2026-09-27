"""
Generic configuration for the RAG engine.
No knowledge of any specific domain (services, birth_registration, etc.)
lives here - everything domain-specific is passed in by the caller.
"""

from dataclasses import dataclass, field

from ai_engine.connectors import (
    BaseConnector,  # <-- real interface, not a bare Callable
)


@dataclass
class EngineConfig:
    """
    Everything the generic AI engine needs to know about ONE project's data.
    Each project (LocalGov, Health, Restro, LMS...) creates one of these
    instead of the engine having any domain-specific code baked in.
    """

    # --- Identity ---
    project_name: str

    # --- Database shape ---
    entity_table: str
    entity_id_field: str
    entity_name_field: str
    detail_fields: list[str] = field(default_factory=list)
    child_table: str | None = None
    child_fk_field: str | None = None
    child_value_field: str | None = None

    # --- Behaviour tuning ---
    similarity_threshold: float = 0.75
    rag_k: int = 3
    rag_score_threshold: float = 0.8

    # --- Pluggable pieces (dependency injection) ---
    db_connector: BaseConnector = None      # type: ignore[assignment]  # was `Callable` - wrong type
    embeddings_model: object = None
    llm: object = None
    fallback_message_en: str = "We don't have information about this."
    fallback_message_native: str = ""

    # --- Optional extras ---
    apply_intent_phrases: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.db_connector is None:
            raise ValueError("db_connector is required")
        if self.embeddings_model is None:
            raise ValueError("embeddings_model is required")
        if self.llm is None:
            raise ValueError("llm is required")