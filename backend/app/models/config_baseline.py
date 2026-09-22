from app.db import database


def get_baseline_collection():
    return database.database["config_baselines"]