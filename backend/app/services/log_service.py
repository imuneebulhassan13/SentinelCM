from app.models.log import get_log_collection


async def save_log(log):

    logs = get_log_collection()

    document = {
        "agent_id": log.agent_id,
        "event_id": log.event_id,
        "source": log.source,
        "level": log.level,
        "log_name": log.log_name,
        "message": log.message,
        "timestamp": log.timestamp,
    }

    await logs.insert_one(document)

    return True