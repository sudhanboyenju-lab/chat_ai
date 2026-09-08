import json

import numpy as np

from rag_engine import ask as rag_ask
from rag_engine import setup_pipeline


# Loading services
def load_services(json_path="services_db.json"):
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

def build_service_embeddings(services, embeddings_model):
    """Embed each service's name once, ahead of time."""
    service_embeddings = {}
    for service_id, data in services.items():
        text = f"{data['name']} - {', '.join(data['documents'][:2])}"
        vector = embeddings_model.embed_query(text)
        service_embeddings[service_id] = vector
    return service_embeddings

def setup_orchestrator():
    services = load_services()
    vectorstore, llm = setup_pipeline()

    # We need the embeddings model separately, not just the vectorstore
    from langchain_google_genai import GoogleGenerativeAIEmbeddings
    embeddings_model = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

    service_embeddings = build_service_embeddings(services, embeddings_model)

    return services, vectorstore, llm, service_embeddings, embeddings_model

#services: a plain dictionary of json
#vectorstore: a langchain vectorstore object
#llm: a langchain llm object
#service_embeddings: a dictionary of service_id to embedding vector
#embeddings_model: a langchain embeddings model object

# Measures how close two vectors are in meaning
def cosine_similarity(vec1, vec2):
    a = np.array(vec1)
    b = np.array(vec2)
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def route_question(question, services, service_embeddings, embeddings_model, similarity_threshold=0.75):
    question_vector = embeddings_model.embed_query(question)

    best_service = None
    best_score = -1

    for service_id, service_vector in service_embeddings.items():
        score = cosine_similarity(question_vector, service_vector)
        if score > best_score:
            best_score = score
            best_service = service_id

    if best_score >= similarity_threshold:
        return "rule_engine", best_service

    return "rag", None

def rule_engine_answer(service_id, services):
    data = services[service_id]
    answer = f"""**{data['name']}**

    Documents required:
    {chr(10).join(['- ' + doc for doc in data['documents']])}

    Fee: {data['fee']}
    Office: {data['office']}
    Hours: {data['hours']}"""
    return answer, [service_id]

def orchestrate(question, services, vectorstore, llm, service_embeddings, embeddings_model):
    route, service_id = route_question(question, services, service_embeddings, embeddings_model)

    if route == "rule_engine":
        print(f"[Routed to: Rule Engine - {service_id}]")
        return rule_engine_answer(service_id, services)
    else:
        print("[Routed to: RAG]")
        return rag_ask(vectorstore, llm, question)