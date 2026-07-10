from pydantic import BaseModel
from datetime import datetime


class LogCreate(BaseModel):
    agent_id: str
    event_id: int
    source: str
    level: str
    log_name: str
    message: str
    timestamp: datetime