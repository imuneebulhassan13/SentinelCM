import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUEUE_FILE = os.path.join(BASE_DIR, "state", "queue.json")


def load_queue():
    if not os.path.exists(QUEUE_FILE):
        return []
    try:
        with open(QUEUE_FILE, "r") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception:
        return []


def save_queue(queue_data):
    try:
        os.makedirs(os.path.dirname(QUEUE_FILE), exist_ok=True)
        with open(QUEUE_FILE, "w") as f:
            json.dump(queue_data, f, indent=2)
    except Exception as e:
        print(f"[Queue Error] Save failed: {e}")


def add_to_queue(log_entry):
    queue = load_queue()
    queue.append(log_entry)
    save_queue(queue)
    print(f"[Offline Queue] Log saved locally to queue.json. Total queued: {len(queue)}")


def flush_queue(post_function):
    queue = load_queue()
    if not queue:
        return

    total = len(queue)
    print(f"\n[Offline Queue] Found {total} buffered log(s). Attempting flush...")
    failed_logs = []

    for idx, item in enumerate(queue):
        endpoint = item.get("endpoint", "/logs/")
        payload = item.get("payload")

        result = post_function(endpoint, payload)
        if result:
            print(f"[Offline Queue] Flushed item {idx + 1}/{total}")
        else:
            print(f"[Offline Queue] Backend still offline. Pausing flush...")
            failed_logs = queue[idx:]
            break

    save_queue(failed_logs)