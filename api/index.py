from flask import Flask, request, jsonify
import requests, os, uuid

app = Flask(__name__)

API_URL = "https://leakosintapi.com/"
API_TOKEN = os.environ.get("API_TOKEN")

cache = {}  # temporary cache {query_id: {"pages": [...]}}

@app.route("/api/search", methods=["POST"])
def search():
    try:
        data = request.get_json()
        query = data.get("query", "").strip()
        if not query:
            return jsonify({"error": "Missing query"}), 400
        if not API_TOKEN:
            return jsonify({"error": "API token not set"}), 500

        payload = {"token": API_TOKEN, "request": query, "limit": 300, "lang": "en"}
        r = requests.post(API_URL, json=payload, timeout=30)
        res = r.json()

        # Handle bad responses
        if "error" in res:
            return jsonify({"error": res["error"]}), 400

        text = res.get("text") or "No data found."
        # split pages every ~2500 chars for smoother display
        pages = [text[i:i+2500] for i in range(0, len(text), 2500)] or ["No data."]
        query_id = str(uuid.uuid4())
        cache[query_id] = {"pages": pages}

        return jsonify({
            "query_id": query_id,
            "pages_count": len(pages),
            "page_text": pages[0]
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/page", methods=["POST"])
def get_page():
    try:
        data = request.get_json()
        qid = data.get("query_id")
        page = int(data.get("page", 0))
        if qid not in cache:
            return jsonify({"error": "Query not found"}), 404
        pages = cache[qid]["pages"]
        if page < 0 or page >= len(pages):
            return jsonify({"error": "Invalid page"}), 400
        return jsonify({"page_text": pages[page]})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)
