from bson import ObjectId
from fastapi import APIRouter, HTTPException
from app.models.agent import get_agent_collection

router = APIRouter(prefix="/alerts", tags=["Alerts"])


def get_collections():
    agent_col = get_agent_collection()
    db = agent_col.database
    return db["alerts"], db["logs"]


def sanitize_doc(doc):
    """Ensure all BSON/ObjectId fields are converted to string safely."""
    clean = {}
    for k, v in doc.items():
        if isinstance(v, ObjectId):
            clean[k] = str(v)
        else:
            clean[k] = v
    clean["_id"] = str(doc.get("_id", ""))
    return clean


@router.get("/")
@router.get("")
async def get_all_alerts():
    alerts_col, logs_col = get_collections()

    # Fetch from alerts collection
    alerts_cursor = alerts_col.find({}).sort("timestamp", -1)
    alerts_list = await alerts_cursor.to_list(length=100)

    # Fetch high severity events from logs collection
    logs_cursor = logs_col.find(
        {"level": {"$in": ["Error", "Critical", "High", "error", "critical", "high"]}}
    ).sort("timestamp", -1)
    logs_list = await logs_cursor.to_list(length=100)

    formatted_alerts = []
    seen_ids = set()

    for raw_a in alerts_list:
        a = sanitize_doc(raw_a)
        a_id = a["_id"]
        if "title" not in a or not a["title"]:
            a["title"] = a.get("log_name", "Security Alert")
        if "severity" not in a or not a["severity"]:
            a["severity"] = (
                "High" if str(a.get("level", "")).capitalize() in ["Error", "Critical", "High"] else "Medium"
            )
        if "message" not in a:
            a["message"] = a.get("log_name", "Security Alert Event")
        if "acknowledged" not in a:
            a["acknowledged"] = False
        formatted_alerts.append(a)
        seen_ids.add(a_id)

    for raw_l in logs_list:
        l = sanitize_doc(raw_l)
        l_id = l["_id"]
        if l_id not in seen_ids:
            if "title" not in l or not l["title"]:
                l["title"] = l.get("log_name", "Critical Security Event")
            if "severity" not in l or not l["severity"]:
                l["severity"] = (
                    "High" if str(l.get("level", "")).capitalize() in ["Error", "Critical", "High"] else "Medium"
                )
            if "acknowledged" not in l:
                l["acknowledged"] = False
            formatted_alerts.append(l)
            seen_ids.add(l_id)

    formatted_alerts.sort(key=lambda x: str(x.get("timestamp", "")), reverse=True)

    return {"alerts": formatted_alerts}


@router.patch("/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    alerts_col, logs_col = get_collections()
    try:
        try:
            obj_id = ObjectId(alert_id)
            query = {"_id": obj_id}
        except Exception:
            query = {"_id": alert_id}

        res1 = await alerts_col.update_one(query, {"$set": {"acknowledged": True}})
        res2 = await logs_col.update_one(query, {"$set": {"acknowledged": True}})

        if res1.modified_count == 0 and res2.modified_count == 0:
            await alerts_col.update_one({"_id": alert_id}, {"$set": {"acknowledged": True}})
            await logs_col.update_one({"_id": alert_id}, {"$set": {"acknowledged": True}})

        return {"message": "Alert acknowledged"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))