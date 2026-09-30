from datetime import datetime, timezone
from app.api.routes.websocket import manager
from app.models.agent import get_agent_collection


def get_collections():
    agent_col = get_agent_collection()
    db = agent_col.database
    return db["fim_baselines"], db["logs"], db["alerts"]


async def get_all_baselines():
    fim_col, _, _ = get_collections()
    cursor = fim_col.find({})
    baselines = await cursor.to_list(length=100)

    for b in baselines:
        b["_id"] = str(b["_id"])

    return baselines


async def process_fim_check(agent_id: str, file_path: str, current_hash: str):
    fim_col, logs_col, alerts_col = get_collections()
    now_str = datetime.now(timezone.utc).isoformat()

    existing = await fim_col.find_one(
        {"agent_id": agent_id, "file_path": file_path}
    )

    if not existing:
        doc = {
            "agent_id": agent_id,
            "file_path": file_path,
            "hash": current_hash,
            "version": 1,
            "drift": False,
            "created_at": now_str,
            "updated_at": now_str,
        }
        await fim_col.insert_one(doc)
        return {
            "status": "Baseline Created",
            "version": 1,
            "drift": False,
        }

    if existing["hash"] == current_hash:
        await fim_col.update_one(
            {"_id": existing["_id"]},
            {"$set": {"drift": False, "updated_at": now_str}},
        )
        return {
            "status": "In Sync",
            "version": existing.get("version", 1),
            "drift": False,
        }

    # Hash Mismatch -> Drift Detected!
    new_version = existing.get("version", 1) + 1

    await fim_col.update_one(
        {"_id": existing["_id"]},
        {
            "$set": {
                "hash": current_hash,
                "version": new_version,
                "drift": True,
                "updated_at": now_str,
            }
        },
    )

    title = "File Integrity Drift Detected"
    msg = f"Monitored file '{file_path}' hash modified! New Hash: {current_hash[:16]}..."

    # 1. Save into Logs Collection (SIEM Event)
    log_doc = {
        "agent_id": agent_id,
        "log_name": title,
        "message": msg,
        "level": "Error",
        "source": "FIM Engine",
        "timestamp": now_str,
    }
    log_res = await logs_col.insert_one(log_doc)
    log_doc["_id"] = str(log_res.inserted_id)

    # 2. Save into Alerts Collection (SIEM Alert)
    alert_doc = {
        "agent_id": agent_id,
        "title": title,
        "message": msg,
        "severity": "High",
        "level": "Error",
        "source": "FIM Engine",
        "acknowledged": False,
        "timestamp": now_str,
    }
    alert_res = await alerts_col.insert_one(alert_doc)
    alert_doc["_id"] = str(alert_res.inserted_id)

    # 3. Real-Time Broadcast via WebSocket to UI
    try:
        await manager.broadcast({"event_type": "NEW_LOG", "data": alert_doc})
    except Exception as ws_err:
        print(f"[WebSocket Broadcast Error]: {ws_err}")

    return {
        "status": "Drift Detected",
        "version": new_version,
        "drift": True,
        "alert_triggered": True,
    }


async def restore_baseline_service(agent_id: str, file_path: str):
    """
    Restores a baseline state by resetting the drift flag back to False,
    updating baseline status, and recording an audit log event.
    """
    fim_col, logs_col, _ = get_collections()
    now_str = datetime.now(timezone.utc).isoformat()

    existing = await fim_col.find_one(
        {"agent_id": agent_id, "file_path": file_path}
    )

    if not existing:
        return {"error": "Baseline record not found"}

    await fim_col.update_one(
        {"_id": existing["_id"]},
        {"$set": {"drift": False, "updated_at": now_str}},
    )

    # Insert Info Audit Log
    log_doc = {
        "agent_id": agent_id,
        "log_name": "Configuration Restored",
        "message": f"Baseline for file '{file_path}' manually restored by Administrator.",
        "level": "Information",
        "source": "FIM Engine",
        "timestamp": now_str,
    }
    await logs_col.insert_one(log_doc)

    return {
        "status": "Baseline Restored",
        "file_path": file_path,
        "drift": False,
    }