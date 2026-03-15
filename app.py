import os

from flask import Flask, render_template, request, jsonify
import chromadb
from chromadb.utils import embedding_functions

CHROMA_PATH = "./chroma_data"
COLLECTION_NAME = "analogies"
MODEL_NAME = "all-MiniLM-L6-v2"

app = Flask(__name__)

ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=MODEL_NAME
)


def get_collection():
    """Get a fresh collection reference each time."""
    try:
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        col = client.get_collection(
            name=COLLECTION_NAME,
            embedding_function=ef,
        )
        if col.count() == 0:
            return None
        return col
    except Exception:
        return None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/concepts")
def concepts():
    collection = get_collection()
    if collection is None:
        return jsonify([])
    all_meta = collection.get()["metadatas"]
    names = sorted(set(m["concept"] for m in all_meta))
    return jsonify(names)


@app.route("/search", methods=["POST"])
def search():
    collection = get_collection()
    if collection is None:
        return jsonify({"error": "Corpus not loaded. Run 'python load_corpus.py' first."}), 503

    data = request.get_json()
    concept = data.get("concept", "").strip()
    if not concept:
        return jsonify({"error": "Please provide a concept."}), 400

    n_results = min(data.get("n_results", 5), 20)
    exclude_ids = set(data.get("exclude_ids", []))

    try:
        results = collection.query(
            query_texts=[concept],
            n_results=n_results + len(exclude_ids),
        )
    except Exception:
        return jsonify({"error": "Search failed."}), 500

    analogies = []
    seen_analogies = set()
    if results["ids"] and results["ids"][0]:
        for i, doc_id in enumerate(results["ids"][0]):
            if doc_id in exclude_ids:
                continue
            meta = results["metadatas"][0][i]
            distance = results["distances"][0][i]
            analogy_text = meta["analogy"]
            if analogy_text in seen_analogies:
                continue
            seen_analogies.add(analogy_text)
            analogies.append({
                "id": doc_id,
                "concept": meta["concept"],
                "analogy": analogy_text,
                "distance": round(distance, 4),
            })

    return jsonify({"results": analogies})


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG", "").lower() == "true", port=5002)
