from datetime import timedelta
from threading import Lock
from typing import TYPE_CHECKING, Any, ClassVar, TypeVar

from app.core.cache import serializer

if TYPE_CHECKING:
    from .typing import STORAGE_NAME, Node, Serializer, Storage

T = TypeVar("T")


class _Locker:
    lock: Lock = Lock()
    result: Any = None


test_set = set()


class Manager:
    serializer: "Serializer" = serializer.JSONSerializer()
    # TODO 应区分本地和远程后端,本地后端不需要序列化和加锁操作
    all_storages: ClassVar[dict[str, "Storage"]] = {}
    _awaiting: ClassVar[dict[str, _Locker]] = {}  #  Thundering Herd Protection

    def register_storage(self, name: "STORAGE_NAME", storage: "Storage") -> None:
        self.all_storages[name] = storage

    def get(self, node: "Node[T]") -> T | None:
        result: T | None = None
        miss_storages: list["Storage"] = []
        ttl: dict[str, timedelta] = {}
        defaul_ttl = timedelta(seconds=120)
        _locker = self._awaiting.setdefault(node.full_key(), _Locker())
        with _locker.lock:
            if _locker.result is None:
                for storage in node.storages:
                    _storage: Storage | None = None
                    if isinstance(storage, str) and storage in self.all_storages:
                        _storage = self.all_storages[storage]
                        ttl[storage] = defaul_ttl
                    elif isinstance(storage, dict) and storage.get("storage") in self.all_storages:
                        _storage = self.all_storages[storage["storage"]]
                        ttl[storage["storage"]] = storage.get("ttl") or defaul_ttl
                    if _storage is None:
                        continue
                    try:
                        ser_result = _storage.get(node.full_key())
                    except Exception as e:
                        self._awaiting.pop(node.full_key(), None)
                        raise e
                    if ser_result is None:
                        # 该存储后端没有缓存,记录在miss_storages中
                        miss_storages.append(_storage)
                    else:
                        result = self.serializer.loads(ser_result)
                        if result is not None:
                            # 该存储后端有缓存,记录在result中
                            break

                if result is None:
                    # 没有缓存,从数据库中加载

                    result = node.load()
                _locker.result = result
                for storage in miss_storages:
                    # 填充缓存
                    storage.set(node.full_key(), self.serializer.dumps(result), ttl.get(storage.get_name()))
                # TODO pop 后就会解锁,再有请求就会再次加载,这是否合理?
                self._awaiting.pop(node.full_key(), None)
            else:
                test_set.add(id(_locker))
                result = _locker.result
        return result

    def set(self, node: "Node[T]", value: T, storage_name: str) -> None:
        storage = self.all_storages[storage_name]
        ttl = self.get_storage_ttl(node, storage_name)
        storage.set(node.full_key(), self.serializer.dumps(value), ttl)

    def remove(self, node: "Node[Any]", storage_name: str) -> None:
        storage = self.all_storages[storage_name]
        storage.remove(node.full_key())

    def get_ttl_from_node(self, node: "Node[Any]") -> dict[str, timedelta]:
        ttl: dict[str, timedelta] = {}
        defaul_ttl = timedelta(seconds=120)
        for storage in node.storages:
            _storage = None
            if isinstance(storage, str) and storage in self.all_storages:
                _storage = self.all_storages[storage]
                ttl[storage] = defaul_ttl
            elif isinstance(storage, dict) and storage.get("storage") in self.all_storages:
                _storage = self.all_storages[storage["storage"]]
                ttl[storage["storage"]] = storage.get("ttl") or defaul_ttl
            if _storage is None:
                continue
        return ttl

    def get_storage_ttl(self, node: "Node[Any]", storage_name: str) -> timedelta:
        ttl = self.get_ttl_from_node(node)
        return ttl.get(storage_name) or timedelta(seconds=120)
