from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import Any, Literal, NamedTuple, Protocol, Self, TypedDict, TypeVar

R = TypeVar("R")

STORAGE_NAME = Literal["local", "redis"]


class Serializer(Protocol):
    def dumps(self, obj: Any) -> bytes:
        raise NotImplementedError()

    def loads(self, blob: bytes) -> Any:
        raise NotImplementedError()


class CachedData(NamedTuple):
    data: Any
    expire: datetime | None = None


class Storage(Protocol):
    def get(self, key: str) -> bytes | None:
        ...

    def get_all(self, keys: Sequence[str]) -> list[bytes | None]:
        ...

    def set(
        self,
        key: str,
        value: bytes,
        ttl: timedelta | None,
    ) -> None:
        ...

    def set_many(self, mapping: dict[str, bytes], ttl: timedelta | None) -> None:
        ...

    def remove(self, key: str) -> None:
        ...

    def get_name(self) -> str:
        ...


class Cache(TypedDict):
    storage: STORAGE_NAME
    ttl: timedelta | None


T_cache = Cache | STORAGE_NAME


class Node(Protocol[R]):
    _full_key: str | None
    storages: list[Cache | STORAGE_NAME]

    def key(self) -> str:
        ...

    def full_key(self) -> str:
        ...

    def load(self) -> R:
        ...

    @classmethod
    def load_all(cls, nodes: Sequence[Self]) -> list[R]:
        ...
