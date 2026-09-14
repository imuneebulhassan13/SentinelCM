from fastapi import APIRouter, Depends, Query

from app.schemas.log import LogCreate
from app.services.log_service import save_log
from app.models.log import get_log_collection
from app.core.dependencies import get_current_user

router = APIRouter(
    prefix="/logs",
    tags=["Logs"]
)


@router.post("/")
async def receive_log(log: LogCreate):

    await save_log(log)

    return {
        "message": "Log received successfully"
    }


@router.get("/")
async def get_logs(
    current_user=Depends(get_current_user),
    search: str | None = Query(default=None),
    level: str | None = Query(default=None),
    source: str | None = Query(default=None),
):
    logs = get_log_collection()

    query = {}

    if search:
        query["$or"] = [
            {"message": {"$regex": search, "$options": "i"}},
            {"log_name": {"$regex": search, "$options": "i"}},
        ]

        # event_id integer hai, isliye usay regex search mein directly use nahi karenge.
        if search.isdigit():
            query["$or"].append({
                "event_id": int(search)
            })

    if level and level.lower() != "all":
        query["level"] = level

    if source and source.lower() != "all":
        query["source"] = source

    documents = (
        await logs
        .find(query)
        .sort("timestamp", -1)
        .limit(100)
        .to_list(length=100)
    )

    for document in documents:
        document["_id"] = str(document["_id"])

    return {
        "logs": documents,
        "total": len(documents)
    }