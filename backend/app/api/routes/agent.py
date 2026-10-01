from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import uuid

from app.models.agent import get_agent_collection

router = APIRouter(prefix="/agents", tags=["Agents"])


class RegisterAgentRequest(BaseModel):
    hostname: str
    ip_address: str = "127.0.0.1"
    os: str = "Windows"


class HeartbeatRequest(BaseModel):
    agent_id: str


@router.get("/")
@router.get("")
async def get_all_agents():
    """Retrieve all registered endpoint agents."""
    agents_col = get_agent_collection()
    cursor = agents_col.find({})
    agents = await cursor.to_list(length=100)

    for ag in agents:
        ag["_id"] = str(ag["_id"])
        # Ensure timestamp field mapping
        ag["last_heartbeat"] = (
            ag.get("last_heartbeat")
            or ag.get("last_seen")
            or ag.get("updated_at")
            or ag.get("timestamp")
        )

    return {"agents": agents}


@router.post("/register")
async def register_agent(payload: RegisterAgentRequest):
    """Register a new endpoint agent or return existing agent details."""
    agents_col = get_agent_collection()
    now_str = datetime.now(timezone.utc).isoformat()

    # Check if agent already exists with same hostname
    existing_agent = await agents_col.find_one({"hostname": payload.hostname})

    if existing_agent:
        await agents_col.update_one(
            {"_id": existing_agent["_id"]},
            {
                "$set": {
                    "status": "online",
                    "last_heartbeat": now_str,
                    "last_seen": now_str,
                }
            },
        )
        return {
            "agent_id": existing_agent["agent_id"],
            "message": "Agent re-registered successfully",
        }

    new_agent_id = str(uuid.uuid4())

    agent_doc = {
        "agent_id": new_agent_id,
        "hostname": payload.hostname,
        "ip_address": payload.ip_address,
        "os": payload.os,
        "status": "online",
        "registered_at": now_str,
        "last_heartbeat": now_str,
        "last_seen": now_str,
    }

    await agents_col.insert_one(agent_doc)
    return {"agent_id": new_agent_id, "message": "Agent registered successfully"}


@router.post("/heartbeat")
async def receive_heartbeat(payload: HeartbeatRequest):
    """Receive heartbeat ping from agent executable."""
    agents_col = get_agent_collection()
    now_str = datetime.now(timezone.utc).isoformat()

    await agents_col.update_one(
        {"agent_id": payload.agent_id},
        {
            "$set": {
                "status": "online",
                "last_heartbeat": now_str,
                "last_seen": now_str,
            }
        },
    )
    return {"message": "Heartbeat received", "timestamp": now_str}


@router.get("/{agent_id}")
async def get_agent_by_id(agent_id: str):
    """Get details for a specific agent by UUID."""
    agents_col = get_agent_collection()
    agent = await agents_col.find_one({"agent_id": agent_id})

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    agent["_id"] = str(agent["_id"])
    agent["last_heartbeat"] = (
        agent.get("last_heartbeat")
        or agent.get("last_seen")
        or agent.get("updated_at")
        or agent.get("timestamp")
    )
    return agent