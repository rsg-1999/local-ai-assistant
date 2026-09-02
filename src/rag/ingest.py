from src.rag.bm25_index import BM25Index
from src.rag.chunking import chunk_text
from src.rag.embeddings import generate_embedding
from src.rag.loader import load_document
from src.rag.retriever import Retriever
from src.rag.store import load_chunks, save_chunks
from src.rag.vector_index import VectorIndex


def build_retriever(chunks):
    vector_index = VectorIndex()
    bm25_index = BM25Index()

    for chunk in chunks:
        document = {"content": chunk["content"], "source": chunk["source"]}
        vector_index.add_vector(chunk["embedding"], document)
        bm25_index.add_document(document)

    return Retriever(vector_index, bm25_index)


def ingest_file(path):
    text = load_document(path)
    pieces = chunk_text(text)
    vectors = generate_embedding(pieces)

    chunks = load_chunks()
    chunks = [c for c in chunks if c["source"] != path]
    for piece, vector in zip(pieces, vectors):
        chunks.append({"content": piece, "embedding": vector, "source": path})
    save_chunks(chunks)

    return build_retriever(chunks)
