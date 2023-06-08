from pydantic import BaseModel, validator

from app.core.schema import validate_username


class LoginScheme(BaseModel):
    username: str
    password: str
    _username = validator("username", allow_reuse=True)(validate_username)
