from src.json_store import load_json, save_json

CHUNKS_FILE = "data/rag_chunks.json"


def load_chunks():
    return load_json(CHUNKS_FILE, [])


def save_chunks(chunks):
    save_json(CHUNKS_FILE, chunks)
