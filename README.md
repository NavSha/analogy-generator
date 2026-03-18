# Analogy Generator

A retrieval-based analogy engine that helps non-technical builders quickly understand technical concepts through vivid, relatable analogies.

Type a concept like "recursion" or "API" and get an instant analogy. Click **"Explain another way"** to see a different one.

## What's inside

- **295 hand-crafted analogies** across **138 concepts** in 10 categories — AI/LLM, web fundamentals, networking, databases, git, programming, hardware, data science, DevOps, and product management
- **Semantic search** via ChromaDB + MiniLM ONNX embeddings — type "docker" and find "Containerization (Docker)"
- **Autocomplete** — concept suggestions as you type, filterable by category
- **Multiple variants** — every concept has 2+ analogies to cycle through
- **Daily analogy** — a different "Analogy of the Day" each day
- **Category browsing** — filter concepts by category pills
- **Copy to clipboard** — one-click copy of any analogy
- **Search analytics** — tracks popular searches

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

Each analogy is embedded as `"{concept}. {analogy}"` using `all-MiniLM-L6-v2` (384-dim ONNX embeddings via ChromaDB's default) and stored in a persistent ChromaDB collection.

**Runtime:** Browser → Flask → ChromaDB

1. On page load, the browser fetches `GET /concepts` for autocomplete and `GET /daily` for the daily analogy
2. User optionally clicks a category pill → filters autocomplete via `GET /concepts?category=...`
3. User searches → `POST /search` with `{ concept, exclude_ids }`
4. Flask embeds the query, searches ChromaDB by cosine similarity, filters out previously seen results
5. "Explain another way" passes seen IDs as `exclude_ids` to get the next variant

See `architecture.html` for an interactive diagram.

## Deployment

Deployed via Docker on Railway.

```bash
# Local Docker build
docker build -t analogy-generator .
docker run -p 5002:5002 analogy-generator
```

The `start.sh` script runs `load_corpus.py` on each startup to rebuild ChromaDB from `corpus.json`, so no persistent storage is needed.

## Project structure

```
app.py                  Flask server (6 routes)
corpus.json             295 analogy entries { id, concept, analogy, category }
load_corpus.py          Embeds corpus into ChromaDB (batched)
templates/index.html    Frontend with daily analogy, category pills, autocomplete, copy button
architecture.html       Interactive architecture diagram
test_app.py             20 pytest tests for all routes and edge cases
requirements.txt        Dependencies
Dockerfile              Docker build for deployment
start.sh                Startup script (load corpus + gunicorn)
railway.toml            Railway deployment config
```

## Tests

```bash
python -m pytest test_app.py -v
```

## API routes

| Route | Method | Description |
|---|---|---|
| `/` | GET | Serves the frontend |
| `/concepts` | GET | List concept names (optional `?category=` filter) |
| `/categories` | GET | List categories with concept counts |
| `/search` | POST | Semantic search for analogies |
| `/daily` | GET | Deterministic daily analogy |
| `/analytics` | GET | Top 20 searched concepts |

## Concept categories

| Category | Concepts |
|---|---|
| AI & LLM | Tokens, context window, temperature, prompts, hallucination, RAG, embeddings, fine-tuning, streaming, guardrails, ML algorithms, overfitting, model training |
| Web Fundamentals | API, frontend/backend, HTTP, JSON, REST vs GraphQL, auth, cookies, CORS, WebSockets, webhooks, DOM, routing, status codes, CRUD, SSR/CSR, middleware, responsive design, local/session storage, query params |
| Networking & Infrastructure | DNS, TCP/IP, load balancing, rate limiting, CDN, CI/CD, serverless, SSL, containerization, bandwidth, latency, localhost, net neutrality, ISP peering, network backdoors, Wi-Fi |
| Databases & Storage | Cache, database index, SQL vs NoSQL, migrations, storage tiers |
| Git & Version Control | Commits, staging, branching, PRs, merge conflicts, stash, version control |
| Programming Concepts | Recursion, encryption, compression, dependencies, package managers, refactoring, technical debt, logging, environment variables, open source licensing |
| Hardware | CPU, GPU, cores/threads, clock speed, SSD vs HDD, VRAM, ARM vs x86, thermal throttling, binary, RAM, LCD, E-ink, overclocking |
| Data Science | A/B testing, feature engineering, data pipelines/ETL, data lakes vs warehouses, bias, p-values, correlation vs causation, outliers, normalization, train/test split, cross-validation |
| DevOps | Infrastructure as Code, Kubernetes, monitoring/alerting, incident management, SLAs/SLOs, blue-green deployments, canary releases, observability, runbooks, chaos engineering |
| Product Management | User stories, product-market fit, MVP, sprints/agile, backlog grooming, OKRs, north star metric, feature flags, stakeholder management, roadmap prioritization, product discovery, technical feasibility |
