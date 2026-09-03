import hashlib
import os
import uuid

import streamlit as st

from src.config import DEFAULT_MODEL
from src.conversation import Conversation
from src.instructions import load_instructions, save_instructions
from src.llm import list_models, model_status, stream_chat
from src.rag.ingest import build_retriever, ingest_file
from src.rag.store import load_chunks, save_chunks
from src.json_store import cleanup_stale_tmp_files
from src.storage import load_conversations, save_conversations
from src.tools.web_search import format_context, search

if "cleaned_tmp_files" not in st.session_state:
    cleanup_stale_tmp_files()
    st.session_state.cleaned_tmp_files = True

if "conversations" not in st.session_state:
    st.session_state.conversations = load_conversations()

if "current_id" not in st.session_state:
    query_chat_id = st.query_params.get("chat")
    st.session_state.current_id = query_chat_id if query_chat_id else str(uuid.uuid4())

if "retriever" not in st.session_state:
    st.session_state.retriever = build_retriever(load_chunks())

if "ingested_files" not in st.session_state:
    st.session_state.ingested_files = {}

with st.sidebar:
    if st.button("+ New chat"):
        st.session_state.current_id = str(uuid.uuid4())
        st.rerun()

    st.divider()

    for conv_id, conv in list(st.session_state.conversations.items()):
        title_col, rename_col, delete_col = st.columns([3, 1, 1])

        with title_col:
            if st.button(conv.title, key=conv_id):
                st.session_state.current_id = conv_id
                st.rerun()

        with rename_col:
            with st.popover("✏️"):
                new_title = st.text_input(
                    "Rename chat", value=conv.title, key=f"rename_input_{conv_id}"
                )
                if st.button("Save", key=f"rename_save_{conv_id}"):
                    conv.rename(new_title)
                    save_conversations(st.session_state.conversations)
                    st.rerun()

        with delete_col:
            if st.button("🗑️", key=f"delete_{conv_id}"):
                del st.session_state.conversations[conv_id]
                save_conversations(st.session_state.conversations)
                if conv_id == st.session_state.current_id:
                    st.session_state.current_id = str(uuid.uuid4())
                st.rerun()

st.query_params["chat"] = st.session_state.current_id

current = st.session_state.conversations.get(
    st.session_state.current_id
) or Conversation(st.session_state.current_id)

with st.popover("⚙️"):
    model_names = [m.model for m in list_models().models]
    default_index = model_names.index(DEFAULT_MODEL) if DEFAULT_MODEL in model_names else 0
    selected_model = st.selectbox("Model", model_names, index=default_index)

    ctx_size = st.selectbox("Context window", [4096, 8192, 16384], index=1)

    status = model_status()
    if status.models:
        for m in status.models:
            gpu_pct = round(100 * m.size_vram / m.size) if m.size else 0
            st.caption(f"{m.model} loaded — {gpu_pct}% GPU")
    else:
        st.caption("No model currently loaded")

    instructions_text = st.text_area(
        "Custom instructions",
        value=load_instructions(),
        placeholder="e.g. Be concise. Don't repeat my question back to me.",
    )
    if st.button("Save instructions"):
        save_instructions(instructions_text)
        st.success("Saved")
        st.rerun()

    search_enabled = st.checkbox("Enable web search")

    uploaded_file = st.file_uploader(
        "Upload a document", type=["md", "txt", "pdf", "docx"]
    )
    if uploaded_file is not None:
        doc_path = f"documents/{uploaded_file.name}"
        file_bytes = uploaded_file.getbuffer()
        content_hash = hashlib.md5(file_bytes).hexdigest()

        if st.session_state.ingested_files.get(doc_path) != content_hash:
            try:
                os.makedirs("documents", exist_ok=True)
                with open(doc_path, "wb") as f:
                    f.write(file_bytes)

                st.session_state.retriever = ingest_file(doc_path)
                st.session_state.ingested_files[doc_path] = content_hash
                st.success(f"Ingested {uploaded_file.name}")
            except Exception as e:
                try:
                    os.remove(doc_path)
                except FileNotFoundError:
                    pass
                st.error(f"Couldn't process {uploaded_file.name}: {e}")

    all_chunks = load_chunks()
    all_sources = sorted(set(c["source"] for c in all_chunks))

    selected_sources = st.multiselect(
        "Search within", all_sources, default=[]
    )

    for source in all_sources:
        source_col, delete_col = st.columns([4, 1])
        with source_col:
            st.caption(source)
        with delete_col:
            if st.button("🗑️", key=f"delete_doc_{source}"):
                all_chunks = [c for c in all_chunks if c["source"] != source]
                save_chunks(all_chunks)
                st.session_state.retriever = build_retriever(all_chunks)
                st.session_state.ingested_files.pop(source, None)
                st.rerun()

for msg in current.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

prompt = st.chat_input("Hi, How can i help you today")
if prompt:
    if st.session_state.current_id not in st.session_state.conversations:
        st.session_state.conversations[st.session_state.current_id] = current

    current.maybe_set_title_from(prompt)

    current.add_message("user", prompt)
    with st.chat_message("user"):
        st.write(prompt)

    messages_for_model = current.messages
    if instructions_text.strip():
        messages_for_model = [
            {"role": "system", "content": instructions_text}
        ] + messages_for_model

    search_results = []
    if search_enabled:
        search_results = search(prompt)
        context = format_context(search_results)
        messages_for_model = messages_for_model + [
            {
                "role": "system",
                "content": f"Use these web search results if they help answer the question:\n\n{context}",
            }
        ]

    doc_results = []
    if selected_sources:
        if set(selected_sources) == set(all_sources):
            search_retriever = st.session_state.retriever
        else:
            scoped_chunks = [c for c in all_chunks if c["source"] in selected_sources]
            search_retriever = build_retriever(scoped_chunks)

        doc_results = search_retriever.search(prompt, k=5)
        doc_context = "\n\n".join(
            f"[{i}] (from {doc['source']})\n{doc['content']}"
            for i, (_, doc) in enumerate(doc_results, start=1)
        )
        messages_for_model = messages_for_model + [
            {
                "role": "system",
                "content": f"Use these excerpts from the user's own documents if they help answer the question:\n\n{doc_context}",
            }
        ]

    with st.chat_message("assistant"):
        reasoning_text = ""
        answer_text = ""

        with st.expander("Reasoning"):
            reasoning_placeholder = st.empty()
        answer_placeholder = st.empty()

        for kind, piece in stream_chat(messages_for_model, model=selected_model, num_ctx=ctx_size):
            if kind == "thinking":
                reasoning_text += piece
                reasoning_placeholder.markdown(reasoning_text)
            else:
                answer_text += piece
                answer_placeholder.markdown(answer_text)

        if search_results:
            with st.expander("Sources"):
                for r in search_results:
                    st.markdown(f"[{r['title']}]({r['href']})")

        if doc_results:
            with st.expander("Document excerpts used"):
                for _, doc in doc_results:
                    st.markdown(f"**{doc['source']}**")
                    st.text(doc["content"][:200])

    current.add_message("assistant", answer_text)
    save_conversations(st.session_state.conversations)
    st.rerun()
