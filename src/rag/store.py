from src.json_store import load_json, save_json

CHUNKS_FILE = "data/rag_chunks.json"


REQUIRED_KEYS = {"content", "embedding", "source"}


def load_chunks():
    raw = load_json(CHUNKS_FILE, [])
    if not isinstance(raw, list):
        return []

    chunks = []
    for chunk in raw:
        if isinstance(chunk, dict) and REQUIRED_KEYS.issubset(chunk):
            chunks.append(chunk)
        else:
            print(f"Skipping malformed chunk entry: {chunk}")

    return chunks


def save_chunks(chunks):
    save_json(CHUNKS_FILE, chunks)
