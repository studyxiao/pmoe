from datetime import timedelta

# 听听  from celery import shared_task
from sms.app import SMS, SMSServiceError
from task.app import app


@app.task(
    name="sms:send_sms",
    autoretry_for=(SMSServiceError,),
    retry_backoff=True,
    retry_jitter=True,
    max_retries=5,
)
def send_sms(mobile: str, code: str, expire: int) -> None:
    _expire = timedelta(seconds=expire)
    SMS.send(mobile, code, _expire)
