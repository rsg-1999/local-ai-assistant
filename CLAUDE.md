# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A fully local, single-user AI assistant: a Streamlit chat UI backed by a local Ollama model (`qwen3:4b` by default), with web search, hybrid RAG over user-uploaded documents, and a custom-instructions system prompt. No cloud APIs, no accounts — everything talks to a local Ollama server (`http://localhost:11434`, set in `src/config.py`).

## Commands

Setup (from the project root):
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Ollama models required (pull once before running):
```bash
ollama pull qwen3:4b
ollama pull nomic-embed-text
```

Run the app:
```bash
streamlit run app.py
```

There is no automated test suite. `src/rag/evaluate.py` is a manual retrieval-quality check (Precision@k, Recall@k, MRR) against a hand-written test set defined in that file — run it after ingesting a document to sanity-check retrieval changes:
```bash
python3 -c "
from src.rag.ingest import build_retriever
from src.rag.store import load_chunks
from src.rag.evaluate import run_evaluation
run_evaluation(build_retriever(load_chunks()))
"
```

## Architecture

**Single process, no backend.** `app.py` is the entire UI and orchestration layer; it talks to Ollama directly via the `ollama` Python client — no FastAPI/Flask layer. All business logic lives under `src/`, kept separate from Streamlit calls so it can be exercised from a plain `python3 -c` without running the UI.

**Persistence is flat JSON files under `data/`, no database.** `src/json_store.py` is the shared low-level layer: `load_json(path, default)` (returns `default` if the file is missing, and also on a corrupt/unparseable file rather than crashing) and `save_json(path, data)` (writes atomically — a uniquely-named temp file per call, then `os.replace()` into place, so a crash mid-write can't corrupt the real file, and two concurrent writers can't collide on the same temp file). Three thin wrappers sit on top of it:
- `src/storage.py` → `data/conversations.json` — all conversations, keyed by a UUID. Converts between the on-disk dict shape and `src/conversation.py`'s `Conversation` objects (`Conversation.from_dict`/`.to_dict()`); a malformed individual entry is skipped (with a printed warning) rather than failing the whole load.
- `src/rag/store.py` → `data/rag_chunks.json` — every ingested document chunk, its embedding vector, and its source file path, as a flat list.
- `src/instructions.py` → `data/instructions.json` — a single string: the user's custom system-prompt instructions.

**A conversation is a `Conversation` object (`src/conversation.py`), not a raw dict.** It owns its own mutation logic — `add_message()`, `rename()`, `maybe_set_title_from()` — and `app.py`/`src/storage.py` interact with it via attributes/methods (`current.title`, `current.messages`, `current.add_message(...)`), not dict keys.

**Conversation lifecycle has a "draft" state.** A new chat is *not* added to `st.session_state.conversations` (and so is invisible in the sidebar and never persisted) until its first message is actually sent — see the `current = st.session_state.conversations.get(current_id) or Conversation(current_id)` fallback and the promotion check right after `st.chat_input` in `app.py`. This is what makes clicking "+ New chat" repeatedly, or switching away from an empty chat, leave no junk behind. The active conversation ID is tracked in the URL (`st.query_params["chat"]`), not only `st.session_state` — `st.session_state` does not survive a browser refresh in Streamlit, so the URL is what makes a refresh reopen the same chat.

**The RAG pipeline (`src/rag/`) is hand-built from scratch, hybrid search, no vector DB.** The files are designed to compose, not to be read in isolation:
1. `loader.py` — extracts raw text per file type (`.md`/`.txt` plain read, `.pdf` via `pypdf`, `.docx` via `python-docx`).
2. `chunking.py` — splits text into overlapping, sentence-grouped chunks.
3. `embeddings.py` — embeds chunks via Ollama's `nomic-embed-text` model — a separate model from the chat model.
4. `vector_index.py` / `bm25_index.py` — two independent, hand-rolled indexes: cosine-similarity search over embeddings, and BM25 keyword search. `bm25_index.py`'s `tokenize()` deliberately keeps hyphenated identifiers (e.g. `INC-2023-Q4-011`) as single tokens via `re.findall`, not `re.split` — splitting on hyphens was a real, measured bug that badly hurt BM25's ability to match structured codes/IDs.
5. `retriever.py` — `Retriever` merges both indexes' rankings via Reciprocal Rank Fusion (RRF). It pulls a much wider candidate pool from each index (`k * 20`) than the final `k` it returns, specifically so a chunk ranked well by only *one* index still has a chance to surface after merging — a narrower pool silently excludes those chunks before RRF ever sees them.
6. `store.py` / `ingest.py` — `ingest_file(path)` runs loader → chunker → embedder → persists → rebuilds indexes. Re-ingesting the same `path` first strips any existing chunks for that source, so re-uploading a file replaces rather than duplicates its chunks. `build_retriever(chunks)` rebuilds `VectorIndex`/`BM25Index` from already-embedded chunks with **no** Ollama calls — this is what keeps app startup and document-selection filtering fast; only `ingest_file` calls the embedding model.

**Search/RAG context is injected per-turn, never persisted into conversation history.** Both web search (`src/tools/web_search.py`) and document search build a throwaway `messages_for_model` list (saved conversation history + one extra `role: "system"` message containing the search results), used only for that one `stream_chat` call. `current["messages"]` — what actually gets saved to `data/conversations.json` — is never touched by search context, so saved conversations don't accumulate stale search results that would otherwise get re-sent on every future turn.

**Streamlit's rerun model dictates the `st.rerun()` calls.** Streamlit re-executes `app.py` top-to-bottom on a widget interaction, but only once per interaction — mutating state (renaming a chat, deleting a document) *after* the widget that displays that state has already rendered in the same pass won't show up until the next interaction unless `st.rerun()` is called explicitly. Every state-mutating button in `app.py` ends with `st.rerun()` for this reason.

**Model split, and thinking is auto-detected, not assumed.** `DEFAULT_MODEL` (`qwen3:4b`, in `src/config.py`) handles chat, but `app.py`'s model dropdown lets the user pick any locally-installed Ollama model; a separate embedding model (`nomic-embed-text`, hardcoded in `src/rag/embeddings.py`) always handles RAG regardless of the chat model chosen. `src/llm.py`'s `model_supports_thinking(model)` (`@lru_cache`d, since a model's capabilities don't change mid-session) checks Ollama's `client.show(model).capabilities` for `"thinking"` before `stream_chat` decides whether to pass `think=True` — never hardcode `think=True`, since Ollama rejects that flag for non-thinking models. When thinking is active, `stream_chat` yields `("thinking", ...)` and `("content", ...)` tuples by reading Ollama's `message.thinking` / `message.content` fields directly, not by regex-parsing `<think>` tags out of raw text.

**No agentic tool-calling.** All tool use is manually triggered by the user, not decided by the model — an "Enable web search" checkbox for web search, and a non-empty "Search within" document selection for document search (selecting zero documents means no document search happens at all). The model itself never decides when to call a tool. This was deliberate. An agentic version (the model deciding for itself, via Ollama's tool-calling API) was attempted and rolled back due to reliability and latency problems on local hardware; if resuming that work, treat it as a fresh design rather than assuming prior agent code exists in this repo.
