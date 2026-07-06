from fastapi import APIRouter
from app.db.database import client

router = APIRouter()

@router.get("/health", tags=["Health"])

def health():

    client.admin.command("ping")

    return {
        "status": "healthy",
        "database": "connected"
    }