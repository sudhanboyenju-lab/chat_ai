from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document


def build_documents(entities, config):
    """Turn ANY project's entity dict into LangChain Documents - domain agnostic."""
    documents = []
    for entity_id, data in entities.items():
        lines = [f"{config.entity_name_field.title()}: {data[config.entity_name_field]}"]

        for field_name in config.detail_fields:
            if field_name in data:
                lines.append(f"{field_name.title()}: {data[field_name]}")

        if data.get("documents"):
            lines.append("Details: " + ", ".join(data["documents"]))

        documents.append(Document(
            page_content="\n".join(lines),
            metadata={"source": entity_id, "name": data[config.entity_name_field]}
        ))
    return documents


def setup_vectorstore(entities, config, persist_dir):
    import os
    documents = build_documents(entities, config)

    if os.path.exists(persist_dir):
        return Chroma(persist_directory=persist_dir, embedding_function=config.embeddings_model)
    return Chroma.from_documents(documents, config.embeddings_model, persist_directory=persist_dir)


def get_response_text(response):
    if isinstance(response.content, str):
        return response.content
    if isinstance(response.content, list):
        parts = []
        for block in response.content:
            if isinstance(block, dict) and block.get("type") == "text":
                parts.append(block["text"])
            elif isinstance(block, str):
                parts.append(block)
        return "".join(parts)
    return str(response.content) if response.content is not None else ""


def rag_ask(vectorstore, question, config, history=None):
    history = history or []

    results_with_scores = vectorstore.similarity_search_with_score(question, k=config.rag_k)
    relevant = [(doc, score) for doc, score in results_with_scores if score < config.rag_score_threshold]

    if not relevant:
        msg = config.fallback_message_native if _looks_native(question, config) else config.fallback_message_en
        return msg, []

    docs = [doc for doc, _ in relevant]
    retrieved_text = "\n\n".join(doc.page_content for doc in docs)
    sources = [doc.metadata.get("source", "unknown") for doc in docs]

    history_text = ""
    if history:
        history_text = "Previous conversation:\n"
        for h in history[-3:]:
            history_text += f"User: {h['question']}\nAssistant: {h['answer']}\n\n"

    prompt = f"""Answer the question using ONLY the information below. Answer in the same language as the question. If the answer isn't in the information, say you don't know.

{history_text}Information:
{retrieved_text}

Question: {question}
"""
    # This is the LLM call that was previously unprotected: if it raises
    # (API error, safety filter, quota, network) the whole /ask request used
    # to 500. Now it degrades to the fallback message instead of crashing,
    # and the print() gives you the real cause in your terminal to diagnose.
    try:
        response = config.llm.invoke(prompt)
        answer = get_response_text(response)
        if not answer.strip():
            raise ValueError("LLM returned an empty response")
        return answer, sources
    except Exception as e:
        print(f"[rag_ask] LLM call failed for question {question!r}: {type(e).__name__}: {e}")
        msg = config.fallback_message_native if _looks_native(question, config) else config.fallback_message_en
        return msg, sources


def _looks_native(text, config):
    if not config.fallback_message_native:
        return False
    return any('\u0900' <= ch <= '\u097F' for ch in text)  # Devanagari range; extend per language as needed
