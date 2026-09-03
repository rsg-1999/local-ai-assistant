import time

from ollama import Client
from .config import OLLAMA_HOST, DEFAULT_MODEL

CAPABILITY_CACHE_TTL = 300  # seconds
_capability_cache = {}

def list_models():
    client = Client(host=OLLAMA_HOST)
    response = client.list()
    return response

def model_supports_thinking(model):
    now = time.time()
    cached = _capability_cache.get(model)
    if cached and now - cached[0] < CAPABILITY_CACHE_TTL:
        return cached[1]

    client = Client(host=OLLAMA_HOST)
    info = client.show(model)
    result = "thinking" in (info.capabilities or [])
    _capability_cache[model] = (now, result)
    return result

def stream_chat(messages, model=DEFAULT_MODEL):
    client = Client(host=OLLAMA_HOST)
    think = model_supports_thinking(model)
    response = client.chat(model=model, messages=messages, stream=True, think=think)
    for chunk in response:
        if chunk["message"].get("thinking"):
            yield ("thinking", chunk["message"].get("thinking"))
        if chunk["message"].get("content"):
            yield ("content", chunk["message"].get("content"))
