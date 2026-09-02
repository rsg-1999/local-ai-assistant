import re

def chunk_text(text, max_sentence_per_chunk=5, overlap=1):
    sentences = re.split(r"(?<=[.!?])\s+", text)

    chunks = []
    start = 0

    while start<len(sentences):
        end = start + max_sentence_per_chunk
        piece = sentences[start:end]
        chunks.append(" ".join(piece))
        start = end-overlap

    return chunks