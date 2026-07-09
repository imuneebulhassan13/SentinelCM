from pydantic import BaseModel
from datetime import datetime


class AgentRegister(BaseModel):
    hostname: str
    ip_address: str
    operating_system: str
    agent_version: str


class AgentResponse(BaseModel):
    agent_id: str
    hostname: str
    status: str