from collections.abc import Sequence
from datetime import timedelta
from pathlib import Path
from typing import Any

from kombu import Queue
from pydantic import BaseSettings, Field


def route_task(name: str, args: Any, kwargs: Any, options: Any, task: Any = None, **kw: Any) -> dict[str, str]:
    """Celery 任务路由. 当任务名中包含 ":" 时,将任务路由到指定队列.

    例如:
    >>> @shared_task(name="email:send")
    >>> def send_email():
    >>>     pass
    >>> send_email.delay()
    >>> # 任务将被路由到 email 队列
    """
    if ":" in name:
        queue, _ = name.split(":")
        return {"queue": queue}
    return {"queue": "default"}


class TaskConfig(BaseSettings):
    """Celery 配置.

    详细配置参考: https://docs.celeryq.dev/en/stable/userguide/configuration.html
    """

    #### 全局
    timezone: str = Field(default="Asia/Shanghai", env="TZ")
    enable_utc: bool = True

    #### task
    # 默认 json
    task_serializer: str = "json"
    # 15分钟
    task_soft_time_limit: int = 60 * 15
    # 任务超时时间比软超时时间多30秒
    task_time_limit: int = task_soft_time_limit + 30
    # 任务在执行完成后(已存储或处理结果)再进行确认,默认行为是在任务发送后立即确认
    task_acks_late: bool = True
    # 如果 worker 进程丢失,拒绝执行任务,默认是 True
    task_reject_on_worker_lost: bool = True
    # 指定默认队列名称,默认是 "celery"
    task_default_queue: str = "default"
    # task_queues 没有指定的队列将不会创建
    task_create_missing_queues: bool = False
    task_queues: Sequence[Queue] = (
        Queue("default"),
        Queue("email"),
        Queue("sms"),
        Queue("high_priority"),
        Queue("low_priority"),
    )
    task_routes: Sequence[Any] = (route_task,)

    #### broker
    broker_url: str = Field(default="redis://localhost:6379/0", env="CELERY_BROKER_URL")
    # 消息代理的可见性超时时间为15分钟,超时后任务会被重新分配
    # 耗时任务不能超过15分钟,延迟任务也不能超过15分钟
    broker_transport_options: dict[str, Any] = Field(
        default_factory=lambda: {
            "visibility_timeout": 60 * 15,
        }
    )
    # gevent 下设置 broker_pool 为 None ,禁止为每个 worker 创建连接
    broker_pool_limit: int = 0
    broker_connection_retry_on_startup: bool = True

    #### worker
    # worker 接受的内容类型
    accept_content: list[str] = Field(default_factory=lambda: ["json"])
    # worker 进程预取任务的数量(默认是4)
    worker_prefetch_multiplier: int = 1
    #  worker 执行最大任务数,之后替换为新的进程
    worker_max_tasks_per_child: int = 500
    # 内存使用超过内存量(KB)后,替换为新的 worke
    worker_max_memory_per_child: int = 5000

    #### result
    result_serializer: str = "json"
    result_backend: str = Field(default="redis://localhost:6379/0", env="CELERY_RESULT_BACKEND")
    # 任务结果保存3天
    result_expires: timedelta = timedelta(days=3)

    class Config(BaseSettings.Config):
        env_file: str = ".env"


class BaseConfig(BaseSettings):
    BASE_DIR: Path | str = Path(__file__).parent.parent

    SECRET_KEY: str = "123456"

    # JWT
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=2)
    JWT_TOKEN_URL: str = "/api/v1/auth/login"
    JWT_ALGORITHM: str = "HS256"

    # DB
    DB_URL: str
    DB_POOL_SIZE: int = 10
    DB_ECHO: bool = False

    # redis
    REDIS_PASSWORD: str
    REDIS_URL: str

    # log
    LOG_LEVEL: str = "INFO"

    # secret
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRES_DELTA: timedelta = timedelta(hours=2)

    # 腾讯 sms
    SMS_SECRET_ID: str
    SMS_SECRET_KEY: str
    SMS_APP_ID: str
    SMS_SIGN_NAME: str
    SMS_TEMPLATE: str

    # 腾讯 cos 设置
    COS_SECRET_ID: str
    COS_SECRET_KEY: str
    COS_BUCKET: str
    COS_REGION: str

    class Config(BaseSettings.Config):
        env_file: str = ".env"


# https://github.com/pydantic/pydantic/issues/3753#issuecomment-1087417884
config: BaseConfig = BaseConfig.parse_obj({})
celery_config: TaskConfig = TaskConfig.parse_obj({})
