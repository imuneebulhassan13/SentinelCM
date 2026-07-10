from fastapi import APIRouter

from app.schemas.log import LogCreate
from app.services.log_service import save_log

router = APIRouter(
    prefix="/logs",
    tags=["Logs"]
)


@router.post("/")
async def receive_log(log: LogCreate):

    await save_log(log)

    return {
        "message": "Log received successfully"
    }