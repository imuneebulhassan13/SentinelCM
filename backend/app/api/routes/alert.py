from bson import ObjectId
from fastapi import APIRouter, HTTPException
from app.models.agent import get_agent_collection

router = APIRouter(prefix="/alerts", tags=["Alerts"])


def get_collections():
    agent_col = get_agent_collection()
    db = agent_col.database
    return db["alerts"], db["logs"]


@router.get("/")
@router.get("")
async def get_all_alerts():
    alerts_col, logs_col = get_collections()

    # Fetch from alerts collection
    alerts_cursor = alerts_col.find({}).sort("timestamp", -1)
    alerts_list = await alerts_cursor.to_list(length=100)

    # Fetch high severity events from logs collection
    logs_cursor = logs_col.find(
        {"level": {"$in": ["Error", "Critical", "High"]}}
    ).sort("timestamp", -1)
    logs_list = await logs_cursor.to_list(length=100)

    formatted_alerts = []
    seen_ids = set()

    for a in alerts_list:
        a_id = str(a["_id"])
        a["_id"] = a_id
        if "title" not in a:
            a["title"] = a.get("log_name", "Security Alert")
        if "severity" not in a:
            a["severity"] = (
                "High" if a.get("level") in ["Error", "Critical"] else "Medium"
            )
        formatted_alerts.append(a)
        seen_ids.add(a_id)

    for l in logs_list:
        l_id = str(l["_id"])
        if l_id not in seen_ids:
            l["_id"] = l_id
            l["title"] = l.get("log_name", "Critical Security Event")
            l["severity"] = (
                "High" if l.get("level") in ["Error", "Critical"] else "Medium"
            )
            l["acknowledged"] = l.get("acknowledged", False)
            formatted_alerts.append(l)
            seen_ids.add(l_id)

    formatted_alerts.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

    return {"alerts": formatted_alerts}


@router.patch("/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    alerts_col, logs_col = get_collections()
    try:
        obj_id = ObjectId(alert_id)
        res1 = await alerts_col.update_one(
            {"_id": obj_id}, {"$set": {"acknowledged": True}}
        )
        res2 = await logs_col.update_one(
            {"_id": obj_id}, {"$set": {"acknowledged": True}}
        )

        if res1.modified_count == 0 and res2.modified_count == 0:
            await alerts_col.update_one(
                {"_id": alert_id}, {"$set": {"acknowledged": True}}
            )
            await logs_col.update_one(
                {"_id": alert_id}, {"$set": {"acknowledged": True}}
            )

        return {"message": "Alert acknowledged"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))