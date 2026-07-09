from fastapi import APIRouter, HTTPException

from app.schemas.heartbeat import HeartbeatRequest
from app.services.heartbeat_service import update_heartbeat

router = APIRouter(
    prefix="/agents",
    tags=["Agents"],
)


@router.post("/heartbeat")
async def heartbeat(data: HeartbeatRequest):

    success = await update_heartbeat(data.agent_id)

    if not success:
        raise HTTPException(
            status_code=404,
            detail="Agent not found"
        )

    return {
        "message": "Heartbeat received"
    }