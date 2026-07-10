from core.api import post


def register_agent(data):

    return post(
        "/agents/register",
        data
    )