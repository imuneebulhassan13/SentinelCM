from datetime import datetime
from pydantic import BaseModel


class AlertCreate(BaseModel):
    agent_id: str
    alert_type: str
    severity: str
    title: str
    message: str
    source: str
    event_id: int | None = None
    timestamp: datetime
    acknowledged: bool = False