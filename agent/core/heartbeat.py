from core.api import post


def send_heartbeat(agent_id):

    return post(
        "/agents/heartbeat",
        {
            "agent_id": agent_id
        }
    )