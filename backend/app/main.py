from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.logger import logger
from app.db.database import connect_to_mongo, close_mongo_connection

from app.api.routes.auth import router as auth_router
from app.api.routes.agent import router as agent_router
from app.api.routes.heartbeat import router as heartbeat_router

import asyncio
from app.services.monitor_service import monitor_agents
from app.api.routes.log import router as log_router

@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("Starting SentinelCM Backend...")

    await connect_to_mongo()

    asyncio.create_task(
        monitor_agents()
    )

    yield

    logger.info("Stopping SentinelCM Backend...")

    await close_mongo_connection()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Lightweight Open-Source SIEM for Centralized Configuration and Integrity Monitoring",
    lifespan=lifespan,
)

app.include_router(auth_router)
app.include_router(agent_router)
app.include_router(heartbeat_router)
app.include_router(log_router)

@app.get("/")
async def root():
    return {
        "message": "Welcome to SentinelCM API",
        "version": settings.APP_VERSION,
        "status": "Running"
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "database": "connected"
    }