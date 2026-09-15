from app.models.alert import get_alert_collection


async def create_alert_from_log(log):
    """
    Create an alert when a security-relevant log is received.
    """

    # Only Error and Warning logs currently generate alerts
    if log.level not in ["Error", "Warning"]:
        return False

    alerts = get_alert_collection()

    severity = "High" if log.level == "Error" else "Medium"

    alert = {
        "agent_id": log.agent_id,
        "alert_type": "Log Event",
        "severity": severity,
        "title": f"{log.level} event detected",
        "message": log.message,
        "source": log.source,
        "event_id": log.event_id,
        "timestamp": log.timestamp,
        "acknowledged": False,
    }

    await alerts.insert_one(alert)

    return True