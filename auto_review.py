"""
Auto-review candidates.json.

Applies heuristics to:
1. Discard low-quality entries (too rambling, off-topic, no clear analogy)
2. Auto-detect concept from the question
3. Auto-detect domain from the analogy content
4. Set audience level based on complexity signals

Run this, then manually spot-check the output.
"""

import json
import re

# Domain detection keywords — map words in the answer to domains
DOMAIN_SIGNALS = {
    "cooking": [
        "recipe", "cook", "kitchen", "ingredient", "bake", "oven", "chef",
        "food", "dish", "meal", "stir", "boil", "fry", "seasoning", "soup",
        "taste", "flavor",
    ],
    "sports": [
        "game", "player", "team", "score", "coach", "ball", "field",
        "match", "race", "athlete", "tournament", "goal", "referee",
        "basketball", "football", "soccer", "baseball", "tennis",
    ],
    "music": [
        "song", "music", "guitar", "piano", "band", "instrument", "melody",
        "chord", "note", "rhythm", "orchestra", "singer", "tune", "concert",
    ],
    "construction": [
        "building", "house", "brick", "foundation", "architect", "blueprint",
        "construction", "wall", "roof", "plumbing", "wire", "structure",
    ],
    "nature": [
        "river", "tree", "ocean", "mountain", "forest", "animal", "plant",
        "water", "rain", "seed", "grow", "ecosystem", "evolution", "species",
    ],
    "everyday life": [
        "car", "drive", "road", "phone", "store", "shop", "mail", "letter",
        "door", "key", "lock", "library", "book", "box", "room", "wallet",
        "bag", "clothes", "school", "class", "friend", "family", "lego",
    ],
}

# Topics that are NOT useful for a tech/concept analogy generator
REJECT_TOPICS = [
    r"divorce", r"gay marriage", r"sex", r"drug", r"arrest", r"rape",
    r"murder", r"suicide", r"penis", r"vagina", r"breast", r"porn",
    r"racist", r"racism", r"trump", r"obama", r"democrat", r"republican",
    r"god\b", r"bible", r"church", r"religion", r"pray",
    r"calories", r"weight loss", r"diet",
]
REJECT_PATTERNS = [re.compile(p, re.IGNORECASE) for p in REJECT_TOPICS]

# Technical/scientific topic keywords — must match at least one
TECHNICAL_KEYWORDS = [
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
    "immune", "vaccine", "antibiotic", "evolution", "natural selection",
    "entropy", "thermodynamic", "energy", "force", "momentum", "acceleration",
    "orbit", "satellite", "telescope", "spectrum", "doppler", "redshift",
    "chemical", "reaction", "catalyst", "oxidation", "ph", "acid", "base",
    # Math
    "calculus", "derivative", "integral", "probability", "statistics",
    "exponential", "logarithm", "dimension", "infinity", "prime number",
    "encryption", "compression", "fourier",
]
TECHNICAL_PATTERNS = [re.compile(rf"\b{kw}\b", re.IGNORECASE) for kw in TECHNICAL_KEYWORDS]

# Complexity signals for audience detection
ADVANCED_SIGNALS = [
    "quantum", "topology", "entropy", "thermodynamic", "eigenvalue",
    "differential equation", "fourier", "bayesian", "stochastic",
    "asymptotic", "polynomial time",
]
INTERMEDIATE_SIGNALS = [
    "algorithm", "protocol", "frequency", "wavelength", "molecule",
    "electron", "voltage", "binary", "compiler", "kernel", "bandwidth",
    "latency", "probability", "statistical",
]


def should_reject(question, answer):
    """Reject off-topic or inappropriate entries."""
    text = f"{question} {answer}"
    for p in REJECT_PATTERNS:
        if p.search(text):
            return True

    # Reject if not a technical/scientific topic
    if not any(p.search(text) for p in TECHNICAL_PATTERNS):
        return True

    # Reject if answer doesn't contain a clear analogy structure
    analogy_phrases = [
        r"it'?s like", r"think of it", r"imagine", r"just like",
        r"similar to", r"same way", r"let'?s say", r"pretend",
    ]
    strong_matches = sum(
        1 for p in analogy_phrases
        if re.search(p, answer, re.IGNORECASE)
    )
    if strong_matches == 0:
        return True

    return False


def detect_domain(answer):
    """Detect the most likely domain from the analogy text."""
    answer_lower = answer.lower()
    scores = {}
    for domain, keywords in DOMAIN_SIGNALS.items():
        score = sum(1 for kw in keywords if kw in answer_lower)
        if score > 0:
            scores[domain] = score

    if not scores:
        return "everyday life"

    return max(scores, key=scores.get)


def detect_audience(question, answer):
    """Detect audience level based on complexity."""
    text = f"{question} {answer}".lower()
    if any(s in text for s in ADVANCED_SIGNALS):
        return "advanced"
    if any(s in text for s in INTERMEDIATE_SIGNALS):
        return "intermediate"
    return "beginner"


def clean_concept(question):
    """Extract a clean concept name from the ELI5 question."""
    # Remove common ELI5 prefixes
    q = question.strip()
    q = re.sub(r"^(ELI5:?\s*|explain like i'?m 5:?\s*)", "", q, flags=re.IGNORECASE)
    q = re.sub(r"^(why|how|what)\s+(is|are|does|do|did|was|were|can)\s+", "", q, flags=re.IGNORECASE)

    # Truncate to a reasonable concept name (first meaningful phrase)
    # If it's a question, use the whole thing up to a reasonable length
    if len(q) > 80:
        # Try to find a natural break point
        for sep in ["?", ".", " - ", " and ", " but ", ", "]:
            idx = q.find(sep)
            if 15 < idx < 80:
                q = q[:idx]
                break
        else:
            q = q[:80]

    return q.strip(" ?.,!")


def review():
    with open("candidates.json") as f:
        candidates = json.load(f)

    kept = 0
    rejected = 0

    for c in candidates:
        question = c["question"]
        answer = c["answer"]

        if should_reject(question, answer):
            c["keep"] = False
            rejected += 1
            continue

        c["keep"] = True
        c["concept"] = clean_concept(question)
        c["domain"] = detect_domain(answer)
        c["audience"] = detect_audience(question, answer)
        kept += 1

    with open("candidates_reviewed.json", "w") as f:
        json.dump(candidates, f, indent=2)

    print(f"Reviewed {len(candidates)} candidates:")
    print(f"  Kept: {kept}")
    print(f"  Rejected: {rejected}")
    print(f"Saved to candidates_reviewed.json")
    print()
    print("Spot-check the file, then run:")
    print("  cp candidates_reviewed.json candidates.json")
    print("  python merge_candidates.py")


if __name__ == "__main__":
    review()
