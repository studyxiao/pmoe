from datetime import timedelta
from pathlib import Path

from pydantic import BaseSettings


class BaseConfig(BaseSettings):
    BASE_DIR: Path | str = Path(__file__).parent.parent

    SECRET_KEY: str = "123456"

    # JWT
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=2)
    JWT_TOKEN_URL: str = "/api/v1/auth/login"
    JWT_ALGORITHM: str = "HS256"

    # DB
    DB_URL: str
    DB_POOL_SIZE: int = 10
    DB_ECHO: bool = False

    # redis
    REDIS_PASSWORD: str
    REDIS_URL: str

    # qcloud 腾讯 cos 设置
    COS_SECRET_ID: str
    COS_SECRET_KEY: str
    COS_BUCKET: str
    COS_REGION: str

    # 腾讯 sms
    SMS_SECRET_ID: str
    SMS_SECRET_KEY: str
    SMS_APP_ID: str
    SMS_SIGN_NAME: str
    SMS_TEMPLATE: str

    # log
    LOG_LEVEL: str = "INFO"

    # secret
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRES_DELTA: timedelta = timedelta(hours=2)

    # redis

    class Config:
        env_file: str = ".env"


# https://github.com/pydantic/pydantic/issues/3753#issuecomment-1087417884
config: BaseConfig = BaseConfig.parse_obj({})
