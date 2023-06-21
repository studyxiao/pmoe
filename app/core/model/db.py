from contextvars import ContextVar
from typing import cast

from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from werkzeug.local import LocalProxy

ctx_session: ContextVar[Session] = ContextVar("session")


class DB:
    def __init__(self, app: Flask | None = None) -> None:
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        self.app = app
        self.config(app)
        app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)

        app.before_request(self.before_request)
        app.teardown_request(self.teardown_request)
        db_url = app.config.get("DB_URL")
        if db_url is None:
            raise ValueError("DB_URL must be set")
        connect_args = {"check_same_thread": False} if "sqlite" in db_url else {}
        self.engine = create_engine(
            url=db_url,  # type: ignore[reportUnknownArgumentType]
            connect_args=connect_args,
            pool_size=app.config.get("DB_POOL_SIZE"),
            pool_recycle=7200,
            echo=app.config.get("DB_ECHO"),
        )
        self.Session = sessionmaker(self.engine)
        app.extensions["sqlalchemy"] = self

    def config(self, app: Flask) -> None:
        app.config.setdefault("DB_URL", "sqlite:///:memory:")
        app.config.setdefault("DB_POOL_SIZE", 10)
        app.config.setdefault("DB_ECHO", False)

    def connect(self) -> "Session":
        """生成新的 session."""
        # session 并不代表连接 只有 execute 时才会真正连接数据库
        # session 可以看作是本地缓存
        return self.Session()

    def teardown_request(self, exception: BaseException | None) -> None:
        try:
            session = ctx_session.get()
            session.close()
            ctx_session.reset(self.token)
        except LookupError:
            pass

    def before_request(self) -> None:
        # 每次 request 创建新的 session 确保事务正确
        self.token = ctx_session.set(self.connect())


db = DB()
session = cast(Session, LocalProxy(ctx_session))
