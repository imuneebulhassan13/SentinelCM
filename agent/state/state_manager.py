import json
import os

STATE_FILE = "state/state.json"


def load_state():

    if not os.path.exists(STATE_FILE):

        return {
            "System": 0,
            "Application": 0,
            "Security": 0
        }

    with open(STATE_FILE, "r") as f:

        return json.load(f)


def save_state(channel, record_number):

    state = load_state()

    state[channel] = record_number

    with open(STATE_FILE, "w") as f:

        json.dump(
            state,
            f,
            indent=4
        )