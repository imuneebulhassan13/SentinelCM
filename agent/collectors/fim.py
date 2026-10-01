import hashlib
import os
from core.api import post

# Initial clean file backup cache
BASELINE_CACHE = {}


def calculate_sha256(file_path):
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        print(f"[FIM Error] Cannot read file {file_path}: {e}")
        return None


def read_file_content(file_path):
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception as e:
        print(f"[FIM Read Error] {e}")
        return None


def write_file_content(file_path, content):
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"\n[FIM AUTO-HEAL] Reverted unauthorized changes in: {file_path}")
        return True
    except Exception as e:
        print(f"[FIM Restore Error] {e}")
        return False


def scan_and_send_fim(agent_id, monitored_directories):
    for directory in monitored_directories:
        if not os.path.exists(directory):
            continue

        for root, _, files in os.walk(directory):
            for file_name in files:
                file_path = os.path.join(root, file_name)
                file_hash = calculate_sha256(file_path)

                if file_hash:
                    # Save clean copy on agent start
                    if file_path not in BASELINE_CACHE:
                        BASELINE_CACHE[file_path] = read_file_content(file_path)

                    payload = {
                        "agent_id": agent_id,
                        "file_path": file_path,
                        "hash": file_hash,
                    }
                    response = post("/fim/check", payload)

                    # Execute restore command if server flagged it
                    if response and response.get("action") == "restore_required":
                        clean_content = BASELINE_CACHE.get(file_path)
                        if clean_content is not None:
                            write_file_content(file_path, clean_content)