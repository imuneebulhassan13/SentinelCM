import json
import os

# Script ke absolute path ke mutabiq directory resolve karna
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "state.json")


def load_state():
    if not os.path.exists(STATE_FILE):
        return {
            "System": 0,
            "Application": 0,
            "Security": 0
        }

    try:
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {
            "System": 0,
            "Application": 0,
            "Security": 0
        }


def save_state(channel, record_number):
    state = load_state()
    state[channel] = record_number

    # Folder exist karna ensure karein
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)

    with open(STATE_FILE, "w") as f:
        json.dump(
            state,
            f,
            indent=4
        )