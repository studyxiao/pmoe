from typing import TYPE_CHECKING

from celery import shared_task
from celery.utils.log import get_task_logger

from task.utils import custom_celery_task

if TYPE_CHECKING:
    from celery.app.task import Task

logger = get_task_logger(__name__)


@shared_task(bind=True, name="test_add")  # 默认是default 队列
def add(self: "Task[[int, int], int]", x: int, y: int) -> int:
    import time

    self.update_state(state="PROGRESS", meta={"progress": 0})
    time.sleep(x)
    return x + y


@shared_task(name="email:test_send_email")
def send_email(email: str) -> None:
    logger.info(f"send email to {email}")  # noqa
    # send email
    import time

    time.sleep(4)
    return


@shared_task(
    name="sms:test_send_sms",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
)
def send_sms(phone: str) -> None:
    import random

    if not random.choice([0, 1]):  # noqa: S311
        logger.error(f"send sms to {phone} failed, retrying...")  # noqa
        raise Exception()
    logger.info(f"send sms to {phone}")  # noqa
    # send sms
    import time

    time.sleep(4)
    return


@custom_celery_task(name="sms:test_send_sms2")
def send_sms2(phone: str) -> None:
    logger.info(f"send sms to {phone}")  # noqa
