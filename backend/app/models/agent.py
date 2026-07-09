from app.db import database as db


def get_agent_collection():
    return db.database["agents"]