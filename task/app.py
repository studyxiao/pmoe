from celery import Celery
from celery.app.task import Task

from config import celery_config

# 为 celery 添加 type hints
Task.__class_getitem__ = classmethod(lambda cls, *args, **kwargs: cls)  # type: ignore[attr-defined]


app = Celery(__name__)
app.config_from_object(celery_config)
# 设置默认 app 可以在其他模块中使用 shared_task 装饰器
app.set_default()

import task.example  # noqa # type: ignore[import]
