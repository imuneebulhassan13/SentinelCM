import requests

from config import SERVER_URL


def send_heartbeat(agent_id):

    response = requests.post(
        f"{SERVER_URL}/agents/heartbeat",
        json={
            "agent_id": agent_id
        },
        timeout=10
    )

    return response.json()