from src.conversation import Conversation
from src.json_store import load_json, save_json

CONVERSATIONS_FILE = "data/conversations.json"

def load_conversations():
    raw = load_json(CONVERSATIONS_FILE, {})

    conversations = {}
    for conv_id, data in raw.items():
        try:
            conversations[conv_id] = Conversation.from_dict(conv_id, data)
        except (TypeError, AttributeError):
            print(f"Skipping malformed conversation entry: {conv_id}")

    return conversations

def save_conversations(conversations):
    raw = {conv_id: conv.to_dict() for conv_id, conv in conversations.items()}
    save_json(CONVERSATIONS_FILE, raw)
