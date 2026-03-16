#!/bin/bash
echo "Loading corpus into ChromaDB..."
python load_corpus.py
echo "Starting server..."
gunicorn app:app --bind 0.0.0.0:${PORT:-5002}
