import json
import os
import uuid


def load_json(path, default):
    if not os.path.exists(path):
        return default

    try:
        with open(path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return default


def save_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp_path = f"{path}.{uuid.uuid4().hex}.tmp"
    with open(tmp_path, "w") as f:
        json.dump(data, f)
    os.replace(tmp_path, path)
