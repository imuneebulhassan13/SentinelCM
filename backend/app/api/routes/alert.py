from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_current_user
from app.models.alert import get_alert_collection


router = APIRouter(
    prefix="/alerts",
    tags=["Alerts"]
)


@router.get("/")
async def get_alerts(
    current_user=Depends(get_current_user),
    severity: str | None = Query(default=None),
    source: str | None = Query(default=None),
):
    alerts = get_alert_collection()

    query = {}

    if severity and severity.lower() != "all":
        query["severity"] = severity

    if source and source.lower() != "all":
        query["source"] = source

    documents = (
        await alerts
        .find(query)
        .sort("timestamp", -1)
        .limit(100)
        .to_list(length=100)
    )

    for document in documents:
        document["_id"] = str(document["_id"])

    return {
        "alerts": documents,
        "total": len(documents),
    }