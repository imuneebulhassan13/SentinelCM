from typing import Optional
from fastapi import APIRouter
from app.models.config_baseline import get_baseline_collection
from app.schemas.config_baseline import ConfigBaselineCreate

router = APIRouter(prefix="/config", tags=["Configuration Baseline"])


@router.post("/baseline")
async def save_baseline(data: ConfigBaselineCreate):
    baselines = get_baseline_collection()

    query = {"agent_id": data.agent_id, "file_path": data.file_path}
    update = {
        "$set": {
            "agent_id": data.agent_id,
            "file_path": data.file_path,
            "file_hash": data.file_hash,
            "file_size": data.file_size,
            "timestamp": data.timestamp,
        }
    }

    await baselines.update_one(query, update, upsert=True)
    return {"message": "Configuration baseline saved successfully"}


@router.get("/baseline")
async def get_baselines(agent_id: Optional[str] = None):
    baselines = get_baseline_collection()
    query = {}
    if agent_id:
        query["agent_id"] = agent_id

    cursor = baselines.find(query).sort("timestamp", -1)
    results = await cursor.to_list(length=100)

    for doc in results:
        doc["_id"] = str(doc["_id"])

    return {"baselines": results}