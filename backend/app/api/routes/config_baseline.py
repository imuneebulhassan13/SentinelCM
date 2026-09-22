from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from app.core.dependencies import get_current_user
from app.models.config_baseline import get_baseline_collection
from app.schemas.config_baseline import ConfigBaselineCreate

router = APIRouter(prefix="/config", tags=["Configuration Baseline"])


@router.post("/baseline")
async def save_baseline(data: ConfigBaselineCreate):
    baselines = get_baseline_collection()

    # Find existing records for this file to calculate the next version number
    existing_records = await baselines.find(
        {"agent_id": data.agent_id, "file_path": data.file_path}
    ).to_list(length=100)

    current_version = len(existing_records) + 1

    # Mark previous baseline records for this file as inactive
    await baselines.update_many(
        {"agent_id": data.agent_id, "file_path": data.file_path},
        {"$set": {"is_active": False}},
    )

    # Insert the new baseline version
    document = {
        "agent_id": data.agent_id,
        "file_path": data.file_path,
        "file_hash": data.file_hash,
        "file_size": data.file_size,
        "version": current_version,
        "timestamp": data.timestamp,
        "is_active": True,
    }

    await baselines.insert_one(document)

    return {
        "message": f"Configuration baseline saved as version v{current_version}",
        "version": current_version,
    }


@router.get("/baseline")
async def get_baselines(agent_id: Optional[str] = None):
    baselines = get_baseline_collection()

    # Retrieve only current active baselines
    query = {"is_active": True}
    if agent_id:
        query["agent_id"] = agent_id

    cursor = baselines.find(query).sort("timestamp", -1)
    results = await cursor.to_list(length=100)

    for doc in results:
        doc["_id"] = str(doc["_id"])

    return {"baselines": results}


@router.get("/history")
async def get_config_history(
    file_path: str,
    agent_id: str,
    current_user=Depends(get_current_user),
):
    baselines = get_baseline_collection()

    # Retrieve all versions for this file sorted newest to oldest
    cursor = baselines.find(
        {"agent_id": agent_id, "file_path": file_path}
    ).sort("version", -1)

    history = await cursor.to_list(length=100)

    if not history:
        raise HTTPException(
            status_code=404, detail="No configuration history found for this file"
        )

    for doc in history:
        doc["_id"] = str(doc["_id"])

    return {
        "agent_id": agent_id,
        "file_path": file_path,
        "total_versions": len(history),
        "history": history,
    }