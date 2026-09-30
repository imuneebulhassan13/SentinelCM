from app.models.agent import get_agent_collection


def get_fim_collection():
    """Returns MongoDB collection handle for FIM baselines."""
    agent_col = get_agent_collection()
    return agent_col.database["fim_baselines"]