from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.fim_service import get_all_baselines, process_fim_check

router = APIRouter(prefix="/fim", tags=["File Integrity Monitoring"])


class FIMCheckSchema(BaseModel):
    agent_id: str
    file_path: str
    hash: str


@router.get("/baselines")
async def fetch_baselines():
    """Retrieve all recorded baselines for UI."""
    baselines = await get_all_baselines()
    return {"baselines": baselines}


@router.post("/check")
async def check_file_integrity(payload: FIMCheckSchema):
    """Endpoint called by endpoint agents to push file hashes."""
    result = await process_fim_check(
        payload.agent_id, payload.file_path, payload.hash
    )
    return result