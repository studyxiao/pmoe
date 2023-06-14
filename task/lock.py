"""使用 redis 实现分布式锁.

充分考虑:
1. 互斥性:同一时刻只有一个客户端能够持有锁,使用 set nx 命令,并考虑重试机制
2. 安全性:避免死锁,设置锁的过期时间,并考虑续约
3. 对称性:锁的持有者和释放者是同一个客户端,锁的值对应客户端唯一标识,并使用 lua 脚本保证原子性
4. 可靠性:服务端分布式部署,使用 redis 集群,使用 lua 脚本保证原子性. TODO
"""
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import timedelta
from types import TracebackType
from typing import Self

import redis


class ServerError(Exception):
    """服务或网络异常."""


class LockNotHoldError(Exception):
    """未持有锁."""


class RedisLockError(Exception):
    """加锁失败."""


@dataclass
class Lock:
    """redis 分布式锁."""

    key: str
    value: str = field(default_factory=lambda: str(uuid.uuid4()))
    expiration: timedelta = timedelta(seconds=60)
    redis_client: redis.Redis | None = None

    def __post_init__(self) -> None:
        if self.redis_client is None:
            raise ValueError("redis_client 不能为空")

    def acquire(self, expiration: timedelta | None = None) -> Self:
        if expiration is not None:
            self.expiration = expiration
        try:
            success = self.redis_client.set(self.key, self.value, nx=True, ex=self.expiration)
        except redis.exceptions.RedisError as e:
            # 网络问题或 redis 服务异常
            raise ServerError() from e
        if not success:
            # 未抢到锁
            raise RedisLockError()
        return self

    def release(self) -> bool:
        release_lock_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
        """
        try:
            res = self.redis_client.eval(release_lock_script, 1, self.key, self.value)
        except redis.exceptions.RedisError as e:
            # 网络问题或 redis 服务异常
            raise ServerError() from e
        if res == 0:
            # 未持有锁,所以不能解锁
            raise LockNotHoldError()
        return True

    def __enter__(self) -> Self:
        return self.acquire()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.release()


@dataclass
class RenewLock:
    """续约锁."""

    key: str
    value: str = field(default_factory=lambda: str(uuid.uuid4()))
    expiration: timedelta = timedelta(seconds=60)
    redis_client: redis.Redis | None = None
    _lock: Lock = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if self.redis_client is None:
            raise ValueError("redis_client must be provided")
        self.renew_thread = None
        # 用于停止续约线程
        self.stop_renewing = threading.Event()
        self._lock = Lock(self.key, self.value, self.expiration, self.redis_client)

    def renew_lock(self, expiration: timedelta | None = None) -> bool:
        """向redis续约锁,返回是否续约成功."""
        expiration = expiration or self.expiration
        renew_lock_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("expire", KEYS[1], ARGV[2])
            else
                return 0
            end
        """
        try:
            res = self.redis_client.eval(
                renew_lock_script,
                1,
                self.key,
                self.value,
                int(expiration.total_seconds()),
            )
        except redis.exceptions.RedisError as e:
            raise ServerError() from e
        if res == 0:
            raise LockNotHoldError()
        return True

    def acquire_with_retry(
        self,
        retry_interval: float,
        retry_times: int,
        expiration: timedelta | None = None,
    ) -> bool:
        """重试获取锁."""
        expiration = expiration or self.expiration
        for _ in range(retry_times):
            try:
                success = self._lock.acquire(expiration)
            except RedisLockError:
                time.sleep(retry_interval)
            else:
                return success
        return False

    def acquire_with_renew(self, expiration: timedelta | None = None) -> bool:
        """获取锁并自动续约."""
        try:
            if not self._lock.acquire(expiration):
                # 加锁失败
                return False
        except RedisLockError:
            # 加锁失败
            return False

        # 已经获取锁,开始一个后台线程来自动续约
        self.renew_thread = threading.Thread(target=self._renew_lock_task)
        # 设置为守护线程,主线程退出后自动退出
        self.renew_thread.daemon = True
        self.renew_thread.start()

        return True

    def release(self) -> bool:
        """释放锁并停止续约."""
        self.stop_renewing.set()
        if self.renew_thread is not None:
            self.renew_thread.join()
            self.renew_thread = None
        return self._lock.release()

    def _renew_lock_task(self) -> None:
        """Background thread to renew the lock periodically."""
        while not self.stop_renewing.is_set():
            # 经过过期时间的一半后续约
            time.sleep(self.expiration.total_seconds() / 2)
            try:
                # 重新判断是否需要续约
                if not self.stop_renewing.is_set():
                    self.renew_lock()
            except redis.exceptions.RedisError:
                # TODO 续约失败,需要处理
                break

    def __enter__(self) -> Self:
        if self.acquire_with_renew():
            return self
        raise RedisLockError("get lock failed")

    def __exit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None
    ) -> None:
        self.release()


if __name__ == "__main__":
    import logging

    from rich.logging import RichHandler

    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        datefmt="[%X]",
        handlers=[
            RichHandler(
                rich_tracebacks=True,
                markup=True,
            )
        ],
    )

    log = logging.getLogger("rich")

    redis_client = redis.Redis.from_url("redis://:123456@localhost:6379/0")

    test_type = 2  # 1: 普通锁 2: 续约锁
    if test_type == 1:
        # 普通锁
        lock = Lock("test", redis_client=redis_client)
        try:
            with lock:
                log.info("get lock")
                time.sleep(20)
                log.info("release lock")
        except RedisLockError:
            log.info("preempt lock failed")
    elif test_type == 2:
        # 续约锁
        # 设置过期时间为 10s
        renew_lock = RenewLock("renew_test", expiration=timedelta(seconds=10), redis_client=redis_client)
        try:
            with renew_lock:
                log.info("get lock")
                # 设置任务执行时间为 20s,超过过期时间10s,锁会被释放
                # 测试是否会自动续约
                time.sleep(20)
                log.info("release lock")
        except RedisLockError:
            log.info("get lock failed")
