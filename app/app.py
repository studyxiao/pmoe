from flask import Flask

from app.core.log import Logger
from config import config

app = Flask(__name__)

Logger(app)
app.config.from_object(config)


@app.get("/")
def index() -> str:
    return "Hello World!"
