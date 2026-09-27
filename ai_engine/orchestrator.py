import numpy as np

from .rag import rag_ask, setup_vectorstore
from .rule_engine import rule_engine_answer


def cosine_similarity(vec1, vec2):
    a, b = np.array(vec1), np.array(vec2)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


def build_entity_embeddings(entities, config):
    embeddings = {}
    for entity_id, data in entities.items():
        sample_details = data.get("documents", [])[:2]
        text = f"{data[config.entity_name_field]} - {', '.join(sample_details)}"
        embeddings[entity_id] = config.embeddings_model.embed_query(text)
    return embeddings


def route_question(question, entities, entity_embeddings, config):
    question_vector = config.embeddings_model.embed_query(question)

    best_id, best_score = None, -1
    for entity_id, vector in entity_embeddings.items():
        score = cosine_similarity(question_vector, vector)
        if score > best_score:
            best_score, best_id = score, entity_id

    if best_score >= config.similarity_threshold:
        return "rule_engine", best_id
    return "rag", None


def wants_to_apply(question, config):
    q = question.lower()
    return any(phrase in q for phrase in config.apply_intent_phrases)


class Engine:
    """One instance = one project's fully configured AI engine."""

    def __init__(self, config, persist_dir):
        self.config = config
        self.entities = config.db_connector.get_all_entities(config)
        self.vectorstore = setup_vectorstore(self.entities, config, persist_dir)
        self.entity_embeddings = build_entity_embeddings(self.entities, config)

    def refresh(self):
        """Call after admin add/edit/delete so routing + RAG see the latest data."""
        self.entities = self.config.db_connector.get_all_entities(self.config)
        self.entity_embeddings = build_entity_embeddings(self.entities, self.config)
        # Note: vectorstore itself needs a rebuild (delete persist_dir) to reflect new docs -
        # left as a manual step for now, same limitation as your original project.

    def ask(self, question, history=None):
        route, entity_id = route_question(question, self.entities, self.entity_embeddings, self.config)

        if route == "rule_engine":
            answer, sources = rule_engine_answer(entity_id, self.entities, self.config)
            action = None
            if wants_to_apply(question, self.config):
                action = {"status": "started", "entity": self.entities[entity_id][self.config.entity_name_field]}
            return answer, sources, action

        answer, sources = rag_ask(self.vectorstore, question, self.config, history=history)
        return answer, sources, None
