from datetime import datetime
from pydantic import BaseModel


class ConfigBaselineCreate(BaseModel):
    agent_id: str
    file_path: str
    file_hash: str
    file_size: int
    timestamp: datetime