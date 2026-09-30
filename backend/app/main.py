import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.agent import router as agent_router
from app.api.routes.alert import router as alert_router
from app.api.routes.auth import router as auth_router
from app.api.routes.config_baseline import router as config_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.heartbeat import router as heartbeat_router
from app.api.routes.log import router as log_router
from app.core.config import settings
from app.core.logger import logger
from app.db.database import close_mongo_connection, connect_to_mongo
from app.services.monitor_service import monitor_agents
from app.services.syslog_service import start_syslog_server
from app.api.routes.websocket import router as ws_router
from app.api.routes.fim import router as fim_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting SentinelCM Backend...")

    await connect_to_mongo()
    await start_syslog_server()  # Starts UDP Syslog Server

    asyncio.create_task(monitor_agents())

    yield

    logger.info("Stopping SentinelCM Backend...")

    await close_mongo_connection()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Lightweight Open-Source SIEM for Centralized Configuration and Integrity Monitoring",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(agent_router)
app.include_router(heartbeat_router)
app.include_router(log_router)
app.include_router(alert_router)
app.include_router(dashboard_router)
app.include_router(config_router)
app.include_router(ws_router)
app.include_router(fim_router)

@app.get("/")
async def root():
    return {
        "message": "Welcome to SentinelCM API",
        "version": settings.APP_VERSION,
        "status": "Running",
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "database": "connected"}