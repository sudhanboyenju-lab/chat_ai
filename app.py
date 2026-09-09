from concurrent.futures import ThreadPoolExecutor, as_completed

from flask import Flask, jsonify, render_template, request

from orchestrator import orchestrate, setup_orchestrator

app = Flask(__name__)

services, vectorstore, llm, service_embeddings, embeddings_model = setup_orchestrator()

@app.route("/")
def home():
    return render_template("index.html")

def answer_one(question, services, vectorstore, llm, service_embeddings, embeddings_model):
    answer, sources = orchestrate(question, services, vectorstore, llm, service_embeddings, embeddings_model)
    return {"question": question, "answer": answer, "sources": sources}

@app.route("/ask", methods=["POST"])
def ask_endpoint():
    data = request.json
    question = data.get("question", "")
    result = answer_one(question, services, vectorstore, llm, service_embeddings, embeddings_model)
    return jsonify({"answer": result["answer"], "sources": result["sources"]})

@app.route("/ask-batch", methods=["POST"])
def ask_batch_endpoint():
    data = request.json
    questions = data.get("questions", [])
    questions = [q.strip() for q in questions if q.strip()]

    if not questions:
        return jsonify({"results": []})

    results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(answer_one, q, services, vectorstore, llm, service_embeddings, embeddings_model)
            for q in questions
        ]
        for future in as_completed(futures):
            results.append(future.result())

    return jsonify({"results": results})

if __name__ == "__main__":
    app.run(debug=True, port=5002)