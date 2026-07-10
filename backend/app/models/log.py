import app.db.database as db


def get_log_collection():
    return db.database["logs"]