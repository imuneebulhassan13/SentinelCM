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
        # Ensure UI fields alignment
        b["status"] = "Drift Detected" if b.get("drift") else "In Sync"

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
            "baseline_hash": current_hash,
            "hash": current_hash,
            "version": 1,
            "drift": False,
            "restore_pending": False,
            "status": "In Sync",
            "created_at": now_str,
            "updated_at": now_str,
        }
        await fim_col.insert_one(doc)
        return {"status": "Baseline Created", "version": 1, "drift": False}

    # Check if UI requested a Restore Command
    if existing.get("restore_pending"):
        await fim_col.update_one(
            {"_id": existing["_id"]},
            {
                "$set": {
                    "hash": existing.get("baseline_hash"),
                    "current_hash": existing.get("baseline_hash"),
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
            "target_hash": existing.get("baseline_hash")
        }

    baseline_hash = existing.get("baseline_hash", existing.get("hash"))

    if current_hash == baseline_hash:
        await fim_col.update_one(
            {"_id": existing["_id"]},
            {
                "$set": {
                    "hash": current_hash,
                    "drift": False,
                    "status": "In Sync",
                    "updated_at": now_str,
                }
            },
        )
        return {"status": "In Sync", "version": existing.get("version", 1), "drift": False}

    # Hash Mismatch -> Drift Detected
    new_version = existing.get("version", 1) + (0 if existing.get("drift") else 1)

    await fim_col.update_one(
        {"_id": existing["_id"]},
        {
            "$set": {
                "hash": current_hash,
                "version": new_version,
                "drift": True,
                "status": "Drift Detected",
                "updated_at": now_str,
            }
        },
    )

    return {"status": "Drift Detected", "version": new_version, "drift": True}


async def restore_baseline_service(agent_id: str, file_path: str):
    fim_col, logs_col, _ = get_collections()
    now_str = datetime.now(timezone.utc).isoformat()

    existing = await fim_col.find_one(
        {"agent_id": agent_id, "file_path": file_path}
    )

    if not existing:
        return {"error": "Baseline record not found"}

    # Set restore_pending flag true for agent pull
    await fim_col.update_one(
        {"_id": existing["_id"]},
        {"$set": {"restore_pending": True, "updated_at": now_str}},
    )

    # SIEM Audit Log Entry
    log_doc = {
        "agent_id": agent_id,
        "log_name": "Configuration Restore Initiated",
        "message": f"Administrator issued restore command for file '{file_path}'.",
        "level": "Information",
        "source": "FIM Engine",
        "timestamp": now_str,
    }
    await logs_col.insert_one(log_doc)

    return {"status": "Restore Command Queued", "file_path": file_path}