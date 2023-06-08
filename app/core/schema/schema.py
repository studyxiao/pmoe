from collections.abc import Callable
from functools import wraps
from inspect import get_annotations
from typing import ParamSpec, TypeVar

from flask import request
from pydantic import BaseModel, ValidationError

from app.core.exception import ParameterException

P = ParamSpec("P")
R = TypeVar("R")
S = TypeVar("S", bound=BaseModel)


def validate(func: Callable[P, R]) -> Callable[P, R]:
    """参数校验装饰器.

    >>> @validate
        def index(path_param: int, query: QuerySchema, body: BodySchema) -> Response:
            pass.
    """

    @wraps(func)
    def wrapper_validate(*args: P.args, **kwargs: P.kwargs) -> R:
        # 解析
        annotations = get_annotations(func)

        query_schema = annotations.get("query")
        body_schema = annotations.get("body")
        # TODO 暂未实现 annotations.get("form")

        if query_schema is not None:
            try:
                data = query_schema.validate(request.args.to_dict())
                kwargs["query"] = data
            except ValidationError as e:
                raise ParameterException(errors=e.errors()) from None
        if body_schema is not None:
            try:
                data = body_schema.validate(request.get_json())
                kwargs["body"] = data
            except ValidationError as e:
                raise ParameterException(errors=e.errors()) from None
        if request.view_args is not None:
            for key, value in request.view_args.items():
                path_param_schema = annotations.get(key)
                if path_param_schema is not None:
                    try:
                        if issubclass(path_param_schema, BaseModel):
                            data = path_param_schema.validate(value)
                        elif path_param_schema is int:
                            data = int(value)
                        else:
                            data = value
                        kwargs[key] = data
                    except ValidationError as e:
                        raise ParameterException(errors=e.errors()) from None
                    except ValueError as e:
                        raise ParameterException(message=str(e)) from None
                    request.view_args[key] = data
        return func(*args, **kwargs)

    return wrapper_validate
