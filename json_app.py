from flask import Flask, jsonify, render_template, request

from extra.json_db_engine import load_services, search_services

app = Flask(__name__)
services = load_services()

@app.route("/")
def home():
    return render_template("json_index.html", services=services)

@app.route("/search", methods=["POST"])
def search_endpoint():
    data = request.json
    query = data.get("query", "")
    results = search_services(query, services)
    return jsonify({"results": results})

if __name__ == "__main__":
    app.run(debug=True, port=5001)