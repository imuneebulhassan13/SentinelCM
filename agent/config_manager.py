import json
import os

CONFIG_FILE = "config.json"


def config_exists():

    return os.path.exists(CONFIG_FILE)


def load_config():

    with open(CONFIG_FILE, "r") as f:
        return json.load(f)


def save_config(data):

    with open(CONFIG_FILE, "w") as f:
        json.dump(data, f, indent=4)