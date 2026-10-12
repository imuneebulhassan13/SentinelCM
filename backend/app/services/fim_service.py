import os
from datetime import datetime, timezone
from app.api.routes.websocket import manager
from app.models.agent import get_agent_collection
from app.services.audit_service import record_audit_log


def normalize_path(path: str) -> str:
    """Standardizes backslashes to forward slashes for database consistency across platforms."""
    if not path:
        return ""
    return os.path.normpath(path).replace("\\", "/")


def get_collections():
    agent_col = get_agent_collection()
    db = agent_col.database
    return db["fim_baselines"], db["logs"], db["alerts"]


async def get_all_baselines():
    fim_col, _, _ = get_collections()
    cursor = fim_col.find({})
    baselines = await cursor.to_list(length=200)

    for b in baselines:
        b["_id"] = str(b["_id"])
        # Ensure path is always clean
        b["file_path"] = normalize_path(b.get("file_path", ""))
        # UI Status alignment
        b["status"] = "Drift Detected" if b.get("drift") else "In Sync"

    return baselines


async def process_fim_check(agent_id: str, raw_file_path: str, current_hash: str):
    file_path = normalize_path(raw_file_path)
    fim_col, logs_col, alerts_col = get_collections()
    now_str = datetime.now(timezone.utc).isoformat()

    existing = await fim_col.find_one(
        {"agent_id": agent_id, "file_path": file_path}
    )

    # 1. New File Baseline Registration
    if not existing:
        doc = {
            "agent_id": agent_id,
            "file_path": file_path,
            "baseline_hash": current_hash,
            "hash": current_hash,
            "current_hash": current_hash,
            "version": 1,
            "drift": False,
            "restore_pending": False,
            "status": "In Sync",
            "created_at": now_str,
            "updated_at": now_str,
        }
        await fim_col.insert_one(doc)
        return {"status": "Baseline Created", "version": 1, "drift": False}

    # 2. Check if Restore was Pending
    if existing.get("restore_pending"):
        target_hash = existing.get("baseline_hash") or existing.get("hash")
        await fim_col.update_one(
            {"_id": existing["_id"]},
            {
                "$set": {
                    "hash": target_hash,
                    "current_hash": target_hash,
                    "baseline_hash": target_hash,
                    "drift": False,
                    "restore_pending": False,
                    "status": "In Sync",
                    "updated_at": now_str,
                }
            },
        )
        return {
            "status": "In Sync",
            "drift": False,
            "action": "restore_required",
            "target_hash": target_hash,
        }

    # Fetch baseline target hash safely
    baseline_hash = existing.get("baseline_hash") or existing.get("hash")

    # 3. Valid Match or Auto-Healed State
    if current_hash == baseline_hash:
        await fim_col.update_one(
            {"_id": existing["_id"]},
            {
                "$set": {
                    "hash": current_hash,
                    "current_hash": current_hash,
                    "baseline_hash": current_hash,
                    "drift": False,
                    "status": "In Sync",
                    "updated_at": now_str,
                }
            },
        )
        return {"status": "In Sync", "version": existing.get("version", 1), "drift": False}

    # 4. Hash Mismatch -> Genuine Drift Detected
    already_drifted = existing.get("drift", False)
    new_version = existing.get("version", 1) + (0 if already_drifted else 1)

    await fim_col.update_one(
        {"_id": existing["_id"]},
        {
            "$set": {
                "hash": current_hash,
                "current_hash": current_hash,
                "version": new_version,
                "drift": True,
                "status": "Drift Detected",
                "updated_at": now_str,
            }
        },
    )

    # 🔴 Only raise new Alert & Log if this is the FIRST time drift is detected (prevents spam)
    if not already_drifted:
        log_entry = {
            "agent_id": agent_id,
            "log_name": "File Integrity Drift Detected",
            "message": f"Unauthorized modification detected in monitored file: '{file_path}'.",
            "level": "Error",
            "source": "FIM Engine",
            "timestamp": now_str,
        }
        await logs_col.insert_one(log_entry)

        alert_entry = {
            "agent_id": agent_id,
            "title": "File Tampering Alert (FIM)",
            "message": f"Critical system file drift on host. Path: {file_path}",
            "severity": "High",
            "source": "FIM Engine",
            "acknowledged": False,
            "timestamp": now_str,
        }
        await alerts_col.insert_one(alert_entry)

        # Broadcast live alert via WebSocket if manager exists
        try:
            await manager.broadcast({
                "event_type": "NEW_LOG",
                "data": log_entry
            })
        except Exception:
            pass

    return {"status": "Drift Detected", "version": new_version, "drift": True}


async def restore_baseline_service(agent_id: str, raw_file_path: str):
    # Both slash variants generate karein
    path_forward = raw_file_path.replace("\\", "/")
    path_backward = raw_file_path.replace("/", "\\")

    await record_audit_log(
        user="Administrator",
        action="FIM_RESTORE",
        resource=raw_file_path,
        details=f"Triggered baseline restoration for file: {raw_file_path}",
    )

    fim_col, logs_col, _ = get_collections()
    now_str = datetime.now(timezone.utc).isoformat()

    # Query with $in operator so BOTH slash variants match the same document!
    existing = await fim_col.find_one({
        "agent_id": agent_id,
        "file_path": {"$in": [path_forward, path_backward, raw_file_path]}
    })

    if not existing:
        return {"error": "Baseline record not found"}

    # Set restore_pending flag and proactively clear drift status
    await fim_col.update_one(
        {"_id": existing["_id"]},
        {
            "$set": {
                "restore_pending": True,
                "drift": False,
                "status": "In Sync",
                "updated_at": now_str,
            }
        },
    )

    # SIEM Audit Log Entry
    log_doc = {
        "agent_id": agent_id,
        "log_name": "Configuration Restore Initiated",
        "message": f"Administrator issued restore command for file '{raw_file_path}'.",
        "level": "Information",
        "source": "FIM Engine",
        "timestamp": now_str,
    }
    await logs_col.insert_one(log_doc)

    return {"status": "Restore Command Queued", "file_path": raw_file_path}