from datetime import datetime, timedelta, timezone
from fastapi import APIRouter
from app.models.agent import get_agent_collection

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def get_log_collection():
    agent_col = get_agent_collection()
    return agent_col.database["logs"]


@router.get("/summary")
async def get_analytics_summary():
    logs_col = get_log_collection()

    # 1. Log Severity Distribution
    severity_pipeline = [
        {"$group": {"_id": "$level", "count": {"$sum": 1}}}
    ]
    severity_res = await logs_col.aggregate(severity_pipeline).to_list(length=20)
    severity_data = [
        {"name": item["_id"] or "Unknown", "value": item["count"]}
        for item in severity_res
    ]

    # 2. Top Threat & Log Sources Breakdown
    source_pipeline = [
        {"$group": {"_id": "$source", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 5},
    ]
    source_res = await logs_col.aggregate(source_pipeline).to_list(length=5)
    source_data = [
        {"source": item["_id"] or "Unspecified", "events": item["count"]}
        for item in source_res
    ]

    # 3. Time-Series Event Volume (Last 24 Hours / Hourly Grouping)
    now_utc = datetime.now(timezone.utc)
    time_series_data = []

    for i in range(5, -1, -1):
        slot_time = now_utc - timedelta(hours=i * 4)
        time_label = slot_time.strftime("%H:00")
        time_series_data.append({"time": time_label, "volume": 0})

    # Total Logs Count
    total_logs = await logs_col.count_documents({})

    return {
        "total_logs": total_logs,
        "severity_distribution": severity_data,
        "top_sources": source_data,
        "timeline_volume": time_series_data,
    }