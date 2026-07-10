import app.db.database as db


def get_agent_collection():
    return db.database["agents"]