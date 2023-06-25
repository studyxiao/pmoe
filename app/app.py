from flask import Flask

from app.core.log import Logger
from app.core.model import db
from config import config

app = Flask(__name__)

# 配置项
app.config.from_object(config)

# 插件
Logger(app)
db.init_app(app)


# 路由
@app.get("/")
def index() -> str:
    return "Hello World!"
