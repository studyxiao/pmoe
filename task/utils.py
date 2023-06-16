# type: ignore
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, ClassVar, ParamSpec, TypeVar

import redis
from celery import shared_task
from celery.app.task import Task
from celery.utils.time import get_exponential_backoff_interval

from task.lock import Lock, RedisLockError

P = ParamSpec("P")
R = TypeVar("R")


@dataclass(kw_only=True)
class custom_celery_task:  # noqa
    """Celery task decorator with exponential backoff retry mechanism.

    Example:
        @custom_celery_task()
        def my_task():
            pass
    https://github.com/testdrivenio/flask-celery-project/blob/master/project/celery_utils.py#LL35C13-L35C13
    """

    # 不会重试的异常
    EXCEPTION_BLOCK_LIST: ClassVar[tuple[type[Exception]]] = (
        IndexError,
        KeyError,
        TypeError,
        UnicodeDecodeError,
        ValueError,
    )

    name: str  # 强制使用 name
    serializer: str | None = None
    bind: bool = False
    autoretry_for: tuple[type[BaseException], ...] | None = field(default_factory=tuple)
    max_retries: int | None = None
    default_retry_delay: int = 5
    acks_late: bool = True
    ignore_result: bool = True
    soft_time_limit: int | None = None
    time_limit: int | None = None
    base: Task | None = None
    retry_kwargs: dict[str, Any] = field(default_factory=dict)
    retry_backoff: bool | int = False
    retry_backoff_max: int = 600
    retry_jitter: bool = True
    typing: bool | None = None
    rate_limit: str | None = None
    trail: bool = True
    send_events: bool = True
    store_errors_even_if_ignored: bool | None = None
    track_started: bool | None = None
    acks_on_failure_or_timeout: bool | None = None
    reject_on_worker_lost: bool | None = None
    throws: tuple[type[Exception], ...] = field(default_factory=tuple)
    expires: float | datetime | None = None
    priority: int | None = None
    resultrepr_maxsize: int = 1024
    request_stack: Any = None
    abstract: bool = True
    queue: str | None = None

    def __post_init__(self) -> None:
        self.task_args = asdict(self)

    def __call__(self, func: Callable[..., Any]) -> Any:
        @wraps(func)
        def wrapper_func(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except self.EXCEPTION_BLOCK_LIST:
                # do not retry for those exceptions
                raise
            except Exception as e:  # noqa
                # here we add Exponential Backoff just like Celery
                countdown = self._get_retry_countdown(task_func)
                raise task_func.retry(exc=e, countdown=countdown) from None

        task_func = shared_task(**self.task_args)(wrapper_func)
        return task_func  # noqa: R504

    def _get_retry_countdown(self, task_func: Callable[..., Any]) -> Any:
        retry_backoff = int(self.task_kwargs.get("retry_backoff", True))
        retry_backoff_max = int(self.task_kwargs.get("retry_backoff_max", 600))
        retry_jitter = self.task_kwargs.get("retry_jitter", True)

        return get_exponential_backoff_interval(
            factor=retry_backoff, retries=task_func.request.retries, maximum=retry_backoff_max, full_jitter=retry_jitter
        )


redis_client = redis.Redis.from_url("redis://:123456@localhost:6379/0")


def single(func: Callable[P, R]) -> Callable[P, R | None]:
    """Celery task 单例装饰器.

    用于防止同一个任务被多个 worker 同时执行.
    """

    @wraps(func)
    def wrapper_single(*args: P.args, **kwargs: P.kwargs) -> R | None:
        self = args[0]
        if isinstance(self, Task):
            lock = None
            try:
                lock = Lock(
                    key=self.request.id,
                    expiration=timedelta(seconds=60),
                    redis_client=redis_client,
                )
                with lock:
                    result = func(*args, **kwargs)
            except RedisLockError:
                # 加锁失败,说明有其他 worker 正在处理同一个任务
                # 60 秒后再次尝试执行任务
                self.apply_async(
                    *args,
                    kwargs={**kwargs},
                    countdown=60,
                )
                return None
            except Exception as e:
                if lock is not None:
                    lock.release()
                raise e
            return result
        return func(*args, **kwargs)

    return wrapper_single
