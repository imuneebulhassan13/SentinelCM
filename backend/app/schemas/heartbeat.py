from pydantic import BaseModel


class HeartbeatRequest(BaseModel):
    agent_id: str