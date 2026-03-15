"""
Remove non-technical/non-scientific entries from corpus.json.
"""

import json
import re

TECHNICAL_KEYWORDS = [
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
    "load balancing", "version control", "git", "microservice", "middleware",
    "rate limiting", "overfitting", "model training", "containerization",
    "branching",
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
    "chemical", "reaction", "catalyst", "oxidation", "acid", "base",
    "calculus", "derivative", "integral", "probability", "statistics",
    "exponential", "logarithm", "dimension", "infinity", "prime number",
    "encryption", "compression", "fourier",
]

PATTERNS = [re.compile(rf"\b{kw}\b", re.IGNORECASE) for kw in TECHNICAL_KEYWORDS]


def is_technical(entry):
    text = f"{entry['concept']} {entry['analogy']}"
    return any(p.search(text) for p in PATTERNS)


def main():
    with open("corpus.json") as f:
        corpus = json.load(f)

    kept = [e for e in corpus if is_technical(e)]
    removed = [e for e in corpus if not is_technical(e)]

    print(f"Original: {len(corpus)} entries")
    print(f"Kept: {len(kept)} technical/scientific entries")
    print(f"Removed: {len(removed)} non-technical entries")

    if removed:
        print("\nRemoved entries:")
        for e in removed:
            print(f"  - [{e['id']}] {e['concept']}")

    with open("corpus.json", "w") as f:
        json.dump(kept, f, indent=2)

    print("\nCorpus updated. Run 'python load_corpus.py' to reload.")


if __name__ == "__main__":
    main()
