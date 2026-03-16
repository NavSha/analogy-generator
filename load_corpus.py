import json
import chromadb

CORPUS_FILE = "corpus.json"
CHROMA_PATH = "./chroma_data"
COLLECTION_NAME = "analogies"


def load():
    with open(CORPUS_FILE) as f:
        entries = json.load(f)

    client = chromadb.PersistentClient(path=CHROMA_PATH)

    # Delete existing collection to avoid stale data
    try:
        client.delete_collection(name=COLLECTION_NAME)
    except Exception:
        pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
    )

    # Batch upsert to avoid timeouts during embedding
    batch_size = 50
    for i in range(0, len(entries), batch_size):
        batch = entries[i:i + batch_size]
        collection.upsert(
            ids=[e["id"] for e in batch],
            documents=[f"{e['concept']}. {e['analogy']}" for e in batch],
            metadatas=[
                {
                    "concept": e["concept"],
                    "analogy": e["analogy"],
                    "category": e.get("category", "Uncategorized"),
                }
                for e in batch
            ],
        )
        print(f"  Loaded batch {i // batch_size + 1} ({min(i + batch_size, len(entries))}/{len(entries)})")

    print(f"Loaded {len(entries)} analogies into ChromaDB.")
    print(f"Collection '{COLLECTION_NAME}' now has {collection.count()} entries.")


if __name__ == "__main__":
    load()
