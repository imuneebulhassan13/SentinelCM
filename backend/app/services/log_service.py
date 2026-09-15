import hashlib

from app.models.log import get_log_collection
from app.services.alert_service import create_alert_from_log


def create_event_hash(log):
    raw_data = (
        f"{log.agent_id}|"
        f"{log.log_name}|"
        f"{log.event_id}|"
        f"{log.source}|"
        f"{log.level}|"
        f"{log.message}|"
        f"{log.timestamp.isoformat()}"
    )

    return hashlib.sha256(
        raw_data.encode("utf-8")
    ).hexdigest()


async def save_log(log):
    logs = get_log_collection()

    event_hash = create_event_hash(log)

    existing_log = await logs.find_one(
        {"event_hash": event_hash}
    )

    if existing_log:
        return False

    document = {
        "agent_id": log.agent_id,
        "event_id": log.event_id,
        "source": log.source,
        "level": log.level,
        "log_name": log.log_name,
        "message": log.message,
        "timestamp": log.timestamp,
        "event_hash": event_hash,
    }

    await logs.insert_one(document)

    await create_alert_from_log(log)
    
    return True