import re
from typing import Any

from pydantic import BaseModel, Field


class PageSchema(BaseModel):
    """客户端传来的分页请求."""

    page: int = Field(0, ge=0, le=100, description="0 <= page <= 100")
    count: int = Field(10, ge=1, le=50, description="1 <= count <= 50")


class ResultPageSchema(BaseModel):
    """服务器返回的分页数据."""

    page: int
    count: int
    total: int
    items: list[Any]


# 手机号: 11位大陆手机号, 包括虚拟运营商
mobile_pattern = r"^(13[0-9]|14[014-9]|15[0-35-9]|16[2567]|17[0-8]|18[0-9]|19[^4])\d{8}$"
# 用户昵称: 4-20位, 只能是字母、汉字和数字, 且不能以数字开头
username_pattern = r"^[a-zA-z\u4e00-\u9fa5][0-9a-zA-z\u4e00-\u9fa5]{3,19}"
# 密码: 6-20位, 包含大小写字母、数字和特殊符号
password_pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@!.,*?&%])[a-zA-Z0-9@!.,*?&%]{6,20}$"  # noqa:S105

# 电子邮箱
email_pattern = r"^[A-Za-z0-9\u4e00-\u9fa5]+@[a-zA-Z0-9_-]+(\.[a-zA-Z0-9_-]+)+$"


def validate_mobile(mobile: str) -> str:
    """验证手机号格式."""
    if not re.match(mobile_pattern, mobile):
        raise ValueError("手机号码有误")
    return mobile


def validate_password(password: str) -> str:
    """验证密码格式."""
    if not re.match(password_pattern, password):
        raise ValueError("密码6-20位, 包含大小写字母、数字和特殊符号")
    return password


def validate_username(username: str) -> str:
    """验证用户名格式."""
    if not re.match(username_pattern, username):
        raise ValueError("4-20位, 只能是字母、汉字和数字, 且不能以数字开头")
    return username
