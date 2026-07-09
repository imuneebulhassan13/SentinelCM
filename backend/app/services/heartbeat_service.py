from datetime import datetime

from app.models.agent import get_agent_collection


async def update_heartbeat(agent_id: str):

    agents = get_agent_collection()

    result = await agents.update_one(
        {"agent_id": agent_id},
        {
            "$set": {
                "last_seen": datetime.utcnow(),
                "status": "online"
            }
        }
    )

    return result.modified_count > 0