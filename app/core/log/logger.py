import logging
import time
import uuid

import structlog
from flask import Flask, Response, g, request
from gunicorn.glogging import Logger as _GunicornLogger  # type: ignore

# 自定义 日志记录,不再使用 flask werkzeug gunicorn 等的日志记录
# access_logger 每次请求都会记录
access_logger: structlog.stdlib.BoundLogger = structlog.get_logger("api.access")
# error_logger 只有在出现异常时才会记录,也可以手动触发,并绑定到了 app.logger
error_logger: structlog.stdlib.BoundLogger = structlog.get_logger("api.error")


class Logger:
    """重写 flask 的日志记录器,不再使用 flask 的日志记录器.

    需要先将 config.configure_structlog(is_production=False, log_level="DEBUG") 设置好.
    """

    def __init__(self, app: Flask) -> None:
        self.app = app

        self.registe_log()

    def registe_log(self) -> None:
        @self.app.before_request
        def log_request_before() -> None:  # type: ignore
            """在请求之前绑定上下文变量."""
            structlog.contextvars.clear_contextvars()
            request_id = str(uuid.uuid4())
            structlog.contextvars.bind_contextvars(
                request_id=request_id,
            )
            g.start_time = time.perf_counter_ns()

        @self.app.after_request
        def log_request_after(response: Response) -> Response:  # type: ignore
            """在请求之后记录日志."""
            process_time = time.perf_counter_ns() - g.start_time if hasattr(g, "start_time") else -1
            http_method = request.method
            url = request.url
            http_version = request.environ.get("SERVER_PROTOCOL")
            status_code = response.status_code
            remote_addr = request.remote_addr
            message = f'{remote_addr} - "{http_method} {url} {http_version}" {status_code}'
            access_logger.info(
                message,
                http={
                    "url": f"{request.url}",
                    "status_code": status_code,
                    "method": http_method,
                    "version": http_version,
                },
                network={"client": remote_addr},
                duration=process_time,
            )
            return response

        self.app.logger = error_logger  # type: ignore


class GunicornLogger(_GunicornLogger):
    """重写 gunicorn 的日志记录器,不再使用 gunicorn 的日志记录器.

    >>> logger_class = "app.core.log.logger.GunicornLogger"
    """

    def __init__(self, cfg):  # noqa # type: ignore
        self.error_log = logging.getLogger("gunicorn.error")
        self.error_log.level = logging.INFO

        self.access_log = logging.getLogger("gunicorn.access")
        self.access_log.level = logging.INFO
        self.cfg = cfg

    def access(self, resp, req, environ, request_time):  # noqa # type: ignore
        """不使用此处记录 access 日志."""
