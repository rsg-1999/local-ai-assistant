from src.conversation import Conversation
from src.json_store import load_json, save_json

CONVERSATIONS_FILE = "data/conversations.json"

def load_conversations():
    raw = load_json(CONVERSATIONS_FILE, {})
    return {conv_id: Conversation.from_dict(conv_id, data) for conv_id, data in raw.items()}

def save_conversations(conversations):
    raw = {conv_id: conv.to_dict() for conv_id, conv in conversations.items()}
    save_json(CONVERSATIONS_FILE, raw)
