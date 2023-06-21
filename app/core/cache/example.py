"""cache 示例文件.

1. 全局初始化缓存管理器
2. 全局注册缓存后端
3. 定于需要缓存的 value class
4. 定义缓存 key (Node):包括缓存后端和缓存过期时间
5. 使用缓存
"""
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from datetime import timedelta

from pydantic import BaseModel
from redis import Redis
from rich import traceback

from app.core.cache import Manager, Node
from app.core.cache.storage import RedisStorage

# dev: 开启 rich traceback
traceback.install(show_locals=True)

# 1. 初始化缓存管理器
cache = Manager()

# 2. 注册缓存后端
r = Redis.from_url("redis://:123456@localhost:6379/0")
cache.register_storage("redis", RedisStorage(r))


# 3. 定义缓存 value
class UserInfo(BaseModel):
    id: int
    name: str
    age: int | None = None


# 4. 定义缓存 key (Node)
class UserNode(Node[UserInfo]):
    storages = [  # noqa: RUF012
        {"storage": "redis", "ttl": timedelta(seconds=120)},
    ]

    def __init__(self, user_id: int) -> None:
        self.user_id = user_id

    def key(self) -> str:
        return str(self.user_id)

    def load(self) -> UserInfo:
        return UserInfo(id=self.user_id, name="test", age=18)


if __name__ == "__main__":
    node = UserNode(1)
    # 5. 使用缓存
    cache.get(node)
    with ThreadPoolExecutor(max_workers=100) as executor:
        tasks: list[Future[UserInfo | None]] = []
        for _ in range(100):
            task = executor.submit(cache.get, node)
            tasks.append(task)
        for task in as_completed(tasks):
            result = task.result()
            print(result)  # noqa: T201
    cache.remove(node, "redis")
