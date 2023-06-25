"""异常处理模块.

- APIException: 重写 HTTPException, 使其返回 json 格式的异常信息.
    参数必须使用关键词参数,否则会报错,
    使用`raise APIException()` 或者 `raise APIException` 都可。
    - status_code: HTTP 状态码.
    - error_code: 自定义错误码.
    - message: 错误信息.
    - errors(可选): 错误信息列表.
- NotFound: 404 异常.

"""
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any

from flask import jsonify
from werkzeug.exceptions import HTTPException

if TYPE_CHECKING:
    from _typeshed.wsgi import StartResponse, WSGIEnvironment


class APIException(HTTPException):
    """重写 HTTPException, 使其返回 json 格式的异常信息.

    ```sh
    HTTP1.1 <status_code> code_message
    Content-Type: application/json

    {
        "code": <error_code>,
        "message": <message>,
        "errors"?: <errors>
    }
    ```
    """

    status_code: int = 500
    error_code: int = 9999
    message: str = "Service Error"
    errors: list[Any] | None = None

    def __init__(
        self,
        /,
        status_code: int | None = None,
        error_code: int | None = None,
        message: str | None = None,
        errors: list[Any] | None = None,
    ) -> None:
        if status_code is not None:
            self.status_code = status_code
        if error_code is not None:
            self.error_code = error_code
        if message is not None:
            self.message = message
        if errors is not None:
            self.errors = errors
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "code": self.error_code,
            "message": self.message,
        }
        if self.errors is not None:
            data["errors"] = self.errors
        return data

    def __call__(self, environ: "WSGIEnvironment", start_response: "StartResponse") -> Iterable[bytes]:
        response = jsonify(self.to_dict())
        response.status_code = self.status_code
        return response(environ, start_response)


class NotFound(APIException):
    status_code: int = 404
    message: str = "Not Found"
    error_code: int = 1004


class ParameterException(APIException):
    status_code: int = 400
    message: str = "Parameter Error"
    error_code: int = 1000


class Unauthorized(APIException):
    status_code: int = 401
    message: str = "Unauthorized"
    error_code: int = 1001


class Forbidden(APIException):
    status_code: int = 403
    message: str = "Forbidden"
    error_code: int = 1003


class ServerError(APIException):
    status_code: int = 500
    message: str = "Server Error"
    error_code: int = 9999
