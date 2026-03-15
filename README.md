# Analogy Generator

A retrieval-based analogy engine that helps non-technical builders quickly understand technical concepts through vivid, relatable analogies.

Type a concept like "recursion" or "API" and get an instant analogy. Click **"Explain another way"** to see a different one.

## What's inside

- **228 hand-crafted analogies** across **105 concepts** — AI/LLM, web fundamentals, networking, databases, git, programming, and hardware
- **Semantic search** via ChromaDB + MiniLM embeddings — type "docker" and find "Containerization (Docker)"
- **Autocomplete** — concept suggestions as you type
- **Multiple variants** — every concept has 2+ analogies to cycle through

## Quick start

```bash
# Install dependencies
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Load the corpus into ChromaDB
python load_corpus.py

# Start the server
python app.py
```

Then open `http://localhost:5002`.

## How it works

**Data pipeline:** `corpus.json` → `load_corpus.py` → ChromaDB

Each analogy is embedded as `"{concept}. {analogy}"` using `all-MiniLM-L6-v2` (384-dim sentence embeddings) and stored in a persistent ChromaDB collection.

**Runtime:** Browser → Flask → ChromaDB

1. On page load, the browser fetches `GET /concepts` for autocomplete
2. User searches → `POST /search` with `{ concept, exclude_ids }`
3. Flask embeds the query, searches ChromaDB by cosine similarity, filters out previously seen results
4. "Explain another way" passes seen IDs as `exclude_ids` to get the next variant

See `architecture.html` for an interactive diagram.

## Project structure

```
app.py                  Flask server (3 routes)
corpus.json             228 analogy entries { id, concept, analogy }
load_corpus.py          Embeds corpus into ChromaDB
templates/index.html    Frontend with autocomplete + "Explain another way"
architecture.html       Interactive architecture diagram
corpus_science.json     Archived science/biology analogies (138 entries)
test_app.py             12 pytest tests for all routes and edge cases
requirements.txt        Pinned dependencies
```

## Tests

```bash
python -m pytest test_app.py -v
```

## Concept categories

| Category | Concepts |
|---|---|
| AI / LLM | Tokens, context window, temperature, prompts, hallucination, RAG, embeddings, fine-tuning, streaming, guardrails, ML algorithms, overfitting |
| Web Fundamentals | Frontend/backend, HTTP, JSON, REST vs GraphQL, auth, cookies, CORS, WebSockets, webhooks, DOM, routing, status codes, CRUD, SSR/CSR |
| Networking & Infra | DNS, TCP/IP, API, load balancing, rate limiting, CDN, CI/CD, serverless, SSL, logging |
| Databases & Storage | Cache, database index, SQL vs NoSQL, migrations, storage tiers |
| Git & Dev Workflow | Commits, staging, branching, PRs, merge conflicts, stash, technical debt, refactoring, open source licensing |
| Programming | Recursion, encryption, Docker, compression, dependencies, package managers, assembly language |
| Hardware | CPU vs GPU, cores/threads, clock speed, SSD vs HDD, VRAM, ARM vs x86, thermal throttling, binary |
