import time

from ollama import Client
from .config import OLLAMA_HOST, DEFAULT_MODEL

CAPABILITY_CACHE_TTL = 300  # seconds


class OllamaClient:
    def __init__(self, host=OLLAMA_HOST):
        self.client = Client(host=host)
        self._capability_cache = {}

    def list_models(self):
        return self.client.list()

    def model_status(self):
        return self.client.ps()

    def unload_model(self, model):
        self.client.generate(model=model, keep_alive=0)

    def model_supports_thinking(self, model):
        now = time.time()
        cached = self._capability_cache.get(model)
        if cached and now - cached[0] < CAPABILITY_CACHE_TTL:
            return cached[1]

        info = self.client.show(model)
        result = "thinking" in (info.capabilities or [])
        self._capability_cache[model] = (now, result)
        return result

    def stream_chat(self, messages, model=DEFAULT_MODEL, num_ctx=8192):
        think = self.model_supports_thinking(model)
        response = self.client.chat(
            model=model,
            messages=messages,
            stream=True,
            think=think,
            options={"num_ctx": num_ctx},
        )
        for chunk in response:
            if chunk["message"].get("thinking"):
                yield ("thinking", chunk["message"].get("thinking"))
            if chunk["message"].get("content"):
                yield ("content", chunk["message"].get("content"))


ollama_client = OllamaClient()
