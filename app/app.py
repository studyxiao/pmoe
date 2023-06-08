from celery import Celery
from flask import Flask

from config import config

app = Flask(__name__)

celery_app = Celery(__name__)

app.config.from_object(config)


@app.get("/")
def index() -> str:
    from app.core.exception import NotFound

    raise NotFound(message="Hello World!")
    return "Hello World!"
