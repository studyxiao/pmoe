"""基于 structlog 的日志收集一揽子方案.

该模块旨在提供一个基于 Structlog 的日志包装器来产生更好的日志记录体验,
它可以将 web 请求期间捕获的所有信息整合到单个日志记录中。
模块中的 Logger 类具有两种模式:
- 开发模式: Log 输出到 stdout。
- 生产模式: Log 输出到 文件(可以 JSON格式), 在生成环境中使用。

使用方法:
应尽可能早的设置,比如启动文件或 gunicorn 的配置文件中
from app.core.log.config import configure_structlog

configure_structlog(is_production=False, log_level="DEBUG")
"""
import logging

import structlog

from .handler import LinRotatingFileHandler

# 无论开发还是生产, 标准 logging 还是 structlog 都需要的 Processors
stdlib_and_struct_processors: list[structlog.typing.Processor] = [
    # 添加上下文变量到 event_dict 最好放在第一位
    structlog.contextvars.merge_contextvars,
    structlog.stdlib.add_logger_name,
    structlog.stdlib.add_log_level,
    # 支持原生 %-style 不加也没报错 具体用在什么情形还没研究
    structlog.stdlib.PositionalArgumentsFormatter(),
    # 将 event_dict 转换成 extra 字典并再添加到 event_dict 中
    structlog.stdlib.ExtraAdder(),
    structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S"),
    structlog.processors.StackInfoRenderer(),
    structlog.processors.UnicodeDecoder(),
]


def configure_structlog(
    log_level: str = "INFO",
    is_production: bool = True,
    log_dir: str = "logs",
    max_bytes: int = 1024 * 1024 * 100,
) -> None:
    processors = stdlib_and_struct_processors
    if is_production:
        # 将 异常堆栈 格式化
        processors.append(structlog.processors.format_exc_info)

        renderer = structlog.dev.ConsoleRenderer(colors=False)
        # 还可以使用 json
        # >>> self.renderer = structlog.processors.JSONRenderer(serializer=json.dumps)
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    init_structlog(processors)
    init_stdliblog(
        processors,
        renderer,
        is_production,
        log_level,
        log_dir,
        max_bytes,
    )


def init_structlog(processors: list[structlog.typing.Processor]) -> None:
    """设置全局 structlog 配置."""
    structlog.configure(
        processors=[
            *processors,
            # 因为需要使用 ProcessorFormatter, 所以最后一个必须是这个
            # ProcessorFormatter 内部的 chain 最后一个必须是 renderer
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def init_stdliblog(
    processors: list[structlog.typing.Processor],
    renderer: structlog.typing.Processor,
    is_production: bool = False,
    log_level: str = "INFO",
    log_dir: str = "logs",
    max_bytes: int = 1024 * 1024 * 100,
) -> None:
    """设置标准库 root logger."""
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=processors,
        processors=[
            # 去除 event_dict 中的 _record 和 _from
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
    )
    root = logging.getLogger()
    if is_production:
        file_handler = LinRotatingFileHandler(log_dir=log_dir, max_bytes=max_bytes)
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
    else:
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        root.addHandler(handler)

    root.setLevel(log_level)
