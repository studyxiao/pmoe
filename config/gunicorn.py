import os

from app.core.log import GunicornLogger, configure_structlog
from config import config as base_config  # config 名称有冲突

is_production = os.getenv("STATE") != "dev"
configure_structlog(is_production=is_production, log_level="DEBUG")

bind = f"0.0.0.0:{base_config.WEB_PORT}"

if not is_production:
    reload = True

worker = 1
worker_class = "gevent"
chdir = "/home/appuser"

# Logging
logger_class = GunicornLogger
