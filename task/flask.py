from typing import TYPE_CHECKING, Any

from celery import Celery, Task  # type: ignore

from config import TaskConfig

if TYPE_CHECKING:
    from flask import Flask

    Task.__class_getitem__ = classmethod(lambda cls, *args, **kwargs: cls)  # type: ignore[attr-defined]


def celery_init_app(app: "Flask") -> Celery:
    class FlaskTask(Task[..., Any]):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(TaskConfig)
    celery_app.set_default()
    app.extensions["celery"] = celery_app  # type: ignore[assignment]
    return celery_app
