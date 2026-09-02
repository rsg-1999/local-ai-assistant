from ollama import Client
from .config import OLLAMA_HOST, DEFAULT_MODEL

def list_models():
    client = Client(host=OLLAMA_HOST)
    response = client.list()
    return response

def model_supports_thinking(model):
    client = Client(host=OLLAMA_HOST)
    info = client.show(model)
    return "thinking" in info.capabilities

def stream_chat(messages, model=DEFAULT_MODEL):
    client = Client(host=OLLAMA_HOST)
    think = model_supports_thinking(model)
    response = client.chat(model=model, messages=messages, stream=True, think=think)
    for chunk in response:
        if chunk["message"].get("thinking"):
            yield ("thinking", chunk["message"].get("thinking"))
        if chunk["message"].get("content"):
            yield ("content", chunk["message"].get("content"))
