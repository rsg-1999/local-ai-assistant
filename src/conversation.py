class Conversation:
    def __init__(self, conv_id, title="New chat", messages=None):
        self.id = conv_id
        self.title = title
        self.messages = messages if messages is not None else []

    def add_message(self, role, content):
        self.messages.append({"role": role, "content": content})

    def rename(self, new_title):
        self.title = new_title

    def maybe_set_title_from(self, text):
        if self.title == "New chat":
            self.title = text[:30]

    def to_dict(self):
        return {"title": self.title, "messages": self.messages}

    @classmethod
    def from_dict(cls, conv_id, data):
        title = data.get("title", "New chat")
        if not isinstance(title, str):
            title = "New chat"

        messages = data.get("messages", [])
        if not isinstance(messages, list):
            messages = []
        else:
            messages = [
                m for m in messages
                if isinstance(m, dict) and "role" in m and "content" in m
            ]

        return cls(conv_id, title=title, messages=messages)
