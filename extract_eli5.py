"""
Extract analogy candidates from the ELI5 dataset.

Scans the dataset for answers that contain analogy patterns
("it's like", "think of it as", "imagine", etc.), extracts them,
and writes candidates to a review file (candidates.json).

You review/edit the candidates, then merge the good ones into corpus.json.

Usage:
    python extract_eli5.py                  # Default: scan 50k entries, keep top 200
    python extract_eli5.py --scan 100000    # Scan more entries
    python extract_eli5.py --keep 500       # Keep more candidates
"""

import argparse
import json
import re
from datasets import load_dataset

# Phrases that signal an analogy is being made
ANALOGY_PATTERNS = [
    r"\bit'?s like\b",
    r"\bthink of it as\b",
    r"\bthink of it like\b",
    r"\bimagine\b",
    r"\bpretend\b",
    r"\banalog(?:y|ous)\b",
    r"\bsimilar to\b",
    r"\bsame way\b",
    r"\bjust like\b",
    r"\bpicture\b",
    r"\bsay you have\b",
    r"\blet'?s say\b",
    r"\bfor example,? imagine\b",
    r"\blike having\b",
    r"\blike when\b",
]

COMPILED_PATTERNS = [re.compile(p, re.IGNORECASE) for p in ANALOGY_PATTERNS]

# Technical/scientific topic keywords — question must match at least one
TOPIC_KEYWORDS = [
    # Computer science & software
    "computer", "software", "hardware", "program", "code", "algorithm",
    "internet", "network", "server", "database", "encrypt", "decrypt",
    "password", "hack", "virus", "malware", "firewall", "router",
    "wifi", "bluetooth", "binary", "bit", "byte", "pixel", "cpu", "gpu",
    "ram", "memory", "cache", "bandwidth", "latency", "compile", "debug",
    "api", "protocol", "http", "tcp", "ip address", "dns", "url",
    "cloud", "virtual", "container", "docker", "linux", "operating system",
    "file system", "process", "thread", "kernel", "machine learning",
    "artificial intelligence", "neural network", "deep learning",
    "blockchain", "bitcoin", "crypto", "data structure", "recursion",
    # Science & engineering
    "atom", "molecule", "electron", "proton", "neutron", "photon",
    "quantum", "gravity", "relativity", "spacetime", "black hole",
    "light speed", "wavelength", "frequency", "radiation", "magnetic",
    "electric", "voltage", "current", "circuit", "transistor", "semiconductor",
    "nuclear", "fission", "fusion", "radioactive", "half-life", "isotope",
    "dna", "rna", "gene", "protein", "cell", "enzyme", "bacteria",
    "virus", "immune", "vaccine", "antibiotic", "evolution", "natural selection",
    "entropy", "thermodynamic", "energy", "force", "momentum", "acceleration",
    "orbit", "satellite", "telescope", "spectrum", "doppler", "redshift",
    "chemical", "reaction", "catalyst", "oxidation", "ph", "acid", "base",
    # Math
    "calculus", "derivative", "integral", "probability", "statistics",
    "exponential", "logarithm", "dimension", "infinity", "prime number",
    "encryption", "compression", "fourier",
]
COMPILED_TOPIC_PATTERNS = [re.compile(rf"\b{kw}\b", re.IGNORECASE) for kw in TOPIC_KEYWORDS]

# Minimum answer quality filters
MIN_ANSWER_LENGTH = 100
MAX_ANSWER_LENGTH = 800


def count_analogy_signals(text):
    """Count how many analogy patterns appear in the text."""
    return sum(1 for p in COMPILED_PATTERNS if p.search(text))


def is_technical_topic(question, answer):
    """Check if the Q&A is about a technical or scientific topic."""
    text = f"{question} {answer}"
    return any(p.search(text) for p in COMPILED_TOPIC_PATTERNS)


def is_good_candidate(question, answer):
    """Check if a Q&A pair is a good analogy candidate."""
    if len(answer) < MIN_ANSWER_LENGTH or len(answer) > MAX_ANSWER_LENGTH:
        return False

    signals = count_analogy_signals(answer)
    if signals == 0:
        return False

    if not is_technical_topic(question, answer):
        return False

    return True


def extract_candidates(scan_limit=50000, keep_limit=200):
    """Scan the ELI5 dataset and extract analogy candidates."""
    print(f"Loading ELI5 dataset (scanning first {scan_limit} entries)...")
    dataset = load_dataset(
        "sentence-transformers/eli5",
        split=f"train[:{scan_limit}]",
    )

    print(f"Scanning {len(dataset)} entries for analogy patterns...")
    candidates = []

    for i, entry in enumerate(dataset):
        question = entry["question"].strip()
        answer = entry["answer"].strip()

        if not is_good_candidate(question, answer):
            continue

        signals = count_analogy_signals(answer)
        candidates.append({
            "question": question,
            "answer": answer,
            "analogy_signals": signals,
            "source_index": i,
        })

    # Sort by number of analogy signals (more = more likely a good analogy)
    candidates.sort(key=lambda x: x["analogy_signals"], reverse=True)
    candidates = candidates[:keep_limit]

    print(f"Found {len(candidates)} candidates (keeping top {keep_limit}).")
    return candidates


def save_candidates(candidates, output_file="candidates.json"):
    """Save candidates in a review-friendly format."""
    review_entries = []
    for i, c in enumerate(candidates):
        review_entries.append({
            "id": i + 1,
            "question": c["question"],
            "answer": c["answer"],
            "analogy_signals": c["analogy_signals"],
            # Fields for you to fill in during review:
            "keep": True,
            "concept": "",
            "domain": "",
            "audience": "beginner",
        })

    with open(output_file, "w") as f:
        json.dump(review_entries, f, indent=2)

    print(f"Saved to {output_file}")
    print()
    print("Next steps:")
    print(f"  1. Open {output_file} and review the candidates")
    print('  2. Set "keep": false for bad ones')
    print('  3. Fill in "concept" and "domain" for the good ones')
    print("  4. Run: python merge_candidates.py")


def main():
    parser = argparse.ArgumentParser(description="Extract analogy candidates from ELI5")
    parser.add_argument("--scan", type=int, default=50000, help="Number of entries to scan")
    parser.add_argument("--keep", type=int, default=200, help="Max candidates to keep")
    args = parser.parse_args()

    candidates = extract_candidates(scan_limit=args.scan, keep_limit=args.keep)
    save_candidates(candidates)


if __name__ == "__main__":
    main()
