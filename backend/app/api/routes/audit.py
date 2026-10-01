from fastapi import APIRouter
from app.services.audit_service import get_all_audit_logs

router = APIRouter(prefix="/audit", tags=["Security Audit Trail"])


@router.get("/logs")
async def fetch_audit_logs():
    """Retrieve all recorded administrative security audit logs."""
    logs = await get_all_audit_logs()
    return {"audit_logs": logs}