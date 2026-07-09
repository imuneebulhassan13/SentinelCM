import requests

from config import SERVER_URL


def register_agent(data):

    response = requests.post(
        f"{SERVER_URL}/agents/register",
        json=data,
        timeout=10
    )

    response.raise_for_status()

    return response.json()