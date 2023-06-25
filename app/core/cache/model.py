from collections.abc import Sequence
from typing import TYPE_CHECKING, ClassVar, Generic, Self, TypeVar, Union

if TYPE_CHECKING:
    from .typing import STORAGE_NAME, Cache
sentinel = object()

T = TypeVar("T")


class Node(Generic[T]):
    _full_key: str | None = None
    _prefix: str | None = None
    storages: ClassVar[list[Union["Cache", "STORAGE_NAME"]]]

    def key(self) -> str:
        raise NotImplementedError()

    def full_key(self) -> str:
        if self._prefix is None:
            self._prefix = self.__class__.__name__.lower()
        if self._full_key is None:
            self._full_key = f"{self._prefix}:{self.key()}"
        return self._full_key

    def load(self) -> T | None:
        raise NotImplementedError()

    @classmethod
    def load_all(cls, nodes: Sequence[Self]) -> list[T | None]:
        results: list[T | None] = []
        for node in nodes:
            results.append(node.load())
        return results
