import asyncio
import json
import logging
import signal
from typing import Any, TypeVar

import websockets
from celery.result import AsyncResult
from celery.signals import task_postrun
from pydantic import BaseModel, ValidationError
from websockets.server import WebSocketServerProtocol, serve

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

R = TypeVar("R", bound=BaseModel)

CLIENTS: set[WebSocketServerProtocol] = set()
USERS = {"123": "xiao"}

ROOMS: dict[str, "Room"] = {}


class Room:
    id: str

    def __init__(self, id: str) -> None:
        self.id = id
        self.clients: set[WebSocketServerProtocol] = set()

    def add(self, client: WebSocketServerProtocol) -> None:
        self.clients.add(client)

    def remove(self, client: WebSocketServerProtocol) -> None:
        self.clients.remove(client)

    def broadcast(self, message: str) -> None:
        websockets.broadcast(self.clients, message)  # type: ignore


class Event(BaseModel):
    """强制使用该结构传递数据."""

    type: str
    data: str | dict[str, Any]


class TokenEvent(Event):
    type: str = "token"
    data: str


def get_user(token: str) -> str | None:
    """获得当前用户."""
    return USERS.get(token)


async def parse_event(websocket: WebSocketServerProtocol, model: type[R]) -> R | None:
    """数据校验."""
    data = await websocket.recv()
    try:
        return model.parse_raw(data)
    except ValidationError as e:
        logging.error(e)
        await websocket.send(json.dumps({"type": "error", "data": "parameter error"}))


async def handler(websocket: WebSocketServerProtocol) -> None:
    logging.log(websocket.remote_address, websocket.path)
    data = await parse_event(websocket, TokenEvent)
    if data is None or data.type != "token":
        # 首次进入必须传递 token
        return
    # 判断 user
    user = await asyncio.to_thread(get_user, data.data)  # 将同步函数转换为异步函数
    if user is None:
        await websocket.close(1011, "authentication failed")
        return
    logging.info(user)

    # 加入客户端列表
    CLIENTS.add(websocket)
    websockets.broadcast(CLIENTS, f"client {len(CLIENTS)}")  # type: ignore
    try:
        async for message in websocket:
            # 之后不再验证 token
            try:
                data = Event.parse_raw(message)
                if data.type == "join" and isinstance(data.data, str):
                    # data.data 必须是 str ,否则会报错
                    await join(data.data, websocket)
                # TODO 处理其他事件
            except ValidationError as e:
                logging.error(e)
                # 客户端需要处理错误后续操作,关闭连接还是重试
                await websocket.send(json.dumps({"type": "error", "data": "参数必须是 json 格式字节"}))
    finally:
        CLIENTS.remove(websocket)
        # TODO 还应该从房间中移除


async def broadcast(message: str) -> None:
    """向所有客户端广播消息."""
    websockets.broadcast(CLIENTS, message)  # type: ignore


def broadcast_room(id: str, message: str) -> None:
    """向指定房间广播消息."""
    room = ROOMS.get(id)
    if room is None:
        return
    room.broadcast(message)


async def join(id: str, websocket: WebSocketServerProtocol) -> None:
    """根据 id 创建或查找房间,并加入."""
    room = ROOMS.setdefault(id, Room(id))
    room.add(websocket)


async def main(port: int = 8765) -> None:
    # set the stop condition when receiving SIGINT or SIGTERM.
    loop = asyncio.get_running_loop()
    stop = loop.create_future()
    loop.add_signal_handler(signal.SIGINT, stop.set_result, None)
    loop.add_signal_handler(signal.SIGTERM, stop.set_result, None)

    async with serve(
        handler,
        "localhost",
        port,
        reuse_port=True,
        open_timeout=10,  # 10 秒内没有完成握手,关闭连接(1011)
        ping_interval=20,  # 20 秒 ping 一次, None 禁用
        ping_timeout=20,  # 20 秒内没有收到 pong,关闭连接(1011)
        close_timeout=None,  # 服务器关闭连接前等待的时间,None 禁用
        max_size=2**20,  # 传递的最大数据量 1MB(1009)
        max_queue=2**5,  # 最大等待队列 32(1012)
        read_limit=2**16,  # 读取的最大数据量 64KB(1009)
        write_limit=2**16,  # 发送的最大数据量 64KB(1009)
    ):
        logging.info("Running server on port %s", port)
        await stop
        logging.info("exit")


def update_celery_task_status(task_id: str) -> None:
    """更新 celery 任务状态, 通过 websocket 通知客户端."""
    task = AsyncResult(task_id)  # type: ignore
    state = task.state

    if state == "FAILURE":
        error = str(task.result)  # type: ignore
        response = {
            "state": state,
            "error": error,
        }
    else:
        response = {
            "state": state,
        }
    broadcast_room(task_id, json.dumps(response))


@task_postrun.connect  # type: ignore
def task_postrun_handler(task_id, **kwargs):  # type: ignore # noqa
    """Celery 任务执行完成后,更新任务状态."""
    update_celery_task_status(task_id)  # type: ignore


if __name__ == "__main__":
    asyncio.run(main())
