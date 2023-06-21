import base64
import hashlib
import hmac
import json
import random
import time
from typing import Any
from urllib.parse import quote, urlencode

import requests

from config import config


class COS:
    """申请腾讯 COS 临时 token.

    修改自: https://github.com/tencentyun/qcloud-cos-sts-sdk/blob/master/python/README.md
    """

    url: str = "https://sts.tencentcloudapi.com/"
    domain: str = "sts.tencentcloudapi.com"  # 域名 默认为 sts.tencentcloudapi.com
    duration_seconds: int = 1800  # 临时密钥有效时长(秒) 默认 1800 半小时, 最大 7200 两小时
    secret_id: str
    secret_key: str  # 固定密钥
    bucket: str  # 存储桶名称: bucketName-appid
    region: str  # 存储桶所在地区: ap-beijing
    allow_prefix: list[str]  # 有权访问的资源前缀: ["a/*", "a.jpg", "*"]
    # 密钥的权限列表 其他权限列表请看 https://cloud.tencent.com/document/product/436/31923
    allow_actions: list[str]
    resource: list[str]

    def __init__(
        self,
        *,
        secret_id: str,
        secret_key: str,
        bucket: str,
        region: str,
        url: str | None = None,
        domain: str | None = None,
        duration_seconds: int | None = None,
        allow_prefix: list[str] | None = None,
        allow_actions: list[str] | None = None,
    ) -> None:
        self.secret_id = secret_id
        self.secret_key = secret_key
        self.bucket = bucket
        self.region = region
        if url is not None:
            self.url = url
        if domain is not None:
            self.domain = domain
        if duration_seconds is not None:
            self.duration_seconds = duration_seconds
        self.allow_prefix = allow_prefix or ["*"]
        self.allow_actions = allow_actions or [
            # 简单上传
            "name/cos:PutObject",
            "name/cos:PostObject",
            # 分片上传
            "name/cos:InitiateMultipartUpload",
            "name/cos:ListMultipartUploads",
            "name/cos:ListParts",
            "name/cos:UploadPart",
            "name/cos:CompleteMultipartUpload",
        ]
        split_index = self.bucket.rfind("-")
        if split_index < 0:
            raise ValueError("Error: bucket is invalid: " + self.bucket)
        appid = str(self.bucket[(split_index + 1) :]).strip()
        self.resource = []
        for prefix in self.allow_prefix:
            _prefix = f"/{prefix}" if not prefix.startswith("/") else prefix
            self.resource.append(f"qcs::cos:{self.region}:uid/{appid}:{self.bucket}{_prefix}")

        policy = {
            "version": "2.0",
            "statement": [
                {
                    "action": self.allow_actions,
                    "effect": "allow",
                    "resource": self.resource,
                }
            ],
        }
        self.policy_encode = quote(json.dumps(policy))

    def get_credential(self) -> dict[str, str]:
        data: dict[str, Any] = {
            "SecretId": self.secret_id,
            "Timestamp": int(time.time()),
            "Nonce": random.randint(100000, 200000),  # noqa: S311
            "Action": "GetFederationToken",
            "Version": "2018-08-13",
            "DurationSeconds": self.duration_seconds,
            "Name": "cos-sts-python",
            "Policy": self.policy_encode,
            "Region": self.region,
        }
        data["Signature"] = self.__encrypt("POST", self.domain, data)
        result_json = None
        try:
            response = requests.post(self.url, data=data, timeout=15)
            result_json = response.json()
            if isinstance(result_json["Response"], dict):
                result_json = result_json["Response"]
            return result_json  # type: ignore
        except Exception as e:  # noqa
            result = "error: "
            if result_json is not None:
                result = str(result_json)
            raise Exception(result, e) from None

    def __encrypt(self, method: str, domain: str, key_values: dict[str, Any]) -> bytes:
        _key_values = sorted(key_values.items(), key=lambda d: d[0])
        _source = method + domain + "/?" + urlencode(_key_values, safe="/%")
        key = bytes(self.secret_key, encoding="utf-8")
        source = bytes(_source, encoding="utf-8")
        sign = hmac.new(key, source, hashlib.sha1).digest()
        return base64.b64encode(sign).rstrip()


# 单例模式
cos: COS = COS(
    secret_id=config.COS_SECRET_ID,
    secret_key=config.COS_SECRET_KEY,
    bucket=config.COS_BUCKET,
    region=config.COS_REGION,
)


if __name__ == "__main__":
    import os

    import dotenv

    dotenv.load_dotenv()
    cos = COS(
        secret_id=os.getenv("COS_SECRET_ID", ""),
        secret_key=os.getenv("COS_SECRET_KEY", ""),
        bucket=os.getenv("COS_BUCKET", ""),
        region=os.getenv("COS_REGION", ""),
    )
    print("result: ", cos.get_credential())  # noqa
