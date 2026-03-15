import json
import chromadb
from chromadb.utils import embedding_functions

CORPUS_FILE = "corpus.json"
CHROMA_PATH = "./chroma_data"
COLLECTION_NAME = "analogies"
MODEL_NAME = "all-MiniLM-L6-v2"


def load():
    with open(CORPUS_FILE) as f:
        entries = json.load(f)

    client = chromadb.PersistentClient(path=CHROMA_PATH)
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=MODEL_NAME
    )

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=ef,
    )

    collection.upsert(
        ids=[e["id"] for e in entries],
        documents=[f"{e['concept']}. {e['analogy']}" for e in entries],
        metadatas=[
            {
                "concept": e["concept"],
                "analogy": e["analogy"],
                "domain": e["domain"],
                "audience": e["audience"],
            }
            for e in entries
        ],
    )

    print(f"Loaded {len(entries)} analogies into ChromaDB.")
    print(f"Collection '{COLLECTION_NAME}' now has {collection.count()} entries.")


if __name__ == "__main__":
    load()
