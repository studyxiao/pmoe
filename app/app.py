from flask import Flask

from app.core.log import Logger
from config import config

app = Flask(__name__)

Logger(app)
app.config.from_object(config)


@app.get("/")
def index() -> str:
    from task.example import send_email, send_sms, send_sms2

    for _ in range(10):
        send_email.apply_async(args=("hello",))
        send_sms.apply_async(args=("hello",))
        send_sms2.apply_async(args=("hello",))
    return "Hello World!"
