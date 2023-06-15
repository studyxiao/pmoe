import os

from app.core.log import GunicornLogger, configure_structlog

is_production = os.getenv("STATE") != "dev"
configure_structlog(is_production=is_production, log_level="DEBUG")

bind = "0.0.0.0:8000"

if not is_production:
    reload = True

worker = 1
worker_class = "gevent"
chdir = "/home/appuser"

# Logging
logger_class = GunicornLogger
