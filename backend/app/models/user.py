import app.db.database as db


def get_user_collection():
    return db.database["users"]