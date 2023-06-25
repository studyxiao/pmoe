from datetime import timedelta

from celery import shared_task

from sms.app import SMS


@shared_task(
    name="sms:send_sms",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
)
def send_sms(mobile: str, code: str, expire: timedelta) -> None:
    SMS.send(mobile, code, expire)
