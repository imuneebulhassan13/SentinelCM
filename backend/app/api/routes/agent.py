from fastapi import APIRouter

from app.schemas.agent import AgentRegister
from app.services.agent_service import register_agent

router = APIRouter(
    prefix="/agents",
    tags=["Agents"],
)


@router.post("/register")
async def register(agent: AgentRegister):

    agent_id = await register_agent(agent)

    return {
        "message": "Agent registered successfully",
        "agent_id": agent_id
    }