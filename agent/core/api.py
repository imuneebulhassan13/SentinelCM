import requests

from config.config import SERVER_URL


def post(endpoint: str, payload: dict):

    response = requests.post(
        f"{SERVER_URL}{endpoint}",
        json=payload,
        timeout=10
    )

    response.raise_for_status()

    return response.json()