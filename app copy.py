from flask import Flask, jsonify, render_template, request

from orchestrator import orchestrate, setup_orchestrator

app = Flask(__name__)

services, vectorstore, llm, service_embeddings, embeddings_model = setup_orchestrator()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask_endpoint():
    data = request.json
    question = data.get("question", "")
    answer, sources = orchestrate(question, services, vectorstore, llm, service_embeddings, embeddings_model)
    return jsonify({"answer": answer, "sources": sources})

if __name__ == "__main__":
    app.run(debug=True, port=5002)