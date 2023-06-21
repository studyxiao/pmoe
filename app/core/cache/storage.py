from collections.abc import Sequence
from datetime import timedelta
from typing import TYPE_CHECKING, Any, Union

from theine.thenie import Cache

if TYPE_CHECKING:
    from redis import Redis, RedisCluster

    BaseRedis = Redis[bytes]
    BaseRedisCluster = RedisCluster[bytes]


class BaseStorage:
    def get(self, key: str) -> bytes | None:
        raise NotImplementedError()

    def get_all(self, keys: Sequence[str]) -> list[bytes | None]:
        raise NotImplementedError()

    def set(
        self,
        key: str,
        value: bytes,
        ttl: timedelta | None,
    ) -> None:
        raise NotImplementedError()

    def set_many(self, mapping: dict[str, Any], ttl: timedelta | None) -> None:
        raise NotImplementedError()

    def remove(self, key: str) -> None:
        raise NotImplementedError()

    def get_name(self) -> str:
        raise NotImplementedError()


class LocalStorage(BaseStorage):
    def __init__(self, policy: str = "tlfu", size: int = 1000) -> None:
        self.client = Cache(policy, size)

    def get(self, key: str) -> bytes | None:
        return self.client.get(key, None)

    def get_all(self, keys: Sequence[str]) -> list[bytes | None]:
        if len(keys) == 0:
            return []
        results: list[Any] = []
        for key in keys:
            v = self.client.get(key, None)
            results.append(v)
        return results

    def remove(self, key: str) -> None:
        self.client.delete(key)

    def set(self, key: str, value: bytes, ttl: timedelta | None) -> None:
        self.client.set(key, value, ttl)

    def set_many(self, mapping: dict[str, bytes], ttl: timedelta | None) -> None:
        for key, value in mapping.items():
            self.client.set(key, value, ttl)

    def get_name(self) -> str:
        return "local"


class RedisStorage(BaseStorage):
    def __init__(self, client: Union["BaseRedis", "BaseRedisCluster"]) -> None:
        self.client = client

    def get(self, key: str) -> bytes | None:
        return self.client.get(key)

    def get_all(self, keys: Sequence[str]) -> list[bytes | None]:
        return self.client.mget(keys)

    def remove(self, key: str) -> None:
        self.client.delete(key)

    def set(self, key: str, value: bytes, ttl: timedelta | None) -> None:
        self.client.set(key, value, ex=ttl)

    def set_many(self, mapping: dict[str, bytes], ttl: timedelta | None) -> None:
        with self.client.pipeline() as pipe:
            for key, value in mapping.items():
                pipe.set(key, value, ex=ttl)
            pipe.execute()

    def get_name(self) -> str:
        return "redis"
