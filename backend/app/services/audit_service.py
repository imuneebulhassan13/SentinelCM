from datetime import datetime, timezone
from app.models.agent import get_agent_collection


def get_audit_collection():
    agent_col = get_agent_collection()
    db = agent_col.database
    return db["audit_logs"]


async def record_audit_log(
    user: str,
    action: str,
    resource: str,
    details: str,
    status: str = "SUCCESS",
    ip_address: str = "127.0.0.1",
):
    """
    Centralized function to log security-sensitive admin/analyst actions.
    """
    audit_col = get_audit_collection()
    now_str = datetime.now(timezone.utc).isoformat()

    doc = {
        "user": user,
        "action": action,  # e.g., 'FIM_RESTORE', 'ALERT_ACKNOWLEDGE', 'USER_LOGIN'
        "resource": resource,  # e.g., 'hosts', 'alert_64a...'
        "details": details,
        "status": status,  # 'SUCCESS' or 'FAILED'
        "ip_address": ip_address,
        "timestamp": now_str,
    }

    res = await audit_col.insert_one(doc)
    doc["_id"] = str(res.inserted_id)
    return doc


async def get_all_audit_logs(limit: int = 100):
    audit_col = get_audit_collection()
    cursor = audit_col.find({}).sort("timestamp", -1).limit(limit)
    logs = await cursor.to_list(length=limit)

    for log in logs:
        log["_id"] = str(log["_id"])

    return logs