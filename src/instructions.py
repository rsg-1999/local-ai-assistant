from src.json_store import load_json, save_json

INSTRUCTION_FILE = "data/instructions.json"

def load_instructions():
    return load_json(INSTRUCTION_FILE, "")

def save_instructions(instructions):
    save_json(INSTRUCTION_FILE, instructions)
