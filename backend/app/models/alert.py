from app.db import database


def get_alert_collection():
    return database.database["alerts"]