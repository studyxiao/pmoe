from celery import Celery
from flask import Flask

app = Flask(__name__)

celery_app = Celery(__name__)


@app.get("/")
def index():
    return "Hello World!"
