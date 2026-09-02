from ollama import Client

from src.config import OLLAMA_HOST

model = "nomic-embed-text"
def generate_embedding(chunks, model=model):
    client = Client(host=OLLAMA_HOST)

    is_list = isinstance(chunks, list)
    input_chunks = chunks if is_list else [chunks]

    result = client.embed(model=model, input=input_chunks)

    return result.embeddings if is_list else result.embeddings[0]