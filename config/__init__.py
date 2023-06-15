from datetime import timedelta
from pathlib import Path

from pydantic import BaseSettings


class TaskConfig:
    """Celery 配置."""

    # 任务在执行完成后(已存储或处理结果)再进行确认
    task_acks_late = True
    # 如果 worker 进程丢失,拒绝执行任务
    task_reject_on_worker_lost = True
    # worker 进程预取任务的数量(默认是4)
    worker_prefetch_multiplier = 1
    # 消息代理的可见性超时时间为15分钟,超时后任务会被重新分配
    broker_transport_options = {"visibility_timeout": 900}

    task_default_queue = "default"
    task_serializer = "json"
    result_serializer = "json"
    # 任务结果保存3天
    result_expires = timedelta(days=3)
    # worker 接受的内容类型
    accept_content = ["json"]
    timezone = "Asia/Shanghai"
    enable_utc = True


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

    # redis

    class Config:
        env_file: str = ".env"


# https://github.com/pydantic/pydantic/issues/3753#issuecomment-1087417884
config: BaseConfig = BaseConfig.parse_obj({})
