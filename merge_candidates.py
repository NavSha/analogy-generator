"""
Merge reviewed candidates into corpus.json.

After reviewing candidates.json (setting keep/concept/domain fields),
run this script to merge the approved ones into the main corpus.

Usage:
    python merge_candidates.py
    python merge_candidates.py --input my_candidates.json
"""

import argparse
import json
import re


def slugify(text):
    """Convert text to a URL-friendly slug."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s-]+", "-", text)
    return text[:30]


def merge(input_file="candidates.json", corpus_file="corpus.json"):
    with open(input_file) as f:
        candidates = json.load(f)

    with open(corpus_file) as f:
        corpus = json.load(f)

    existing_ids = {e["id"] for e in corpus}
    added = 0
    skipped = 0

    for c in candidates:
        if not c.get("keep", False):
            skipped += 1
            continue

        concept = c.get("concept", "").strip()
        domain = c.get("domain", "").strip()
        audience = c.get("audience", "beginner").strip()
        analogy = c.get("answer", "").strip()

        if not concept or not analogy:
            print(f"  Skipping #{c['id']}: missing concept or answer")
            skipped += 1
            continue

        # Generate a unique ID
        base_id = f"{slugify(concept)}-{slugify(domain or 'general')}"
        entry_id = base_id
        counter = 1
        while entry_id in existing_ids:
            counter += 1
            entry_id = f"{base_id}-{counter:03d}"

        corpus.append({
            "id": entry_id,
            "concept": concept,
            "analogy": analogy,
            "domain": domain or "everyday life",
            "audience": audience,
        })
        existing_ids.add(entry_id)
        added += 1

    with open(corpus_file, "w") as f:
        json.dump(corpus, f, indent=2)

    print(f"Done. Added {added} entries, skipped {skipped}.")
    print(f"Corpus now has {len(corpus)} total entries.")
    print()
    print("Don't forget to reload ChromaDB:")
    print("  python load_corpus.py")


def main():
    parser = argparse.ArgumentParser(description="Merge reviewed candidates into corpus")
    parser.add_argument("--input", default="candidates.json", help="Reviewed candidates file")
    parser.add_argument("--corpus", default="corpus.json", help="Target corpus file")
    args = parser.parse_args()

    merge(input_file=args.input, corpus_file=args.corpus)


if __name__ == "__main__":
    main()
