import sys
from loguru import logger

logger.remove()

logger.add(
    sys.stdout,
    level="INFO",
    colorize=True,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
           "<level>{level}</level> | "
           "<cyan>{message}</cyan>",
)

logger.add(
    "logs/sentinelcm.log",
    rotation="10 MB",
    retention="30 days",
    level="INFO",
)