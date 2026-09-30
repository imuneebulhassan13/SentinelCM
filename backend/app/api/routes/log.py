from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Query
from pydantic import BaseModel
from app.models.agent import get_agent_collection

router = APIRouter(prefix="/logs", tags=["Logs"])


def get_log_collection():
    agent_col = get_agent_collection()
    return agent_col.database["logs"]


class LogIngestSchema(BaseModel):
    agent_id: str
    log_name: str
    message: str
    level: str
    source: str
    timestamp: Optional[str] = None


@router.post("/")
@router.post("")
async def receive_log(payload: LogIngestSchema):
    """Ingest incoming logs and standardize timestamp format for MongoDB sorting."""
    logs_col = get_log_collection()
    now_utc = datetime.now(timezone.utc)

    # Standardize timestamp to UTC ISO 8601 string
    try:
        if payload.timestamp:
            dt = datetime.fromisoformat(
                payload.timestamp.replace("Z", "+00:00")
            )
            iso_time = dt.astimezone(timezone.utc).isoformat()
        else:
            iso_time = now_utc.isoformat()
    except Exception:
        iso_time = now_utc.isoformat()

    doc = payload.dict()
    doc["timestamp"] = iso_time

    res = await logs_col.insert_one(doc)
    doc["_id"] = str(res.inserted_id)

    # Broadcast via WebSocket
    from app.api.routes.websocket import manager

    try:
        await manager.broadcast({"event_type": "NEW_LOG", "data": doc})
    except Exception as ws_err:
        print(f"[WebSocket Broadcast Error]: {ws_err}")

    return {"message": "Log ingested successfully", "id": doc["_id"]}


@router.delete("/clear")
async def clear_old_logs():
    """Clear old non-standardized logs from MongoDB."""
    logs_col = get_log_collection()
    res = await logs_col.delete_many({})
    return {"message": f"Cleared {res.deleted_count} logs"}


@router.get("/")
@router.get("")
async def get_logs(
    search: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
):
    logs_col = get_log_collection()
    query = {}

    if search:
        query["$or"] = [
            {"log_name": {"$regex": search, "$options": "i"}},
            {"message": {"$regex": search, "$options": "i"}},
            {"agent_id": {"$regex": search, "$options": "i"}},
            {"source": {"$regex": search, "$options": "i"}},
        ]

    if level and level.lower() != "all":
        query["level"] = {"$regex": f"^{level}$", "$options": "i"}

    if source and source.lower() != "all":
        query["source"] = {"$regex": f"^{source}$", "$options": "i"}

    # Sort descending by timestamp
    cursor = logs_col.find(query).sort("timestamp", -1)
    logs = await cursor.to_list(length=100)

    for log in logs:
        log["_id"] = str(log["_id"])

    return {"logs": logs}