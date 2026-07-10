import asyncio
from datetime import datetime, timedelta

from app.models.agent import get_agent_collection
from app.core.logger import logger


async def monitor_agents():

    while True:

        agents = get_agent_collection()

        threshold = datetime.utcnow() - timedelta(seconds=90)

        result = await agents.update_many(
            {
                "last_seen": {
                    "$lt": threshold
                }
            },
            {
                "$set": {
                    "status": "offline"
                }
            }
        )

        if result.modified_count > 0:
            logger.info(f"{result.modified_count} agent(s) marked offline.")

        await asyncio.sleep(30)