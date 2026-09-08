from flask import Flask, jsonify, render_template, request

from orchestrator import orchestrate, setup_orchestrator

app = Flask(__name__)

# Set up everything once when the server starts
services, vectorstore, llm = setup_orchestrator()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/ask", methods=["POST"])
def ask_endpoint():
    data = request.json
    question = data.get("question", "")
    answer = orchestrate(question, services, vectorstore, llm)
    return jsonify({"answer": answer})

if __name__ == "__main__":
    app.run(debug=True, port=5002)