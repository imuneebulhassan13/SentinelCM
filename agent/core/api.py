import requests

BASE_URL = "http://127.0.0.1:8000"


def post(endpoint, json_data, timeout=5):
    # Ensure full URL scheme is present
    if not endpoint.startswith("http://") and not endpoint.startswith(
        "https://"
    ):
        url = f"{BASE_URL}{endpoint if endpoint.startswith('/') else '/' + endpoint}"
    else:
        url = endpoint

    try:
        response = requests.post(url, json=json_data, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as err:
        print(f"[API Warning] Backend communication error: {err}")
        return None