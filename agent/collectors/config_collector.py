import hashlib
import os
from datetime import datetime
import requests

API_URL = "http://127.0.0.1:8000"


def calculate_sha256(file_path: str) -> str:
    """Calculate SHA-256 hash of a given file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def create_file_baseline(agent_id: str, target_file_path: str):
    """Calculates SHA-256 hash and creates a local baseline backup copy."""
    if not os.path.exists(target_file_path):
        print(f"[Config Collector] File not found: {target_file_path}")
        return False

    abs_path = os.path.abspath(target_file_path)
    file_hash = calculate_sha256(abs_path)
    file_size = os.path.getsize(abs_path)
    current_time = datetime.now().isoformat()

    # Create local baseline backup file (.bak)
    backup_path = abs_path + ".bak"
    try:
        with open(abs_path, "r") as src, open(backup_path, "w") as bak:
            bak.write(src.read())
        print(f"[Baseline] Local backup file created at: {backup_path}")
    except Exception as e:
        print(f"[Baseline Backup Error] Failed to create backup: {e}")

    payload = {
        "agent_id": agent_id,
        "file_path": abs_path,
        "file_hash": file_hash,
        "file_size": file_size,
        "timestamp": current_time,
    }

    try:
        response = requests.post(
            f"{API_URL}/config/baseline", json=payload, timeout=5
        )
        if response.status_code == 200:
            res_data = response.json()
            msg = res_data.get("message", "Saved successfully")
            version = res_data.get("version", 1)
            print(f"[Baseline] {msg}")
            print(f"           File: {abs_path}")
            print(f"           Version: v{version}")
            print(f"           SHA-256: {file_hash}")
            return True
        else:
            print(
                f"[Baseline Error] Failed with status {response.status_code}: {response.text}"
            )
            return False
    except Exception as e:
        print(f"[Baseline Exception] Error connecting to backend: {e}")
        return False


def check_config_drift(agent_id: str, target_file_path: str):
    """Compares current file SHA-256 hash against saved backend baseline."""
    if not os.path.exists(target_file_path):
        print(f"[Drift Check Error] File missing: {target_file_path}")
        return False

    abs_path = os.path.abspath(target_file_path)
    current_hash = calculate_sha256(abs_path)

    try:
        response = requests.get(
            f"{API_URL}/config/baseline?agent_id={agent_id}", timeout=5
        )
        if response.status_code != 200:
            print("[Drift Check Error] Could not fetch baseline from backend")
            return False

        baselines = response.json().get("baselines", [])
        matched_baseline = next(
            (b for b in baselines if b["file_path"] == abs_path), None
        )

        if not matched_baseline:
            print(f"[Drift Check] No baseline registered for file: {abs_path}")
            return False

        baseline_hash = matched_baseline["file_hash"]

        if current_hash != baseline_hash:
            print("\n[ALERT] CONFIGURATION DRIFT DETECTED!")
            print(f"        File: {abs_path}")
            print(f"        Baseline Hash: {baseline_hash}")
            print(f"        Current Hash:  {current_hash}")

            drift_log = {
                "agent_id": agent_id,
                "event_id": 9001,
                "source": "FIM Engine",
                "level": "Error",
                "log_name": "FileIntegrity",
                "message": (
                    f"Configuration integrity violation detected on file: {abs_path}. "
                    f"Expected Hash: {baseline_hash[:10]}... Got: {current_hash[:10]}..."
                ),
                "timestamp": datetime.now().isoformat(),
            }

            log_res = requests.post(
                f"{API_URL}/logs/", json=drift_log, timeout=5
            )
            if log_res.status_code == 200:
                print(
                    "[Drift Check] High severity security alert sent to SIEM engine!\n"
                )
            return True
        else:
            print(f"[Integrity OK] File hash matches baseline: {abs_path}")
            return False

    except Exception as e:
        print(f"[Drift Check Exception] Error: {e}")
        return False


def restore_config_file(target_file_path: str) -> bool:
    """Restores the target file using its .bak baseline copy."""
    abs_path = os.path.abspath(target_file_path)
    backup_path = abs_path + ".bak"

    if not os.path.exists(backup_path):
        print(f"[Restore Error] Backup file not found: {backup_path}")
        return False

    try:
        with open(backup_path, "r") as bak, open(abs_path, "w") as target:
            target.write(bak.read())

        restored_hash = calculate_sha256(abs_path)
        print("\n[RESTORE SUCCESSFUL] File restored to baseline state!")
        print(f"                      File: {abs_path}")
        print(f"                      Restored Hash: {restored_hash}")
        return True
    except Exception as e:
        print(f"[Restore Error] Failed to restore file: {e}")
        return False