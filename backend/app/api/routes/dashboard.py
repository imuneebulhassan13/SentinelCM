from fastapi import APIRouter, Depends

from app.core.dependencies import get_current_user
from app.models.agent import get_agent_collection
from app.models.log import get_log_collection


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


@router.get("/summary")
async def dashboard_summary(
    current_user=Depends(get_current_user)
):
    agents = get_agent_collection()
    logs = get_log_collection()

    total_agents = await agents.count_documents({})

    online_agents = await agents.count_documents({
        "status": "online"
    })

    offline_agents = await agents.count_documents({
        "status": "offline"
    })

    total_logs = await logs.count_documents({})

    error_logs = await logs.count_documents({
        "level": "Error"
    })

    warning_logs = await logs.count_documents({
        "level": "Warning"
    })

    information_logs = await logs.count_documents({
        "level": "Information"
    })

    return {
        "agents": {
            "total": total_agents,
            "online": online_agents,
            "offline": offline_agents
        },
        "logs": {
            "total": total_logs,
            "error": error_logs,
            "warning": warning_logs,
            "information": information_logs
        }
    }