import uuid
from datetime import datetime

from app.models.agent import get_agent_collection


async def register_agent(agent):

    agents = get_agent_collection()

    existing = await agents.find_one(
        {
            "hostname": agent.hostname
        }
    )

    if existing:

        await agents.update_one(
            {"hostname": agent.hostname},
            {
                "$set": {
                    "ip_address": agent.ip_address,
                    "operating_system": agent.operating_system,
                    "agent_version": agent.agent_version,
                    "status": "online",
                    "last_seen": datetime.utcnow()
                }
            }
        )

        return existing["agent_id"]

    agent_id = str(uuid.uuid4())

    document = {
        "agent_id": agent_id,
        "hostname": agent.hostname,
        "ip_address": agent.ip_address,
        "operating_system": agent.operating_system,
        "agent_version": agent.agent_version,
        "status": "online",
        "registered_at": datetime.utcnow(),
        "last_seen": datetime.utcnow()
    }

    await agents.insert_one(document)

    return agent_id