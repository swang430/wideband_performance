import asyncio
from typing import List

class LogManager:
    """
    管理 WebSocket 日志广播。
    """
    def __init__(self):
        self.active_connections: List[asyncio.Queue] = []

    async def connect(self) -> asyncio.Queue:
        queue = asyncio.Queue()
        self.active_connections.append(queue)
        return queue

    def disconnect(self, queue: asyncio.Queue):
        if queue in self.active_connections:
            self.active_connections.remove(queue)

    async def broadcast(self, message: str):
        for queue in self.active_connections:
            await queue.put(message)

    def sync_broadcast(self, message: str):
        """
        供同步代码调用的广播方法 (fire-and-forget)。
        """
        try:
            # print(f"[DEBUG] LogManager broadcasting to {len(self.active_connections)} clients: {message}")
            loop = asyncio.get_running_loop()
            loop.create_task(self.broadcast(message))
        except RuntimeError as e:
            print(f"[DEBUG] LogManager Failed: No running loop. {e}")
        except Exception as e:
            print(f"[DEBUG] LogManager Failed: {e}")

manager = LogManager()
