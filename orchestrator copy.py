import json

from rag_engine import ask as rag_ask
from rag_engine import setup_pipeline


def load_services(json_path="services_db.json"):
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

def route_question(question, services):
    """Decide: exact service lookup, or RAG needed?"""
    question_lower = question.lower()

    for service_id, data in services.items():
        if service_id.replace("_", " ") in question_lower or data["name"].lower() in question_lower:
            return "rule_engine", service_id

    return "rag", None

def rule_engine_answer(service_id, services):
    """Direct, exact answer from structured data - no LLM needed."""
    data = services[service_id]
    answer = f"""**{data['name']}**

    Documents required:
    {chr(10).join(['- ' + doc for doc in data['documents']])}

    Fee: {data['fee']}
    Office: {data['office']}
    Hours: {data['hours']}"""
    return answer, [service_id]

def setup_orchestrator():
    services = load_services()
    vectorstore, llm = setup_pipeline()
    return services, vectorstore, llm

def orchestrate(question, services, vectorstore, llm):
    route, service_id = route_question(question, services)

    if route == "rule_engine":
        print(f"[Routed to: Rule Engine - {service_id}]")
        return rule_engine_answer(service_id, services)
    else:
        print("[Routed to: RAG]")
        return rag_ask(vectorstore, llm, question)