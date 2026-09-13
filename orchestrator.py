import json

import numpy as np
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from rag_engine import ask as rag_ask
from rag_engine import setup_pipeline


def load_services(json_path="services_db.json"):
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

def build_service_embeddings(services, embeddings_model):
    service_embeddings = {}
    for service_id, data in services.items():
        text = f"{data['name']} - {', '.join(data['documents'][:2])}"
        vector = embeddings_model.embed_query(text)
        service_embeddings[service_id] = vector
    return service_embeddings

def setup_orchestrator():
    services = load_services()

    # Build the embeddings model ONCE here, reuse it everywhere
    embeddings_model = GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")

    vectorstore, llm = setup_pipeline(embeddings_model)
    service_embeddings = build_service_embeddings(services, embeddings_model)

    return services, vectorstore, llm, service_embeddings, embeddings_model

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

def wants_to_apply(question):
    apply_phrases = ["i want to apply", "start my application", "apply for", "i want to start",
                      "begin my application", "आवेदन दिन", "सुरु गर्न"]
    question_lower = question.lower()
    return any(phrase in question_lower for phrase in apply_phrases)

def start_application(service_id, services):
    data = services[service_id]
    application_id = f"APP-{service_id[:4].upper()}-2026-{abs(hash(service_id)) % 10000:04d}"
    return {
        "status": "started",
        "service": data["name"],
        "application_id": application_id,
        "next_step": f"Visit {data['office']} with the required documents to complete your application."
    }

def orchestrate(question, services, vectorstore, llm, service_embeddings, embeddings_model, history=None):
    route, service_id = route_question(question, services, service_embeddings, embeddings_model)

    if route == "rule_engine":
        print(f"[Routed to: Rule Engine - {service_id}]")
        answer, sources = rule_engine_answer(service_id, services)

        action = None
        if wants_to_apply(question):
            print(f"[Intent detected: start application for {service_id}]")
            action = start_application(service_id, services)

        return answer, sources, action

    print("[Routed to: RAG]")
    answer, sources = rag_ask(vectorstore, llm, question, history=history)
    return answer, sources, None