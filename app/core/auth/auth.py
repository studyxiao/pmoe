"""JWT 认证.

环境变量:
- JWT_SECRET_KEY: 密钥[必须],或设置 SECRET_KEY
- JWT_ALGORITHM: 算法
- JWT_ACCESS_TOKEN_EXPIRES: 过期时间
- JWT_TOKEN_URL: 获取 token 的路由.

使用:
```python
from app.core.auth import Auth, current_user
from app.user.model import User

# 注册
auth = Auth(app)

# 当前用户(view 函数中使用)
user = current_user.get()
```
"""
import datetime
from contextvars import ContextVar
from dataclasses import asdict, dataclass
from datetime import timedelta
from typing import Any

import jwt
from flask import Flask, Response, request

from app.core.exception import ParameterException, Unauthorized
from app.core.schema import validate

from .model import User
from .schema import LoginScheme

current_user: ContextVar[User | None] = ContextVar("user")
""" 当前用户
>>> user = current_user.get()
还可以使用 proxy 封装以便直接使用 current_user
"""


@dataclass
class JWTPayload:
    sub: dict[str, str] | None = None
    exp: int | None = None
    iat: int | None = None


def encode_token(
    data: dict[str, Any],
    secret_key: str,
    expires: timedelta | None = None,
    algorithm: str | None = None,
) -> str:
    expires = expires or timedelta(minutes=120)
    algorithm = algorithm or "HS256"
    now = datetime.datetime.now(tz=datetime.UTC)
    iat = int(now.timestamp())
    exp = int((now + expires).timestamp())
    payload = JWTPayload(
        sub=data,
        iat=iat,
        exp=exp,
    )
    return jwt.encode(  # type: ignore 严格模式下参数部分类型未知错误
        payload=asdict(payload),
        key=secret_key,
        algorithm=algorithm,
    )


def decode_token(
    token: str,
    secret_key: str,
    algorithm: str | None = "HS256",
) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            jwt=token,
            key=secret_key,
            algorithms=[algorithm] if algorithm else None,
        )
        return payload.get("sub")
    except jwt.ExpiredSignatureError:
        # 过期
        raise Unauthorized(message="Token has expired") from None
    except jwt.InvalidTokenError:
        # 无效
        raise Unauthorized(message="Token is invalid") from None


class Auth:
    user: type[User] = User

    def __init__(
        self,
        app: Flask | None = None,
    ) -> None:
        if app:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        self.app = app
        self.config(app)
        # 注册获取 token (登录)的路由
        app.add_url_rule(
            self.app.config.get("JWT_TOKEN_URL", "/token"), view_func=validate(self.login), methods=["POST"]
        )
        app.before_request(self.before_request)
        app.after_request(self.after_request)

    def config(self, app: Flask) -> None:
        """需要配置的参数."""
        app.config.setdefault("JWT_TOKEN_URL", "/token")
        app.config.setdefault("JWT_SECRET_KEY", app.config.get("SECRET_KEY", None))
        app.config.setdefault("JWT_ALGORITHM", "HS256")
        app.config.setdefault("JWT_ACCESS_TOKEN_EXPIRES", datetime.timedelta(minutes=120))
        if app.config.get("JWT_SECRET_KEY") is None:
            raise ValueError("JWT_SECRET_KEY must be set")

    def before_request(self) -> None:
        user = self.identify(silent=True)
        if user is not None:
            self.current_user_token = current_user.set(user)

    def after_request(self, response: Response) -> Response:
        if hasattr(self, "current_user_token") and self.current_user_token:
            current_user.reset(self.current_user_token)
        return response

    @staticmethod
    def get_bearer_token(silent: bool = False) -> str | None:
        """Extracts the token from the authorization header."""
        authorization = request.headers.get("Authorization", "")
        if not authorization or not authorization.startswith("Bearer "):
            if silent:
                return None
            raise Unauthorized()
        return authorization[7:]

    def identify(self, silent: bool = False) -> User | None:
        """Returns the current user."""
        token_from_header = self.get_bearer_token(silent)
        if token_from_header is None:
            return None
        data = decode_token(
            token=token_from_header,
            secret_key=self.app.config.get("JWT_SECRET_KEY"),  # type: ignore
            algorithm=self.app.config.get("JWT_ALGORITHM"),
        )
        user = self.user.get_by_id(data["user_id"])
        if user is None:
            if silent:
                return None
            raise ParameterException(message="Invalid user")
        return user

    def validate_credential(self, username: str, password: str, scope: str = "") -> dict[str, str]:
        """Authenticates the user and returns an access token."""
        scopes = scope.split()  # type: ignore # noqa
        user = self.user.validate_credential(username, password)
        if user is None:
            raise ParameterException(message="Invalid credentials")
        data = {"user_id": user.id}
        if self.app.config.get("JWT_SECRET_KEY") is None:
            raise ValueError("JWT_SECRET_KEY must be set")
        token = encode_token(
            data,
            self.app.config.get("JWT_SECRET_KEY"),  # type: ignore
            self.app.config.get("JWT_ACCESS_TOKEN_EXPIRES"),
            self.app.config.get("JWT_ALGORITHM"),
        )
        return {"access_token": token}

    def login(self, body: LoginScheme) -> dict[str, str]:
        return self.validate_credential(body.username, body.password)
