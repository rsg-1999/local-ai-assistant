# Local AI Assistant

A fully local, single-user AI assistant — chat, web search, and RAG over your own documents, all running on your machine via Ollama. See `CLAUDE.md` for architecture details.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Pull the required models:
```bash
ollama pull qwen3:4b
ollama pull nomic-embed-text
```

## One-time machine setup (recommended, especially on 8GB Macs)

These are Ollama server settings, not part of the app itself — set them once, then relaunch the Ollama app for them to take effect.

**Halve the memory cost of the context window** (KV-cache quantization + flash attention):
```bash
launchctl setenv OLLAMA_FLASH_ATTENTION 1
launchctl setenv OLLAMA_KV_CACHE_TYPE q8_0
```

**Only ever keep one model loaded in memory at a time** (Ollama's default allows up to 3):
```bash
launchctl setenv OLLAMA_MAX_LOADED_MODELS 1
```

After running these, quit and relaunch the Ollama app for them to take effect.

## Run the app

```bash
streamlit run app.py
```
