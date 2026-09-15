from datetime import datetime


EVENT_LEVELS = {
    1: "Error",
    2: "Warning",
    4: "Information",
}


def parse_event(event, agent_id, log_name):
    """
    Convert a raw Windows Event Log record
    into SentinelCM standardized log format.
    """

    event_type = getattr(event, "EventType", None)

    level = EVENT_LEVELS.get(
        event_type,
        "Information"
    )

    message_parts = getattr(
        event,
        "StringInserts",
        None
    )

    if message_parts:
        message = " ".join(
            str(part) for part in message_parts
        )
    else:
        message = ""

    timestamp = getattr(
        event,
        "TimeGenerated",
        None
    )

    if timestamp is None:
        timestamp = datetime.now()

    return {
        "agent_id": agent_id,
        "event_id": int(event.EventID),
        "source": "Windows",
        "level": level,
        "log_name": log_name,
        "message": message,
        "timestamp": timestamp.isoformat(),
    }