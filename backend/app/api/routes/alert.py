from typing import Optional
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query
from app.models.alert import get_alert_collection
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.get("/")
async def get_alerts(
    severity: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    current_user=Depends(get_current_user),
):
    alerts = get_alert_collection()
    query = {}

    if severity and severity.lower() != "all":
        query["severity"] = severity

    if source and source.lower() != "all":
        query["source"] = source

    cursor = alerts.find(query).sort("timestamp", -1).limit(100)
    alerts_list = await cursor.to_list(length=100)

    for alert in alerts_list:
        alert["_id"] = str(alert["_id"])

    return {"alerts": alerts_list}


@router.patch("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str, current_user=Depends(get_current_user)
):
    alerts = get_alert_collection()

    try:
        obj_id = ObjectId(alert_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid Alert ID format")

    result = await alerts.update_one(
        {"_id": obj_id}, {"$set": {"acknowledged": True}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Alert not found")

    return {"message": "Alert acknowledged successfully"}